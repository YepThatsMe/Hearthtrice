import sys
sys.path = [p for p in sys.path if not (p.endswith("utils") or p.endswith("utils/") or p.endswith("utils\\"))]

import hashlib
import json
import os
import time
from io import BytesIO
from typing import Optional

import psycopg2
import requests
from PIL import Image

DB_TABLE = "cards_std"
DB_NAME = "hearth_db"
DB_PORT = "5432"
API_URL = "https://hearthstone.wiki.gg/api.php"
USER_AGENT = "HearthtriceCardBot/0.1 (repair duplicate images)"
REQUEST_DELAY_SEC = 0.35


def connect_db():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if root not in sys.path:
        sys.path.insert(0, root)
    import credentials

    return psycopg2.connect(
        dbname=DB_NAME,
        user=credentials.USER,
        password=credentials.PASSWORD,
        host=credentials.IP,
        port=getattr(credentials, "DB_PORT", DB_PORT),
        connect_timeout=10,
    )


def eq(a, b):
    if a is None or a == "":
        a = None
    if b is None or b == "":
        b = None
    if a is None and b is None:
        return True
    try:
        return int(a) == int(b)
    except (TypeError, ValueError):
        return a == b


def match_meta(db_row, meta: dict) -> bool:
    return (
        db_row[1] == meta.get("name")
        and eq(db_row[2], meta.get("cardtype"))
        and bool(db_row[3]) == bool(meta.get("istoken"))
        and eq(db_row[4], meta.get("manacost"))
        and eq(db_row[5], meta.get("attack"))
        and eq(db_row[6], meta.get("health"))
    )


class WikiClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def _get(self, params: dict) -> dict:
        time.sleep(REQUEST_DELAY_SEC)
        response = self.session.get(API_URL, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            raise RuntimeError(data["error"])
        return data

    def cargo_by_dbf(self, dbf_id: int) -> Optional[dict]:
        data = self._get(
            {
                "action": "cargoquery",
                "tables": "CardTag,DerivedCard,Card",
                "fields": "CardTag.dbfId,Card.name,Card.id,DerivedCard.img,DerivedCard.imgFullArt,DerivedCard.imgArt",
                "join_on": "CardTag.dbfId=DerivedCard.dbfId,CardTag.dbfId=Card.dbfId",
                "where": f"CardTag.dbfId={int(dbf_id)}",
                "limit": 1,
                "format": "json",
            }
        )
        rows = data.get("cargoquery") or []
        if not rows:
            return None
        return rows[0].get("title", {})

    def resolve_image_url(self, filename: str) -> Optional[str]:
        if not filename:
            return None
        title = filename if filename.startswith("File:") else f"File:{filename}"
        data = self._get(
            {
                "action": "query",
                "titles": title,
                "prop": "imageinfo",
                "iiprop": "url",
                "format": "json",
            }
        )
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            if "missing" in page:
                continue
            infos = page.get("imageinfo") or []
            if infos:
                return infos[0].get("url")
        return None

    def download_bytes(self, url: str) -> Optional[bytes]:
        time.sleep(REQUEST_DELAY_SEC)
        response = self.session.get(url, timeout=60)
        if response.status_code != 200:
            print(f"download failed {response.status_code}: {url}")
            return None
        return response.content


def resize_card_png(raw: bytes) -> bytes:
    with Image.open(BytesIO(raw)) as img:
        img_resized = img.resize((769, 1107), Image.LANCZOS)
        out = BytesIO()
        img_resized.save(out, format="PNG")
        return out.getvalue()


def art_to_png(raw: bytes) -> bytes:
    with Image.open(BytesIO(raw)) as img:
        if img.mode in ("P", "LA"):
            img = img.convert("RGBA")
        elif img.mode == "CMYK":
            img = img.convert("RGB")
        out = BytesIO()
        img.save(out, format="PNG")
        return out.getvalue()


def calculate_hash(fields: dict) -> str:
    data = "".join(sorted(f"{k}={fields[k]}" for k in fields if k != "hash")).encode("utf-8")
    return hashlib.md5(data).hexdigest()


def invalidate_local_cache(ids):
    cache_dir = os.path.join(os.getenv("LOCALAPPDATA", ""), "Hearthtrice", "cache_std")
    index_path = os.path.join(cache_dir, "index.json")
    images_dir = os.path.join(cache_dir, "images")
    if not os.path.isfile(index_path):
        print("Local cache_std index not found, skip invalidate")
        return
    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)
    changed = False
    for card_id in ids:
        key = str(card_id)
        item = index.pop(key, None)
        if item is not None:
            changed = True
        img = os.path.join(images_dir, f"{card_id}.png")
        if os.path.isfile(img):
            os.remove(img)
        if item:
            legacy = os.path.join(images_dir, f"{item.get('name', '')}.png")
            if os.path.isfile(legacy):
                os.remove(legacy)
    if changed:
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=4, ensure_ascii=False)
        print(f"Invalidated {len(ids)} ids in local cache_std")


def main():
    meta_path = os.path.join("src", "assets", "std", "std_metadata.json")
    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    conn = connect_db()
    cur = conn.cursor()
    cur.execute(
        f"""
        SELECT name
        FROM {DB_TABLE}
        GROUP BY name
        HAVING COUNT(*) > 1
        ORDER BY name
        """
    )
    dup_names = [r[0] for r in cur.fetchall()]
    print(f"Duplicate names in DB: {len(dup_names)}")

    wiki = WikiClient()
    fixed_ids = []
    failed = 0

    for name in dup_names:
        cur.execute(
            f"""
            SELECT id, name, cardtype, istoken, manacost, attack, health, description, rarity, classtype, tribe, tokens, comment, command
            FROM {DB_TABLE}
            WHERE name = %s
            ORDER BY id
            """,
            (name,),
        )
        rows = cur.fetchall()
        metas = [m for m in metadata if m.get("name") == name]
        print(f"\n{name}: db={len(rows)} meta={len(metas)}")

        for row in rows:
            db_id = row[0]
            matched = next((m for m in metas if match_meta(row, m)), None)
            if not matched:
                print(f"  id={db_id}: no metadata match")
                failed += 1
                continue

            dbf_id = matched.get("dbfId")
            wiki_row = wiki.cargo_by_dbf(dbf_id)
            if not wiki_row:
                print(f"  id={db_id} dbfId={dbf_id}: wiki row not found")
                failed += 1
                continue

            img_name = wiki_row.get("img") or ""
            url = wiki.resolve_image_url(img_name)
            if not url:
                print(f"  id={db_id}: no image url ({img_name})")
                failed += 1
                continue
            raw = wiki.download_bytes(url)
            if not raw:
                failed += 1
                continue
            card_image = resize_card_png(raw)

            picture = None
            art_name = wiki_row.get("imgFullArt") or wiki_row.get("imgArt") or ""
            if art_name:
                art_url = wiki.resolve_image_url(art_name)
                if art_url:
                    art_raw = wiki.download_bytes(art_url)
                    if art_raw:
                        picture = art_to_png(art_raw)

            new_hash = calculate_hash(
                {
                    "name": row[1],
                    "description": row[7],
                    "manacost": row[4],
                    "rarity": row[8],
                    "cardtype": row[2],
                    "classtype": row[9],
                    "attack": row[5],
                    "health": row[6],
                    "tribe": row[10],
                    "istoken": row[3],
                    "card_image_len": len(card_image),
                    "picture_len": len(picture) if picture else 0,
                }
            )

            cur.execute(
                f"""
                UPDATE {DB_TABLE}
                SET card_image = %s,
                    picture = COALESCE(%s, picture),
                    hash = %s
                WHERE id = %s
                """,
                (
                    psycopg2.Binary(card_image),
                    psycopg2.Binary(picture) if picture else None,
                    new_hash,
                    db_id,
                ),
            )
            conn.commit()
            fixed_ids.append(db_id)
            print(f"  fixed id={db_id} dbfId={dbf_id} img={img_name} md5={hashlib.md5(card_image).hexdigest()}")

    cur.close()
    conn.close()

    if fixed_ids:
        invalidate_local_cache(fixed_ids)

    print(f"\nDone: fixed={len(fixed_ids)}, failed={failed}")
    print("Next: open app and Refresh — only fixed cards will redownload to cache_std.")


if __name__ == "__main__":
    main()
