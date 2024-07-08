# from pymongo.mongo_client import MongoClient
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

try:
    print("\n^^^^^^^^^^^^  START SCAN  ^^^^^^^^^^^^")
    pilot = []
    ability = []
    # pilots = list(collections_pilots.find())
    # pilots = list(collections_pilots.find({"xws": "sithinfiltrator"}))
    pilot = list(
        collections_pilots.find(
            {"pilots.xws": "kyloren"}, {"pilots.$": 1, "_id": 0}
        )
    )
    print(f"Pilot found in collection: {pilot}")

    ability = pilot[0]["pilots"][0]["ability"]
    print(f"\nPilot ability: {ability}")
    print("^^^^^^^^^^^^  STOP SCAN  ^^^^^^^^^^^^\n")
except Exception as e:
    print(e)

def find_pilot(str: xws):
    """Get all pilot data

    Args:
        str (xws): xws id
    """

# try:
#     pilots = []
#     ability = []
#     # pilots = list(collections_pilots.find())
#     # pilots = list(collections_pilots.find({"xws": "sithinfiltrator"}))
#     pilots_data = list(
#         collections_pilots.find(
#             # search for all sabine* names (case-insensitive)
#             {"pilots.name": {"$regex": "^sabine.*", "$options": "i"}},
#             {"pilots.$": 1, "_id": 0},
#         )
#     )
#     print(f"Pilots found in collection: {pilots_data}")
#     # iterates over each entry in the pilots_data list,
#     # then iterates over each pilot dictionary within
#     # the 'pilots' key of each pilots_entry
#     for pilots_entry in pilots_data:
#         for pilot in pilots_entry["pilots"]:
#             ability = pilot["ability"]
#             pilot_name = pilot["name"]
#             pilot_caption = pilot["caption"]
#             print(f'\n{pilot_name} "{pilot_caption}" ability: {ability}')
# except Exception as e:
#     print(e)

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
