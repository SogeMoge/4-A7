"""Variables for xws_dict conversion to pretty format."""


def convert_xws(string):
    """Convert xws faction name to readable format."""
    mapping = {
        "rebelalliance": "Rebel Alliance",
        "galacticempire": "Galactic Empire",
        "scumandvillainy": "Scum and Villainy",
        "firstorder": "First Order",
        "resistance": "Resistance",
        "galacticrepublic": "Galactic Republic",
        "separatistalliance": "Separatist Alliance",
    }
    words = string.split()
    converted_words = [
        mapping.get(word.lower(), word) for word in words
    ]
    return " ".join(converted_words)


def convert_faction_to_dir(string):
    """Convert xws faction name to xwing-data2 directories."""
    mapping = {
        "rebelalliance": "rebel-alliance",
        "galacticempire": "galactic-empire",
        "scumandvillainy": "scum-and-villainy",
        "firstorder": "first-order",
        "resistance": "resistance",
        "galacticrepublic": "galactic-republic",
        "separatistalliance": "separatist-alliance",
    }
    words = string.split()
    converted_words = [
        mapping.get(word.lower(), word) for word in words
    ]
    return " ".join(converted_words)


ship_emojis = {
    "asf01bwing": "<:asf01bwing:1158007152250736711>",
    "arc170starfighter": "<:arc170starfighter:1158007149235019908>",
    "attackshuttle": "<:attackshuttle:1158007154012323952>",
    "auzituckgunship": "<:auzituckgunship:1158007156927381574>",
    "btla4ywing": "<:btla4ywing:1158007162723901551>",
    "btls8kwing": "<:btls8kwing:1158007201395388456>",
    "ewing": "<:ewing:1158007223516143689>",
    "fangfighter": "<:fangfighter:1158007270806921257>",
    "hwk290lightfreighter": "<:hwk290lightfreighter:1158007292395008092>",
    "modifiedyt1300lightfreighter": "<:modifiedyt1300lightfreighter:1158007338171645972>",
    "rz1awing": "<:rz1awing:1158007388440379453>",
    "sheathipedeclassshuttle": "<:sheathipedeclassshuttle:1158007489153990716>",
    "t65xwing": "<:t65xwing:1158007500822548531>",
    "ut60duwing": "<:ut60duwing:1158007612806275172>",
    "vcx100lightfreighter": "<:vcx100lightfreighter:1158007639603687505>",
    "yt2400lightfreighter": "<:yt2400lightfreighter:1158007652169830470>",
    "yt2400lightfreighter2023": "<:yt2400lightfreighter2023:1160494092065706034>",
    "z95af4headhunter": "<:z95af4headhunter:1158007658037653605>",
    "aggressorassaultfighter": "<:aggressorassaultfighter:1158007144080216065>",
    "jumpmaster5000": "<:jumpmaster5000:1158007317476945920>",
    "kihraxzfighter": "<:kihraxzfighter:1158007320635265024>",
    "lancerclasspursuitcraft": "<:lancerclasspursuitcraft:1158007326301769809>",
    "m12lkimogilafighter": "<:m12lkimogilafighter:1158007330726744105>",
    "m3ainterceptor": "<:m3ainterceptor:1158007329225187378>",
    "modifiedtielnfighter": "<:modifiedtielnfighter:1158007335323705384>",
    "quadrijettransferspacetug": "<:quadrijettransferspacetug:1158007376453042246>",
    "rogueclassstarfighter": "<:rogueclassstarfighter:1158007386729099264>",
    "scurrgh6bomber": "<:scurrgh6bomber:1158007487488872598>",
    "st70assaultship": "<:st70assaultship:1158007493444771851>",
    "starviperclassattackplatform": "<:starviperclassattackplatform:1158007496280133632>",
    "tridentclassassaultship": "<:tridentclassassaultship:1158007607685030013>",
    "yv666lightfreighter": "<:yv666lightfreighter:1158007654678024264>",
    "customizedyt1300lightfreighter": "<:customizedyt1300lightfreighter:1158007210526396456>",
    "escapecraft": "<:escapecraft:1158007218914996354>",
    "g1astarfighter": "<:g1astarfighter:1158007279111647333>",
    "alphaclassstarwing": "<:alphaclassstarwing:1158007146672312372>",
    "gauntletfighter": "<:gauntletfighter:1158007280722247741>",
    "gozanticlasscruiser": "<:gozanticlasscruiser:1158007283737968691>",
    "lambdaclasst4ashuttle": "<:lambdaclasst4ashuttle:1158007324636614696>",
    "raiderclasscorvette": "<:raiderclasscorvette:1158007377916866590>",
    "tieadvancedv1": "<:tieadvancedv1:1158007505440481390>",
    "tieadvancedx1": "<:tieadvancedx1:1158007533013848124>",
    "tieininterceptor": "<:tieininterceptor:1158007545454145576>",
    "tiereaper": "<:tiereaper:1158007588282179694>",
    "tieddefender": "<:tieddefender:1158007541394067506>",
    "tieagaggressor": "<:tieagaggressor:1158007534435700746>",
    "tiecapunisher": "<:tiecapunisher:1158007538516766843>",
    "tielnfighter": "<:tielnfighter:1158007547194777701>",
    "tiephphantom": "<:tiephphantom:1158007556023795732>",
    "tiesabomber": "<:tiesabomber:1158007589993447454>",
    "tieskstriker": "<:tieskstriker:1158007598742769665>",
    "vt49decimator": "<:vt49decimator:1158007642258673724>",
    "tierbheavy": "<:tierbheavy:1158007557277888533>",
    "gr75mediumtransport": "<:gr75mediumtransport:1158007287135354992>",
    "mg100starfortresssf17": "<:mg100starfortresssf17:1158007333553713242>",
    "scavengedyt1300": "<:scavengedyt1300:1158007484196331580>",
    "rz2awing": "<:rz2awing:1158007391091175514>",
    "t70xwing": "<:t70xwing:1158007502349271142>",
    "resistancetransport": "<:resistancetransport:1158007380701876224>",
    "resistancetransportpod": "<:resistancetransportpod:1158007383029723247>",
    "fireball": "<:fireball:1158007272576909312>",
    "btanr2ywing": "<:btanr2ywing:1158007161104908288>",
    "tiebainterceptor": "<:tiebainterceptor:1158007536998420571>",
    "tiefofighter": "<:tiefofighter:1158007542790754304>",
    "tiesffighter": "<:tiesffighter:1158007596192641198>",
    "tievnsilencer": "<:tievnsilencer:1158007602140155975>",
    "upsilonclasscommandshuttle": "<:upsilonclasscommandshuttle:1158007611023708171>",
    "xiclasslightshuttle": "<:xiclasslightshuttle:1158007649544196146>",
    "tiesebomber": "<:tiesebomber:1158007593244041357>",
    "tiewiwhispermodifiedinterceptor": "<:tiewiwhispermodifiedinterceptor:1158007605919232100>",
    "vultureclassdroidfighter": "<:vultureclassdroidfighter:1158007646457184346>",
    "croccruiser": "<:croccruiser:1158007208517304400>",
    "belbullab22starfighter": "<:belbullab22starfighter:1158007158626078811>",
    "sithinfiltrator": "<:sithinfiltrator:1158007491985145926>",
    "hyenaclassdroidbomber": "<:hyenaclassdroidbomber:1158007293976260648>",
    "nantexclassstarfighter": "<:nantexclassstarfighter:1158007370048340058>",
    "droidtrifighter": "<:droidtrifighter:1158007215475675167>",
    "hmpdroidgunship": "<:hmpdroidgunship:1158007288955687012>",
    "firesprayclasspatrolcraft": "<:firesprayclasspatrolcraft:1158007275504541746>",
    "delta7aethersprite": "<:delta7aethersprite:1158007213688881252>",
    "cr90corelliancorvette": "<:cr90corelliancorvette:1158007205908463707>",
    "v19torrentstarfighter": "<:v19torrentstarfighter:1158007638051795005>",
    "nabooroyaln1starfighter": "<:nabooroyaln1starfighter:1158007367909244988>",
    "btlbywing": "<:btlbywing:1158007165244678196>",
    "eta2actis": "<:eta2actis:1158007220508839946>",
    "laatigunship": "<:laatigunship:1158007322107457596>",
    "nimbusclassvwing": "<:nimbusclassvwing:1158007373315719249>",
    "syliureclasshyperspacering": "<:syliureclasshyperspacering:1158007498113032263>",
    "clonez95headhunter": "<:clonez95headhunter:1158007204285251715>",
}
