"""get legacy-yasb link and convert it to XWS"""
import re

# import pandas

def squad2xws(xws):
    """post welcome message on member join"""

    regex_result = re.search("v\dZ.*", xws)
    separated_xws = regex_result.group().split("Z")
    print(separated_xws)

    game_mode = separated_xws[1]
    print(f"#### game mode = {game_mode}")

    list_points = separated_xws[2]
    print(f"#### points = {list_points}")

    pilots_uncut = separated_xws[3]
    print(f"#### pilots uncut = {pilots_uncut}")

    name_uncut = pilots_uncut[
        pilots_uncut.find("&sn") : pilots_uncut.find("&obs=")
    ]
    name_formatted = name_uncut.replace("%20", " ").lstrip("&sn=")
    print(f"#### squad name = {name_formatted}")

    pilots_cut = pilots_uncut[: pilots_uncut.find("&sn")].strip()
    print(f"#### piots cut = {pilots_cut}")

    separated_pilots = pilots_cut.split("Y")
    print(separated_pilots)

    return separated_pilots


XWS_TEST = """ http://xwing-legacy.com/\
              ?f=Separatist%20Alliance\
              &d=v8ZsZ200Z421XWWWWY429XWWWWWWWY326XWWWW237\
              &sn=Unnamed%20Squadron&obs=" """

squad2xws(XWS_TEST)
