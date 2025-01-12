import os
import hashlib
import json
import shutil
import traceback
from typing import List
from datetime import timedelta

from DataPresenter import DataPresenter
from DataTypes import CardMetadata
from utils.BytesEncoder import bytes_to_pixmap
from utils.string import sanitize


class CacheManager:
    def __init__(self, data_presenter: DataPresenter, ttl_days=7):
        self.data_presenter = data_presenter
        self.ttl = timedelta(days=ttl_days)

        self.cache_dir = os.path.join(os.getcwd(), "cache")
        if os.getenv("LOCALAPPDATA"):
            self.cache_dir = os.path.join(os.getenv("LOCALAPPDATA"), "Hearthtrice", "cache")

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

    def save_cache(self, card_metadata: List[CardMetadata]):
        """Обновление или добавление данных в кэш."""
        try:
            local_hahslist = self.__read_local_hashlist()
            for meta in card_metadata:
                img = bytes_to_pixmap(meta.card_image)
                img.save(os.path.join(self.images_dir, sanitize(meta.name) + ".png"))

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
                                            "hash": meta.hash }
                
            self.__save_local_hashlist(local_hahslist)
        except Exception as e:
            traceback.print_exc()
            self.clear_cache()
            exit()

    def get_cache(self) -> List[CardMetadata]:
        try:
            local_hahslist = self.__read_local_hashlist()

            metadata_list = []
            for id, meta in local_hahslist.items():
                metadata = CardMetadata()
                metadata.id = id
                metadata.update(meta)
                with open(os.path.join(self.images_dir, sanitize(metadata.name) + ".png"), 'rb') as f:
                    metadata.card_image = f.read()
                
                metadata_list.append(metadata)

            return metadata_list
        except Exception as e:
            traceback.print_exc()
            self.clear_cache()
            exit()

    def delete_from_cache(self, id: int):
        try:
            local_hahslist = self.__read_local_hashlist()

            name = str()
            if id in local_hahslist:
                name = local_hahslist[id]["name"]
                del local_hahslist[id]

            image = os.path.join(self.images_dir, sanitize(name) + ".png")
            if os.path.exists(image):
                os.remove(image)

            self.__save_local_hashlist(local_hahslist)
        except Exception as e:
            traceback.print_exc()
            self.clear_cache()
            exit()

    def get_discrepant_ids(self, remote_hashlist: List[dict]) -> List[int]:
        """
        Returns IDs that are missing from local cache 
        or those whose hash is different
        """
        try:
            local_hahslist = self.__read_local_hashlist()

            mismatched_ids = []
            
            for remote_dict_item in remote_hashlist:
                id = remote_dict_item['id']
                if id not in local_hahslist.keys():
                    mismatched_ids.append(id)
                elif local_hahslist[id]["hash"] != remote_dict_item["hash"]:
                    mismatched_ids.append(id)

            return mismatched_ids
        except Exception as e:
            traceback.print_exc()
            self.clear_cache()
            exit()

    def clear_cache(self):
        if os.path.isdir(self.cache_dir):
            shutil.rmtree(self.cache_dir)
            print("Cache cleared")
