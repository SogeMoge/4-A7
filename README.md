# 4-A7

Discord bot that converts http://xwing-legacy.com/ URL to rich embed messages
![](https://static.wikia.nocookie.net/starwars/images/c/ce/4A-7-TCWf.png/revision/latest?cb=20200501010504)

<a href="https://discord.com/api/oauth2/authorize?client_id=1076175997143105536&permissions=274878195776&scope=bot%20applications.commands">Add to Discord</a>

# Features

## Convert Legacy YASB URL to human-readable lists

Just paste your list URL into a channel and let the bot handle it! (on Windows, you can press F6 then CTRL+C to copy URL to clipboard)

What happens under the hood:
1. Parses user messages in server channels for <https://xwing-legacy.com/> urls.
2. Converts YASB URSL to XWS with `https://rollbetter-linux.azurewebsites.net/lists/xwing-legacy?` endpoint.
3. Enriches pilots and upgrades with full data from [xwing-data2-legacy](https://github.com/SogeMoge/xwing-data2-legacy/releases)
4. Contructs human-readable rich embedded messages and sends them in original channel as a response.
5. Creates a view with confirmation buttons for a user to delete their origina message to redce channel clutter.

## Slash `/` commands

### Display links to X-Wing 2.0 Legacy Rules
Type `/rules` in discord channel to get rules for gamemodes:
- [Standard](https://x2po.org/standard)
- [Epic](https://x2po.org/standard)
- [Wild Space](https://x2po.org/standard)
- [Adopted Battle Scenarios](https://x2po.org/battle-scenarios)

And more!
- [Video tutorials](https://x2po.org/media)
- [Google sheets with points retrospective](https://points.x2po.org)

### Display links to X-Wing 2.0 Legacy compatible builders
Type `/builders` in discord channel to get URLs for gamemodes:
- [YASB 2.0 Legacy](https://xwing-legacy.com/)
- [X-Wing 2nd Ed. Squads Designer](https://www.dmborque.eu/swz)
- [Infinite Arenas](https://infinitearenas.com/legacy/)
- Launch Bay Next ([Android](http://play.google.com/store/apps/details?id=com.launchbaynext)/[iOS](https://apps.apple.com/us/app/launch-bay-next/id1422488966))

### Show them the way
Type `/thisistheway` in discord channel to get directions.

### Show True Love
Type `/reinforcements` in discord channel to greet newcomers.


# How To

## Run tests

Tests are located in [test_main.py](test_main.py)

```shell
python -m pytest
```

## Start MongoDB
4-A7 checks if DB is initialised upon start and populates it with data if it is not present.
> Run docker-compose stack with mondodb for storing xwing-data2-legacy repo.
```
sudo docker-compose -f /deploy/db/stack.yml up -d
```

## Generate ship emojis

Run [fonts/fonts_mapping.py](fonts/fonts_mapping.py) to extract ship icons from [fonts/xwing-miniatures-ships.ttf](fonts/xwing-miniatures-ships.ttf)


## Start api server (WIP):

**Linux**
```shell
uvicorn api:app --port 7000 --reload
```

**Windows**
```powershell
C:/Python311/python.exe -m uvicorn api:app --port 7000 --reload
```

# Inspired by

<a href="https://github.com/Apollonaut13/r2-d7">R2-D7</a> bot
