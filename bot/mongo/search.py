# Presumed location: bot/mongo/search.py

import logging
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os

# --- Get MongoDB URI ---
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://root:example@localhost:27017/xwingdata?authSource=admin",
)

logger = logging.getLogger(__name__)

# --- Create Persistent MongoDB Client and Collections ---
try:
    client = MongoClient(MONGODB_URI, server_api=ServerApi("1"))
    client.admin.command("ping")
    logger.info("Successfully connected to MongoDB.")
    xws_db = client["xwing-data2"]
    pilots_collection = xws_db["pilots"]
    upgrades_collection = xws_db["upgrades"]
    factions_collection = xws_db["factions"]
except Exception as e:
    logger.critical(
        f"FATAL: Failed to connect to MongoDB at {MONGODB_URI}: {e}",
        exc_info=True,
    )
    pilots_collection = upgrades_collection = factions_collection = (
        None  # Set to None on failure
    )


# --- Index Recommendation ---
# For optimal query performance, ensure MongoDB indexes are created on:
# - pilots collection: index on "pilots.xws"
# - upgrades collection: index on "xws"
# - factions collection: index on "xws"


def find_pilot(xws: str):
    """Finds a pilot's data within the nested structure using its xws name."""
    # --- FIX: Use 'is None' for collection check ---
    if pilots_collection is None:
        logger.error("MongoDB pilots_collection not available.")
        return None
    try:
        doc = pilots_collection.find_one(
            {"pilots.xws": xws}, {"pilots.$": 1, "_id": 0}
        )
        if doc and "pilots" in doc and doc["pilots"]:
            return doc["pilots"][0]
        else:
            logger.warning(f"Pilot with xws '{xws}' not found in database.")
            return None
    except Exception as e:
        logger.error(f"Error querying pilot '{xws}': {e}", exc_info=True)
        return None


def find_upgrade(xws: str):
    """Finds an upgrade by its xws name using the global connection."""
    # --- FIX: Use 'is None' for collection check ---
    if upgrades_collection is None:
        logger.error("MongoDB upgrades_collection not available.")
        return None
    try:
        upgrade_data = upgrades_collection.find_one({"xws": xws}, {"_id": 0})
        if not upgrade_data:
            logger.warning(f"Upgrade with xws '{xws}' not found in database.")
        return upgrade_data
    except Exception as e:
        logger.error(f"Error querying upgrade '{xws}': {e}", exc_info=True)
        return None


def find_ship_by_pilot(xws: str):
    """
    Finds the ship data (parent document) associated with a pilot
    using the pilot's xws name and the global connection.
    """
    # --- FIX: Use 'is None' for collection check ---
    if pilots_collection is None:  # Check the correct collection variable
        logger.error("MongoDB pilots_collection not available.")
        return None
    try:
        ship_data = pilots_collection.find_one({"pilots.xws": xws}, {"_id": 0})
        if not ship_data:
            logger.warning(
                f"Ship data for pilot xws '{xws}' not found (pilot document missing)."
            )
        return ship_data
    except Exception as e:
        logger.error(
            f"Error querying ship for pilot '{xws}': {e}", exc_info=True
        )
        return None


def find_faction(xws: str):
    """Finds a faction by its xws name using the global connection."""
    # --- FIX: Use 'is None' for collection check ---
    if factions_collection is None:
        logger.error("MongoDB factions_collection not available.")
        return None
    try:
        faction_data = factions_collection.find_one({"xws": xws}, {"_id": 0})
        if not faction_data:
            logger.warning(f"Faction with xws '{xws}' not found in database.")
        return faction_data
    except Exception as e:
        logger.error(f"Error querying faction '{xws}': {e}", exc_info=True)
        return None


# Optional: Add a function to close the client connection gracefully on shutdown
# def close_db_connection():
#     if client:
#         client.close()
#         logger.info("MongoDB connection closed.")
