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

    xws_string = json.dumps(xws_raw.json())
    xws_dict = json.loads(xws_string)
    
    squad_list = {}

    embed = discord.Embed(
        title=xws_dict['name'],
        colour=discord.Colour.random(),
        url=message.content,
        description=xws_dict['faction'] + "[" + xws_dict['points'] + "]" + "\n" + xws_dict['pilots'][0] + "\n" + xws_dict['pilots'][2],
    )

    # embed.add_field(
    #     name=discord.Embed.Empty,
    #     value=xws_dict['points'],
    #     inline=True,
    # )

    # embed.add_field(
    #     name=discord.Embed.Empty,
    #     value=xws_dict['pilots'],
    #     inline=True,
    # )

    # for i, ember_heare in enumerate(xws_dict)

    embed.set_footer(
        text=message.author.display_name,
        icon_url=message.author.display_avatar,
    )

    await yasb_channel.send(embed=embed)
    await message.delete()

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
