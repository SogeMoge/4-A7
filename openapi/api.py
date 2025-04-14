from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from bot.mongo.search import find_pilot
from bot.mongo.init_db import reload_collections

mongodb_uri = (
    "mongodb://root:example@localhost:27017/xwingdata?authSource=admin"
)
data_root_dir = "submodules/xwing-data2/data"


class ReinitResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    error: str


app = FastAPI(
    title="X-Wing Data API", version="1.0.0", openapi_url="/openapi.json"
)


@app.post(
    "/reinit_db",
    response_model=ReinitResponse,
    responses={500: {"model": ErrorResponse}},  # Improved error handling
)
async def reinit_db():
    try:
        reload_collections(data_root_dir, mongodb_uri)
        pilot = find_pilot("firstordertestpilot", mongodb_uri)
        if pilot:
            print("Reinitialization successful. Test pilot found.")
        else:
            print(
                "Reinitialization successful, but Test pilot not found. Check your data."
            )
        return ReinitResponse(message="Database reinitialized successfully.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pilot/{xws}")
async def get_pilot(xws: str):
    try:
        pilot = find_pilot(xws, mongodb_uri)
        return pilot
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Pilot not found: {e}")
