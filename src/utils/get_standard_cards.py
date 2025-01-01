import requests
from typing import List
import json
import os

from PIL import Image
from io import BytesIO

class NoKeyException(BaseException):
    pass

# Download from https://rapidapi.com/omgvamp/api/hearthstone
base_url = 'https://omgvamp-hearthstone-v1.p.rapidapi.com/cards/sets/'
headers = {
    'X-RapidAPI-Key': 'cfb8a4ff50mshf4a0583c4bc1afap197f77jsn475b97f9e948', # API key here
    'X-RapidAPI-Host': 'omgvamp-hearthstone-v1.p.rapidapi.com'
}

sets = ['Basic', 'Classic', 'Hall of Fame', 'Naxxramas', 'Goblins vs Gnomes', 'Blackrock Mountain', 'The Grand Tournament', 'The League of Explorers', 'Whispers of the Old Gods', 'One Night in Karazhan', 'Mean Streets of Gadgetzan', "Journey to Un'Goro", 'Knights of the Frozen Throne', 'Kobolds & Catacombs', 'The Witchwood']
classes = ['Neutral', 'Druid', 'Hunter', 'Mage', 'Paladin', 'Priest', 'Rogue', 'Shaman', 'Warlock', 'Warrior']
types = ['Hero', 'Minion', 'Spell', 'Enchantment', 'Weapon', 'Hero Power', 'Location']

def get_byte_image_from_url(url: str) -> bytes:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        img_bytes = response.content
    else:
        print(f'Ошибка при скачивании изображения: статус код {response.status_code}')
        return None
    return img_bytes

def get_cards_json(set_names: List[str]) -> List[dict]:
    all_sets_json = []
    for set_name in set_names:
        set_url = base_url + set_name
        response = requests.get(set_url, headers=headers)
        if response.status_code == 200:
            set_data = response.json()  # Предполагаем, что ответ - это JSON
            if isinstance(set_data, list):
                all_sets_json.extend(set_data)  # Если ответ - список словарей
            elif isinstance(set_data, dict):
                all_sets_json.append(set_data)  # Если ответ - один словарь
        else:
            print(f"Error fetching data for {set_name}: {response.status_code}")

    return all_sets_json

def save_card(name: str, card_image: bytes, img_path: str):
    with Image.open(BytesIO(card_image)) as img:
        img_resized = img.resize((769, 1107), Image.LANCZOS)
        
        img_resized.save(os.path.join(img_path, name + ".png"))

def create_or_overwrite_qrc_file(filename: str, resource_paths: list):
    with open(filename, 'w') as file:
        file.write('<!DOCTYPE RCC><RCC version="1.0">\n')
        file.write('<qresource>\n')
        
        for path in resource_paths:
            file.write(f'    <file>{path}</file>\n')
        
        file.write('</qresource>\n')
        file.write('</RCC>\n')

    print(f"QRC '{filename}' has been overwritten successfully.")

def start(sets: List[str]):
    if headers['X-RapidAPI-Key'] == '':
        raise NoKeyException()
    
    os.makedirs(IMG_PATH, exist_ok=True)

    set_data = get_cards_json(sets)

    card_jsons = []
    qrc_entries = []
    for i, card_json in enumerate(set_data):
        try:
            name = card_json['name']
            if card_json['type'] == 'Enchantment':
                print(f"Skip #{i} {name}: Enchantment")
                continue
            if 'img' not in card_json:
                print(f"Skip #{i} {name}: No img")
                continue
            if str(card_json['cardId']).startswith("BG_"):
                print(f"Skip #{i} {name}: BG Card")
                continue
            if str(card_json['cardId']).startswith("TB_"):
                print(f"Skip #{i} {name}: TB Card")
                continue

            description = card_json.get('text')
            manacost = card_json['cost']
            rarity = card_json.get('rarity')
            if not rarity or rarity == 'Free':
                rarity = 1
            elif rarity == 'Common':
                rarity = 2
            elif rarity == 'Rare':
                rarity = 3
            elif rarity == 'Epic':
                rarity = 4
            elif rarity == 'Legendary':
                rarity = 5
            cardtype = card_json['type']
            if cardtype == 'Minion':
                cardtype = 1
            elif cardtype == 'Spell':
                cardtype = 2
            elif cardtype == 'Weapon':
                cardtype = 3
            elif cardtype == 'Hero':
                cardtype = 4
            elif cardtype == 'Hero Power':
                cardtype = 5
            else:
                print(f"Skip #{i} {name}: Bad card type")
                continue

            classtype = card_json.get('playerClass')
            if not classtype or classtype == 'Neutral':
                classtype = 1
            elif classtype == 'Mage':
                classtype = 2
            elif classtype == 'Hunter':
                classtype = 3
            elif classtype == 'Paladin':
                classtype = 4
            elif classtype == 'Warrior':
                classtype = 5
            elif classtype == 'Druid':
                classtype = 6
            elif classtype == 'Rogue':
                classtype = 7
            elif classtype == 'Priest':
                classtype = 8
            elif classtype == 'Warlock':
                classtype = 9
            elif classtype == 'Shaman':
                classtype = 10
            else:
                print(f"Skip #{i} {name}: Bad class type")
                continue
            attack = card_json.get('attack')
            health = card_json.get('health')
            tribe = card_json.get('race')
            istoken = 0
            if not card_json.get('collectible'):
                istoken = 1
            card_image = get_byte_image_from_url(card_json['img'])
            if not card_image:
                continue

            params_set = {"name": name,
                "description": description,
                "manacost": manacost,
                "rarity": rarity, 
                "cardtype": cardtype, 
                "classtype": classtype,
                "attack": attack, 
                "health": health, 
                "tribe": tribe,
                "istoken": istoken,
                "card_image": card_image}
            
            save_card(name, card_image, IMG_PATH)
            print(f'Saved #{i} {name}')

            params_set['card_image_path'] = f"std/img/{name}.png"
            params_set["card_image"] = None

            card_jsons.append(params_set)
            qrc_entries.append(params_set['card_image_path'])

        except Exception as e:
            print(f"Error skip #{i} {name}:", str(e))
            continue

    with open(os.path.join(IMG_PATH, "..", "std_metadata.json"), 'w') as f:
        json.dump(card_jsons, f, indent=4)

    qrc_entries.append("std/std_metadata.json")
    create_or_overwrite_qrc_file(os.path.join(IMG_PATH, "..", "..", "resource_list_std.qrc"), qrc_entries)

if __name__ == '__main__':
    IMG_PATH = os.path.join("src", "assets", "std", "img")
    sets = ['Legacy', 'Classic', 'Naxxramas', 'Hall of Fame']
    start(sets)
    
    