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
        collections_pilots = xws_db["pilots"]

        pilot_data = list(
            collections_pilots.find(
                {"pilots.xws": xws}, {"pilots.$": 1, "_id": 0}
            )
        )
        if pilot_data:
            return pilot_data[0]["pilots"][0]
        else:
            raise ValueError(f"Pilot with xws name '{xws}' not found.")
    finally:
        client.close()
