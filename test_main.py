import json
import re
from unittest.mock import ANY, AsyncMock, MagicMock

import discord
import pytest

import main

# --- Constants  ---
CORRECT_RB_ENDPOINT = (
    "https://rollbetter-linux.azurewebsites.net/lists/xwing-legacy?"
)
CORRECT_YASB_URL_PATTERN = re.compile(
    r"https?:\/\/xwing-legacy\.com\/(preview)?\/?\?f=[^\s]+"
)
CORRECT_MODE_URL_PATTERN = re.compile(r"&d=v8Z[sheq]Z\d*Z")
CORRECT_MODE_MAPPING = {
    "s": "Standard",
    "h": "Wildspace",
    "e": "Epic",
    "q": "Quickbuild",
}

# --- Mock Data ---
MOCK_XWS_RESPONSE_SCUM = {
    "description": "",
    "faction": "scumandvillainy",
    "name": "Variable cost test",
    "pilots": [
        {
            "id": "oldteroch",
            "name": "Old Teroch",
            "points": 63,
            "ship": "fangfighter",
            "upgrades": {"modification": ["afterburners"]},
        },
        {
            "id": "shadowporthunter",
            "name": "Shadowport Hunter",
            "points": 56,
            "ship": "lancerclasspursuitcraft",
            "upgrades": {"modification": ["hullupgrade"]},
        },
        {
            "id": "freightercaptain",
            "name": "Freighter Captain",
            "points": 45,
            "ship": "customizedyt1300lightfreighter",
            "upgrades": {"gunner": ["migsmayfeld"]},
        },
        {
            "id": "spicerunner",
            "name": "Spice Runner",
            "points": 26,
            "ship": "hwk290lightfreighter",
            "upgrades": {},
        },
    ],
    "points": 190,
    "vendor": {
        "yasb": {
            "builder": "YASB 2.0",
            "builder_url": "https://xwing-legacy.com",
            "link": (
                "https://xwing-legacy.com/?f=Scum%20and%20Villainy"
                "&d=v8ZhZ250Z98XWW105Y128XWWW164WY92XWWW461WWWY230XWWWWW"
                "&sn=Variable%20cost%20test&obs="
            ),
        }
    },
    "version": "2023/10/10",
}
MOCK_SCUM_FACTION_DATA = {
    "name": "Scum and Villainy",
    "xws": "scumandvillainy",
}
MOCK_OLDTEROCH_PILOT = {
    "name": "Old Teroch",
    "xws": "oldteroch",
    "cost": 60,
    "initiative": 5,
    "image": "ot_img",
}
MOCK_SHADOWPORT_PILOT = {
    "name": "Shadowport Hunter",
    "xws": "shadowporthunter",
    "cost": 50,
    "initiative": 2,
    "image": "sh_img",
}
MOCK_FREIGHTER_PILOT = {
    "name": "Freighter Captain",
    "xws": "freightercaptain",
    "cost": 40,
    "initiative": 1,
    "image": "fc_img",
}
MOCK_SPICERUNNER_PILOT = {
    "name": "Spice Runner",
    "xws": "spicerunner",
    "cost": 26,
    "initiative": 1,
    "image": "sr_img",
}
MOCK_FANG_SHIP = {
    "name": "Fang Fighter",
    "xws": "fangfighter",
    "size": "small",
    "stats": [{"type": "agility", "value": 3}],
}
MOCK_LANCER_SHIP = {
    "name": "Lancer-class Pursuit Craft",
    "xws": "lancerclasspursuitcraft",
    "size": "large",
    "stats": [{"type": "agility", "value": 0}],
}
MOCK_YT1300_SHIP = {
    "name": "Customized YT-1300",
    "xws": "customizedyt1300lightfreighter",
    "size": "large",
    "stats": [{"type": "agility", "value": 1}],
}
MOCK_HWK_SHIP = {
    "name": "HWK-290",
    "xws": "hwk290lightfreighter",
    "size": "small",
    "stats": [{"type": "agility", "value": 2}],
}
MOCK_UPGRADE_AFTERBURNERS = {
    "name": "Afterburners",
    "xws": "afterburners",
    "cost": {"value": 3},
    "sides": [{"image": "ab_img"}],
}
MOCK_UPGRADE_HULLUPGRADE = {
    "name": "Hull Upgrade",
    "xws": "hullupgrade",
    "cost": {"value": 6},
    "sides": [{"image": "hu_img"}],
}
MOCK_UPGRADE_MIGS = {
    "name": "Migs Mayfeld",
    "xws": "migsmayfeld",
    "cost": {"value": 5},
    "sides": [{"image": "mm_img"}],
}
MOCK_SHIP_DETAILS_SIZE = {
    "name": "X-Wing",
    "xws": "xwing",
    "size": "small",
    "stats": [{"type": "agility", "value": 2}],
}
MOCK_SHIP_DETAILS_AGILITY = {
    "name": "Y-Wing",
    "xws": "ywing",
    "size": "small",
    "stats": [{"type": "agility", "value": 1}],
}
MOCK_PILOT_INFO_INITIATIVE = {"name": "Luke", "xws": "luke", "initiative": 5}
MOCK_UPGRADE_FIXED_COST = {"name": "R2-D2", "cost": {"value": 8}}
MOCK_UPGRADE_VARIABLE_SIZE = {
    "name": "Shield Upgrade",
    "cost": {
        "variable": "size",
        "values": {"small": 6, "medium": 8, "large": 10},
    },
}
MOCK_UPGRADE_VARIABLE_AGILITY = {
    "name": "Stealth Device",
    "cost": {
        "variable": "agility",
        "values": {"0": 3, "1": 4, "2": 6, "3": 8},
    },
}
MOCK_UPGRADE_VARIABLE_INITIATIVE = {
    "name": "Vet Turret Gunner",
    "cost": {
        "variable": "initiative",
        "values": {"1": 2, "2": 3, "3": 4, "4": 5, "5": 6, "6": 7},
    },
}


# ========= Helper Function Tests (Unchanged) =========
@pytest.mark.parametrize(
    "url, expected_mode, expected_points",
    [
        (
            "https://xwing-legacy.com/?f=Scum&d=v8ZhZ250Z98XWW&sn=Test&obs=",
            "Wildspace",
            250,
        ),
        (
            "https://xwing-legacy.com/?f=Rebel&d=v8ZsZ200Z5XW&sn=Test&obs=",
            "Standard",
            200,
        ),
        (
            "https://xwing-legacy.com/?f=Empire&d=v8ZeZ500Z416X&sn=Test&obs=",
            "Epic",
            500,
        ),
        (
            "https://xwing-legacy.com/?f=Resistance&d=v8ZqZ0Z&sn=Test&obs=",
            "Quickbuild",
            0,
        ),
        (
            "http://xwing-legacy.com/?f=Scum&d=v8ZhZ250Z98XWW&sn=Test&obs=",
            "Wildspace",
            250,
        ),
    ],
)
def test_get_gamemode_valid(mocker, url, expected_mode, expected_points):
    mocker.patch("main.config.MODE_URL_PATTERN", CORRECT_MODE_URL_PATTERN)
    mocker.patch("main.config.MODE_MAPPING", CORRECT_MODE_MAPPING)
    assert main.get_gamemode(url) == (expected_mode, expected_points)


@pytest.mark.parametrize(
    "url",
    [
        "https://xwing-legacy.com/?f=Rebel&d=v9ZsZ20Z5XW&sn=WrongVersion&obs=",
        "https://xwing-legacy.com/?f=Rebel&sn=NoData&obs=",
        "not_a_url",
        "https://xwing-legacy.com/?f=Rebel&d=v8ZsZabcZ5XW&sn=BadPoints&obs=",
    ],
)
def test_get_gamemode_invalid(mocker, url):
    mocker.patch("main.config.MODE_URL_PATTERN", CORRECT_MODE_URL_PATTERN)
    mocker.patch("main.config.MODE_MAPPING", CORRECT_MODE_MAPPING)
    assert main.get_gamemode(url) is None


STATS_LIST_FOR_TEST = [
    {"type": "attack", "value": 3},
    {"type": "agility", "value": 2},
    {"type": "hull", "value": 4},
    {"type": "shields", "value": 2},
]


@pytest.mark.parametrize(
    "stats_list, stat_type, expected_value",
    [
        (STATS_LIST_FOR_TEST, "agility", 2),
        (STATS_LIST_FOR_TEST, "hull", 4),
        (STATS_LIST_FOR_TEST, "speed", None),
        ([], "agility", None),
        (None, "agility", None),
        ("not a list", "agility", None),
        ([{"typ": "agility", "val": 1}], "agility", None),
    ],
)
def test_get_ship_stat_value(stats_list, stat_type, expected_value):
    assert main.get_ship_stat_value(stats_list, stat_type) == expected_value


@pytest.mark.parametrize(
    "upgrade_data, ship_details, pilot_info, expected_cost",
    [
        (
            MOCK_UPGRADE_FIXED_COST,
            MOCK_SHIP_DETAILS_SIZE,
            MOCK_PILOT_INFO_INITIATIVE,
            8,
        ),
        (
            MOCK_UPGRADE_VARIABLE_SIZE,
            MOCK_SHIP_DETAILS_SIZE,
            MOCK_PILOT_INFO_INITIATIVE,
            6,
        ),
        (
            MOCK_UPGRADE_VARIABLE_SIZE,
            {**MOCK_SHIP_DETAILS_SIZE, "size": "large"},
            MOCK_PILOT_INFO_INITIATIVE,
            10,
        ),
        (
            MOCK_UPGRADE_VARIABLE_AGILITY,
            MOCK_SHIP_DETAILS_SIZE,
            MOCK_PILOT_INFO_INITIATIVE,
            6,
        ),
        (
            MOCK_UPGRADE_VARIABLE_AGILITY,
            MOCK_SHIP_DETAILS_AGILITY,
            MOCK_PILOT_INFO_INITIATIVE,
            4,
        ),
        (
            MOCK_UPGRADE_VARIABLE_AGILITY,
            {
                **MOCK_SHIP_DETAILS_SIZE,
                "stats": [{"type": "agility", "value": 0}],
            },
            MOCK_PILOT_INFO_INITIATIVE,
            3,
        ),
        (
            MOCK_UPGRADE_VARIABLE_INITIATIVE,
            MOCK_SHIP_DETAILS_SIZE,
            MOCK_PILOT_INFO_INITIATIVE,
            6,
        ),
        (
            MOCK_UPGRADE_VARIABLE_INITIATIVE,
            MOCK_SHIP_DETAILS_SIZE,
            {**MOCK_PILOT_INFO_INITIATIVE, "initiative": 2},
            3,
        ),
        (None, MOCK_SHIP_DETAILS_SIZE, MOCK_PILOT_INFO_INITIATIVE, None),
        ({}, MOCK_SHIP_DETAILS_SIZE, MOCK_PILOT_INFO_INITIATIVE, None),
        (
            {"name": "Test", "cost": {}},
            MOCK_SHIP_DETAILS_SIZE,
            MOCK_PILOT_INFO_INITIATIVE,
            None,
        ),
        (
            {"name": "Test", "cost": {"value": "abc"}},
            MOCK_SHIP_DETAILS_SIZE,
            MOCK_PILOT_INFO_INITIATIVE,
            None,
        ),
        (
            {
                "name": "Test",
                "cost": {"variable": "agility", "values": {"1": "a"}},
            },
            MOCK_SHIP_DETAILS_AGILITY,
            MOCK_PILOT_INFO_INITIATIVE,
            None,
        ),
        (
            {
                "name": "Test",
                "cost": {"variable": "size", "values": {"medium": 5}},
            },
            MOCK_SHIP_DETAILS_SIZE,
            MOCK_PILOT_INFO_INITIATIVE,
            None,
        ),
    ],
)
def test_calculate_upgrade_cost(
    upgrade_data, ship_details, pilot_info, expected_cost
):
    assert (
        main.calculate_upgrade_cost(upgrade_data, ship_details, pilot_info)
        == expected_cost
    )


# ========= ConfirmationView Tests (Unchanged) =========
@pytest.fixture
def mock_view_objects():
    mock_original_message = MagicMock(spec=main.discord.Message)
    mock_original_message.author = MagicMock(spec=main.discord.User)
    mock_original_message.author.id = 12345
    mock_original_message.id = 54321
    mock_original_message.channel = AsyncMock(spec=main.discord.TextChannel)
    mock_original_message.channel.id = 9876
    mock_original_message.delete = AsyncMock()
    mock_interaction = AsyncMock(spec=main.discord.Interaction)
    mock_interaction.user = MagicMock(spec=main.discord.User)
    mock_interaction.response = AsyncMock(
        spec=main.discord.InteractionResponse
    )
    mock_interaction.response.defer = AsyncMock()
    mock_interaction.response.send_message = AsyncMock()
    mock_interaction.followup = AsyncMock(spec=main.discord.Webhook)
    mock_interaction.followup.send = AsyncMock()
    mock_interaction.delete_original_response = AsyncMock()
    mock_interaction.channel_id = 9876
    return mock_original_message, mock_interaction


def find_button_callback(view, custom_id):
    for item in view.children:
        if isinstance(item, discord.ui.Button) and item.custom_id == custom_id:
            return item.callback
    raise ValueError(f"Button with custom_id '{custom_id}' not found in view")


@pytest.mark.asyncio
async def test_confirmation_view_interaction_check_pass(mock_view_objects):
    mock_original_message, mock_interaction = mock_view_objects
    mock_interaction.user.id = 12345
    view = main.ConfirmationView(original_message=mock_original_message)
    assert await view.interaction_check(mock_interaction) is True
    mock_interaction.response.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_confirmation_view_interaction_check_fail(mock_view_objects):
    mock_original_message, mock_interaction = mock_view_objects
    mock_interaction.user.id = 55555
    view = main.ConfirmationView(original_message=mock_original_message)
    assert await view.interaction_check(mock_interaction) is False
    mock_interaction.response.send_message.assert_called_once_with(
        ANY, ephemeral=True
    )


@pytest.mark.asyncio
async def test_confirmation_view_yes_button_callback_success(
    mocker, mock_view_objects
):
    mock_original_message, mock_interaction = mock_view_objects
    mock_interaction.user.id = 12345
    view = main.ConfirmationView(original_message=mock_original_message)
    mocker.patch.object(view, "stop")
    yes_callback = find_button_callback(view, "confirm_delete_yes")
    await yes_callback(mock_interaction)
    mock_interaction.response.defer.assert_awaited_once_with(ephemeral=True)
    mock_original_message.delete.assert_awaited_once()
    mock_interaction.delete_original_response.assert_awaited_once()
    mock_interaction.followup.send.assert_not_awaited()
    assert view.message_deleted is True
    view.stop.assert_called_once()


@pytest.mark.asyncio
async def test_confirmation_view_yes_button_callback_forbidden(
    mocker, mock_view_objects
):
    mock_original_message, mock_interaction = mock_view_objects
    mock_interaction.user.id = 12345
    mock_original_message.delete.side_effect = discord.Forbidden(
        MagicMock(), "cannot delete"
    )
    view = main.ConfirmationView(original_message=mock_original_message)
    mocker.patch.object(view, "stop")
    yes_callback = find_button_callback(view, "confirm_delete_yes")
    await yes_callback(mock_interaction)
    mock_interaction.response.defer.assert_awaited_once_with(ephemeral=True)
    mock_original_message.delete.assert_awaited_once()
    mock_interaction.delete_original_response.assert_awaited_once()
    mock_interaction.followup.send.assert_awaited_once_with(
        content=ANY, ephemeral=True
    )
    assert (
        "lacks authorization"
        in mock_interaction.followup.send.await_args.kwargs["content"]
    )
    assert view.message_deleted is False
    view.stop.assert_called_once()


@pytest.mark.asyncio
async def test_confirmation_view_no_button_callback(mocker, mock_view_objects):
    mock_original_message, mock_interaction = mock_view_objects
    mock_interaction.user.id = 12345
    view = main.ConfirmationView(original_message=mock_original_message)
    mocker.patch.object(view, "stop")
    no_callback = find_button_callback(view, "confirm_delete_no")
    await no_callback(mock_interaction)
    mock_interaction.response.defer.assert_awaited_once_with(ephemeral=True)
    mock_original_message.delete.assert_not_awaited()
    mock_interaction.delete_original_response.assert_awaited_once()
    mock_interaction.followup.send.assert_not_awaited()
    assert view.message_deleted is False
    view.stop.assert_called_once()


@pytest.mark.asyncio
async def test_confirmation_view_on_timeout(mocker, mock_view_objects):
    mock_original_message, _ = mock_view_objects
    mock_delete_button_message = mocker.patch(
        "main.ConfirmationView._delete_button_message",
        new_callable=AsyncMock,
    )
    view = main.ConfirmationView(original_message=mock_original_message)
    await view.on_timeout()
    mock_delete_button_message.assert_awaited_once()


# ========= on_message Tests (Corrected aiohttp Mock) =========


@pytest.fixture
def mock_message():
    msg = AsyncMock(spec=main.discord.Message)
    msg.author = MagicMock(spec=main.discord.User)
    msg.author.id = 111
    msg.author.name = "ScumTester"
    msg.author.display_name = "ScumTester"
    msg.author.display_avatar = MagicMock(url="avatar_url")
    msg.author.mention = "<@111>"
    msg.channel = AsyncMock(spec=main.discord.TextChannel)
    msg.channel.id = 999
    msg.channel.send = AsyncMock()
    msg.guild = MagicMock(spec=main.discord.Guild)
    msg.id = 12345
    msg.content = ""
    return msg


@pytest.fixture
def mock_aiohttp_get(mocker):
    # Mock for the response object yielded by the context manager
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.raise_for_status = MagicMock()  # No-op for success
    mock_response.text = AsyncMock(
        return_value=json.dumps(MOCK_XWS_RESPONSE_SCUM)
    )

    # Mock for the async context manager object
    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__.return_value = mock_response
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)

    # Mock for the session.get() method itself
    # session.get() returns the context manager, it's not awaited itself
    mock_session_get = MagicMock(return_value=mock_context_manager)

    # Patch the session instance within the outer context manager
    mock_session_instance = mocker.patch(
        "main.aiohttp.ClientSession"
    ).return_value.__aenter__.return_value
    mock_session_instance.get = mock_session_get  # Assign the mock get method

    # Return the mock for session.get() and the mock_response for
    # assertions/modification
    return mock_session_get, mock_response


def configure_scum_db_mocks(mocker):
    mock_find_pilot = mocker.patch("main.find_pilot")
    mock_find_ship = mocker.patch("main.find_ship_by_pilot")
    mock_find_upgrade = mocker.patch("main.find_upgrade")
    mocker.patch("main.find_faction", return_value=MOCK_SCUM_FACTION_DATA)

    def find_pilot_se(pilot_id):
        pilots = {
            p["xws"]: p
            for p in [
                MOCK_OLDTEROCH_PILOT,
                MOCK_SHADOWPORT_PILOT,
                MOCK_FREIGHTER_PILOT,
                MOCK_SPICERUNNER_PILOT,
            ]
        }
        return pilots.get(pilot_id)

    def find_ship_se(pilot_xws):
        ships = {
            "oldteroch": MOCK_FANG_SHIP,
            "shadowporthunter": MOCK_LANCER_SHIP,
            "freightercaptain": MOCK_YT1300_SHIP,
            "spicerunner": MOCK_HWK_SHIP,
        }
        return ships.get(pilot_xws)

    def find_upgrade_se(upgrade_id):
        upgrades = {
            u["xws"]: u
            for u in [
                MOCK_UPGRADE_AFTERBURNERS,
                MOCK_UPGRADE_HULLUPGRADE,
                MOCK_UPGRADE_MIGS,
            ]
        }
        return upgrades.get(upgrade_id)

    mock_find_pilot.side_effect = find_pilot_se
    mock_find_ship.side_effect = find_ship_se
    mock_find_upgrade.side_effect = find_upgrade_se
    return mock_find_pilot, mock_find_ship, mock_find_upgrade


@pytest.fixture(autouse=True)
def mock_bot_instance(mocker):
    mock_bot = MagicMock(spec=main.discord.Bot)
    mock_bot.user = MagicMock(spec=main.discord.ClientUser, id=99999)
    mocker.patch("main.bot", mock_bot)
    return mock_bot


@pytest.mark.asyncio
async def test_on_message_scum_success(
    mocker, mock_message, mock_aiohttp_get, mock_bot_instance
):
    # --- Setup Mocks ---
    mocker.patch("main.config.RB_ENDPOINT", CORRECT_RB_ENDPOINT)
    mocker.patch("main.config.YASB_URL_PATTERN", CORRECT_YASB_URL_PATTERN)
    mocker.patch("main.config.MODE_URL_PATTERN", CORRECT_MODE_URL_PATTERN)
    mocker.patch("main.config.MODE_MAPPING", CORRECT_MODE_MAPPING)
    mocker.patch("main.config.DISCORD_EMBED_DESCRIPTION_LIMIT", 4096)
    mocker.patch("main.config.FOOTER_PHRASES", ["Test Footer"])
    mocker.patch("main.config.GOLDENROD_PILOTS_URL", "pilot_img_base/")
    mocker.patch("main.config.GOLDENROD_UPGRADES_URL", "upgrade_img_base/")
    mocker.patch("main.logging", autospec=True)
    mocker.patch("main.prepare_collections")
    mocker.patch("main.convert_faction_to_color", return_value=0x33DD33)
    mocker.patch(
        "main.ship_emojis",
        {
            "fangfighter": "<:fang:123>",
            "lancerclasspursuitcraft": "<:lancer:123>",
            "customizedyt1300lightfreighter": "<:yt1300s:123>",
            "hwk290lightfreighter": "<:hwk:123>",
        },
    )
    mocker.patch(
        "main.ini_emojis", {1: "<:i1:123>", 2: "<:i2:123>", 5: "<:i5:123>"}
    )
    mock_confirmation_view = mocker.patch("main.ConfirmationView")
    mock_find_pilot, mock_find_ship, mock_find_upgrade = (
        configure_scum_db_mocks(mocker)
    )
    mock_http_get, _ = mock_aiohttp_get
    correct_url = MOCK_XWS_RESPONSE_SCUM["vendor"]["yasb"]["link"]
    mock_message.content = f"List pls: {correct_url}"
    mock_lock_instance = AsyncMock()
    mocker.patch("asyncio.Lock", return_value=mock_lock_instance)
    mocker.patch("main.channel_locks", {})

    # --- Run on_message ---
    await main.on_message(mock_message)
    # --- --- --- --- --- --

    # --- Assertions ---
    mock_lock_instance.__aenter__.assert_awaited_once()
    mock_http_get.assert_called_once_with(
        CORRECT_RB_ENDPOINT + correct_url, timeout=20
    )
    mock_find_pilot.assert_any_call("oldteroch")
    embed_call = next(
        (
            c
            for c in mock_message.channel.send.await_args_list
            if isinstance(c.kwargs.get("embed"), discord.Embed)
        ),
        None,
    )
    assert embed_call is not None, "Embed was not sent"
    mock_confirmation_view.assert_called_once_with(
        original_message=mock_message
    )
    view_call = next(
        (
            c
            for c in mock_message.channel.send.await_args_list
            if isinstance(c.kwargs.get("view"), MagicMock)
        ),
        None,
    )
    assert view_call is not None, "Confirmation View message not sent"
    mock_lock_instance.__aexit__.assert_awaited_once()


@pytest.mark.asyncio
async def test_on_message_no_url(mocker, mock_message, mock_bot_instance):
    mock_message.content = "Hello there"
    await main.on_message(mock_message)
    mock_message.channel.send.assert_not_called()


@pytest.mark.asyncio
async def test_on_message_http_error(
    mocker, mock_message, mock_aiohttp_get, mock_bot_instance
):
    mocker.patch("main.config.RB_ENDPOINT", CORRECT_RB_ENDPOINT)
    mocker.patch("main.config.YASB_URL_PATTERN", CORRECT_YASB_URL_PATTERN)
    mocker.patch("main.logging", autospec=True)
    mocker.patch("main.channel_locks", {})
    mocker.patch("asyncio.Lock", return_value=AsyncMock())
    mock_confirmation_view = mocker.patch("main.ConfirmationView")
    mock_http_get, mock_response = mock_aiohttp_get
    mock_response.status = 404
    # Configure the context manager's __aenter__ to raise the error
    # via raise_for_status
    mock_response.raise_for_status.side_effect = (
        main.aiohttp.ClientResponseError(
            MagicMock(), (), status=404, message="Not Found"
        )
    )
    mock_message.content = (
        "https://xwing-legacy.com/?f=Rebel&d=v8ZsZ200Zbad&sn=Error&obs="
    )
    await main.on_message(mock_message)

    mock_http_get.assert_called_once()
    embed_send_calls = [
        c
        for c in mock_message.channel.send.await_args_list
        if "embed" in c.kwargs
    ]
    assert len(embed_send_calls) == 0
    mock_confirmation_view.assert_not_called()
