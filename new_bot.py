import json
import logging
import os
import re

import discord
import requests
from dotenv import load_dotenv

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

    def get_ship_stat_value(stats_list, stat_type_to_find):
        """Safely extracts a specific stat value (like agility) from the ship's stats list."""
        if not isinstance(stats_list, list):
            return None
        for stat in stats_list:
            # Ensure stat is a dictionary before accessing keys
            if (
                isinstance(stat, dict)
                and stat.get("type") == stat_type_to_find
            ):
                return stat.get("value")  # Return the value if type matches
        return None  # Stat type not found

    def calculate_upgrade_cost(upgrade_data, ship_details, pilot_info):
        """
        Calculates the cost of an upgrade based on its potentially complex cost structure.
        Returns the integer cost or None if undetermined.
        """
        if not isinstance(upgrade_data, dict):
            return None
        cost_obj = upgrade_data.get("cost")

        # Case 1: Simple {'value': X} cost
        if "value" in cost_obj:
            try:
                # Directly return the integer value
                return int(cost_obj["value"])
            except (ValueError, TypeError):
                # Value wasn't a valid integer representation
                return None

        # Case 2: Variable cost {'variable': '...', 'values': {...}}
        if "variable" in cost_obj:
            variable_type = cost_obj.get("variable")
            values_dict = cost_obj.get("values")
            if not isinstance(values_dict, dict):
                # Malformed variable cost structure
                return None

            lookup_key = None
            # Determine the key needed to look up the cost in values_dict
            if variable_type == "size":
                # Key is ship size (e.g., "Small", "Medium")
                lookup_key = ship_details.get("size")
            elif variable_type == "agility":
                # Key is ship agility (e.g., "0", "1", "2")
                # Need to extract agility from ship_details['stats']
                agility = get_ship_stat_value(
                    ship_details.get("stats"), "agility"
                )
                if agility is not None:
                    lookup_key = str(
                        agility
                    )  # Keys in values_dict are usually strings
            elif variable_type == "initiative":
                # Key is pilot initiative (e.g., "0", "1", ..., "6")
                initiative = pilot_info.get("initiative")
                if initiative is not None:
                    lookup_key = str(
                        initiative
                    )  # Keys in values_dict are usually strings
            # Add other variable types here if needed (e.g., 'hull', etc.)

            if lookup_key is not None:
                # We have a key, now look up the cost in the values dictionary
                raw_cost = values_dict.get(lookup_key)
                if raw_cost is not None:
                    try:
                        # Convert the found cost to integer
                        return int(raw_cost)
                    except (ValueError, TypeError):
                        # Value associated with the key wasn't a valid integer
                        return None
                else:
                    # The specific key (e.g., "Huge" or agility "3") wasn't in values_dict
                    return None
            else:
                # Could not determine the lookup key (e.g., ship size missing)
                return None

        # If neither 'value' nor 'variable' key was found in cost_obj
        return None

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

        # pilots_details = [
        #     find_pilot(pilot["id"], MONGODB_URI)
        #     for pilot in xws_dict["pilots"]
        # ]

        list_details = [
            {
                # Fetch pilot details using the pilot's 'id'
                "pilot_info": find_pilot(pilot["id"], MONGODB_URI),
                # Fetch details for all upgrades associated with this pilot
                "upgrades_info": [
                    find_upgrade(upgrade_id, MONGODB_URI)
                    # Iterate through the lists of upgrade IDs found in the
                    # pilot's 'upgrades' dictionary values
                    for upgrade_ids_list in pilot.get("upgrades", {}).values()
                    if isinstance(upgrade_ids_list, list)
                    # Iterate through each individual upgrade ID within
                    # those lists
                    for upgrade_id in upgrade_ids_list
                ],
            }
            # Iterate through each pilot dictionary in the main 'pilots' list
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
            f"-# Bid: {bid}\n"
        )
        embed_description = embed_list_title

        for pilot_data in list_details:
            pilot = pilot_data["pilot_info"]
            upgrades = pilot_data["upgrades_info"]
            ship_details = find_ship_by_pilot(pilot["xws"], MONGODB_URI)

            # --- Initialize Total Cost variable ---
            current_pilot_total_cost = 0
            try:
                current_pilot_total_cost += int(pilot["cost"])
            except (ValueError, TypeError, KeyError):
                print(
                    f"Warning: Could not parse pilot cost for {pilot.get('name', 'Unknown Pilot')}"
                )

            pilot_line_base = (
                f"{ship_emojis[ship_details['xws']]} "
                f"{ini_emojis[pilot['initiative']]} "
                f"**[{pilot['name']}]({pilot['image']})**({pilot['cost']})"
            )

            if upgrades:
                upgrade_display_parts = []  # To store each "[Name](URL) (Cost)" part

                for upg in upgrades:
                    # --- Calculate Cost ---
                    cost = calculate_upgrade_cost(upg, ship_details, pilot)
                    if cost is not None:
                        # Add valid upgrade costs to the running total
                        current_pilot_total_cost += cost
                    else:
                        # Optional: Log a warning if an upgrade cost couldn't be determined
                        print(
                            f"Warning: Could not determine cost for upgrade "
                            f"{upg.get('name', 'Unknown Upgrade')} "
                            f"on pilot {pilot.get('name', 'Unknown Pilot')}"
                        )

                    # Format cost string: "(X)" or "(?)" if cost is None
                    cost_str = f"({cost})" if cost is not None else "(?)"

                    # --- Get Image URL --- (using logic from previous steps)
                    sides_list = upg.get("sides", [])
                    image_url = (
                        sides_list[0].get("image", "{GOLDENROD_UPGRADES_URL}")
                        if sides_list
                        else "{GOLDENROD_UPGRADES_URL}"
                    )
                    upgrade_name = upg.get("name", "Unknown Upgrade")

                    # --- Create Link + Cost String ---
                    link_part = f"[{upgrade_name}]({image_url})"
                    # Combine link and cost: e.g., "[Hopeful](url) (1)"
                    display_string = f"{link_part} {cost_str}"

                    upgrade_display_parts.append(display_string)

                # Join all upgrade parts with ", ", add leading ": " and wrap in italics
                if upgrade_display_parts:
                    upgrades_formatted = (
                        f": *{', '.join(upgrade_display_parts)}*"
                    )
            else:
                upgrades_formatted = ""

            if upgrades_formatted == "":
                final_pilot_line = f"{pilot_line_base}\n"
            else:
                final_pilot_line = f"{pilot_line_base}{upgrades_formatted}"
                final_pilot_line += f" __**[{current_pilot_total_cost}]**__\n"
            embed_description += final_pilot_line

        embed = discord.Embed(
            description=embed_description,
            color=discord.Color.blue(),  # Optional: set a color
        )
        embed.set_footer(
            text=f"List submitted by: {message.author.display_name}",
            icon_url=message.author.display_avatar.url,
        )
        # You could add the original YASB link as a field or in the description
        # embed.add_field(
        #     name="Original Link",
        #     value=f"[View on YASB]({found_url})",
        #     inline=False,
        # )
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
