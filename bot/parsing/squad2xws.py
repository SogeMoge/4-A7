"""get legacy-yasb link and convert it to XWS"""
import re

# import pandas


def parse_yasb_link(yasb_link):
    """parse xwing-legacy yasb link
    and get pilots with upgrades as a list"""

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


def get_yasb_ships(yasb_link):
    """parse yasb link to get list of ships in a list"""

    separated_yasb_link = parse_yasb_link(yasb_link)
    ships_uncut = separated_yasb_link[3]

    ships_cut = ships_uncut[: ships_uncut.find("&sn")].strip()
    ships_list = ships_cut.split("Y")

    return ships_list


# def parse_yasb_pilots(ships_list):
#     """get pilots from list of ships"""

#     for i in range(len(pilots_list)):
#         print(pilots_list[i])


# def parse_yasb_upgrades(ships_list):
#     """get upgrades from list of hips per pilot"""

#     for i in range(len(ships_list)):
#         print(ships_list[i])


XWS_TEST = """ http://xwing-legacy.com//?f=Separatist%20Alliance&d=v8ZsZ200Z615XWW98W32WWWWY408XWW354WWWW323Y335XWWWWWWW216W353&sn=Pupa&obs= """
# XWS_TEST = """ http://xwing-legacy.com//?f=Galactic%20Republic&d=v8ZsZ200Z361XW471W88W213W71W108Y412XWWW32WWW&sn=Unnamed%20Squadron&obs= """
print(f"gamemode: {get_yasb_gamemode(XWS_TEST)}")
print(f"points:   {get_yasb_points(XWS_TEST)}")
print(f"name:     {get_yasb_squadname(XWS_TEST)}")
print(f"pilots:   {get_yasb_ships(XWS_TEST)}")
