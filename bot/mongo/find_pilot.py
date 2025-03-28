from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from pymongo.server_api import ServerApi

uri = "mongodb://root:example@localhost:27017/xwingdata?authSource=admin"
client = MongoClient(uri, server_api=ServerApi("1"))
xws_db = client["xwing-data2"]
collections_pilots = xws_db["pilots"]


def find_pilot(xws):
    """
    Finds a pilot in the 'pilots' collection by their xws name.
    Args:
        xws (str): The xws name of the pilot to search for.
    Returns:
        dict: A dictionary containing the pilot's data if found.
    Raises:
        ValueError: If no pilot with the given xws name is found.
    """

    pilot_data = list(
        collections_pilots.find({"pilots.xws": xws}, {"pilots.$": 1, "_id": 0})
    )
    if pilot_data:
        return pilot_data[0]["pilots"][0]
    else:
        raise ValueError(f"Pilot with xws name '{xws}' not found.")


if __name__ == "__main__":
    try:
        import sys

        if len(sys.argv) > 1:
            xws_name = sys.argv[1]
            pilot = find_pilot(xws_name)
            if pilot:
                print(pilot)
        else:
            print("Please provide an xws name as a command-line argument.")
    except ConnectionFailure as e:
        print(f"Could not connect to MongoDB: {e}")
    except ValueError as e:
        print(e)
    finally:
        client.close()
