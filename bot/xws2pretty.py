"""Variables for xws_dict conversion to pretty format."""


def convert_xws(string):
    """Convert xws faction name to readable format."""
    mapping = {
        'rebelalliance': 'Rebel Alliance',
        'rebels': 'Rebel Alliance',
        'rebel': 'Rebel Alliance',
        'galacticempire': 'Galactic Empire',
        'imperial': 'Galactic Empire',
        'scumandvillainy': 'Scum and Villainy',
        'firstorder': 'First Order',
        'resistance': 'Resistance',
        'galacticrepublic': 'Galactic Republic',
        'separatistalliance': 'Separatist Alliance'
    }
    words = string.split()
    converted_words = [mapping.get(word.lower(), word) for word in words]
    return " ".join(converted_words)

# exportObj.fromXWSUpgrade =
#     'amd': 'Astromech'
#     'astromechdroid': 'Astromech'
#     'ept': 'Talent'
#     'elitepilottalent': 'Talent'
#     'system': 'Sensor'
#     'mod': 'Modification'
#     'force-power':'Force'
#     'tactical-relay':'Tactical Relay'


# ship_emojis = {
#     'tieinterceptor': '🛩️',
#     'tiefighter': '🤖',
#     'tiebomber': '🍕',
#     # Add more ship names and emojis as needed
# }

ship_emojis = {
    "asf01bwing": "b",
    "arc170starfighter": "c",
    "attackshuttle": "g",
    "auzituckgunship": "@",
    "btla4ywing": "y",
    "btls8kwing": "k",
    "ewing": "1158007223516143689",
    "fangfighter": "M",
    "hwk290lightfreighter": "h",
    "modifiedyt1300lightfreighter": "m",
    "rz1awing": "a",
    "sheathipedeclassshuttle": "%",
    "t65xwing": "x",
    "ut60duwing": "u",
    "vcx100lightfreighter": "G",
    "yt2400lightfreighter": "o",
    "z95af4headhunter": "z",
    "aggressorassaultfighter": "i",
    "jumpmaster5000": "p",
    "kihraxzfighter": "r",
    "lancerclasspursuitcraft": "L",
    "m12lkimogilafighter": "K",
    "m3ainterceptor": "s",
    "modifiedtielnfighter": "C",
    "quadrijettransferspacetug": "q",
    "rogueclassstarfighter": "|",
    "scurrgh6bomber": "H",
    "st70assaultship": "'",
    "starviperclassattackplatform": "v",
    "tridentclassassaultship": "7",
    "yv666lightfreighter": "t",
    "customizedyt1300lightfreighter": "W",
    "escapecraft": "X",
    "g1astarfighter": "n",
    "alphaclassstarwing": "&",
    "gauntletfighter": "6",
    "gozanticlasscruiser": "4",
    "lambdaclasst4ashuttle": "l",
    "raiderclasscorvette": "3",
    "tieadvancedv1": "R",
    "tieadvancedx1": "A",
    "tieininterceptor": "I",
    "tiereaper": "V",
    "tieddefender": "D",
    "tieagaggressor": "`",
    "tiecapunisher": "N",
    "tielnfighter": "F",
    "tiephphantom": "P",
    "tiesabomber": "B",
    "tieskstriker": "T",
    "vt49decimator": "d",
    "tierbheavy": "J",
    "gr75mediumtransport": "1",
    "mg100starfortresssf17": "Z",
    "scavengedyt1300": "Y",
    "rz2awing": "E",
    "t70xwing": "w",
    "resistancetransport": ">",
    "resistancetransportpod": "?",
    "fireball": "0",
    "btanr2ywing": "{",
    "tiebainterceptor": "j",
    "tiefofighter": "O",
    "tiesffighter": "S",
    "tievnsilencer": "$",
    "upsilonclasscommandshuttle": "U",
    "xiclasslightshuttle": "Q",
    "tiesebomber": "!",
    "tiewiwhispermodifiedinterceptor": "#",
    "vultureclassdroidfighter": "_",
    "croccruiser": "5",
    "belbullab22starfighter": "[",
    "sithinfiltrator": "]",
    "hyenaclassdroidbomber": "=",
    "nantexclassstarfighter": ";",
    "droidtrifighter": "+",
    "hmpdroidgunship": ".",
    "firesprayclasspatrolcraft": "f",
    "delta7aethersprite": "\\",
    "cr90corelliancorvette": "2",
    "v19torrentstarfighter": "^",
    "nabooroyaln1starfighter": "<",
    "btlbywing": ":",
    "eta2actis": "-",
    "laatigunship": "/",
    "nimbusclassvwing": ",",
    "syliureclasshyperspacering": "*",
    "clonez95headhunter": "}"
}
