"""Main bot file witt slash commands and events."""
# pylint: disable=wrong-import-position, consider-using-f-string, E0602:undefined-variable

import ctypes

import logging
import json
import datetime
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
from bot.xws2pretty import convert_faction_to_color

# fixes libgcc_s.so.1 must be installed for pthread_cancel to work
libgcc_s = ctypes.CDLL("libgcc_s.so.1")


# Define a custom formatter that outputs log records as JSON objects
class JsonFormatter(logging.Formatter):
    """Log parsing instance in json format.

    Args:
        logging.Formatter: The base formatter class to inherit from.
    """

    def format(self, record):
        """Format the specified log record as a JSON object.

        Args:
            record (logging.LogRecord): The log record to format.

        Returns:
            str: The log record formatted as a JSON object.

        """
        log_dict = {
            "timestamp": datetime.datetime.fromtimestamp(
                record.created
            ).strftime("%Y-%m-%d %H:%M:%S"),
            "unix_timestamp": record.created,
            "level": record.levelname,
            "message": record.getMessage(),
            "yasb_url": record.yasb_url,
            "squad_list": record.squad_list,
            "username": record.username,
            "module": record.module,
            "line": record.lineno,
            "function": record.funcName,
        }
        return json.dumps(log_dict)


# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler("xwsbot.log")
file_handler.setFormatter(JsonFormatter())
logger.addHandler(file_handler)

intents = discord.Intents().all()
bot = discord.Bot(intents=intents)

# Load .env vars and discord token
load_dotenv()
token = os.environ.get("DISCORD_TOKEN")


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
    bot_has_message_permissions = (
        message.guild
        and message.channel.permissions_for(
            message.guild.me
        ).manage_messages
    )
    # Parse message for YASB link
    yasb_url_pattern = re.compile(
        # r"https?:\/\/xwing-legacy\.com\/\?f=[^\s]+"
        r"https?:\/\/xwing-legacy\.com\/(preview)?\/?\?f=[^\s]+"
    )
    yasb_url_match = yasb_url_pattern.search(message.content)

    # Vars block start
    # Prefix url for squad 2 xws conversion
    RB_ENDPOINT = (
        "https://rollbetter-linux.azurewebsites.net/lists/xwing-legacy?"
    )
    UPGRADES_DIR = "xwing-data2/data/upgrades"
    yasb_url = (
        "https://xwing-legacy.com/?f=Rebel%20Alliance&d=v8ZsZ200Z"
        "&sn=Something%20went%20wrong&obs="
    )
    xws_dict = {}
    FACTION_PILOTS_DIR = "xwing-data2/data/pilots/"

    # if "://xwing-legacy.com/?f" in message.content:
    if yasb_url_match:
        yasb_url = yasb_url_match.group(0)
        yasb_url = yasb_url.replace("http://", "https://")
        yasb_channel = message.channel

        # convert YASB link to XWS
        yasb_rb_url = RB_ENDPOINT + yasb_url
        xws_raw = requests.get(yasb_rb_url, timeout=10)
        # Load xws json as a py dict
        try:
            xws_string = json.dumps(xws_raw.json())
        except Exception as e:
            logger.error(
                f"Transmission failed, wrong URL: {e}",
                extra={
                    "yasb_url": yasb_url,
                    "squad_list": None,
                    "username": message.author.name,
                },
            )
        xws_dict = json.loads(xws_string)
        # Get faction and pilots dir
        xws_faction = str(xws_dict["faction"])
        faction_color = convert_faction_to_color(xws_faction)
        FACTION_PILOTS_DIR += convert_faction_to_dir(xws_faction)
    else:
        return

    def get_upgrades_list(upgrades, upgrades_dir):
        """Get list of upgrades per pilot.

        Args:
            upgrades (dict): upgrades dict from xws
            upgrades_dir (str): upgrades dir in xwing-data2 repo

        Returns:
            str: list of upgrades
        """
        upgrades_list = []
        if not isinstance(upgrades, dict):
            return upgrades_list

        for upgrade_type, upgrade in upgrades.items():
            for item in upgrade:
                for filename in os.listdir(UPGRADES_DIR):
                    if not filename.endswith(".json"):
                        continue

                    with open(
                        os.path.join(UPGRADES_DIR, filename),
                        encoding="UTF-8",
                    ) as f:
                        data = json.load(f)

                    for upgrade_obj in data:
                        if upgrade_obj["xws"] == item:
                            # add hyperlink to goldenrod project
                            upgrade_obj[
                                "name"
                            ] = f"[{upgrade_obj['name']}](https://github.com/SogeMoge/x-wing2.0-project-goldenrod/blob/2.0/src/images/En/upgrades/{upgrade_obj['xws']}.png)"
                            # add cost
                            if "variable" in upgrade_obj["cost"]:
                                upgrade_obj[
                                    "name"
                                ] += f"({upgrade_obj['cost']['variable']})"
                            else:
                                upgrade_obj[
                                    "name"
                                ] += f"({upgrade_obj['cost']['value']})"
                            item = upgrade_obj["name"]
                            break

                upgrades_list.insert(0, item)

        return upgrades_list

    def get_pilot_name(pilot_id, faction_pilots_dir):
        """Get pilot name from xws.

        Args:
            pilot_id (str): pilot xws from yasb
            faction_pilots_dir (str): pilots dir in xwing-data2 repo

        Returns:
            None: converts pilot xws to pilot name with cost
        """
        for filename in os.listdir(FACTION_PILOTS_DIR):
            if filename.endswith(".json"):
                with open(
                    os.path.join(FACTION_PILOTS_DIR, filename),
                    encoding="UTF-8",
                ) as f:
                    data = json.load(f)
                # replace xws with the name of the pilot
                for pilots_obj in data["pilots"]:
                    if pilots_obj["xws"] == pilot_id:
                        pilots_obj["name"] = f"**{pilots_obj['name']}**"
                        pilots_obj["name"] += f"({pilots_obj['cost']})"
                        return pilots_obj["name"]
        return None
    
    def get_gamemode(yasb_url: str) -> tuple[str,int]: #TODO remember type hint for "Or None"
        """Very quick and dirty method to extract game mode of built squad
        

        Args:
            yasb_url (str): original url of squad from xwing-legacy.com

        Returns:
            tuple[str,int]: Game mode information (Game mode name, Total points)
                            Returns None if extraction fails 
        """

        MODE_MAPPING = {
            "s": "Standard",
            "h": "Wildspace",
            "e": "Epic",
            "q": "Quickbuild"
        }

        # Very dirty, will need modified if squadbuilder changes url format
        MODE_CHAR_LOC = 6
        TOTAL_POINTS_SLICE_START = 8
        TOTAL_POINTS_SLICE_END = -1

        # Extract mode and points total from url
        url_mode_pattern = re.compile(
            r"&d=v8Z[sheq]Z\d*Z"
        )
        mode_match = url_mode_pattern.search(yasb_url)
        mode_indicator = mode_match.group()
        
        try: 
            return ( 
            MODE_MAPPING[mode_indicator[MODE_CHAR_LOC]],
            int(mode_indicator[TOTAL_POINTS_SLICE_START:
                               TOTAL_POINTS_SLICE_END]) 
            ) 
        
        except ValueError as e:
            return #Failure of integer conversion implies URL format is off 

        
        
        
    def get_squad_list(xws_dict, upgrades_dir, faction_pilots_dir):
        """Get yasb link and convert it to readable embed.

        Args:
            xws_dict (dict): loaded json from Roll Better endpoint
            upgrades_dir (str): upgrades dir in xwing-data2 repo
            faction_pilots_dir (str): pilots dir in xwing-data2 repo

        Returns:
            str: multiline string of pilots and upgrades
        """
        squad_list = ""
        squad_list += (
            convert_xws(str(xws_dict["faction"]))
            + " ["
            + str(xws_dict["points"])
            + "]\n"
        )
        # Check if pilots is a list and iterate throught pilots
        if "pilots" in xws_dict and isinstance(
            xws_dict["pilots"], list
        ):
            for item in xws_dict["pilots"]:
                # Make sure nesessary keys are present
                if all(
                    key in item
                    for key in ["ship", "id", "points", "upgrades"]
                ):
                    values = [
                        item[key]
                        for key in ["ship", "id", "points", "upgrades"]
                    ]
                    upgrades_list = get_upgrades_list(
                        values[3], UPGRADES_DIR
                    )

                    upgrades_str = ", ".join(upgrades_list)

                    # Replace pilot xws with pilot name
                    pilot_name = get_pilot_name(
                        values[1], FACTION_PILOTS_DIR
                    )
                    if pilot_name:
                        values[1] = pilot_name

                    # If there are upgrades, add them to the list
                    if len(upgrades_str) > 0:
                        squad_list += (
                            f"{ship_emojis.get(values[0])} {values[1]}: "
                            f"{upgrades_str} [{values[2]}]\n"
                        )
                    else:
                        squad_list += f"{ship_emojis.get(values[0])} {values[1]}\n"
        return squad_list

    # Get converted squad list
    squad_list = get_squad_list(
        xws_dict, UPGRADES_DIR, FACTION_PILOTS_DIR
    )
    # Post squad as a description in embed
    embed = discord.Embed(
        title=xws_dict["name"],
        colour=faction_color,
        url=yasb_url,
        description=squad_list,
    )
    embed.set_footer(
        text=message.author.display_name,
        icon_url=message.author.display_avatar,
    )
    await yasb_channel.send(embed=embed)
    logger.info(
        "Incoming YASB link",
        extra={
            "yasb_url": yasb_url,
            "squad_list": squad_list,
            "username": message.author.name,
        },
    )
    # allow the user to delete their query message
    if bot_has_message_permissions:
        prompt_delete_previous_message = await message.channel.send(
            "Delete your message?"
        )
        await prompt_delete_previous_message.add_reaction("✅")
        await prompt_delete_previous_message.add_reaction("❌")
        try:
            reaction, user = await bot.wait_for(
                event="reaction_add",
                timeout=10,
                check=lambda reaction, user: user == message.author,
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
        label="Standard",
        url="https://x2po.org/standard",
    )
    button2 = Button(
        label="Epic",
        url="https://x2po.org/epic",
    )
    button3 = Button(
        label="Wild Space",
        url="https://x2po.org/wild-space",
    )
    button4 = Button(
        label="Adopted Battle Scenarios",
        url="https://x2po.org/battle-scenarios",
    )
    button5 = Button(
        label="Video tutorials",
        url="https://x2po.org/media",
    )
    view = View(button1, button2, button3, button4, button5)
    await ctx.respond("Rules:", view=view)


@bot.slash_command(
    # guild_ids=[test_guild_id, russian_guild_id]
)  # create a slash command for the supplied guilds
async def builders(ctx):
    """Post X-Wing 2.0 Legacy compatible Squad Builders."""
    button1 = Button(
        label="YASB 2.0 Legacy", url="https://xwing-legacy.com/"
    )
    button2 = Button(
        label="X-Wing 2nd Ed. Squads Designer",
        url="https://www.dmborque.eu/swz",
    )
    button3 = Button(
        label="Infinite Arenas",
        url="https://infinitearenas.com/legacy/",
    )
    view = View(button1, button2, button3)
    await ctx.respond("Squad Builders:", view=view)


bot.run(token)
