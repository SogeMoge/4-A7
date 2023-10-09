"""Main bot file witt slash commands and events."""
# pylint: disable=wrong-import-position, consider-using-f-string, E0602:undefined-variable

import ctypes

import logging
import json
import re
import os
import asyncio
import requests
from dotenv import load_dotenv

# pycord modules
import discord
from discord.ui import Button, View

# custom bot modules
from bot.xws2pretty import convert_xws
from bot.xws2pretty import ship_emojis
from bot.xws2pretty import convert_faction_to_dir

# fixes libgcc_s.so.1 must be installed for pthread_cancel to work
libgcc_s = ctypes.CDLL("libgcc_s.so.1")

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
token = os.environ.get("DISCORD_TOKEN")

# Prefix url for squad 2 xws conversion
RB_ENDPOINT = (
    """ https://rollbetter-linux.azurewebsites.net/lists/xwing-legacy? """
)

#  #########################
#  EVENTS
#  #########################


@bot.event
async def on_ready():
    """Send on_ready console message."""
    print(f"{bot.user} is operational! Roger? Roger!")


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

        xws_string = json.dumps(xws_raw.json())
        xws_dict = json.loads(xws_string)
        xws_faction = str(xws_dict['faction'])
        faction_pilots_dir = "xwing-data2/data/pilots/" + convert_faction_to_dir(xws_faction)
        upgrades_dir = "xwing-data2/data/upgrades"

    squad_list = ""
    squad_list += (
        convert_xws(str(xws_dict['faction']))
        + ' ['
        + str(xws_dict['points'])
        + ']\n'
    )

    if 'pilots' in xws_dict and isinstance(xws_dict['pilots'], list):
        for item in xws_dict['pilots']:
            # squad_list += str(item) + '\n'
            if all(key in item for key in ["ship", "id", "points", "upgrades"]):
                values = [
                    item[key]
                    for key in ["ship", "id", "points", "upgrades"]
                ]
                upgrades_list = []
                if isinstance(item['upgrades'], dict):
                    for upgrade_type, upgrade in item['upgrades'].items():
                        for item in upgrade:
                            for filename in os.listdir(upgrades_dir):
                                if filename.endswith(".json"):
                                    with open(
                                        os.path.join(
                                            upgrades_dir, filename
                                        ),
                                        encoding='UTF-8'
                                    ) as f:
                                        data = json.load(f)
                                    for upgrade_obj in data:
                                        if upgrade_obj["xws"] == item:
                                            # Print the name of the matching pilot
                                            item = upgrade_obj["name"]
                            upgrades_list.insert(0, item)
                    upgrades_str = ", ".join(upgrades_list)
                    if values[0] in ship_emojis:
                        # Replace the first word of each line (starting with the second) with the corresponding emoji
                        values[0] = ship_emojis[values[0]]
                    if values[1]:
                        for filename in os.listdir(faction_pilots_dir):
                            if filename.endswith(".json"):
                                with open(
                                    os.path.join(
                                        faction_pilots_dir, filename
                                    ),
                                    encoding='UTF-8'
                                ) as f:
                                    data = json.load(f)
                                for pilots_obj in data["pilots"]:
                                    if pilots_obj["xws"] == values[1]:
                                        values[1] = pilots_obj["name"]
                    if len(upgrades_str) > 0:
                        squad_list += (
                            f"{values[0]} **{values[1]}**: {upgrades_str} [{values[2]}]\n"
                        )
                    else:
                        squad_list += (
                            f"{values[0]} **{values[1]}** [{values[2]}]\n"
                        )

    # lines = squad_list.splitlines()

    # converted_lines = [convert_xws(line) for line in lines]
    # converted_squad_list = "\n".join(converted_lines)

    # lines = converted_squad_list.splitlines()

    # # Join the lines back together into a single string
    # converted_squad_list = "\n".join(lines)

    embed = discord.Embed(
        title=xws_dict['name'],
        colour=discord.Colour.random(),
        url=yasb_url,
        # description=converted_squad_list,
        description=squad_list,
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
    """Post X-Wing 2.0 Legacy rules url."""
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
    """Post Squad Builders for X-Wing from community."""
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
