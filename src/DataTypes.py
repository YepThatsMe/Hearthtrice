from enum import IntEnum, auto
import json
from typing import List


class Response:
    def __init__(self, ok: bool, msg: str = ""):
        self.ok = ok
        self.msg = msg


class DeckCard:
    class Side(IntEnum):
        MAINDECK = auto()
        SIDEBOARD = auto()

    def __init__(self):
        self.id: int
        self.count: int
        self.side: DeckCard.Side

        # optional
        self.manacost: int
        self.name: str
        self.istoken: bool


class Deck:
    def __init__(self):
        self.id: int
        self.name: str
        self.cards: List[DeckCard] = []
        self.owner: str
    

class ClassType(IntEnum):
    NEUTRAL: int = auto()
    MAGE: int = auto()
    HUNTER: int = auto()
    PALADIN: int = auto()
    WARRIOR: int = auto()
    DRUID: int = auto()
    ROGUE: int = auto()
    PRIEST: int = auto()
    WARLOCK: int = auto()
    SHAMAN: int = auto()
    DEMONHUNTER: int = auto()

class Rarity(IntEnum):
    NONE: int = auto()
    COMMON: int = auto()
    RARE: int = auto()
    EPIC: int = auto()
    LEGENDARY: int = auto()

class CardType(IntEnum):
    MINION: int = auto()
    SPELL: int = auto()

class CardMetadata:
    id: int
    name: str
    description: str
    manacost: int
    rarity: Rarity
    cardtype: CardType
    classtype: ClassType
    attack: int
    health: int
    tribe: str

    istoken: bool
    tokens: str

    comment: str
    picture: bytes
    move_x: int    
    move_y: int
    zoom: int

    card_image: bytes
    hash: str

    def __init__(self, json_meta: dict = None) -> None:
        if not json_meta:
            return
        self.__dict__ = json_meta
        
    def to_json(self) -> str:
        return json.dumps(self.__dict__, indent=2)
    
    def all(self) -> dict:
        return self.__dict__

    def update(self, data: dict) -> None:
        self.__dict__.update(data)

    def pop(self, key: str) -> str:
        return self.__dict__.pop(key)

    def __getitem__(self, key: str):
        return self.__dict__.get(key)
    
    def __getattr__(self, __name: str):
        return self.__getitem__(__name)
