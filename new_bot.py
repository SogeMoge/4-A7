import json
import logging
import os
import re

import discord
import requests
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

RB_ENDPOINT = "https://rollbetter-linux.azurewebsites.net/lists/xwing-legacy?"

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
        # Rollbetter endpoint expects the *full* YASB URL as a query parameter value
        # Example: https://rollbetter-linux.azurewebsites.net/lists/xwing-legacy?https://xwing-legacy.com/?f=...
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
    # --- Data Extraction Start ---
    try:
        # 1. Get Faction
        faction = xws_dict.get("faction", "Unknown Faction")

        # 2. Get Squad Name
        squad_name = xws_dict.get("name", "Unnamed Squad")

        # 3. Get Pilot IDs and their Upgrades
        pilots_details = []
        pilots_list_data = xws_dict.get("pilots", [])

        for pilot_data in pilots_list_data:
            pilot_id = pilot_data.get("id")
            pilot_upgrades = []
            upgrades_data = pilot_data.get("upgrades", {})

            for upgrade_type, upgrade_ids_list in upgrades_data.items():
                for upgrade_id in upgrade_ids_list:
                    pilot_upgrades.append(
                        {"type": upgrade_type, "id": upgrade_id}
                    )
            pilots_details.append({"id": pilot_id, "upgrades": pilot_upgrades})
        # --- Data Extraction End ---

        logger.info(
            f"Successfully extracted data for '{squad_name}' ({faction})"
        )
        logger.info(f"Faction: {faction}")
        logger.info(f"Squad Name: {squad_name}")
        for pilot in pilots_details:
            logger.info(f"  Pilot ID: {pilot['id']}")
            if pilot["upgrades"]:
                for upgrade in pilot["upgrades"]:
                    logger.info(
                        f"    - Upgrade Type: {upgrade['type']}, ID: {upgrade['id']}"
                    )
            else:
                logger.info("    - No upgrades")

        # Example of using the extracted data in the embed:
        # You can format this much better, this is just a basic example
        embed_description = f"**Squad:** {squad_name}\n"
        embed_description += f"**Faction:** {faction.replace('_', ' ').title()}\n\n"  # Format faction name nicely
        embed_description += "**Pilots:**\n"
        for pilot in pilots_details:
            embed_description += f"- `{pilot['id']}`\n"
            for upgrade in pilot["upgrades"]:
                embed_description += (
                    f"  - *{upgrade['type']}*: `{upgrade['id']}`\n"
                )
        embed = discord.Embed(
            title=f"Squad Details: {squad_name}",
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
        # Catch potential errors during data extraction (e.g., unexpected format)
        logger.error(
            f"Error processing XWS data structure for URL {found_url}. Error: {e}",
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
