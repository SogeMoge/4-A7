import asyncio  # <-- Import asyncio
import json
import logging
import os
import re

import discord
import requests
from dotenv import load_dotenv

# Assuming these are correctly defined/imported from your project structure
from bot.mongo.init_db import prepare_collections
from bot.mongo.search import (
    find_faction,
    find_pilot,
    find_ship_by_pilot,
    find_upgrade,
)
from bot.xws2pretty import ini_emojis, ship_emojis

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
GOLDENROD_PILOTS_URL = (
    "https://github.com/SogeMoge/x-wing2.0-project-goldenrod/blob/2.0/"
    "src/images/En/pilots/"
)
GOLDENROD_UPGRADES_URL = (
    "https://github.com/SogeMoge/x-wing2.0-project-goldenrod/blob/2.0/"
    "src/images/En/upgrades/"
)

# --- Constants ---
DISCORD_EMBED_DESCRIPTION_LIMIT = 4096

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
log_file = "xwsbot.log"
file_handler = logging.FileHandler(log_file)
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
file_handler.setFormatter(formatter)
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

# --- Lock Storage ---
# Dictionary to hold an asyncio.Lock for each channel being processed
channel_locks = {}


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    logger.info(f"{bot.user} is operational! Roger? Roger!.")


# --- Helper Functions (can remain here or be moved outside on_message) ---
# It's often cleaner to define helpers outside the event handler if they don't
# depend directly on message-specific variables other than passed arguments.
def get_gamemode(yasb_url: str) -> tuple[str, int]:
    MODE_MAPPING = {
        "s": "Standard",
        "h": "Wildspace",
        "e": "Epic",
        "q": "Quickbuild",
    }
    MODE_CHAR_LOC = 6
    TOTAL_POINTS_SLICE_START = 8
    TOTAL_POINTS_SLICE_END = -1
    url_mode_pattern = re.compile(r"&d=v8Z[sheq]Z\d*Z")
    mode_match = url_mode_pattern.search(yasb_url)
    # Basic check to prevent error if pattern not found (optional but safer)
    if not mode_match:
        raise ValueError("Could not find game mode pattern in URL")
    mode_indicator = mode_match.group()
    try:
        return (
            MODE_MAPPING[mode_indicator[MODE_CHAR_LOC]],
            int(
                mode_indicator[TOTAL_POINTS_SLICE_START:TOTAL_POINTS_SLICE_END]
            ),
        )
    except (ValueError, KeyError, IndexError):
        # Catch potential errors during parsing/lookup
        raise ValueError(
            "Failed to parse game mode or points from URL substring"
        )


def get_ship_stat_value(stats_list, stat_type_to_find):
    if not isinstance(stats_list, list):
        return None
    for stat in stats_list:
        if isinstance(stat, dict) and stat.get("type") == stat_type_to_find:
            return stat.get("value")
    return None


def calculate_upgrade_cost(upgrade_data, ship_details, pilot_info):
    # Simplified version from previous steps, assuming structure mostly correct
    if not isinstance(upgrade_data, dict):
        return None
    cost_obj = upgrade_data.get("cost")
    if not isinstance(cost_obj, dict):
        return None
    if "value" in cost_obj:
        try:
            return int(cost_obj["value"])
        except (ValueError, TypeError):
            return None
    if "variable" in cost_obj:
        variable_type = cost_obj.get("variable")
        values_dict = cost_obj.get("values")
        if not isinstance(values_dict, dict):
            return None
        lookup_key = None
        # Ensure ship_details and pilot_info are not None before accessing .get()
        ship_size = ship_details.get("size") if ship_details else None
        ship_stats = ship_details.get("stats") if ship_details else None
        pilot_initiative = pilot_info.get("initiative") if pilot_info else None

        if variable_type == "size":
            lookup_key = ship_size
        elif variable_type == "agility":
            agility = get_ship_stat_value(ship_stats, "agility")
            if agility is not None:
                lookup_key = str(agility)
        elif variable_type == "initiative":
            if pilot_initiative is not None:
                lookup_key = str(pilot_initiative)

        if lookup_key is not None:
            raw_cost = values_dict.get(lookup_key)
            if raw_cost is not None:
                try:
                    return int(raw_cost)
                except (ValueError, TypeError):
                    return None
            else:
                return None
        else:
            return None
    return None


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    yasb_url_pattern = re.compile(
        r"https?:\/\/xwing-legacy\.com\/(preview)?\/?\?f=[^\s]+"
    )
    yasb_url_match = yasb_url_pattern.search(message.content)

    if yasb_url_match:
        # --- Get or create lock for this channel ---
        # Using setdefault is a concise way to get the lock if it exists,
        # or create and store it if it doesn't.
        lock = channel_locks.setdefault(message.channel.id, asyncio.Lock())

        # --- Acquire lock before processing ---
        # The 'async with' ensures the lock is released even if errors occur
        async with lock:
            logger.info(
                f"Acquired lock for channel {message.channel.id} by user {message.author.name}"
            )  # Optional: Log lock acquisition

            # --- Start of Protected Processing Block ---
            found_url = yasb_url_match.group(0)
            if found_url.startswith("http://"):
                found_url = found_url.replace("http://", "https://", 1)

            logger.info(
                f"Processing locked request:\n"
                f" Channel: {message.channel.id}\n"
                f" From: {message.author.name}\n"
                f" URL: {found_url}"
            )

            rollbetter_url = RB_ENDPOINT + found_url
            logger.info(f"Requesting XWS from Rollbetter: {rollbetter_url}")

            try:
                response = requests.get(rollbetter_url, timeout=15)
                response.raise_for_status()
                try:
                    xws_dict = response.json()
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
                    await message.channel.send(
                        f"Sorry, {message.author.mention},"
                        " I couldn't understand the format"
                        " of the list from that link."
                    )
                    return  # Exit the locked section

            except requests.exceptions.RequestException as e:
                logger.error(
                    f"Failed to fetch XWS data from Rollbetter.\n"
                    f"URL: {rollbetter_url}. Error: {e}",
                    extra={
                        "yasb_url": found_url,
                        "username": message.author.name,
                    },
                )
                await message.channel.send(
                    f"Sorry, {message.author.mention},"
                    " I couldn't retrieve the list data from the server."
                )
                return  # Exit the locked section

            # --- Data Extraction Start (inside lock) ---
            try:
                faction_xws = xws_dict["faction"]
                faction_details = find_faction(faction_xws, MONGODB_URI)
                if not faction_details:  # Basic check for safety
                    logger.error(
                        f"Could not find faction details for {faction_xws}"
                    )
                    await message.channel.send(
                        f"Sorry, could not find details for faction '{faction_xws}'."
                    )
                    return  # Exit locked section

                squad_name = xws_dict.get("name", "Unnamed Squad")
                squad_points = xws_dict["points"]
                squad_gamemode = get_gamemode(
                    xws_dict["vendor"]["yasb"]["link"]
                )
                bid = (
                    int(squad_gamemode[1]) - int(squad_points)
                    if squad_gamemode
                    else None
                )

                if "pilots" not in xws_dict or not xws_dict["pilots"]:
                    logger.warning(f"No pilots found in list: {found_url}")
                    await message.channel.send(
                        f"The list appears to be empty, {message.author.mention}."
                    )
                    return  # Exit locked section

                list_details_raw = []
                for pilot_entry in xws_dict["pilots"]:
                    pilot_id = pilot_entry.get("id")
                    if not pilot_id:
                        logger.warning("Skipping pilot entry with missing ID.")
                        continue  # Skip malformed entry

                    pilot_info = find_pilot(pilot_id, MONGODB_URI)
                    if not pilot_info:
                        logger.error(
                            f"Could not find pilot info for ID: {pilot_id}"
                        )
                        # Consider how to handle missing pilot - skip or show error?
                        # Skipping for now to avoid crashing embed generation
                        continue

                    upgrades_info = []
                    for upgrade_ids_list in pilot_entry.get(
                        "upgrades", {}
                    ).values():
                        if isinstance(upgrade_ids_list, list):
                            for upgrade_id in upgrade_ids_list:
                                upgrade_details = find_upgrade(
                                    upgrade_id, MONGODB_URI
                                )
                                if not upgrade_details:
                                    logger.error(
                                        f"Could not find upgrade info for ID: {upgrade_id}"
                                    )
                                    # Add placeholder or skip? Adding placeholder for now.
                                    upgrades_info.append(
                                        {
                                            "name": f"Unknown({upgrade_id})",
                                            "cost_calculated": None,
                                            "sides": [{"image": ""}],
                                        }
                                    )
                                else:
                                    upgrades_info.append(upgrade_details)

                    list_details_raw.append(
                        {
                            "pilot_entry": pilot_entry,  # Keep if needed elsewhere
                            "pilot_info": pilot_info,
                            "upgrades_info": upgrades_info,
                        }
                    )

                logger.info(
                    f"Successfully extracted data for '{squad_name}' ({faction_xws}) in channel {message.channel.id}"
                )

                # --- Embed Generation (inside lock) ---
                squad_hyperlink = f"[{squad_name}]({found_url})"
                embed_list_title = (
                    f"{squad_hyperlink}\n"
                    f"{faction_details['name']} "
                    f"[{squad_points}/{squad_gamemode[1]}: {squad_gamemode[0]}]\n"
                    f"-# Bid: {bid if bid is not None else '?'}\n"
                )

                embeds_to_send = []
                current_description = embed_list_title

                for pilot_data_raw in list_details_raw:
                    pilot = pilot_data_raw["pilot_info"]
                    upgrades = pilot_data_raw[
                        "upgrades_info"
                    ]  # Use pre-fetched upgrade list
                    ship_details = find_ship_by_pilot(
                        pilot.get("xws"), MONGODB_URI
                    )  # Fetch ship details
                    if not ship_details:  # Handle missing ship case
                        logger.error(
                            f"Could not find ship details for pilot {pilot.get('name')} ({pilot.get('xws')})"
                        )
                        # Use placeholder to prevent crash
                        ship_details = {
                            "xws": "unknown_ship",
                            "name": "Unknown Ship",
                            "size": "Unknown",
                            "stats": [],
                        }

                    current_pilot_total_cost = 0
                    try:
                        current_pilot_total_cost += int(
                            pilot.get("cost", 0)
                        )  # Use .get with default
                    except (ValueError, TypeError):
                        logger.warning(
                            f"Could not parse pilot cost for {pilot.get('name', 'Unknown Pilot')}"
                        )

                    # Use .get for safety with emojis and pilot details
                    ship_emoji = ship_emojis.get(ship_details["xws"], "❓")
                    ini_emoji = ini_emojis.get(pilot.get("initiative"), "❓")
                    pilot_name = pilot.get("name", "Unknown Pilot")
                    pilot_image = pilot.get(
                        "image", GOLDENROD_PILOTS_URL
                    )  # Fallback URL
                    pilot_cost = pilot.get("cost", "?")

                    pilot_line_base = (
                        f"{ship_emoji} {ini_emoji} "
                        f"**[{pilot_name}]({pilot_image})**({pilot_cost})"
                    )

                    upgrades_formatted = ""
                    if upgrades:
                        upgrade_display_parts = []
                        for upg in upgrades:
                            # Calculate cost using fetched details
                            cost = calculate_upgrade_cost(
                                upg, ship_details, pilot
                            )
                            if cost is not None:
                                current_pilot_total_cost += cost
                            else:
                                logger.warning(
                                    f"Could not determine cost for upgrade {upg.get('name', 'Unknown Upgrade')} on pilot {pilot_name}"
                                )

                            cost_str = (
                                f"({cost})" if cost is not None else "(?)"
                            )
                            # Safely get upgrade details
                            upgrade_name = upg.get("name", "Unknown Upgrade")
                            image_url = GOLDENROD_UPGRADES_URL  # Default
                            try:
                                # Check structure before accessing
                                if (
                                    upg.get("sides")
                                    and isinstance(upg["sides"], list)
                                    and len(upg["sides"]) > 0
                                    and isinstance(upg["sides"][0], dict)
                                ):
                                    image_url = upg["sides"][0].get(
                                        "image", GOLDENROD_UPGRADES_URL
                                    )
                            except Exception as img_err:  # Catch any error during image access
                                logger.error(
                                    f"Error accessing image URL for upgrade {upgrade_name}: {img_err}"
                                )

                            link_part = f"[{upgrade_name}]({image_url})"
                            display_string = f"{link_part} {cost_str}"
                            upgrade_display_parts.append(display_string)

                        if upgrade_display_parts:
                            upgrades_formatted = (
                                f": *{', '.join(upgrade_display_parts)}*"
                            )

                    if upgrades_formatted == "":
                        final_pilot_line = (
                            f"{pilot_line_base} {upgrades_formatted}\n"
                        )
                    else:
                        final_pilot_line = f"{pilot_line_base}{upgrades_formatted} __**[{current_pilot_total_cost}]**__\n"

                    if (
                        len(current_description) + len(final_pilot_line)
                        > DISCORD_EMBED_DESCRIPTION_LIMIT
                    ):
                        embed = discord.Embed(
                            description=current_description,
                            color=discord.Color.blue(),
                        )
                        embeds_to_send.append(embed)
                        current_description = final_pilot_line
                    else:
                        current_description += final_pilot_line

                # --- Add the last embed (inside lock) ---
                if current_description:
                    final_embed = discord.Embed(
                        description=current_description,
                        color=discord.Color.blue(),
                    )
                    embeds_to_send.append(final_embed)

                # --- Finalize and Send Embeds (inside lock) ---
                if not embeds_to_send:
                    logger.warning(
                        f"No embeds generated for {squad_name} in channel {message.channel.id}, list might be empty or header too long."
                    )
                else:
                    total_embeds = len(embeds_to_send)
                    base_footer_text = (
                        f"List submitted by: {message.author.display_name}"
                    )
                    footer_icon_url = (
                        message.author.display_avatar.url
                        if message.author.display_avatar
                        else None
                    )

                    logger.info(
                        f"Sending {total_embeds} embed(s) for {squad_name} in channel {message.channel.id}"
                    )
                    for i, embed_to_send in enumerate(embeds_to_send):
                        part_counter = f"Part {i + 1}/{total_embeds}"
                        final_footer_text = (
                            f"{base_footer_text} | {part_counter}"
                            if total_embeds > 1
                            else base_footer_text
                        )
                        embed_to_send.set_footer(
                            text=final_footer_text, icon_url=footer_icon_url
                        )
                        # Send messages sequentially while holding the lock
                        await message.channel.send(embed=embed_to_send)
                    logger.info(
                        f"Finished sending embeds for {squad_name} in channel {message.channel.id}"
                    )

            except Exception as e:
                # Catch errors during data extraction/processing inside the lock
                logger.error(
                    f"Error processing XWS data structure for URL {found_url} in channel {message.channel.id}. Error: {e}",
                    exc_info=True,
                    extra={
                        "yasb_url": found_url,
                        "username": message.author.name,
                        "xws_data": xws_dict
                        if "xws_dict" in locals()
                        else "XWS data not available",
                    },
                )
                await message.channel.send(
                    f"Sorry, {message.author.mention},"
                    " there was an issue processing the structure"
                    " of the squad list."
                )
                # Lock will still be released automatically by 'async with'

            # --- End of Protected Processing Block ---
            logger.info(
                f"Released lock for channel {message.channel.id}"
            )  # Optional: Log lock release


# --- Bot Startup ---
if not DISCORD_TOKEN or DISCORD_TOKEN == "YOUR_REAL_BOT_TOKEN":
    logger.error("FATAL: Discord bot token is missing or placeholder!")
    exit(
        "Discord bot token is missing."
        " Please set it in your .env file or script."
    )
else:
    try:
        prepare_collections(XWS_DATA_ROOT_DIR, MONGODB_URI)
        logger.info("Starting bot...")
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
