import sys
sys.path = [p for p in sys.path if not (p.endswith("utils") or p.endswith("utils/") or p.endswith("utils\\"))]

import hashlib
import html
import json
import os
import re
import time
from io import BytesIO
from typing import Iterable, List, Optional, Set

import psycopg2
import requests
from PIL import Image

DOWNLOAD = 1
UPLOAD_DB = 1

DB_TABLE = "cards_std"
DB_NAME = "hearth_db"
DB_PORT = "5432"

API_URL = "https://hearthstone.wiki.gg/api.php"
IMG_BASE = "https://hearthstone.wiki.gg/images/"
USER_AGENT = "HearthtriceCardBot/0.1 (std cards import; local)"
REQUEST_DELAY_SEC = 0.35
CARGO_PAGE_SIZE = 100

CLASSIC_SET_IDS = frozenset({2, 3, 4, 1635, 1637, 1810})
SKIP_SET_IDS = frozenset({1414, 1463, 1578, 1776})

SET_ID_TO_NAME = {
    12: "Naxxramas",
    13: "Goblins vs Gnomes",
    14: "Blackrock Mountain",
    15: "The Grand Tournament",
    20: "League of Explorers",
    21: "Whispers of the Old Gods",
    23: "One Night in Karazhan",
    25: "Mean Streets of Gadgetzan",
    27: "Journey to Un'Goro",
    1001: "Knights of the Frozen Throne",
    1004: "Kobolds & Catacombs",
    1125: "The Witchwood",
}

EXPANSION_SET_IDS = (
    12, 13, 14, 15, 20, 21, 23, 25, 27,
    1001, 1004, 1125,
)

DOWNLOAD_SET_IDS = (13, 14,)

SET_NAME_ALIASES = {
    "BASIC": "Classic",
    "EXPERT1": "Classic",
    "LEGACY": "Classic",
    "HOF": "Classic",
    "2": "Classic",
    "3": "Classic",
    "4": "Classic",
    "1635": "Classic",
    "1637": "Classic",
    "1810": "Classic",
    "NAXX": "Naxxramas",
    "12": "Naxxramas",
    "GVG": "Goblins vs Gnomes",
    "13": "Goblins vs Gnomes",
    "BRM": "Blackrock Mountain",
    "14": "Blackrock Mountain",
    "TGT": "The Grand Tournament",
    "15": "The Grand Tournament",
    "LOE": "League of Explorers",
    "20": "League of Explorers",
    "OG": "Whispers of the Old Gods",
    "WOG": "Whispers of the Old Gods",
    "21": "Whispers of the Old Gods",
    "KARA": "One Night in Karazhan",
    "23": "One Night in Karazhan",
    "GANGS": "Mean Streets of Gadgetzan",
    "MSG": "Mean Streets of Gadgetzan",
    "25": "Mean Streets of Gadgetzan",
    "UNGORO": "Journey to Un'Goro",
    "UNG": "Journey to Un'Goro",
    "27": "Journey to Un'Goro",
    "ICECROWN": "Knights of the Frozen Throne",
    "KFT": "Knights of the Frozen Throne",
    "1001": "Knights of the Frozen Throne",
    "LOOTAPALOOZA": "Kobolds & Catacombs",
    "LOOT": "Kobolds & Catacombs",
    "1004": "Kobolds & Catacombs",
    "GILNEAS": "The Witchwood",
    "WITCHWOOD": "The Witchwood",
    "1125": "The Witchwood",
}

WIKI_RARITY_TO_APP = {
    1: 2,
    2: 1,
    3: 3,
    4: 4,
    5: 5,
}

WIKI_TYPE_TO_APP = {
    3: 4,
    4: 1,
    5: 2,
    7: 3,
}

WIKI_CLASS_TO_APP = {
    2: 6,
    3: 3,
    4: 2,
    5: 4,
    6: 8,
    7: 7,
    8: 10,
    9: 9,
    10: 5,
    12: 1,
    14: 11,
}

SKIP_TYPE_IDS = {6}


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
            raise RuntimeError(f"Wiki API error: {data['error']}")
        return data

    def cargo_query(
        self,
        tables: str,
        fields: str,
        where: Optional[str] = None,
        join_on: Optional[str] = None,
        order_by: Optional[str] = None,
        limit: int = CARGO_PAGE_SIZE,
        offset: int = 0,
    ) -> List[dict]:
        params = {
            "action": "cargoquery",
            "tables": tables,
            "fields": fields,
            "limit": limit,
            "offset": offset,
            "format": "json",
        }
        if where:
            params["where"] = where
        if join_on:
            params["join_on"] = join_on
        if order_by:
            params["order_by"] = order_by
        data = self._get(params)
        rows = []
        for item in data.get("cargoquery", []):
            rows.append(item.get("title", {}))
        return rows

    def cargo_query_all(self, **kwargs) -> List[dict]:
        rows = []
        offset = 0
        page_size = kwargs.pop("limit", CARGO_PAGE_SIZE)
        while True:
            page = self.cargo_query(limit=page_size, offset=offset, **kwargs)
            rows.extend(page)
            if len(page) < page_size:
                break
            offset += page_size
        return rows

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
            print(f"Image download failed {response.status_code}: {url}")
            return None
        return response.content


def clean_card_text(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    text = html.unescape(text)
    text = text.replace("<b>", "").replace("</b>", "")
    text = text.replace("<i>", "").replace("</i>", "")
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("\\n", "\n")
    return text.strip()


def to_int(value, default=None):
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_related_ids(raw: Optional[str]) -> List[int]:
    if not raw:
        return []
    ids = []
    for part in re.split(r"[,;\|\&\s]+", str(raw)):
        if not part:
            continue
        value = to_int(part)
        if value is not None:
            ids.append(value)
    return ids


def map_rarity(rarity_id, is_collectible: bool) -> int:
    rid = to_int(rarity_id)
    if rid is None:
        return 1 if not is_collectible else 1
    return WIKI_RARITY_TO_APP.get(rid, 1)


def map_cardtype(type_id) -> Optional[int]:
    tid = to_int(type_id)
    if tid is None or tid in SKIP_TYPE_IDS:
        return None
    return WIKI_TYPE_TO_APP.get(tid)


def map_classtype(class_id) -> Optional[int]:
    cid = to_int(class_id)
    if cid is None:
        return 1
    if cid not in WIKI_CLASS_TO_APP:
        return None
    return WIKI_CLASS_TO_APP[cid]


def map_set_name(set_id) -> Optional[str]:
    sid = to_int(set_id)
    if sid is None:
        return None
    if sid in SKIP_SET_IDS:
        return None
    if sid in CLASSIC_SET_IDS:
        return "Classic"
    name = SET_ID_TO_NAME.get(sid)
    if name:
        return name
    return SET_NAME_ALIASES.get(str(sid), str(sid))


def normalize_set_name(raw) -> Optional[str]:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    if text in SET_NAME_ALIASES:
        return SET_NAME_ALIASES[text]
    sid = to_int(text)
    if sid is not None:
        return map_set_name(sid)
    return text


def safe_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "_", name)


def card_identity_key(
    name,
    description,
    manacost,
    rarity,
    cardtype,
    classtype,
    attack,
    health,
    tribe,
    istoken,
    set_name,
) -> tuple:
    return (
        (name or "").strip(),
        (description or "").strip(),
        to_int(manacost),
        to_int(rarity),
        to_int(cardtype),
        to_int(classtype),
        to_int(attack),
        to_int(health),
        (tribe or "").strip() if tribe else "",
        1 if istoken in (True, 1, "1", "true", "True") else 0,
        (set_name or "").strip(),
    )


def merge_metadata(meta_path: str, new_cards: List[dict]) -> List[dict]:
    existing = []
    if os.path.isfile(meta_path):
        try:
            existing = load_metadata(meta_path)
        except Exception as e:
            print(f"Warning: failed to load existing metadata: {e}")
            existing = []

    by_dbf = {}
    without_dbf = []
    for card in existing:
        dbf_id = to_int(card.get("dbfId"))
        if dbf_id is None:
            without_dbf.append(card)
        else:
            by_dbf[dbf_id] = card

    for card in new_cards:
        dbf_id = to_int(card.get("dbfId"))
        if dbf_id is None:
            without_dbf.append(card)
        else:
            by_dbf[dbf_id] = card

    merged = without_dbf + [by_dbf[k] for k in sorted(by_dbf.keys())]
    return merged


def save_card_image(name: str, card_image: bytes, img_path: str, unique_key=None):
    safe_name = safe_filename(name)
    if unique_key is not None:
        safe_name = f"{safe_name}__{unique_key}"
    out_path = os.path.join(img_path, safe_name + ".png")
    with Image.open(BytesIO(card_image)) as img:
        img_resized = img.resize((769, 1107), Image.LANCZOS)
        img_resized.save(out_path)
    return safe_name


def save_art_image(safe_name: str, art_image: bytes, arts_path: str) -> Optional[str]:
    out_name = f"{safe_name}.png"
    with Image.open(BytesIO(art_image)) as img:
        if img.mode in ("P", "LA"):
            img = img.convert("RGBA")
        elif img.mode == "CMYK":
            img = img.convert("RGB")
        img.save(os.path.join(arts_path, out_name), format="PNG")
    return out_name


class StandardCardsImporter:
    FIELDS = (
        "CardTag.dbfId,"
        "Card.name,"
        "Card.id,"
        "CardTag.cost,"
        "CardTag.attack,"
        "CardTag.health,"
        "CardTag.durability,"
        "CardTag.armor,"
        "CardTag.rarityId,"
        "CardTag.typeId,"
        "CardTag.classId,"
        "CardTag.raceId,"
        "CardTag.isCollectible,"
        "DerivedCard.text,"
        "DerivedCard.img,"
        "DerivedCard.imgArt,"
        "DerivedCard.imgFullArt,"
        "DerivedCard.relatedCardDbfIds,"
        "DerivedCard.choiceCardDbfIds,"
        "DerivedCard.setId,"
        "DerivedCard.minionTypeStrings,"
        "DerivedCard.formats,"
        "DerivedCard.isRemoved,"
        "DerivedCard._pageName"
    )
    JOIN_ON = "CardTag.dbfId=DerivedCard.dbfId,CardTag.dbfId=Card.dbfId"

    def __init__(self, client: WikiClient, img_path: str, arts_path: str, limit: Optional[int] = None):
        self.client = client
        self.img_path = img_path
        self.arts_path = arts_path
        self.limit = limit
        self.warnings: List[str] = []

    def fetch_rows_by_dbf_ids(self, dbf_ids: Iterable[int]) -> List[dict]:
        ids = sorted({int(x) for x in dbf_ids})
        if not ids:
            return []
        rows = []
        chunk_size = 40
        for i in range(0, len(ids), chunk_size):
            chunk = ids[i:i + chunk_size]
            where = "CardTag.dbfId IN (" + ",".join(str(x) for x in chunk) + ")"
            rows.extend(
                self.client.cargo_query_all(
                    tables="CardTag,DerivedCard,Card",
                    fields=self.FIELDS,
                    join_on=self.JOIN_ON,
                    where=where,
                    order_by="CardTag.dbfId",
                )
            )
        return rows

    def fetch_collectible_from_sets(self, set_ids: Iterable[int], limit: Optional[int] = None) -> List[dict]:
        set_list = ",".join(str(x) for x in set_ids)
        where = (
            f"DerivedCard.setId IN ({set_list}) "
            "AND CardTag.isCollectible=1 "
            "AND (DerivedCard.isRemoved IS NULL OR DerivedCard.isRemoved='' OR DerivedCard.isRemoved=0)"
        )
        if limit is None:
            return self.client.cargo_query_all(
                tables="CardTag,DerivedCard,Card",
                fields=self.FIELDS,
                join_on=self.JOIN_ON,
                where=where,
                order_by="CardTag.dbfId",
            )
        return self.client.cargo_query(
            tables="CardTag,DerivedCard,Card",
            fields=self.FIELDS,
            join_on=self.JOIN_ON,
            where=where,
            order_by="CardTag.dbfId",
            limit=limit,
        )

    def fetch_collectible_by_names(self, names: List[str], set_ids: Iterable[int]) -> List[dict]:
        if not names:
            return []
        set_list = ",".join(str(x) for x in set_ids)
        quoted = ",".join("\"" + n.replace("\"", "\\\"") + "\"" for n in names)
        where = (
            f"Card.name IN ({quoted}) "
            f"AND DerivedCard.setId IN ({set_list}) "
            "AND CardTag.isCollectible=1"
        )
        return self.client.cargo_query_all(
            tables="CardTag,DerivedCard,Card",
            fields=self.FIELDS,
            join_on=self.JOIN_ON,
            where=where,
            order_by="CardTag.dbfId",
        )

    def collect_related_token_ids(self, collectible_rows: List[dict]) -> Set[int]:
        known = {to_int(r.get("dbfId")) for r in collectible_rows}
        related: Set[int] = set()
        for row in collectible_rows:
            for dbf_id in parse_related_ids(row.get("relatedCardDbfIds")):
                if dbf_id not in known:
                    related.add(dbf_id)
        return related

    def normalize_row(self, row: dict) -> Optional[dict]:
        name = row.get("name") or row.get("_pageName")
        dbf_id = to_int(row.get("dbfId"))
        if not name or dbf_id is None:
            self.warnings.append(f"Skip dbfId={row.get('dbfId')}: missing name")
            return None

        set_id = to_int(row.get("setId"))
        if set_id in SKIP_SET_IDS:
            self.warnings.append(f"Skip {name} ({dbf_id}): ignored setId={set_id}")
            return None

        cardtype = map_cardtype(row.get("typeId"))
        if cardtype is None:
            self.warnings.append(f"Skip {name} ({dbf_id}): unsupported/skipped typeId={row.get('typeId')}")
            return None

        classtype = map_classtype(row.get("classId"))
        if classtype is None:
            self.warnings.append(f"Skip {name} ({dbf_id}): unsupported classId={row.get('classId')}")
            return None

        is_collectible = to_int(row.get("isCollectible"), 0) == 1
        attack = to_int(row.get("attack"))
        health = to_int(row.get("health"))
        durability = to_int(row.get("durability"))
        armor = to_int(row.get("armor"))

        if cardtype == 3 and durability is not None:
            health = durability
        if cardtype == 4 and health is None and armor is not None:
            health = armor

        tribe = row.get("minionTypeStrings") or None
        if tribe == "":
            tribe = None

        related_ids = parse_related_ids(row.get("relatedCardDbfIds"))
        choice_ids = parse_related_ids(row.get("choiceCardDbfIds"))

        return {
            "dbfId": dbf_id,
            "cardId": row.get("id"),
            "name": name,
            "description": clean_card_text(row.get("text")),
            "manacost": to_int(row.get("cost"), 0),
            "rarity": map_rarity(row.get("rarityId"), is_collectible),
            "cardtype": cardtype,
            "classtype": classtype,
            "attack": attack,
            "health": health,
            "tribe": tribe,
            "istoken": 0 if is_collectible else 1,
            "related_dbf_ids": related_ids,
            "choice_dbf_ids": choice_ids,
            "setId": set_id,
            "formats": row.get("formats") or "",
            "img": row.get("img") or "",
            "img_art": row.get("imgFullArt") or row.get("imgArt") or "",
            "page": row.get("_pageName") or name,
            "raw_rarityId": to_int(row.get("rarityId")),
            "raw_typeId": to_int(row.get("typeId")),
            "raw_classId": to_int(row.get("classId")),
            "is_collectible": is_collectible,
        }

    def download_named_image(self, img_name: str, card_name: str, kind: str) -> Optional[bytes]:
        if not img_name:
            return None
        url = self.client.resolve_image_url(img_name)
        if not url:
            url = IMG_BASE + img_name
        data = self.client.download_bytes(url)
        if not data:
            alt = img_name[0].upper() + img_name[1:]
            if alt != img_name:
                url = self.client.resolve_image_url(alt)
                if url:
                    data = self.client.download_bytes(url)
        if not data:
            self.warnings.append(f"{card_name}: failed to download {kind} ({img_name})")
        return data

    def download_image(self, card: dict) -> Optional[bytes]:
        img_name = card.get("img")
        if not img_name:
            self.warnings.append(f"{card['name']}: no image filename")
            return None
        return self.download_named_image(img_name, card["name"], "card image")

    def download_art(self, card: dict) -> Optional[bytes]:
        return self.download_named_image(card.get("img_art") or "", card["name"], "art")

    def run(self, set_ids: Iterable[int] = DOWNLOAD_SET_IDS, prefer_names: Optional[List[str]] = None) -> List[dict]:
        os.makedirs(self.img_path, exist_ok=True)
        os.makedirs(self.arts_path, exist_ok=True)
        prefer_names = prefer_names or []
        set_ids = [int(x) for x in set_ids if to_int(x) not in SKIP_SET_IDS]

        print(f"Fetching collectible cards from setIds={list(set_ids)} limit={self.limit}")
        preferred_rows = self.fetch_collectible_by_names(prefer_names, set_ids) if prefer_names else []
        remaining = None if self.limit is None else max(self.limit - len(preferred_rows), 0)
        other_rows = []
        if remaining is None or remaining > 0:
            other_rows = self.fetch_collectible_from_sets(
                set_ids,
                limit=None if remaining is None else remaining + len(preferred_rows),
            )

        preferred_ids = {to_int(r.get("dbfId")) for r in preferred_rows}
        collectible_rows = list(preferred_rows)
        for row in other_rows:
            dbf_id = to_int(row.get("dbfId"))
            if dbf_id in preferred_ids:
                continue
            collectible_rows.append(row)
            if self.limit is not None and len(collectible_rows) >= self.limit:
                break

        if self.limit is not None:
            collectible_rows = collectible_rows[: self.limit]

        print(f"Selected {len(collectible_rows)} collectible cards")
        for row in collectible_rows:
            print(f"  - {row.get('name')} (dbfId={row.get('dbfId')}, related={row.get('relatedCardDbfIds')})")

        token_ids = self.collect_related_token_ids(collectible_rows)
        print(f"Discovered related dbfIds (potential tokens): {sorted(token_ids)}")
        token_rows = self.fetch_rows_by_dbf_ids(token_ids) if token_ids else []
        print(f"Fetched {len(token_rows)} related card rows")

        all_rows = collectible_rows + token_rows
        seen_dbf: Set[int] = set()
        cards: List[dict] = []
        for row in all_rows:
            dbf_id = to_int(row.get("dbfId"))
            if dbf_id in seen_dbf:
                continue
            seen_dbf.add(dbf_id)
            normalized = self.normalize_row(row)
            if normalized:
                cards.append(normalized)

        dbf_to_index = {c["dbfId"]: i for i, c in enumerate(cards)}
        output = []
        skipped_existing = 0

        for i, card in enumerate(cards):
            safe_name = safe_filename(card["name"])
            if card.get("dbfId") is not None:
                safe_name = f"{safe_name}__{card['dbfId']}"
            img_file = os.path.join(self.img_path, safe_name + ".png")
            art_file = os.path.join(self.arts_path, safe_name + ".png")
            art_path = f"std/arts/{safe_name}.png" if os.path.isfile(art_file) else None

            if os.path.isfile(img_file):
                skipped_existing += 1
                print(f"Skip download #{i} {card['name']}: file exists")
                if not os.path.isfile(art_file):
                    art = self.download_art(card)
                    if art:
                        art_filename = save_art_image(safe_name, art, self.arts_path)
                        if art_filename:
                            art_path = f"std/arts/{art_filename}"
                            print(f"Saved art #{i} {card['name']} -> {art_filename}")
            else:
                image = self.download_image(card)
                if not image:
                    print(f"Skip #{i} {card['name']}: no image")
                    continue
                safe_name = save_card_image(card["name"], image, self.img_path, unique_key=card.get("dbfId"))
                art = self.download_art(card)
                if art:
                    art_filename = save_art_image(safe_name, art, self.arts_path)
                    if art_filename:
                        art_path = f"std/arts/{art_filename}"
                        print(f"Saved art #{i} {card['name']} -> {art_filename}")
                else:
                    print(f"No art #{i} {card['name']}")
                print(f"Saved #{i} {card['name']} collectible={not card['istoken']} related={card['related_dbf_ids']}")

            if not os.path.isfile(os.path.join(self.img_path, safe_name + ".png")):
                continue
            if art_path is None and os.path.isfile(art_file):
                art_path = f"std/arts/{safe_name}.png"

            related_local_ids = []
            for related_dbf in card["related_dbf_ids"]:
                if related_dbf in dbf_to_index:
                    related_local_ids.append(str(related_dbf))

            params_set = {
                "name": card["name"],
                "description": card["description"],
                "manacost": card["manacost"],
                "rarity": card["rarity"],
                "cardtype": card["cardtype"],
                "classtype": card["classtype"],
                "attack": card["attack"],
                "health": card["health"],
                "tribe": card["tribe"],
                "istoken": card["istoken"],
                "tokens": ",".join(related_local_ids) if related_local_ids else None,
                "dbfId": card["dbfId"],
                "cardId": card["cardId"],
                "setId": card["setId"],
                "set": map_set_name(card["setId"]),
                "formats": card["formats"],
                "card_image_path": f"std/img/{safe_name}.png",
                "art_image_path": art_path,
                "card_image": None,
            }
            output.append(params_set)

        meta_path = os.path.join(self.img_path, "..", "std_metadata.json")
        merged = merge_metadata(meta_path, output)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=4, ensure_ascii=False)

        report_path = os.path.join(self.img_path, "..", "std_import_report.json")
        report = {
            "set_ids": list(set_ids),
            "batch_saved": len(output),
            "batch_skipped_existing_files": skipped_existing,
            "merged_total": len(merged),
            "collectible_count": sum(1 for c in output if not c["istoken"]),
            "token_count": sum(1 for c in output if c["istoken"]),
            "warnings": self.warnings,
            "cards": [
                {
                    "name": c["name"],
                    "dbfId": c["dbfId"],
                    "istoken": c["istoken"],
                    "tokens": c["tokens"],
                    "set": c.get("set"),
                    "description": c["description"],
                    "manacost": c["manacost"],
                    "attack": c["attack"],
                    "health": c["health"],
                    "tribe": c["tribe"],
                    "rarity": c["rarity"],
                    "cardtype": c["cardtype"],
                    "classtype": c["classtype"],
                    "img": c["card_image_path"],
                    "art": c.get("art_image_path"),
                }
                for c in output
            ],
        }
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4, ensure_ascii=False)

        print(f"Wrote metadata: {meta_path} (merged total={len(merged)}, batch={len(output)}, reused files={skipped_existing})")
        print(f"Wrote report: {report_path}")
        if self.warnings:
            print("Warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")
        return output


def calculate_card_hash(fields: dict) -> str:
    data = "".join(sorted(f"{k}={fields[k]}" for k in fields if k != "hash")).encode("utf-8")
    return hashlib.md5(data).hexdigest()


def resolve_asset_path(std_root: str, relative_path: Optional[str]) -> Optional[str]:
    if not relative_path:
        return None
    if relative_path.startswith("std/"):
        relative_path = relative_path[len("std/"):]
    full = os.path.join(std_root, relative_path)
    return full if os.path.isfile(full) else None


def load_metadata(meta_path: str) -> List[dict]:
    with open(meta_path, "r", encoding="utf-8") as f:
        return json.load(f)


def connect_db():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if root not in sys.path:
        sys.path.insert(0, root)
    import credentials

    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=credentials.USER,
        password=credentials.PASSWORD,
        host=credentials.IP,
        port=getattr(credentials, "DB_PORT", DB_PORT),
        connect_timeout=10,
    )
    return conn


def upload_cards_to_db(cards: List[dict], std_root: str, table: str = DB_TABLE):
    if not cards:
        print("UPLOAD_DB: no cards to upload")
        return

    conn = connect_db()
    cur = conn.cursor()
    print(f"UPLOAD_DB: connected, table={table}, cards={len(cards)}")

    cur.execute(
        f"""
        SELECT id, name, description, manacost, rarity, cardtype, classtype,
               attack, health, tribe, istoken, "set"
        FROM {table}
        """
    )
    existing_by_key = {}
    for row in cur.fetchall():
        set_name = normalize_set_name(row[11]) or (row[11] or "")
        key = card_identity_key(
            row[1], row[2], row[3], row[4], row[5], row[6],
            row[7], row[8], row[9], row[10], set_name,
        )
        existing_by_key[key] = row[0]
    print(f"UPLOAD_DB: existing identity keys={len(existing_by_key)}")

    insert_sql = f"""
        INSERT INTO {table}
            (name, description, manacost, rarity, cardtype, classtype,
             attack, health, tribe, istoken, tokens, comment, command,
             picture, move_x, move_y, zoom, card_image, hash, "set")
        VALUES
            (%s, %s, %s, %s, %s, %s,
             %s, %s, %s, %s, %s, %s, %s,
             %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """
    update_sql = f"UPDATE {table} SET tokens = %s WHERE id = %s"

    dbf_to_db_id = {}
    uploaded = []
    skipped = 0
    failed = 0

    for i, card in enumerate(cards):
        try:
            card_img_path = resolve_asset_path(std_root, card.get("card_image_path"))
            art_path = resolve_asset_path(std_root, card.get("art_image_path"))
            if not card_img_path:
                print(f"Skip upload #{i} {card.get('name')}: no card_image file")
                continue

            set_name = normalize_set_name(card.get("set"))
            if not set_name and card.get("setId") is not None:
                set_name = map_set_name(card.get("setId"))
            if to_int(card.get("setId")) in SKIP_SET_IDS or str(card.get("set") or "") in {"1414", "1463", "1578", "1776"}:
                print(f"Skip upload #{i} {card.get('name')}: ignored set")
                continue
            if set_name is None and card.get("setId") is not None:
                print(f"Skip upload #{i} {card.get('name')}: unknown/ignored setId={card.get('setId')}")
                continue

            identity = card_identity_key(
                card.get("name"),
                card.get("description"),
                card.get("manacost"),
                card.get("rarity"),
                card.get("cardtype"),
                card.get("classtype"),
                card.get("attack"),
                card.get("health"),
                card.get("tribe"),
                card.get("istoken"),
                set_name,
            )
            existing_id = existing_by_key.get(identity)
            if existing_id is not None:
                skipped += 1
                dbf_id = card.get("dbfId")
                if dbf_id is not None:
                    dbf_to_db_id[int(dbf_id)] = existing_id
                print(f"Skip upload #{i} {card.get('name')}: already in db id={existing_id}")
                continue

            with open(card_img_path, "rb") as f:
                card_image = f.read()

            picture = None
            if art_path:
                with open(art_path, "rb") as f:
                    picture = f.read()

            hash_fields = {
                "name": card.get("name"),
                "description": card.get("description"),
                "manacost": card.get("manacost"),
                "rarity": card.get("rarity"),
                "cardtype": card.get("cardtype"),
                "classtype": card.get("classtype"),
                "attack": card.get("attack"),
                "health": card.get("health"),
                "tribe": card.get("tribe"),
                "istoken": card.get("istoken"),
                "set": set_name,
                "card_image_len": len(card_image),
                "picture_len": len(picture) if picture else 0,
            }
            card_hash = calculate_card_hash(hash_fields)

            params = (
                card.get("name"),
                card.get("description"),
                card.get("manacost"),
                card.get("rarity"),
                card.get("cardtype"),
                card.get("classtype"),
                card.get("attack"),
                card.get("health"),
                card.get("tribe"),
                bool(card.get("istoken")),
                None,
                "",
                "",
                psycopg2.Binary(picture) if picture else None,
                0,
                0,
                0,
                psycopg2.Binary(card_image),
                card_hash,
                set_name,
            )
            cur.execute(insert_sql, params)
            db_id = cur.fetchone()[0]
            conn.commit()

            existing_by_key[identity] = db_id
            dbf_id = card.get("dbfId")
            if dbf_id is not None:
                dbf_to_db_id[int(dbf_id)] = db_id
            uploaded.append((db_id, card))
            print(f"Uploaded #{i} id={db_id} {card.get('name')} dbfId={dbf_id} set={set_name}")
        except Exception as e:
            conn.rollback()
            failed += 1
            print(f"UPLOAD_DB failed #{i} {card.get('name')}: {e}")

    for db_id, card in uploaded:
        raw_tokens = card.get("tokens")
        if not raw_tokens:
            continue
        try:
            mapped = []
            for part in str(raw_tokens).split(","):
                part = part.strip()
                if not part:
                    continue
                try:
                    related_dbf = int(part)
                except ValueError:
                    continue
                related_id = dbf_to_db_id.get(related_dbf)
                if related_id is not None:
                    mapped.append(str(related_id))
            if mapped:
                cur.execute(update_sql, (",".join(mapped), db_id))
                conn.commit()
                print(f"Updated tokens id={db_id} {card.get('name')} -> {','.join(mapped)}")
        except Exception as e:
            conn.rollback()
            print(f"UPLOAD_DB tokens failed id={db_id} {card.get('name')}: {e}")

    cur.close()
    conn.close()
    print(f"UPLOAD_DB: done, inserted={len(uploaded)}, skipped_existing={skipped}, failed={failed}")

def start(limit: Optional[int] = None):
    if limit is not None and limit <= 0:
        limit = None
    std_root = os.path.join("src", "assets", "std")
    img_path = os.path.join(std_root, "img")
    arts_path = os.path.join(std_root, "arts")
    meta_path = os.path.join(std_root, "std_metadata.json")

    cards = None

    if DOWNLOAD:
        print(f"DOWNLOAD=1: fetching from wiki (limit={'all' if limit is None else limit})")
        client = WikiClient()
        importer = StandardCardsImporter(client, img_path=img_path, arts_path=arts_path, limit=limit)
        cards = importer.run(
            set_ids=DOWNLOAD_SET_IDS,
            prefer_names=None,
        )
    else:
        print("DOWNLOAD=0: skip wiki download")

    if UPLOAD_DB:
        print("UPLOAD_DB=1: uploading to database")
        if cards is None:
            if not os.path.isfile(meta_path):
                raise FileNotFoundError(f"No metadata for upload: {meta_path}")
            cards = load_metadata(meta_path)
            print(f"Loaded {len(cards)} cards from {meta_path}")
        upload_cards_to_db(cards, std_root=std_root, table=DB_TABLE)
    else:
        print("UPLOAD_DB=0: skip database upload")

    return cards


if __name__ == "__main__":
    if not DOWNLOAD and not UPLOAD_DB:
        print("Nothing to do: set DOWNLOAD=1 and/or UPLOAD_DB=1")
    else:
        start(limit=None)
