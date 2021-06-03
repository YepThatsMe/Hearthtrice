import webbrowser as wb

def login():
    wb.get().open("http://www.hearthcards.net/", new=2)

def read(path):
    import xml.etree.ElementTree as ET
    hs = ET.parse(path)
    enter = hs.findall("cards/card[type = 'Minion']") + hs.findall("cards/card[type = 'Spell']") + hs.findall(
        "cards/card[type = 'Weapon']") + hs.findall("cards/card[type = 'Hero']")
    esc = {i[0].text + ".png": "".join(i[2].attrib.values()) for i in enter}
    # count = int(input('Введите число карт:\n'))
    return esc