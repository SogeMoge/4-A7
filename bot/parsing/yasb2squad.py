"""get legacy-yasb link and convert it to XWS"""
import re
import json

##### YASB PARSING VARS #####
GITHUB_USER = "SogeMoge"
GITHUB_BRANCH = "legacy"
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/xwing-data2/{GITHUB_BRANCH}/"
MANIFEST = "data/manifest.json"
CHECK_FREQUENCY = 900  # 15 minutes
##### YASB PARSING VARS #####


def parse_yasb_link(yasb_link):
    """parse xwing-legacy yasb link
    and get pilots with upgrades as a list"""

    # search link part containing elements of a squad
    regex_result = re.search(r"v\dZ.*", yasb_link)
    separated_yasb_link = regex_result.group().split("Z")

    return separated_yasb_link


def get_yasb_gamemode(yasb_link):
    """parse yasb link as list to find gamemode"""

    separated_yasb_link = parse_yasb_link(yasb_link)
    game_mode = separated_yasb_link[1]

    return game_mode


def get_yasb_points(yasb_link):
    """parse yasb link as list to find total list points"""

    separated_yasb_link = parse_yasb_link(yasb_link)
    list_points = separated_yasb_link[2]

    return list_points


def get_yasb_squadname(yasb_link):
    """parse yasb link as list to find name of a squad"""

    separated_yasb_link = parse_yasb_link(yasb_link)
    pilots_uncut = separated_yasb_link[3]

    name_uncut = pilots_uncut[
        pilots_uncut.find("&sn") : pilots_uncut.find("&obs=")
    ]
    yasb_squadname_formatted = name_uncut.replace("%20", " ").lstrip(
        "&sn="
    )

    return yasb_squadname_formatted


def get_yasb_faction(yasb_link):
    """parse yasb link to get faction name"""

    regex_result = re.search(r"f=.*&d", yasb_link)

    yasb_faction = (
        regex_result.group()
        .replace("%20", " ")
        .lstrip("f=")
        .rstrip("&d")
    )

    return yasb_faction


def get_yasb_ships(yasb_link):
    """parse yasb link to get list of ships in a list"""

    separated_yasb_link = parse_yasb_link(yasb_link)
    ships_uncut = separated_yasb_link[3]

    ships_cut = ships_uncut[: ships_uncut.find("&sn")].strip()
    ships_list = ships_cut.split("Y")

    return ships_list


def get_yasb_pilots(yasb_link):
    """get pilots from list of ships"""

    ships_list = get_yasb_ships(yasb_link)
    pilots_list = []

    for i, ships_list in enumerate(ships_list):
        # search pilot numbers at the beginning of a string
        regex_result = re.search(r"^\d*", ships_list)
        pilot = regex_result.group()
        pilots_list.append(pilot)

    return pilots_list

XWS_TEST = """ http://xwing-legacy.com/?f=Separatist%20Alliance&d=v8ZsZ200Z615XWW98W32WWWWY408XWW354WWWW323Y335XWWWWWWW216W353&sn=Pupa&obs= """

print(f"gamemode: {get_yasb_gamemode(XWS_TEST)}")
print(f"points:   {get_yasb_points(XWS_TEST)}")
print(f"faction:  {get_yasb_faction(XWS_TEST)}")
print(f"name:     {get_yasb_squadname(XWS_TEST)}")
print(f"ships:    {get_yasb_ships(XWS_TEST)}")
print(f"pilots:   {get_yasb_pilots(XWS_TEST)}")
# print(xws_compare(XWS_TEST))
# print(f"upgrades: {get_yasb_upgrades(XWS_TEST)}")
