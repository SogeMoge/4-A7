import asyncio
import json
import logging
import random

import aiohttp
import discord
from discord import ButtonStyle, Interaction
from discord.ui import Button, View, button

from bot import config
from bot.mongo.init_db import reload_collections
from bot.mongo.search import (
    find_faction,
    find_pilot,
    find_ship_by_pilot,
    find_upgrade,
)
from bot.xws2pretty import convert_faction_to_color, ini_emojis, ship_emojis

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
    mode_match = config.MODE_URL_PATTERN.search(yasb_url)
    if not mode_match:
        return None
    mode_indicator = mode_match.group()
    try:
        mode_char = mode_indicator[6]
        points_str = mode_indicator[8:-1]
        mode_name = config.MODE_MAPPING.get(mode_char)
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
        self.button_message_deleted = False
        self.button_message: discord.Message | None = None

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.interaction_user_id:
            await interaction.response.send_message(
                "Directive override: Only the originator of the "
                "list may utilize these controls.",
                ephemeral=True,
            )
            return False
        return True

    # Helper to attempt message deletion safely
    async def _delete_button_message(self, log_context):
        if self.button_message and not self.button_message_deleted:
            try:
                await self.button_message.delete()
                logger.info(
                    f"Deleted button message {self.button_message.id}.",
                    extra=log_context,
                )
                self.button_message_deleted = True
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
            "User clicked YES for original message "
            f"{self.original_message.id}",
            extra=log_context,
        )
        await interaction.response.defer(ephemeral=True)

        confirmation_text = ""
        try:
            await self.original_message.delete()
            logger.info(
                f"Original message {self.original_message.id} "
                "deleted successfully.",
                extra=log_context,
            )
            self.message_deleted = True
        except discord.Forbidden:
            logger.error(
                f"Permission denied deleting msg {self.original_message.id}",
                extra=log_context,
            )
            confirmation_text = "Negative. This unit lacks authorization"
            confirmation_text += " (permissions) to delete the"
            confirmation_text += " specified message."
            self.message_deleted = False
        except discord.NotFound:
            logger.warning(
                f"Original message {self.original_message.id} not found.",
                extra=log_context,
            )
            confirmation_text = "Analysis indicates the original message"
            confirmation_text += " no longer exists in the channel records."
            self.message_deleted = None
        except Exception as e:
            logger.error(
                f"Error deleting message {self.original_message.id}: {e}",
                extra=log_context,
                exc_info=True,
            )
            confirmation_text = "Critical error encountered during "
            confirmation_text += "message deletion sub-routine."
            self.message_deleted = False

        try:
            await interaction.delete_original_response()
        except discord.HTTPException as e:
            logger.warning(
                f"Could not delete confirmation message: {e}",
                extra=log_context,
            )

        if confirmation_text:
            await interaction.followup.send(
                content=confirmation_text, ephemeral=True
            )
        # await self._delete_button_message(log_context)
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
                f"Could not delete confirmation message: {e}",
                extra=log_context,
            )

        if confirmation_text:
            await interaction.followup.send(
                content=confirmation_text, ephemeral=True
            )
        self.stop()

    async def on_timeout(self):
        log_context = {
            "channel_id": self.original_message.channel.id
            if self.original_message
            else "Unknown"
        }
        logger.info(
            f"Confirmation view for original message "
            f"""{
                self.original_message.id
                if self.original_message
                else "Unknown"
            }"""
            " timed out.",
            extra=log_context,
        )
        await self._delete_button_message(log_context)


# --- Bot Events ---
@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    logger.info(f"{bot.user} is operational! Roger? Roger!.")
    bot.add_view(Builders())
    logger.info("Persistent Builders view added.")
    bot.add_view(Rules())
    logger.info("Persistent Rules view added.")


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user or not message.content:
        return

    yasb_url_match = config.YASB_URL_PATTERN.search(message.content)
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
            rollbetter_url = config.RB_ENDPOINT + found_url
            xws_dict = None
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(
                        rollbetter_url, timeout=20
                    ) as response:
                        response.raise_for_status()
                        response_text = await response.text()
                        xws_dict = json.loads(response_text)
                        logger.debug("Received XWS JSON", extra=log_context)
                except (
                    aiohttp.ClientResponseError
                ) as e:  # Handles response.raise_for_status() errors
                    logger.error(
                        f"HTTP error fetching XWS: {e.status} {e.message}",
                        extra=log_context,
                        exc_info=True,
                    )
                    return
                except (
                    asyncio.TimeoutError
                ):  # aiohttp uses asyncio.TimeoutError for timeouts
                    logger.error(
                        f"Timeout fetching XWS data from {rollbetter_url}",
                        extra=log_context,
                    )
                    return
                except (
                    aiohttp.ClientError
                ) as e:  # Catches other connection errors
                    logger.error(
                        f"Failed to fetch XWS data (aiohttp ClientError): {e}",
                        extra=log_context,
                        exc_info=True,
                    )
                    return
                # Catch unexpected errors during the fetch/parse block
                except Exception as e_fetch:
                    logger.error(
                        f"Unexpected error during XWS fetch/parse: {e_fetch}",
                        extra=log_context,
                        exc_info=True,
                    )
                    await message.channel.send(
                        f"Sorry {message.author.display_name}, "
                        "an unexpected error occurred while getting list data",
                        ephemeral=True,
                    )
                    return

            if xws_dict is None:
                # Error message already sent in the except blocks
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
                    f"The list appears to be empty, {message.author.mention}.",
                    ephemeral=True,
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
                                        "name": f"{upgrade_id}",
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
                pilot_image = pilot.get("image", config.GOLDENROD_PILOTS_URL)

                upgrade_display_parts = []
                for upg in upgrades:
                    cost = calculate_upgrade_cost(upg, ship, pilot)
                    if cost is not None:
                        pilot_total_cost += cost
                    cost_str = f"({cost})" if cost is not None else "(?)"
                    upg_name = upg.get("name", "Unknown Upgrade")
                    img_url = config.GOLDENROD_UPGRADES_URL
                    try:
                        if upg.get("sides") and upg["sides"][0]:
                            img_url = upg["sides"][0].get(
                                "image", config.GOLDENROD_UPGRADES_URL
                            )
                    except (IndexError, KeyError, TypeError):
                        pass
                    if img_url:
                        upgrade_display_parts.append(
                            f"[{upg_name}]({img_url}){cost_str}"
                        )
                    else:
                        upgrade_display_parts.append(
                            f"[{upg_name}]({img_url}){cost_str}"
                        )

                upgrades_formatted = (
                    f"{', '.join(upgrade_display_parts)}"
                    if upgrade_display_parts
                    else ""
                )
                # If pilot has no upgrades display cost in square brackets
                if upgrades_formatted == "":
                    pilot_cost_str = f"__**[{pilot.get('cost', '?')}]**__"
                    pilot_total_str = ""
                else:
                    pilot_cost_str = f"({pilot.get('cost', '?')})"
                    pilot_total_str = f" __**[{pilot_total_cost}]**__"
                # Constuct all parts of a pilot line for embed description
                pilot_line_base = f"{ship_emoji} {ini_emoji}"
                pilot_line_base += f"**[{pilot_name}]({pilot_image})**"
                pilot_line_base += f"{pilot_cost_str}"

                final_pilot_line = (
                    f"{pilot_line_base}: {upgrades_formatted} "
                    f"{pilot_total_str}\n"
                )

                if (
                    len(current_description) + len(final_pilot_line)
                    > config.DISCORD_EMBED_DESCRIPTION_LIMIT
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
                random_phrase = random.choice(config.FOOTER_PHRASES)
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
                "an unexpected error occurred.",
                ephemeral=True,
            )
        finally:
            logger.info("Released lock", extra=log_context)


#  #########################
# INFO COMMANDS
#  #########################


class Rules(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Standard",
        style=discord.ButtonStyle.primary,
        custom_id="persistent_rules:standatd",
    )
    async def standard_button_callback(self, button, interaction):
        await interaction.response.send_message(
            "<https://x2po.org/standard>", ephemeral=True
        )

    @discord.ui.button(
        label="Epic",
        style=discord.ButtonStyle.primary,
        custom_id="persistent_rules:epic",
    )
    async def epic_button_callback(self, button, interaction):
        await interaction.response.send_message(
            "<https://x2po.org/epic>", ephemeral=True
        )

    @discord.ui.button(
        label="Wild Space",
        style=discord.ButtonStyle.primary,
        custom_id="persistent_rules:wildspace",
    )
    async def ws_button_callback(self, button, interaction):
        await interaction.response.send_message(
            "<https://x2po.org/wild-space>", ephemeral=True
        )

    @discord.ui.button(
        label="Adopted Battle Scenarios",
        style=discord.ButtonStyle.secondary,
        custom_id="persistent_rules:adoption",
    )
    async def bs_button_callback(self, button, interaction):
        await interaction.response.send_message(
            "<https://x2po.org/battle-scenarios>", ephemeral=True
        )

    @discord.ui.button(
        label="Video tutorials",
        style=discord.ButtonStyle.secondary,
        custom_id="persistent_rules:vedotutorials",
    )
    async def vt_button_callback(self, button, interaction):
        await interaction.response.send_message(
            "<https://x2po.org/media>", ephemeral=True
        )

    @discord.ui.button(
        label="Points",
        style=discord.ButtonStyle.success,
        custom_id="persistent_rules:points",
    )
    async def points_button_callback(self, button, interaction):
        await interaction.response.send_message(
            "<https://points.x2po.org>", ephemeral=True
        )


class Builders(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="YASB 2.0 Legacy",
        style=discord.ButtonStyle.primary,
        custom_id="persistent_builders:yasb",
    )
    async def yasb_button_callback(self, button, interaction):
        await interaction.response.send_message(
            "https://xwing-legacy.com/", ephemeral=True
        )

    @discord.ui.button(
        label="X-Wing 2nd Ed. Squads Designer",
        style=discord.ButtonStyle.secondary,
        custom_id="persistent_builders:dmborque",
    )
    async def dmborque_button_callback(self, button, interaction):
        await interaction.response.send_message(
            "https://www.dmborque.eu/swz", ephemeral=True
        )

    @discord.ui.button(
        label="Infinite Arenas",
        style=discord.ButtonStyle.secondary,
        custom_id="persistent_builders:ia",
    )
    async def ia_button_callback(self, button, interaction):
        await interaction.response.send_message(
            "https://infinitearenas.com/legacy/", ephemeral=True
        )

    @discord.ui.button(
        label="Launch Bay Next",
        style=discord.ButtonStyle.secondary,
        custom_id="persistent_builders:lbn",
    )
    async def lbn_button_callback(self, button, interaction):
        await interaction.response.send_message(
            "Launch Bay Next:\n"
            "[iOS](<https://apps.apple.com/us/app/launch-bay-next/id1422488966>) /"
            "[Android](<http://play.google.com/store/apps/details?id=com.launchbaynext>)",
            ephemeral=True,
        )


@bot.slash_command(name="rules", description="Get X-Wing 2.0 Legacy rules.")
async def rules(ctx):
    view = Rules()
    await ctx.respond("**X-Wing 2.0 Legacy** rules:", view=view)


@bot.slash_command(
    name="builders",
    description="Post X-Wing 2.0 Legacy compatible Squad Builders.",
)
async def builders(ctx):
    """Post X-Wing 2.0 Legacy compatible Squad Builders."""
    view = Builders()
    await ctx.respond("**2.0 Legacy** compatible Squad Builders:", view=view)


@bot.slash_command(description="200 000 units are ready")
async def reinforcements(ctx):
    await ctx.defer()
    await ctx.respond(random.choice(config.WELCOME_GIFS))


@bot.slash_command(name="thisistheway", description="Show the Way")
async def this_is_the_wayre(ctx):
    await ctx.defer()
    await ctx.respond(random.choice(config.THE_WAY_GIFS))


# --- Bot Startup ---
if __name__ == "__main__":
    if (
        not config.DISCORD_TOKEN
        or config.DISCORD_TOKEN == "YOUR_REAL_BOT_TOKEN"
    ):
        logger.critical("FATAL: Discord bot token is missing or placeholder!")
        exit("Discord token configuration error.")

    try:
        # --- Reinstate prepare_collections call ---
        logger.info("Preparing data collections (if needed)...")
        reload_collections(
            config.XWS_DATA_ROOT_DIR, config.MONGODB_URI
        )  # Pass required vars
        logger.info("Data collections prepared.")
        # --- End reinstate ---

        logger.info("Starting bot...")
        bot.run(config.DISCORD_TOKEN)
    except discord.errors.LoginFailure:
        logger.critical("FATAL: Improper token passed.")
        exit("Discord login failed.")
    # --- Reinstate FileNotFoundError ---
    except FileNotFoundError:
        logger.critical(
            "FATAL: Could not find XWS data directory: "
            f"{config.XWS_DATA_ROOT_DIR}"
        )
        exit("XWS data directory not found.")
    # --- End reinstate ---
    except Exception as e:
        logger.critical(f"FATAL: Bot run failed: {e}", exc_info=True)
        exit("Unexpected error during bot startup.")
