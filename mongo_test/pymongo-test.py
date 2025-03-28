# from pymongo.mongo_client import MongoClient
import json
import os
from glob import iglob
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# uri = "mongodb+srv://sogemoge:MPCGdnAgeMunZDWD@unknown-regions.tyaoq7q.mongodb.net/?retryWrites=true&w=majority"
# uri = "mongodb://admin:pass@localhost:27017/test?authSource=admin"
uri = "mongodb://root:example@localhost:27017/xwingdata?authSource=admin"
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi("1"))
# set a name for xws database
xws_db = client["xwing-data2"]
# set collections corresponding to xwing-data2 objects
# collection_actions = xws_database["actions"]
# collection_conditions = xws_database["conditions"]
# collection_damage_decks = xws_database["damage-decks"]
# collection_factions = xws_database["factions"]
collections_pilots = xws_db["pilots"]
# collections_quick_builds = xws_database["quick-builds"]
# collections_stats = xws_database["stats"]
# collections_upgrades = xws_database["upgrades"]

collection = xws_db["factions"]


if "factions" not in xws_db.list_collection_names():
    with open(
        "U:\\xwing\\protocols\\4-A7\\submodules\\xwing-data2\\data\\factions\\factions.json"
    ) as file:
        file_data = json.load(file)

    if isinstance(file_data, list):
        collection.insert_many(file_data)
    else:
        collection.insert_one(file_data)
else:
    print(f"collection {collection} already exists")

try:
    xws_faction = "galacticempire"
    faction_name = list(
        collection.find({"xws": xws_faction}, {"_id": 0, "name": 1})
    )
    print(faction_name[0]["name"])
except Exception as e:
    print(f"ERROR: {e}")

if "pilots" not in xws_db.list_collection_names():
    rootdir_glob = (
        "U:/xwing/protocols/4-A7/submodules/xwing-data2/data/pilots/**/*"
    )
    file_list = [
        f for f in iglob(rootdir_glob, recursive=True) if os.path.isfile(f)
    ]
    for f in file_list:
        with open(f, "r", encoding="utf8") as file:
            # file_data = json.load(file)
            collections_pilots.insert_one(json.load(file))
    else:
        print(f"collection {collections_pilots} already exists")


    # try:
    #     client.admin.command("ping")
#     print("Pinged your deployment. You successfully connected to MongoDB!")
# except Exception as e:
#     print(e)

# try:
#     print(client.list_database_names())
# except Exception as e:
#     print(e)

try:
    print(
        f"\n0........collections after import: {xws_db.list_collection_names()}"
    )
except Exception as e:
    print(e)

try:
    pilot = []
    ability = []
    # pilots = list(collections_pilots.find())
    # pilots = list(collections_pilots.find({"xws": "sithinfiltrator"}))
    pilot = list(
        collections_pilots.find(
            {"pilots.xws": "gorgol"}, {"pilots.$": 1, "_id": 0}
        )
    )
    print(f"Pilot found in collection: {pilot}")

    ability = pilot[0]["pilots"][0]["ability"]
    print(f"\nPilot ability: {ability}")

except Exception as e:
    print(e)

# try:
#     xws_db.drop_collection(collection)
#     xws_db.drop_collection(collections_pilots)
#     print(f"3........collections after drop: {xws_db.list_collection_names()}")
# except Exception as e:
#     print(e)

client.close()
# try:
#     current_db = client.admin.command("show dbs")
#     print(f"You are connected to {current_db}")
# except Exception as e:
#     print(e)

# {
#   "pilots.xws": "breach"
# },
# {
#   "pilots.$": 1, _id: 0
#
# {
#   pilots: { $elemMatch: { xws: "breach"} }
# }
# {
#   "pilots.$": 1,  _id: 0
# }
#
# https://stackoverflow.com/questions/28982285/mongodb-projection-of-nested-arrays
