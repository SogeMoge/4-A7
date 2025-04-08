import json
import os
import time
from glob import iglob

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from pymongo.server_api import ServerApi

# mongodb_uri = "mongodb://root:example@localhost:27017/xwingdata?authSource=admin"

# Create a new client and connect to the server


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


def drop_collections(mongodb_uri):
    """Drops all collections defined in COLLECTIONS_UPLOAD from the
        'xwing-data2' database.

    This function connects to a MongoDB instance using the provided URI,
    accesses the 'xwing-data2' database, and attempts to drop each collection
    specified in the `COLLECTIONS_UPLOAD` dictionary. It handles cases where
    a collection might not exist and reports any errors encountered during
    the process.

    Args:
        mongodb_uri (str): The MongoDB connection URI.

    Returns:
        None

    Raises:
        pymongo.errors.ConnectionFailure:
            If a connection to the MongoDB server cannot be established.
        pymongo.errors.OperationFailure:
            If an error occurs during a database operation.
        Exception: If any other unexpected error occurs.
    """
    client = MongoClient(mongodb_uri, server_api=ServerApi("1"))
    try:
        xws_db = client["xwing-data2"]

        for collection_name in COLLECTIONS_UPLOAD:
            try:
                if collection_name in xws_db.list_collection_names():
                    xws_db.drop_collection(collection_name)
                    print(
                        f"Collection '{collection_name}' dropped successfully."
                    )
                else:
                    print(f"Collection '{collection_name}' does not exist.")
            except Exception as e:
                print(f"Error dropping collection '{collection_name}': {e}")
        print(f"Collections after drop: {xws_db.list_collection_names()}")
    finally:
        client.close()


def retry_mongodb_connection(
    func, mongodb_uri, *args, max_retries=10, retry_delay=5
):
    """Retries a MongoDB function with exponential backoff."""
    retries = 0
    while retries < max_retries:
        try:
            return func(*args, mongodb_uri=mongodb_uri)
        except ConnectionFailure as e:
            print(
                f"MongoDB connection failed: {e}. Retrying in "
                f"{retry_delay} seconds..."
            )
            retries += 1
            time.sleep(retry_delay)
    raise ConnectionFailure(
        "Max retries reached. Failed to connect to MongoDB."
    )


def import_collection(collection_name, data_dir, mongodb_uri):
    """Imports data from JSON files into a specified MongoDB collection.

    This function connects to a MongoDB database, creates a collection if it
    doesn't exist, and then imports data from JSON files located in a
    specified directory. It handles both JSON objects and arrays, using
    `insert_one` and `insert_many` respectively.

    Args:
        collection_name (str): The name of the MongoDB collection to
            import data into.
        data_dir (str): The root directory containing the data files.
        mongodb_uri (str): The MongoDB connection URI.

    Returns:
        None

    Raises:
        pymongo.errors.ConnectionFailure: If a connection to the
            MongoDB server cannot be established.
        pymongo.errors.OperationFailure: If an error occurs during a
            database operation.
        json.JSONDecodeError: If a JSON file cannot be decoded.
        FileNotFoundError: If a file in the specified directory
            cannot be found.
        Exception: If any other unexpected error occurs.
    """
    client = MongoClient(mongodb_uri, server_api=ServerApi("1"))
    try:
        xws_db = client["xwing-data2"]

        collection = xws_db[collection_name]
        if collection_name not in xws_db.list_collection_names():
            rootdir_glob = os.path.join(data_dir, collection_name, "**/*")
            file_list = [
                f
                for f in iglob(rootdir_glob, recursive=True)
                if os.path.isfile(f)
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
    finally:
        client.close()


def prepare_collections(data_root_dir, mongodb_uri):
    """Imports all collections from the xwing-data2 dataset into MongoDB.

    This function iterates through the `COLLECTIONS_UPLOAD` dictionary,
    and for each collection name, it calls the `import_collection` function
    to import the corresponding data from the xwing-data2 dataset into the
    MongoDB database specified by `mongodb_uri`.

    Args:
        data_root_dir (str): The root directory of the xwing-data2 dataset.
        mongodb_uri (str): The MongoDB connection URI.

    Returns:
        None

    Raises:
        pymongo.errors.ConnectionFailure: If a connection to the
            MongoDB server cannot be established.
        pymongo.errors.OperationFailure: If an error occurs during a
            database operation.
        json.JSONDecodeError: If a JSON file cannot be decoded.
        FileNotFoundError: If a file in the specified directory
            cannot be found.
        Exception: If any other unexpected error occurs.
    """
    for collection_name in COLLECTIONS_UPLOAD:
        retry_mongodb_connection(
            import_collection, mongodb_uri, collection_name, data_root_dir
        )


def reload_collections(data_root_dir, mongodb_uri):
    """Reinitializes the MongoDB database with data from the
        xwing-data2 dataset.

    This function first drops all existing collections defined in
    `COLLECTIONS_UPLOAD` from the 'xwing-data2' database. Then, it re-imports
    all the data from the xwing-data2 dataset into the database, effectively
    refreshing the database with the latest data. This is useful for
    accommodating updates to the data files.

    Args:
        data_root_dir (str): The root directory of the xwing-data2 dataset.
        mongodb_uri (str): The MongoDB connection URI.

    Returns:
        None

    Raises:
        pymongo.errors.ConnectionFailure: If a connection to the
            MongoDB server cannot be established.
        pymongo.errors.OperationFailure: If an error occurs during a
            database operation.
        json.JSONDecodeError: If a JSON file cannot be decoded.
        FileNotFoundError: If a file in the specified directory
            cannot be found.
        Exception: If any other unexpected error occurs.
    """
    retry_mongodb_connection(drop_collections, mongodb_uri)
    for collection_name in COLLECTIONS_UPLOAD:
        retry_mongodb_connection(
            import_collection, mongodb_uri, collection_name, data_root_dir
        )
