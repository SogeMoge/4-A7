"""Main bot file witt slash commands and events."""
# pylint: disable=wrong-import-position, consider-using-f-string, E0602:undefined-variable

# https://stackoverflow.com/a/65908383
# fixes libgcc_s.so.1 must be installed for pthread_cancel to work
import ctypes

libgcc_s = ctypes.CDLL("libgcc_s.so.1")

# module for importing env variables
from os import environ

# import subprocess
from datetime import date

# modules for YASB link parsing
import json

# from sqlite3 import Error
import logging

# to get http responce from RB
import requests

# pycord modules
import discord

# from discord.ext import commands
# from discord.utils import get
# from discord.commands import Option

# from discord.commands import permissions
from discord.ui import Button, View

# import requests
from dotenv import load_dotenv

# custom bot modules
# import bot.parsing.yasb2squad as yasb_converter


# Configure logging
logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(
    filename="xwsbot.log", encoding="utf-8", mode="w"
)
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)

intents = discord.Intents().all()
bot = discord.Bot(intents=intents)

# Load .env vars and discord token
load_dotenv()
token = environ.get("DISCORD_TOKEN")

#  #########################
# YASB PARSING VARS
GITHUB_USER = "Gan0n29"
GITHUB_BRANCH = "xwing-legacy"
BASE_URL = (
    f"https://raw.githubusercontent.com/{GITHUB_USER}"
    "/ttt-xwing-overlay/{GITHUB_BRANCH}/src/assets/plugins/xwing-data2/"
)
MANIFEST = "data/manifest.json"
CHECK_FREQUENCY = 900  # 15 minutes
#  #########################

UPDATE_REACTION = "\U0001f504"  # circle arrows
accept_reactions = ["\U00002705", "\U0000274e"]  # check and cross marks
date = date.today()

RB_ENDPOINT = (
    """ https://rollbetter-linux.azurewebsites.net/lists/yasb? """
)

#  #########################
#  EVENTS
#  #########################


@bot.event
async def on_ready():
    """Send on_ready console message."""
    print(f"{bot.user} is ready!")


#  #########################
#  LEGACY BUILDER PARSING
#  #########################


@bot.event
async def on_message(message):
    """Parse legacy-yasb link to post embed list."""
    if message.author.bot:  # check that author is not the bot itself
        return

    # if "://xwing-legacy.com/?f" in message.content:
    if "://yasb.app/?f" in message.content:
        yasb_channel = message.channel

        # convert YASB link to XWS
        yasb_link = message.content
        yasb_rb_link = RB_ENDPOINT + yasb_link
        xws_raw = requests.get(yasb_rb_link)

    # await yasb_channel.send(xws_raw.json())

    xws_dict = json.dumps(xws_raw)

    for (
        key,
        value,
    ) in (
        xws_dict.items()
    ):  # add embed title with list name as hyperlink
        if key in ["name"]:
            embed = discord.Embed(
                title=value,
                colour=discord.Colour.random(),
                url=message.content,
                description="YASB 2.5 list",
            )
    try:  # use custom name for squads with default name from yasb
        embed
    except NameError:
        embed = discord.Embed(
            title="Infamous Squadron",
            colour=discord.Colour.random(),
            url=message.content,
            description="YASB 2.5 list",
        )

    embed.set_footer(
        text=message.author.display_name,
        icon_url=message.author.display_avatar,
    )

    await yasb_channel.send(embed=embed)
    await message.delete()


# @bot.event
# async def on_message(message):
#     """parse legacy-yasb link to post embed list"""
#     if message.author.bot:  # check that author is not the bot itself
#         return

#     if "://xwing-legacy.com/?f" in message.content:
#         yasb_channel = message.channel

#         # convert YASB link to XWS
#         yasb_link = message.content
#         # print(f"1) yasb_link = {yasb_link}")
#         yasb_convert = yasb_link.replace(
#             "://xwing-legacy.com/",
#             "://squad2xws.herokuapp.com/yasb/xws",
#         )
#         # print(f"2) yasb_convert = {yasb_convert}")
#         yasb_xws = requests.get(yasb_convert, timeout=10)
#         # print(f"3) yasb_xws = {yasb_xws}")
#         #############
#         # don't know if it works at all???
#         # yasb_xws = unescape(yasb_xws) # delete all characters which prevents proper parsing

#         yasb_json = yasb_xws.json()  # raw XWS in JSON
#         # print(f"4) yasb_json = {yasb_json}")
#         yasb_json = json.dumps(
#             yasb_json
#         )  # convert single quotes to double quotes
#         # print(f"5) yasb_json = {yasb_json}")
#         yasb_dict = json.loads(
#             yasb_json
#         )  # convert JSON to python object
#         # print(f"6) yasb_dict = {yasb_dict}")
#         #############
#         for (
#             key,
#             value,
#         ) in (
#             yasb_dict.items()
#         ):  # add embed title with list name as hyperlink
#             if key in ["name"]:
#                 embed = discord.Embed(
#                     title=value,
#                     colour=discord.Colour.random(),
#                     url=message.content,
#                     description="YASB Legacy 2.0 list",
#                 )
#         try:  # use custom name for squads with default name from yasb
#             embed
#         except NameError:
#             embed = discord.Embed(
#                 title="Infamous Squadron",
#                 colour=discord.Colour.random(),
#                 url=message.content,
#                 description="YASB Legacy 2.0 list",
#             )

#         embed.set_footer(
#             text=message.author.display_name,
#             icon_url=message.author.display_avatar,
#         )

#         ####### TO DO ######## compare parsed results to data in xwing-data manifest
#         # # get JSON manifest from ttt-xwing-overlay repo
#         # manifest_link = requests.get(BASE_URL + MANIFEST)
#         # manifest = manifest_link.json()

#         # files = (
#         #     manifest['damagedecks'] +
#         #     manifest['upgrades'] +
#         #     [manifest['conditions']] +
#         #     [ship for faction in manifest['pilots']
#         #         for ship in faction['ships']]
#         # )

#         # _data = {}
#         # loop = asyncio.get_event_loop()
#         # # get JSON manifest from ttt-xwing-overlay repo
#         ####### TO DO ######## compare parsed results to data in xwing-data manifest

#     for (
#         key,
#         value,
#     ) in (
#         yasb_dict.items()
#     ):  # add embed fields with faction and list name
#         if key in ["faction"]:
#             embed.add_field(name=key, value=value, inline=True)

#     pilots_total = len(yasb_dict["pilots"])

#     for pilot in range(
#         pilots_total
#     ):  # add embed fields for each pilot in a list
#         embed.add_field(
#             name=yasb_dict["pilots"][pilot]["id"],
#             # value=list(yasb_dict["pilots"][pilot]["upgrades"].values()),
#             value=re.sub(
#                 r"[\[\]\']",
#                 "\u200b",
#                 str(
#                     list(
#                         yasb_dict["pilots"][pilot]["upgrades"].values()
#                     )
#                 ),
#             ),
#             inline=False,
#         )
#     await yasb_channel.send(embed=embed)
#     await message.delete()


# http://xwing-legacy.com/ -> http://squad2xws.herokuapp.com/yasb/xws
# http://xwing-legacy.com/?f=Separatist%20Alliance&d=v8ZsZ200Z305X115WW207W229Y356X456W248Y542XW470WW367WY542XW470WW367W&sn=Royal%20escort&obs=

#  #########################
# INFO COMMANDS
#  #########################


@bot.slash_command(
    # guild_ids=[test_guild_id, russian_guild_id]
)  # create a slash command for the supplied guilds
async def rules(ctx):
    """X-Wing 2.0 Legacy rules"""

    button1 = Button(
        label="X-Wing 2.0 Legacy rules",
        url="https://x2po.org/standard",
    )
    view = View(button1)
    await ctx.respond("Rules:", view=view)


@bot.slash_command(
    # guild_ids=[test_guild_id, russian_guild_id]
)  # create a slash command for the supplied guilds
async def builders(ctx):
    """Squad Builders for X-Wing from comunity"""

    button1 = Button(
        label="YASB 2.0 Legacy", url="https://xwing-legacy.com/"
    )
    button2 = Button(
        label="X-Wing 2nd Ed. Squads Designer",
        url="https://www.dmborque.eu/swz",
    )
    view = View(button1, button2)
    await ctx.respond("Squad Builders:", view=view)


bot.run(token)
