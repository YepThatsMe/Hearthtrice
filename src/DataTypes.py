from enum import IntEnum, auto
import json
from typing import List


class Response:
    def __init__(self, ok: bool, msg: str = ""):
        self.ok = ok
        self.msg = msg

class BaseEnum(IntEnum):
    @classmethod
    def get_name(cls, value: int) -> str:
        try:
            return cls(value).name
        except ValueError:
            return "UNKNOWN"
        
    @classmethod
    def get_value(cls, name: str) -> int:
        val = cls.__members__.get(name.upper(), None)
        if val: return int(val)
        return None
    
class DeckCard:
    class Side(BaseEnum):
        MAINDECK = auto()
        SIDEBOARD = auto()
        TOKENS = auto()

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
    

class ClassType(BaseEnum):
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

class Rarity(BaseEnum):
    NONE: int = auto()
    COMMON: int = auto()
    RARE: int = auto()
    EPIC: int = auto()
    LEGENDARY: int = auto()

class CardType(BaseEnum):
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
    command: str

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
    
    def dict(self) -> dict:
        return self.__dict__
    
    def values(self) -> list:
        return self.__dict__.values()

    def update(self, data: dict) -> None:
        self.__dict__.update(data)

    def pop(self, key: str) -> str:
        return self.__dict__.pop(key)

    def __getitem__(self, key: str):
        return self.__dict__.get(key)
    
    def __getattr__(self, __name: str):
        return self.__getitem__(__name)

class StdMetadata(CardMetadata):
    isstandard: bool = True
    card_image_path: str

