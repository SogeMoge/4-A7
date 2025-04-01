from pymongo import MongoClient
from pymongo.server_api import ServerApi


def find_pilot(xws, mongodb_uri):
    """
    Finds a pilot in the 'pilots' collection by their xws name.
    Args:
        xws (str): The xws name of the pilot to search for.
        mongodb_uri (str): The MongoDB URI to connect to.
    Returns:
        dict: A dictionary containing the pilot's data if found.
    Raises:
        ValueError: If no pilot with the given xws name is found.
    """

    client = MongoClient(mongodb_uri, server_api=ServerApi("1"))
    try:
        xws_db = client["xwing-data2"]
        pilots_collection = xws_db["pilots"]

        pilot_data = list(
            pilots_collection.find(
                {"pilots.xws": xws}, {"pilots.$": 1, "_id": 0}
            )
        )
        if pilot_data:
            return pilot_data[0]["pilots"][0]
        else:
            raise ValueError(f"Pilot with xws name '{xws}' not found.")
    finally:
        client.close()


def find_upgrade(xws, mongodb_uri):
    """
    Finds an upgrade in the 'upgrades' collection by its xws name.

    Args:
        xws (str): The xws name of the upgrade to search for.
        mongodb_uri (str): The MongoDB URI to connect to.

    Returns:
        dict: A dictionary containing the upgrade's data if found.

    Raises:
        ValueError: If no upgrade with the given xws name is found.
    """
    client = MongoClient(mongodb_uri, server_api=ServerApi("1"))
    try:
        xws_db = client["xwing-data2"]
        upgrades_collection = xws_db["upgrades"]

        upgrade_data = list(
            upgrades_collection.find(
                {"xws": xws}, {"_id": 0}
            )
        )
        if upgrade_data:
            return upgrade_data[0]
        else:
            raise ValueError(f"Upgrade with xws name '{xws}' not found.")
    finally:
        client.close()


def find_ship_by_pilot(xws, mongodb_uri):
    """
    Finds the ship data associated with a pilot by the pilot's xws name.

    Args:
        xws (str): The xws name of the pilot to search for.
        mongodb_uri (str): The MongoDB URI to connect to.

    Returns:
        dict: A dictionary containing the ship data associated with the pilot if found.

    Raises:
        ValueError: If no pilot with the given xws name is found.
    """
    client = MongoClient(mongodb_uri, server_api=ServerApi("1"))
    try:
        xws_db = client["xwing-data2"]
        pilots_collection = xws_db["pilots"]

        pilot_data = list(
            pilots_collection.find(
                {"pilots.xws": xws}, {"_id": 0}
            )
        )
        if pilot_data:
            return pilot_data[0]
        else:
            raise ValueError(f"Pilot with xws name '{xws}' not found.")
    finally:
        client.close()


def find_faction(xws, mongodb_uri):
    """
    Finds a faction by its xws name.

    Args:
        xws (str): The xws name of the faction to search for.
        mongodb_uri (str): The MongoDB URI to connect to.

    Returns:
        dict: A dictionary containing the faction's data if found.

    Raises:
        ValueError: If no faction with the given xws name is found.
    """
    client = MongoClient(mongodb_uri, server_api=ServerApi("1"))
    try:
        xws_db = client["xwing-data2"]
        factions_collection = xws_db["factions"]

        faction_data = list(
            factions_collection.find({"xws": xws}, {"_id": 0})
        )
        if faction_data:
            return faction_data[0]
        else:
            raise ValueError(f"Faction with xws name '{xws}' not found.")
    finally:
        client.close()
