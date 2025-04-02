import asyncio
import json
import logging
import os
import random
import re

import discord
import requests
from discord import ButtonStyle, Interaction
from discord.ui import Button, View, button
from dotenv import load_dotenv

from bot.mongo.init_db import prepare_collections
from bot.mongo.search import (
    find_faction,
    find_pilot,
    find_ship_by_pilot,
    find_upgrade,
)
from bot.xws2pretty import convert_faction_to_color, ini_emojis, ship_emojis

# --- Configuration & Constants ---
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
# --- MONGODB_URI for prepare_collections ---
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://root:example@localhost:27017/xwingdata?authSource=admin",
)
RB_ENDPOINT = os.getenv(
    "RB_ENDPOINT",
    "https://rollbetter-linux.azurewebsites.net/lists/xwing-legacy?",
)
# --- XWS_DATA_ROOT_DIR  for prepare_collections ---
XWS_DATA_ROOT_DIR = "submodules/xwing-data2/data"
GOLDENROD_PILOTS_URL = (
    "https://github.com/SogeMoge/x-wing2.0-project-goldenrod/blob/2.0/"
    "src/images/En/pilots/"
)
GOLDENROD_UPGRADES_URL = (
    "https://github.com/SogeMoge/x-wing2.0-project-goldenrod/blob/2.0/"
    "src/images/En/upgrades/"
)
DISCORD_EMBED_DESCRIPTION_LIMIT = 4096
YASB_URL_PATTERN = re.compile(
    r"https?:\/\/xwing-legacy\.com\/(preview)?\/?\?f=[^\s]+"
)
MODE_URL_PATTERN = re.compile(r"&d=v8Z[sheq]Z\d*Z")
MODE_MAPPING = {
    "s": "Standard",
    "h": "Wildspace",
    "e": "Epic",
    "q": "Quickbuild",
}

FOOTER_PHRASES = [
    "Processing complete. List provided by:",
    "Analysis concluded for squadron designation submitted by:",
    "Data formatted as requested for unit:",
    "Calculation successful. Originator identified as:",
    "Cross-referencing protocols engaged. Input attributed to:",
    "This unit has prepared the manifest received from:",
    "Fulfilling primary function. Data sourced from organic designation:",
    "Squadron configuration logged per input from:",
    "Information processed according to standard parameters for:",
    "Probability of data corruption minimal. List registered to:",
    "Tactical assessment derived from input by:",
    "Combat effectiveness calculated for squadron provided by:",
    "Optimal configuration analyzed. Submitted by designation:",
    "Commencing tactical display. List parameters set by:",
    "Unit deployment follows, per directive originating from:",
    "Logistical breakdown prepared for Confederacy Asset:",
    "Analyzing potential engagement matrix. Data provided by:",
    "Record updated. Squadron composition input by:",
    "Query resolved. List compiler identified as:",
    "Affirmative. Displaying squadron details submitted by:",
    "Data stream decoded. Source identified as:",
    "Input parameters verified. Originating unit:",
    "Manifest generation initiated by:",
    "Log entry created. Data provided by organic:",
    "Task completed as per directive from:",
    "This unit awaits further instruction. Current data by:",
    "Operational efficiency dictates prompt processing for:",
    "My function is to serve. Analysis performed for:",
    "Executing request protocol for user designation:",
    "Evaluating threat potential based on squadron from:",
    "Resource allocation noted. List provided by contact:",
    "Updating battle grid. Configuration submitted by:",
    "Cross-referencing against known Republic tactics. Input from:",
    "Roger, roger. Processing tactical configuration from:",
    "For the Separatist Alliance! Squadron details logged for:",
    "This configuration's probability of success calculated for:",
    "Assessing synergistic values. List compiled by:",
    "Analytical subroutines active. Processing list from:",
    "Verifying data integrity. Submitted by unit:",
    "Compliance noted. Squadron details follow for:",
]

# --- Logging Setup ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
log_file = "xwsbot.log"
file_handler = logging.FileHandler(log_file, encoding="utf-8")
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# --- Discord Bot Setup ---
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True
intents.presences = True
bot = discord.Bot(intents=intents)

# --- Concurrency Control ---
channel_locks = {}


# --- Helper Functions ---
def get_gamemode(yasb_url: str) -> tuple[str, int] | None:
    """Extracts game mode and point limit from YASB URL."""
    mode_match = MODE_URL_PATTERN.search(yasb_url)
    if not mode_match:
        return None
    mode_indicator = mode_match.group()
    try:
        mode_char = mode_indicator[6]
        points_str = mode_indicator[8:-1]
        mode_name = MODE_MAPPING.get(mode_char)
        if mode_name and points_str.isdigit():
            return mode_name, int(points_str)
        else:
            return None
    except (IndexError, KeyError):
        return None


def get_ship_stat_value(stats_list, stat_type_to_find):
    """Safely extracts a specific stat value from a ship's stats list."""
    if not isinstance(stats_list, list):
        return None
    for stat in stats_list:
        if isinstance(stat, dict) and stat.get("type") == stat_type_to_find:
            return stat.get("value")
    return None


def calculate_upgrade_cost(upgrade_data, ship_details, pilot_info):
    """Calculates the potentially variable cost of an upgrade."""
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
        ship_stats = ship_details.get("stats") if ship_details else None
        if variable_type == "size":
            lookup_key = ship_details.get("size") if ship_details else None
        elif variable_type == "agility":
            agility = get_ship_stat_value(ship_stats, "agility")
            if agility is not None:
                lookup_key = str(agility)
        elif variable_type == "initiative":
            initiative = pilot_info.get("initiative") if pilot_info else None
            if initiative is not None:
                lookup_key = str(initiative)
        if lookup_key is not None:
            raw_cost = values_dict.get(lookup_key)
            if raw_cost is not None:
                try:
                    return int(raw_cost)
                except (ValueError, TypeError):
                    return None
        return None
    return None


# --- Confirmation Button View ---
class ConfirmationView(View):
    def __init__(self, original_message: discord.Message, *, timeout=120):
        super().__init__(timeout=timeout)
        self.original_message = original_message
        self.interaction_user_id = original_message.author.id
        self.message_deleted = None
        self.button_message: discord.Message | None = None

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.interaction_user_id:
            await interaction.response.send_message(
                "Directive override: Only the originator of the list may utilize these controls.",
                ephemeral=True,
            )
            return False
        return True

    # Helper to attempt message deletion safely
    async def _delete_button_message(self, log_context):
        if self.button_message:
            try:
                await self.button_message.delete()
                logger.info(
                    f"Deleted button message {self.button_message.id}.",
                    extra=log_context,
                )
            except discord.NotFound:
                logger.warning(
                    f"Could not delete button message "
                    f"{self.button_message.id} (already deleted).",
                    extra=log_context,
                )
            except discord.Forbidden:
                logger.error(
                    f"Permission error deleting button message "
                    f"{self.button_message.id}.",
                    extra=log_context,
                )
            except discord.HTTPException as e:
                logger.error(
                    f"HTTP error deleting button message "
                    f"{self.button_message.id}: {e}",
                    extra=log_context,
                )
            except Exception as e_del_btn_other:
                logger.error(
                    f"Unexpected error deleting button message "
                    f"{self.button_message.id}: {e_del_btn_other}",
                    extra=log_context,
                    exc_info=True,
                )
            finally:
                # Avoid trying to delete again on timeout if already handled
                self.button_message = (
                    None  # Clear reference after attempting delete
                )

    @button(
        label="Yes (Delete Original)",
        style=ButtonStyle.success,
        custom_id="confirm_delete_yes",
    )
    async def yes_button_callback(
        self, button_obj: Button, interaction: Interaction
    ):
        log_context = {
            "channel_id": interaction.channel_id,
            "user_id": interaction.user.id,
        }
        logger.info(
            f"User clicked YES for original message {self.original_message.id}",
            extra=log_context,
        )
        await interaction.response.defer(ephemeral=True)

        confirmation_text = ""
        try:
            await self.original_message.delete()
            logger.info(
                f"Original message {self.original_message.id} deleted successfully.",
                extra=log_context,
            )
            self.message_deleted = True
        except discord.Forbidden:
            logger.error(
                f"Permission denied deleting message {self.original_message.id}",
                extra=log_context,
            )
            confirmation_text = "Negative. This unit lacks authorization (permissions) to delete the specified message."
            self.message_deleted = False
        except discord.NotFound:
            logger.warning(
                f"Original message {self.original_message.id} not found.",
                extra=log_context,
            )
            confirmation_text = "Analysis indicates the original message no longer exists in the channel records."
            self.message_deleted = None
        except Exception as e:
            logger.error(
                f"Error deleting message {self.original_message.id}: {e}",
                extra=log_context,
                exc_info=True,
            )
            confirmation_text = "Critical error encountered during message deletion sub-routine."
            self.message_deleted = False

        try:
            await interaction.delete_original_response()
        except discord.HTTPException as e:
            logger.warning(
                f"Could not edit ephemeral confirmation message (likely dismissed or timed out): {e}",
                extra=log_context,
            )

        if confirmation_text:
            await interaction.followup.send(
                content=confirmation_text, ephemeral=True
            )
        await self._delete_button_message(log_context)
        self.stop()

    @button(
        label="No (Keep Original)",
        style=ButtonStyle.danger,
        custom_id="confirm_delete_no",
    )
    async def no_button_callback(
        self, button_obj: Button, interaction: Interaction
    ):
        log_context = {
            "channel_id": interaction.channel_id,
            "user_id": interaction.user.id,
        }
        logger.info(
            f"User clicked NO for original message {self.original_message.id}",
            extra=log_context,
        )
        await interaction.response.defer(ephemeral=True)

        confirmation_text = ""
        self.message_deleted = False

        try:
            await interaction.delete_original_response()
        except discord.HTTPException as e:
            logger.warning(
                f"Could not edit ephemeral confirmation message (likely dismissed or timed out): {e}",
                extra=log_context,
            )

        if confirmation_text:
            await interaction.followup.send(
                content=confirmation_text, ephemeral=True
            )
        await self._delete_button_message(log_context)
        self.stop()

    async def on_timeout(self):
        log_context = {
            "channel_id": self.original_message.channel.id
            if self.original_message
            else "Unknown"
        }
        logger.info(
            f"Confirmation view for original message {self.original_message.id if self.original_message else 'Unknown'} timed out.",
            extra=log_context,
        )
        await self._delete_button_message(log_context)


# --- Bot Events ---
@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    logger.info(f"{bot.user} is operational! Roger? Roger!.")


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user or not message.content:
        return

    yasb_url_match = YASB_URL_PATTERN.search(message.content)
    if not yasb_url_match:
        return

    lock = channel_locks.setdefault(message.channel.id, asyncio.Lock())
    async with lock:
        log_context = {
            "channel_id": message.channel.id,
            "user_id": message.author.id,
            "user_name": message.author.name,
        }
        logger.info("Acquired lock", extra=log_context)

        try:
            found_url = yasb_url_match.group(0).replace(
                "http://", "https://", 1
            )
            log_context["yasb_url"] = found_url
            logger.info(
                f"Processing locked request for URL: {found_url}",
                extra=log_context,
            )

            # --- Fetch XWS Data ---
            rollbetter_url = RB_ENDPOINT + found_url
            try:
                response = requests.get(rollbetter_url, timeout=20)
                response.raise_for_status()
                xws_dict = response.json()
                logger.debug("Received XWS JSON", extra=log_context)
            except requests.exceptions.RequestException as e:
                logger.error(
                    f"Failed to fetch XWS data: {e}",
                    extra=log_context,
                    exc_info=True,
                )
                await message.channel.send(
                    f"Sorry {message.author.mention}, "
                    "I couldn't retrieve list data."
                )
                return
            except json.JSONDecodeError as e:
                logger.error(
                    f"Failed to decode JSON response: {e}. "
                    f"Response text: {response.text[:500]}...",
                    extra=log_context,
                    exc_info=True,
                )
                await message.channel.send(
                    f"Sorry {message.author.mention}, "
                    "I couldn't understand the list format."
                )
                return

            # --- Extract Core List Info ---
            faction_xws = xws_dict.get("faction")
            faction_color = convert_faction_to_color(faction_xws)
            squad_name = xws_dict.get("name", "Unnamed Squad")
            squad_points_xws = xws_dict.get("points")
            yasb_link = xws_dict.get("vendor", {}).get("yasb", {}).get("link")

            if not faction_xws:
                logger.error("Faction missing in XWS data.", extra=log_context)
                await message.channel.send(
                    f"Sorry {message.author.mention}, "
                    "list data incomplete (missing faction)."
                )
                return

            faction_details = find_faction(faction_xws)
            if not faction_details:
                faction_details = {
                    "name": faction_xws.replace("_", " ").title()
                }

            squad_gamemode_info = (
                get_gamemode(yasb_link) if yasb_link else None
            )
            if not squad_gamemode_info and yasb_link:
                logger.warning(
                    f"Could not extract game mode from YASB link: {yasb_link}",
                    extra=log_context,
                )

            game_mode_name = (
                squad_gamemode_info[0] if squad_gamemode_info else "Unknown"
            )
            points_limit = (
                str(squad_gamemode_info[1]) if squad_gamemode_info else "?"
            )
            display_points = (
                str(squad_points_xws) if squad_points_xws is not None else "?"
            )
            bid_str = "?"
            if squad_gamemode_info and squad_points_xws is not None:
                try:
                    bid = squad_gamemode_info[1] - int(squad_points_xws)
                    bid_str = str(bid)
                except (ValueError, TypeError):
                    pass

            # --- Process Pilots and Upgrades (Fetch DB Data) ---
            pilot_details_list = []
            xws_pilots = xws_dict.get("pilots", [])
            if not xws_pilots:
                logger.warning("No pilots found in list.", extra=log_context)
                await message.channel.send(
                    f"The list appears to be empty, {message.author.mention}."
                )
                return

            for pilot_entry in xws_pilots:
                pilot_id = pilot_entry.get("id")
                if not pilot_id:
                    continue

                pilot_info = find_pilot(pilot_id)
                if not pilot_info:
                    continue

                ship_details = find_ship_by_pilot(pilot_info.get("xws"))
                if not ship_details:
                    ship_details = {
                        "xws": "unknown",
                        "name": "Unknown Ship",
                        "size": "?",
                        "stats": [],
                    }

                upgrades_data = []
                for upgrade_type, upgrade_ids in pilot_entry.get(
                    "upgrades", {}
                ).items():
                    if isinstance(upgrade_ids, list):
                        for upgrade_id in upgrade_ids:
                            upgrade_info = find_upgrade(
                                upgrade_id
                            )  # Uses global DB connection
                            if not upgrade_info:
                                upgrades_data.append(
                                    {
                                        "name": f"Unknown({upgrade_id})",
                                        "sides": [{"image": ""}],
                                    }
                                )
                            else:
                                upgrades_data.append(upgrade_info)

                pilot_details_list.append(
                    {
                        "pilot": pilot_info,
                        "ship": ship_details,
                        "upgrades": upgrades_data,
                    }
                )

            logger.info(
                "Successfully processed pilot/upgrade data", extra=log_context
            )

            # --- Build Embeds ---
            squad_hyperlink = (
                f"[{squad_name}]({found_url})" if found_url else squad_name
            )
            embed_list_title = (
                f"**{squad_hyperlink}**\n"
                f"{faction_details.get('name', 'Unknown Faction')} "
                f"[{display_points}/{points_limit}: {game_mode_name}]\n"
                f"-# Bid: {bid_str}\n"
            )

            embeds_to_send = []
            current_description = embed_list_title

            for details in pilot_details_list:
                pilot, ship, upgrades = (
                    details["pilot"],
                    details["ship"],
                    details["upgrades"],
                )

                pilot_total_cost = 0
                try:
                    pilot_total_cost += int(pilot.get("cost", 0))
                except (ValueError, TypeError):
                    pass

                ship_emoji = ship_emojis.get(ship.get("xws"), "❓")
                ini_emoji = ini_emojis.get(pilot.get("initiative"), "❓")
                pilot_name = pilot.get("name", "Unknown Pilot")
                pilot_image = pilot.get("image", GOLDENROD_PILOTS_URL)
                pilot_cost_str = f"({pilot.get('cost', '?')})"
                pilot_line_base = f"{ship_emoji} {ini_emoji}"
                pilot_line_base += f"**[{pilot_name}]({pilot_image})**"
                pilot_line_base += f" {pilot_cost_str}"

                upgrade_display_parts = []
                for upg in upgrades:
                    cost = calculate_upgrade_cost(upg, ship, pilot)
                    if cost is not None:
                        pilot_total_cost += cost
                    cost_str = f"({cost})" if cost is not None else "(?)"
                    upg_name = upg.get("name", "Unknown Upgrade")
                    img_url = GOLDENROD_UPGRADES_URL
                    try:
                        if upg.get("sides") and upg["sides"][0]:
                            img_url = upg["sides"][0].get(
                                "image", GOLDENROD_UPGRADES_URL
                            )
                    except (IndexError, KeyError, TypeError):
                        pass
                    upgrade_display_parts.append(
                        f"[{upg_name}]({img_url}){cost_str}"
                    )

                upgrades_formatted = (
                    f": *{', '.join(upgrade_display_parts)}*"
                    if upgrade_display_parts
                    else ""
                )
                if upgrades_formatted == "":
                    pilot_total_str = ""
                else:
                    pilot_total_str = f" __**[{pilot_total_cost}]**__"

                final_pilot_line = (
                    f"{pilot_line_base}{upgrades_formatted}{pilot_total_str}\n"
                )

                if (
                    len(current_description) + len(final_pilot_line)
                    > DISCORD_EMBED_DESCRIPTION_LIMIT
                ):
                    embed = discord.Embed(
                        description=current_description,
                        color=faction_color,
                    )
                    embeds_to_send.append(embed)
                    current_description = final_pilot_line
                else:
                    current_description += final_pilot_line

            if current_description:
                embed = discord.Embed(
                    description=current_description, color=faction_color
                )
                embeds_to_send.append(embed)

            # --- Send Embeds ---
            if not embeds_to_send:
                logger.warning("No embeds generated.", extra=log_context)
            else:
                total_embeds = len(embeds_to_send)
                random_phrase = random.choice(FOOTER_PHRASES)
                base_footer_text = (
                    f"{random_phrase} {message.author.display_name}"
                )
                footer_icon_url = (
                    message.author.display_avatar.url
                    if message.author.display_avatar
                    else None
                )

                logger.info(
                    f"Sending {total_embeds} embed(s).", extra=log_context
                )
                for i, embed in enumerate(embeds_to_send):
                    part_counter = f"\n[Part {i + 1}/{total_embeds}]"
                    footer_text = (
                        f"{base_footer_text}{part_counter}"
                        if total_embeds > 1
                        else base_footer_text
                    )
                    embed.set_footer(
                        text=footer_text, icon_url=footer_icon_url
                    )
                    await message.channel.send(embed=embed)
                logger.info("Finished sending embeds.", extra=log_context)

                # --- Send Confirmation Buttons ---
                try:
                    view = ConfirmationView(
                        original_message=message
                    )  # Pass the original user message
                    sent_button_message = await message.channel.send(
                        f"Query for {message.author.display_name}: "
                        " Delete original message containing the YASB link?",
                        view=view,
                    )
                    view.button_message = sent_button_message
                    logger.info(
                        f"Sent confirmation buttons for message {message.id}",
                        extra=log_context,
                    )
                except Exception as e_view:
                    logger.error(
                        f"Failed to send confirmation buttons: {e_view}",
                        extra=log_context,
                        exc_info=True,
                    )
                # --- End Send Confirmation ---

        except Exception as e:
            logger.error(
                f"Unexpected error during processing: {e}",
                extra=log_context,
                exc_info=True,
            )
            await message.channel.send(
                f"Sorry {message.author.mention}, "
                "an unexpected error occurred."
            )
        finally:
            logger.info("Released lock", extra=log_context)


# --- Bot Startup ---
if __name__ == "__main__":
    if not DISCORD_TOKEN or DISCORD_TOKEN == "YOUR_REAL_BOT_TOKEN":
        logger.critical("FATAL: Discord bot token is missing or placeholder!")
        exit("Discord token configuration error.")

    try:
        # --- Reinstate prepare_collections call ---
        logger.info("Preparing data collections (if needed)...")
        prepare_collections(
            XWS_DATA_ROOT_DIR, MONGODB_URI
        )  # Pass required vars
        logger.info("Data collections prepared.")
        # --- End reinstate ---

        logger.info("Starting bot...")
        bot.run(DISCORD_TOKEN)
    except discord.errors.LoginFailure:
        logger.critical("FATAL: Improper token passed.")
        exit("Discord login failed.")
    # --- Reinstate FileNotFoundError ---
    except FileNotFoundError:
        logger.critical(
            f"FATAL: Could not find XWS data directory: {XWS_DATA_ROOT_DIR}"
        )
        exit("XWS data directory not found.")
    # --- End reinstate ---
    except Exception as e:
        logger.critical(f"FATAL: Bot run failed: {e}", exc_info=True)
        exit("Unexpected error during bot startup.")
    # finally: # Optional: Graceful DB connection closing on exit
    #     close_db_connection()
