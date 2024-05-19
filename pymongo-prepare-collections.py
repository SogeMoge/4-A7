# from pymongo.mongo_client import MongoClient

import json
import os
from glob import iglob

from pymongo import MongoClient

from pymongo.server_api import ServerApi


uri = "mongodb://root:example@localhost:27017/xwingdata?authSource=admin"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi("1"))

# set a name for xws database
xws_db = client["xwing-data2"]

# set collections corresponding to xwing-data2 objects
collection_actions = xws_db["actions"]
collection_conditions = xws_db["conditions"]
collection_damage_decks = xws_db["damage-decks"]
collection_factions = xws_db["factions"]
collections_pilots = xws_db["pilots"]
collections_quick_builds = xws_db["quick-builds"]
collections_stats = xws_db["stats"]
collections_upgrades = xws_db["upgrades"]

# set corellation with xwing-data2 dir structure and collections
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
    """Get string with the name of a variable and use it as variable itself

    Args:
        var_name (str): name of a variable to be replaced with actual variable

    Returns:
        str: name of a variable
    """
    # Using locals() to access local variables
    globals_dict = globals()
    if var_name in globals_dict:
        return globals_dict[var_name]
    else:
        return None  # Variable not found


def is_json_array(file_path):
    """Check if processing json file is array.
    If true then insert_many should be used.

    Args:
        file_path (str): path to json file

    Returns:
        bool: true if file is an array
    """
    with open(file_path, "r", encoding="utf-8") as file:
        try:
            data = json.load(file)
            return isinstance(data, list)
        except json.JSONDecodeError:
            return False


def import_collection():
    """Import all xwing-data2 files into mongodb collections
    representing each game component type.
    """
    for key, value in COLLECTIONS_UPLOAD.items():
        # Insert files only if collection is not present in db
        if key not in xws_db.list_collection_names():
            rootdir_glob = "submodules/xwing-data2/data/" + key + "/**/*"
            # generate list of files for each game component type
            file_list = [
                f
                for f in iglob(rootdir_glob, recursive=True)
                if os.path.isfile(f)
            ]
            # import file/files into collections
            for f in file_list:
                with open(f, "r", encoding="utf8") as file:
                    if is_json_array(f):
                        access_variable_by_string(value).insert_many(
                            json.load(file)
                        )
                    else:
                        access_variable_by_string(value).insert_one(
                            json.load(file)
                        )
        else:
            print(f"collection {key} already exists")
    # display imported collections
    try:
        print(f"\nCollections after import: {xws_db.list_collection_names()}")
    except Exception as e:
        print(e)

    return


def drop_collections():
    for key, value in COLLECTIONS_UPLOAD.items():
        try:
            xws_db.drop_collection(key)

        except Exception as e:
            print(e)
    print(f"Collections after drop: {xws_db.list_collection_names()}")


try:
    client.admin.command("ping")
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)


try:
    print(client.list_database_names())
except Exception as e:
    print(e)

# drop_collections()
import_collection()


client.close()
