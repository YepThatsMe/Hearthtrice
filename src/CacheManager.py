import os
import hashlib
import json
import shutil
import traceback
from typing import List, Type
from datetime import timedelta

from DataPresenter import DataPresenter
from DataTypes import CardMetadata
from utils.BytesEncoder import bytes_to_pixmap
from utils.string import sanitize

from main import DEBUG
CACHE_PATH = "cache" if not DEBUG else "cache_dbg"
CACHE_STD_PATH = "cache_std" if not DEBUG else "cache_std_dbg"

class CacheManager:
    def __init__(self, data_presenter: DataPresenter, ttl_days=7, cache_subdir: str = None, meta_cls: Type[CardMetadata] = CardMetadata):
        self.data_presenter = data_presenter
        self.ttl = timedelta(days=ttl_days)
        self.meta_cls = meta_cls

        if cache_subdir is None:
            cache_subdir = CACHE_PATH

        self.cache_dir = os.path.join(os.getcwd(), cache_subdir)
        if os.getenv("LOCALAPPDATA"):
            self.cache_dir = os.path.join(os.getenv("LOCALAPPDATA"), "Hearthtrice", cache_subdir)

        self.index_path = os.path.join(self.cache_dir, "index.json")
        self.images_dir = os.path.join(self.cache_dir, "images")
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)

        if not os.path.exists(self.index_path):
            with open(self.index_path, "w") as f:
                json.dump({}, f)

    def calculate_hash(self, card_metadata: CardMetadata) -> str:
        data = ''.join(sorted(str(m) for k, m in card_metadata.dict().items() if k != 'hash')).encode("utf-8")
        return hashlib.md5(data).hexdigest()
    
    def __read_local_hashlist(self) -> dict:
        with open(self.index_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {int(key): value for key, value in data.items()}


    def __save_local_hashlist(self, data: dict):
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def _image_path(self, name: str) -> str:
        return os.path.join(self.images_dir, sanitize(name) + ".png")

    def save_cache(self, card_metadata: List[CardMetadata]):
        """Обновление или добавление данных в кэш."""
        try:
            local_hahslist = self.__read_local_hashlist()
            for meta in card_metadata:
                img = bytes_to_pixmap(meta.card_image)
                img.save(self._image_path(meta.name))

                local_hahslist[meta.id] = { "name": meta.name,
                                            "description": meta.description,
                                            "manacost": meta.manacost,
                                            "rarity": meta.rarity,
                                            "cardtype": meta.cardtype,
                                            "classtype": meta.classtype,
                                            "attack": meta.attack,
                                            "health": meta.health,
                                            "tribe": meta.tribe,
                                            "istoken": meta.istoken,
                                            "tokens": meta.tokens,
                                            "comment": meta.comment,
                                            "command": meta.command,
                                            "hash": meta.hash }
                
            self.__save_local_hashlist(local_hahslist)
        except Exception as e:
            traceback.print_exc()
            print(f"save_cache error: {e}")

    def get_cache(self) -> List[CardMetadata]:
        try:
            local_hahslist = self.__read_local_hashlist()
            metadata_list = []
            broken_ids = []

            for id, meta in sorted(local_hahslist.items()):
                metadata = self.meta_cls()
                metadata.id = id
                metadata.update(meta)
                image_path = self._image_path(metadata.name)
                if not os.path.isfile(image_path):
                    print(f"Cache image missing for id={id} ({metadata.name}), will redownload")
                    broken_ids.append(id)
                    continue
                with open(image_path, "rb") as f:
                    metadata.card_image = f.read()
                metadata_list.append(metadata)

            if broken_ids:
                for broken_id in broken_ids:
                    local_hahslist.pop(broken_id, None)
                self.__save_local_hashlist(local_hahslist)

            return metadata_list
        except Exception as e:
            traceback.print_exc()
            print(f"get_cache error: {e}")
            return []

    def delete_from_cache(self, id: int):
        try:
            local_hahslist = self.__read_local_hashlist()

            name = str()
            if id in local_hahslist:
                name = local_hahslist[id]["name"]
                del local_hahslist[id]

            image = self._image_path(name) if name else ""
            if image and os.path.exists(image):
                os.remove(image)

            self.__save_local_hashlist(local_hahslist)
        except Exception as e:
            traceback.print_exc()
            print(f"delete_from_cache error: {e}")

    def get_discrepant_ids(self, remote_hashlist: List[dict]) -> List[int]:
        """
        Returns IDs that are missing from local cache
        or those whose hash is different
        or whose image file is missing
        """
        try:
            local_hahslist = self.__read_local_hashlist()
            mismatched_ids = []

            for remote_dict_item in remote_hashlist:
                id = remote_dict_item["id"]
                if id not in local_hahslist:
                    mismatched_ids.append(id)
                    continue

                local_item = local_hahslist[id]
                if local_item.get("hash") != remote_dict_item["hash"]:
                    mismatched_ids.append(id)
                    continue

                image_path = self._image_path(local_item.get("name", ""))
                if not os.path.isfile(image_path):
                    mismatched_ids.append(id)

            return mismatched_ids
        except Exception as e:
            traceback.print_exc()
            print(f"get_discrepant_ids error: {e}")
            return [item["id"] for item in remote_hashlist]

    def clear_cache(self):
        if os.path.isdir(self.cache_dir):
            shutil.rmtree(self.cache_dir)
            print("Cache cleared")
