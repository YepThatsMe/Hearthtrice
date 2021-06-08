def read(path):
    import xml.etree.ElementTree as ET

    hs = ET.parse(path)
    enter = hs.findall("cards/card[type = 'Minion']") + hs.findall("cards/card[type = 'Spell']") + hs.findall(
        "cards/card[type = 'Weapon']") + hs.findall("cards/card[type = 'Hero']")
    esc = {i[0].text + ".png": "".join(i[2].attrib.values()) for i in enter}
    # count = int(input('Введите число карт:\n'))
    return esc



def loadPic(esc, path):
    import requests
    import os
    from PIL import Image
    from io import BytesIO
    a = []
    for i in esc.keys():
        a.append(i)

    path = path[:path.rfind('/')]
    os.chdir(path)
    path = r"../pics/downloadedPics/HT/"
    l = os.listdir(path=path)

    if len(esc) == len(l):
        return
    if len(a) < len(l):
        diff = set(l).difference(set(a))
        diff = list(diff)

        for j in diff:
            print(j)
            print(esc)
            if j in esc:
                r = requests.get(esc[j])
                im = Image.open(BytesIO(r.content))
                im.save(f'{path}{j}.png')

    if len(a) > len(l):
        diff = set(a).difference(set(l))
        diff = list(diff)

        for j in diff:
            if j in esc:
                r = requests.get(esc[j])
                im = Image.open(BytesIO(r.content))
                im.save(f'{path}{j}.png')


def roll(esc):
    import numpy.random as rnd
    roll = rnd.choice(list(esc.keys()), size=3, replace=False)
    return roll

def roll_std(Hero, path_std):
    import numpy.random as rnd
    import os
    heroes = {'Маг': 'Mage', 'Друид': "Druid", "Охотник": "Hunter", "Паладин": "Paladin",
             "Жрец": "Priest", "Разбойник": "Rogue", "Шаман": "Shaman",
              "Чернокнижник": "Warlock", "Воин": "Warrior"}
    path = f"{path_std}{heroes[Hero]}"
    cards = os.listdir(path=path)
    roll_std_l = rnd.choice(cards, size=3, replace=False)
    return roll_std_l


def create(names, cnt, deck_name, esc):
    import xml.etree.ElementTree as ET
    deck = ET.Element('cockatrice_deck')
    deck.set('version', '1')
    main = ET.Element('zone')
    main.set('name', 'main')

    def add_card(names, cnt, ind):
        # global esc
        if names[ind] in esc:
            ET.SubElement(main, 'card', attrib={'number': f'{cnt[ind]}', 'name': names[ind][:-4]})
        else:
            ET.SubElement(main, 'card', attrib={'number': f'{cnt[ind]}', 'name': names[ind]})
    for i in range(len(names)):
        add_card(names, cnt, i)

    deck.append(main)
    deck = ET.ElementTree(deck)
    deck.write(f'{deck_name}.cod')
