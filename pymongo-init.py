import json
import os
from glob import iglob

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from pymongo.server_api import ServerApi

uri = "mongodb://root:example@localhost:27017/xwingdata?authSource=admin"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi("1"))
xws_db = client["xwing-data2"]

COLLECTIONS_UPLOAD = {
    "actions": "collection_actions",
    "conditions": "collection_conditions",
    "damage-decks": "collection_damage_decks",
    "factions": "collection_factions",
    "pilots": "collections_pilots",
    "quick-builds": "collections_quick_builds",
    "stats": "collections_stats",
    "upgrades": "collections_upgrades",
}


def access_variable_by_string(var_name):
    globals_dict = globals()
    if var_name in globals_dict:
        return globals_dict[var_name]
    else:
        return None


def is_json_array(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        try:
            data = json.load(file)
            return isinstance(data, list)
        except json.JSONDecodeError:
            return False


def import_collection(collection_name, data_dir):
    """Imports data for a specific collection."""
    collection = xws_db[collection_name]
    if collection_name not in xws_db.list_collection_names():
        rootdir_glob = os.path.join(data_dir, collection_name, "**/*")
        file_list = [
            f for f in iglob(rootdir_glob, recursive=True) if os.path.isfile(f)
        ]
        for f in file_list:
            with open(f, "r", encoding="utf8") as file:
                try:
                    data = json.load(file)
                    if is_json_array(f):
                        collection.insert_many(data)
                    else:
                        collection.insert_one(data)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON in file {f}: {e}")
        print(f"Collection '{collection_name}' imported successfully.")
    else:
        print(f"Collection '{collection_name}' already exists.")


def prepare_collections(data_root_dir):
    """Checks and imports all collections if needed."""
    for collection_name in COLLECTIONS_UPLOAD:
        import_collection(collection_name, data_root_dir)


if __name__ == "__main__":
    try:
        data_root_dir = "submodules/xwing-data2/data"  # Adjust if needed
        prepare_collections(data_root_dir)
        print(f"\nCollections after import: {xws_db.list_collection_names()}")
    except ConnectionFailure as e:
        print(f"Could not connect to MongoDB: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        client.close()
