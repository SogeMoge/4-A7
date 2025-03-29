import json
import logging
import os
import re

import discord
import requests
from dotenv import load_dotenv

from bot.mongo.init_db import prepare_collections
from bot.mongo.search import find_faction, find_pilot, find_ship_by_pilot
from bot.xws2pretty import ship_emojis

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://root:example@localhost:27017/xwingdata?authSource=admin",
)
RB_ENDPOINT = os.getenv(
    "RB_ENDPOINT",
    "https://rollbetter-linux.azurewebsites.net/lists/xwing-legacy?",
)
XWS_DATA_ROOT_DIR = "submodules/xwing-data2/data"

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(
    logging.INFO
)  # Changed to INFO for less verbose default logging
log_file = "xwsbot.log"
file_handler = logging.FileHandler(log_file)
# Added timestamp, level, logger name, and message
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
file_handler.setFormatter(formatter)
# Add a stream handler to see logs in the console too
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True
intents.presences = True

bot = discord.Bot(intents=intents)


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    logger.info(f"{bot.user} is operational! Roger? Roger!.")


@bot.event
async def on_message(message: discord.Message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Define the regex pattern for YASB URLs
    yasb_url_pattern = re.compile(
        r"https?:\/\/xwing-legacy\.com\/(preview)?\/?\?f=[^\s]+"
    )
    yasb_url_match = yasb_url_pattern.search(message.content)

    if yasb_url_match:
        found_url = yasb_url_match.group(0)
        if found_url.startswith("http://"):
            found_url = found_url.replace("http://", "https://", 1)

        logger.info(
            f"Detected potential yasb URL:\n"
            f" From: {message.author.name}\n"
            f" URL: {found_url}"
        )

        # Construct the Rollbetter URL
        # Rollbetter endpoint expects the *full* YASB URL
        #   as a query parameter value
        # Ex: https://rollbetter-linux.azurewebsites.net/lists/xwing-legacy?
        #   https://xwing-legacy.com/?f=...
        rollbetter_url = RB_ENDPOINT + found_url
        logger.info(f"Requesting XWS from Rollbetter: {rollbetter_url}")

        try:
            response = requests.get(rollbetter_url, timeout=15)
            # Raise an exception for bad status codes (4xx or 5xx)
            response.raise_for_status()

            # Attempt to parse the JSON response
            try:
                xws_dict = response.json()
                # Pretty print the raw JSON to log for debugging
                logger.debug(
                    f"Received XWS JSON:\n{json.dumps(xws_dict, indent=2)}"
                )
            except json.JSONDecodeError as e:
                logger.error(
                    f"Failed to decode JSON response from Rollbetter.\n"
                    f"URL: {rollbetter_url}.\n"
                    f"Error: {e}. Response text: {response.text[:500]}...",
                    extra={
                        "yasb_url": found_url,
                        "username": message.author.name,
                    },
                )
                # notify the user in Discord
                await message.channel.send(
                    f"Sorry, {message.author},"
                    " I couldn't understand the format"
                    " of the list from that link."
                )
                return

        except requests.exceptions.RequestException as e:
            logger.error(
                f"Failed to fetch XWS data from Rollbetter.\n"
                f"URL: {rollbetter_url}. Error: {e}",
                extra={"yasb_url": found_url, "username": message.author.name},
            )
            # notify the user in Discord
            await message.channel.send(
                f"Sorry, {message.author},"
                " I couldn't retrieve the list data from the server."
            )
            return

    def get_gamemode(
        yasb_url: str,
    ) -> tuple[str, int]:  # TODO remember type hint for "Or None"
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
            "q": "Quickbuild",
        }

        # Very dirty, will need modified if squadbuilder changes url format
        MODE_CHAR_LOC = 6
        TOTAL_POINTS_SLICE_START = 8
        TOTAL_POINTS_SLICE_END = -1

        # Extract mode and points total from url
        url_mode_pattern = re.compile(r"&d=v8Z[sheq]Z\d*Z")
        mode_match = url_mode_pattern.search(yasb_url)
        mode_indicator = mode_match.group()

        try:
            return (
                MODE_MAPPING[mode_indicator[MODE_CHAR_LOC]],
                int(
                    mode_indicator[
                        TOTAL_POINTS_SLICE_START:TOTAL_POINTS_SLICE_END
                    ]
                ),
            )
        except ValueError:
            return  # Failure of integer conversion implies URL format is off

    # --- Data Extraction Start ---
    try:
        # 1. Get Faction
        faction_xws = xws_dict.get("faction", "Unknown Faction")
        faction_details = find_faction(faction_xws, MONGODB_URI)

        # 2. Get Squad Name
        squad_name = xws_dict.get("name", "Unnamed Squad")

        # 3. Get Squad points
        squad_points = xws_dict.get("points", "Unnamed Squad")

        # 4. Get Squad game mode
        squad_gamemode = get_gamemode(
            xws_dict.get("vendor").get("yasb").get("link")
        )
        if squad_gamemode:
            bid = int(squad_gamemode[1]) - int(squad_points)
        else:
            bid = None

        pilots_details = [
            find_pilot(pilot["id"], MONGODB_URI)
            for pilot in xws_dict["pilots"]
        ]
        # --- Data Extraction End ---

        logger.info(
            f"Successfully extracted data for '{squad_name}' ({faction_xws})"
        )

        # Example of using the extracted data in the embed:
        # You can format this much better, this is just a basic example
        squad_hyperlink = f"[{squad_name}]({found_url})"
        embed_list_title = (
            f"{squad_hyperlink}\n"
            f"{faction_details['name']} "
            f"[{squad_points}/"
            + str(squad_gamemode[1])
            + ": "
            + str(squad_gamemode[0])
            + "]\n"
            f"Bid: {bid}\n"
        )
        embed_description = embed_list_title

        for pilot in pilots_details:
            ship_details = find_ship_by_pilot(pilot["xws"], MONGODB_URI)
            pilot_line = (
                f"{ship_emojis[ship_details['xws']]} "
                f"i{pilot['initiative']} {pilot['name']}\n"
            )
            embed_description += pilot_line
        embed = discord.Embed(
            description=embed_description,
            color=discord.Color.blue(),  # Optional: set a color
        )
        embed.set_footer(
            text=f"List submitted by: {message.author.display_name}",
            icon_url=message.author.display_avatar.url,
        )
        # You could add the original YASB link as a field or in the description
        embed.add_field(
            name="Original Link",
            value=f"[View on YASB]({found_url})",
            inline=False,
        )
        await message.channel.send(embed=embed)

    except Exception as e:
        # Catch potential errors during data extraction
        #   (e.g., unexpected format)
        logger.error(
            "Error processing XWS data structure for"
            f" URL {found_url}. Error: {e}",
            exc_info=True,  # Include traceback information in the log
            extra={
                "yasb_url": found_url,
                "username": message.author.name,
                "xws_data": xws_dict,
            },
        )
        # Optionally notify the user
        await message.channel.send(
            f"Sorry, {message.author},"
            " there was an issue processing the structure"
            " of the squad list."
        )

        embed = discord.Embed(description=f"XWS export: {xws_dict}")
        embed.set_footer(
            text=f"{message.author.display_name}",
            icon_url=message.author.display_avatar.url,
        )
        await message.channel.send(embed=embed)


if not DISCORD_TOKEN or DISCORD_TOKEN == "YOUR_REAL_BOT_TOKEN":
    logger.error("FATAL: Discord bot token is missing or placeholder!")
    exit(
        "Discord bot token is missing."
        " Please set it in your .env file or script."
    )
else:
    try:
        prepare_collections(XWS_DATA_ROOT_DIR, MONGODB_URI)
        bot.run(DISCORD_TOKEN)
    except discord.errors.LoginFailure:
        logger.error(
            "FATAL: Improper token passed. Check your Discord bot token."
        )
    except Exception as e:
        logger.error(
            f"FATAL: An unexpected error occurred while running the bot: {e}",
            exc_info=True,
        )
