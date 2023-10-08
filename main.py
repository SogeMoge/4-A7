"""Main bot file witt slash commands and events."""
# pylint: disable=wrong-import-position, consider-using-f-string, E0602:undefined-variable

import ctypes

import logging
import json
import re
import os
from datetime import date
import asyncio
import requests
from dotenv import load_dotenv

# pycord modules
import discord
from discord.ui import Button, View

# custom bot modules
from bot.xws2pretty import convert_xws
from bot.xws2pretty import ship_emojis

# fixes libgcc_s.so.1 must be installed for pthread_cancel to work
libgcc_s = ctypes.CDLL("libgcc_s.so.1")

# # Configure logging
# logger = logging.getLogger("discord")
# logger.setLevel(logging.INFO)
# handler = logging.FileHandler(
#     filename="xwsbot.log", encoding="utf-8", mode="w"
# )
# handler.setFormatter(
#     logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
# )
# logger.addHandler(handler)
# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('xwsbot.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
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
    """ https://rollbetter-linux.azurewebsites.net/lists/xwing-legacy? """
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
    bot_has_message_permissions = message.guild and \
        message.channel.permissions_for(message.guild.me).manage_messages
    yasb_url_pattern = re.compile(
        r'https?:\/\/xwing-legacy\.com\/\?f=[^\s]+')
    yasb_url_match = yasb_url_pattern.search(message.content)

    # if "://xwing-legacy.com/?f" in message.content:
    if yasb_url_match:
        yasb_url = yasb_url_match.group(0)
        yasb_url = yasb_url.replace('http://', 'https://')
        yasb_channel = message.channel

        # convert YASB link to XWS
        yasb_rb_url = RB_ENDPOINT + yasb_url
        xws_raw = requests.get(yasb_rb_url, timeout=10)

    # await yasb_channel.send(xws_raw.json())

        xws_string = json.dumps(xws_raw.json())
        xws_dict = json.loads(xws_string)
        xws_faction = str(xws_dict['faction'])
        faction_pilots_dir = "xwing-data2/data/pilots" + xws_faction
        upgrades_dir = "xwing-data2/data/upgrades"

        squad_list = ""
        squad_list += (
            str(xws_dict['faction']) +
            ' [' +
            str(xws_dict['points']) +
            ']' +
            '\n'
        )

        if 'pilots' in xws_dict and isinstance(xws_dict['pilots'], list):
            for item in xws_dict['pilots']:
                if all(key in item for key in ["ship", "name", "points", "upgrades"]):
                    values = [item[key] for key in [
                                    "ship",
                                    "xws",
                                    "points",
                                    "upgrades"
                            ]
                    ]
                    upgrades = []
                    for upgrade_type, upgrade_list in item['upgrades'].items():
                        # change upgrade to card name
                        for upgrade in upgrade_list:
                            for filename in os.listdir(faction_pilots_dir):
                                if filename.endswith(".json"):
                                    # Load the JSON data from the file
                                    with open(os.path.join(upgrades_dir, filename), encoding='utf-8') as f:
                                        data = json.load(f)
                                    # Search for the xws value in the upgrades objects  
                                    for obj in data:
                                        if obj["xws"] == values[1]:
                                            # Add name of the matching upgrade to the list
                                            upgrade = str(obj["name"])   
                                            upgrades.extend(upgrade)
                    upgrades_str = ", ".join(upgrades)
                    
                    # change xws to card name
                    for filename in os.listdir(faction_pilots_dir):
                        if filename.endswith(".json"):
                            # Load the JSON data from the file
                            with open(os.path.join(faction_pilots_dir, filename), encoding='utf-8') as f:
                                data = json.load(f)
                            # Search for the xws value in the pilots array
                            for pilot in data["pilots"]:
                                if pilot["xws"] == values[1]:
                                    # Print the name of the matching pilot
                                    values[1] = str(pilot["name"])

                    squad_list += f"{values[0]}, {values[1]}: {upgrades_str} [{values[2]}]\n"

        lines = squad_list.splitlines()

        converted_lines = [convert_xws(line) for line in lines]
        converted_squad_list = "\n".join(converted_lines)

        lines = converted_squad_list.splitlines()
    
    # Replace the first word of each line (starting with the second) with the ship emoji
    for i in range(1, len(lines)):
        words = lines[i].split()
        ship_name = words[0].lower().replace(',', '')
        print(ship_name)
        if ship_name in ship_emojis:
            words[0] = ship_emojis[ship_name]
            print(words[0])
        lines[i] = " ".join(words)

    # Join the lines back together into a single string
    converted_squad_list = "\n".join(lines)

    embed = discord.Embed(
        title=xws_dict['name'],
        colour=discord.Colour.random(),
        url=yasb_url,
        description=converted_squad_list,
    )

    embed.set_footer(
        text=message.author.display_name,
        icon_url=message.author.display_avatar,
    )

    await yasb_channel.send(embed=embed)

    # allow the user to delete their query message
    if bot_has_message_permissions:
        prompt_delete_previous_message = await message.channel.send("Delete your message?")
        await prompt_delete_previous_message.add_reaction("✅")
        await prompt_delete_previous_message.add_reaction("❌")
        try:
            reaction, user = await bot.wait_for(
                event="reaction_add",
                timeout=10,
                check=lambda reaction, user: user == message.author
            )
            if str(reaction.emoji) == "✅":
                await message.delete()
                await prompt_delete_previous_message.delete()
                return
            if str(reaction.emoji) == "❌":
                await prompt_delete_previous_message.delete()
                return
        except asyncio.TimeoutError:
            await prompt_delete_previous_message.delete()
            return


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
