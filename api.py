from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from bot.mongo.find_pilot import find_pilot
from bot.mongo.init_db import prepare_collections


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
    data_root_dir = "submodules/xwing-data2/data"
    try:
        prepare_collections(data_root_dir)
        pilot = find_pilot("blackout")
        if pilot:
            print("Reinitialization successful. Pilot Blackout found.")
        else:
            print(
                "Reinitialization successful, but pilot Blackout not found. Check your data."
            )
        return ReinitResponse(message="Database reinitialized successfully.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pilot/{xws}")
async def get_pilot(xws: str):
    try:
        pilot = find_pilot(xws)
        return pilot
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Pilot not found: {e}")
