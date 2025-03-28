from bot.mongo.init_db import prepare_collections
from bot.mongo.find_pilot import find_pilot

if __name__ == "__main__":
    data_root_dir = "submodules/xwing-data2/data"
    prepare_collections(data_root_dir)
    pilot = find_pilot("blackout")
    print(pilot)
