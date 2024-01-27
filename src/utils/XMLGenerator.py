from typing import List
from xml.dom import minidom

import xml.etree.ElementTree as ET

from DataTypes import CardMetadata, CardType, ClassType, Rarity, Deck, DeckCard

class XMLGenerator:
    def generate_xml_library(cards: List[CardMetadata]):
        card_database = ET.Element("cockatrice_carddatabase", version="3")

        set_element = ET.SubElement(card_database, "set")
        set_name = ET.SubElement(set_element, "name")
        set_name.text = "name"
        set_longname = ET.SubElement(set_element, "longname")
        set_longname.text = "longname"
        set_settype = ET.SubElement(set_element, "settype")
        set_settype.text = "settype"
        set_releasedate = ET.SubElement(set_element, "releasedate")
        set_releasedate.text = "releasedate"

        cards_element = ET.SubElement(card_database, "cards")

        for card in cards:
            card_element = ET.SubElement(cards_element, "card")

            card_name = ET.SubElement(card_element, "name")
            card_name.text = card.name

            card_text = ET.SubElement(card_element, "text")
            card_text.text = card.description

            prop_element = ET.SubElement(card_element, "prop")
            prop_manacost = ET.SubElement(prop_element, "manacost")
            prop_manacost.text = str(card.manacost)
            prop_colors = ET.SubElement(prop_element, "colors")
            prop_colors.text = str(card.cardtype)

            if card.cardtype == CardType.MINION:# or card.cardtype == CardType.WEAPON:
                prop_pt = ET.SubElement(prop_element, "pt")
                prop_pt.text = str(card.attack) + "/" + str(card.health)

            rarity = Rarity(card.rarity).name if card.rarity else "NONE"
            classtype = ClassType(card.classtype).name if card.classtype else "NEUTRAL"
            set_text = ET.SubElement(card_element, "set", rarity=rarity)
            set_text.text = classtype

        tree = ET.ElementTree(card_database)
        rough_string = ET.tostring(card_database, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty_string = reparsed.toprettyxml(indent="\t")
        with open("example.xml", "w", encoding="utf-8") as file:
            file.write(pretty_string) 

    def generate_xml_deck(deck: Deck):
        root = ET.Element("cockatrice_deck", version="1")
        ET.SubElement(root, "deckname").text = deck.name

        zones = {"main": [], "side": [], "tokens": []}
        for card in deck.cards:
            if card.side == DeckCard.Side.MAINDECK:
                zone = "main"
            elif card.side == DeckCard.Side.SIDEBOARD:
                zone = "side"
            else:
                zone = "tokens"
            zones[zone].append((card.name, card.count))

        for zone_name, zone_cards in zones.items():
            zone_element = ET.SubElement(root, "zone", name=zone_name)
            for name, count in zone_cards:
                card_element = ET.SubElement(zone_element, "card", number=str(count), name=name)

        rough_string = ET.tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="\t")

        with open("example.xml", "w", encoding="utf-8") as file:
            file.write(pretty_xml) 