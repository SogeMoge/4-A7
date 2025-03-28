from bot.mongo.find_pilot import find_pilot
from bot.mongo.init_db import prepare_collections

mongodb_uri = (
    "mongodb://root:example@localhost:27017/xwingdata?authSource=admin"
)
data_root_dir = "submodules/xwing-data2/data"

if __name__ == "__main__":
    prepare_collections(data_root_dir, mongodb_uri)
    pilot = find_pilot("firstordertestpilot", mongodb_uri)
    print(pilot)
