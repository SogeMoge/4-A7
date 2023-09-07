"""get legacy-yasb link and convert it to XWS"""
import re
import json

##### YASB PARSING VARS #####
# GITHUB_USER = "SogeMoge"
# GITHUB_BRANCH = "legacy"
# BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/xwing-data2/{GITHUB_BRANCH}/"
# MANIFEST = "data/manifest.json"
# CHECK_FREQUENCY = 900  # 15 minutes
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

RB_ENDPOINT = """ https://rollbetter-linux.azurewebsites.net/lists/yasb? """
YASB_APP_LINK = """ https://yasb.app/?f=Rebel%20Alliance&d=v9ZhZ20Z462X130WW371Y16X331W133W108Y73X119WWWWW235WW313Y500X135W106W445Y79XW11WWWW249&sn=Random%20Squad&obs= """

print(f"gamemode: {get_yasb_gamemode(XWS_TEST)}")
print(f"points:   {get_yasb_points(XWS_TEST)}")
print(f"faction:  {get_yasb_faction(XWS_TEST)}")
print(f"name:     {get_yasb_squadname(XWS_TEST)}")
print(f"ships:    {get_yasb_ships(XWS_TEST)}")
print(f"pilots:   {get_yasb_pilots(XWS_TEST)}")
# print(xws_compare(XWS_TEST))
# print(f"upgrades: {get_yasb_upgrades(XWS_TEST)}")
