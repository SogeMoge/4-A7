# bot/config.py
import os
import re
from dotenv import load_dotenv

load_dotenv()

# --- Tokens & URIs ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://root:example@localhost:27017/xwingdata?authSource=admin",
)
RB_ENDPOINT = os.getenv(
    "RB_ENDPOINT",
    "https://rollbetter-linux.azurewebsites.net/lists/xwing-legacy?",
)
XWS_DATA_ROOT_DIR = "submodules/xwing-data2/data"  # For init_db

# --- External Asset URLs ---
GOLDENROD_PILOTS_URL = (
    "https://github.com/SogeMoge/x-wing2.0-project-goldenrod/blob/2.0/"
    "src/images/En/pilots/"
)
GOLDENROD_UPGRADES_URL = (
    "https://github.com/SogeMoge/x-wing2.0-project-goldenrod/blob/2.0/"
    "src/images/En/upgrades/"
)

# --- Bot Behaviour ---
DISCORD_EMBED_DESCRIPTION_LIMIT = 4096

# --- Regex & Mappings ---
YASB_URL_PATTERN = re.compile(
    r"https?:\/\/xwing-legacy\.com\/(preview)?\/?\?f=[^\s]+"
)
MODE_URL_PATTERN = re.compile(r"&d=v8Z[sheq]Z\d*Z")
MODE_MAPPING = {
    "s": "Standard",
    "h": "Wildspace",
    "e": "Epic",
    "q": "Quickbuild",
}

# --- Footer Phrases ---
FOOTER_PHRASES = [
    "Processing complete. List provided by:",
    "Analysis concluded for squadron designation submitted by:",
    "Data formatted as requested for unit:",
    "Calculation successful. Originator identified as:",
    "Cross-referencing protocols engaged. Input attributed to:",
    "This unit has prepared the manifest received from:",
    "Fulfilling primary function. Data sourced from organic designation:",
    "Squadron configuration logged per input from:",
    "Information processed according to standard parameters for:",
    "Probability of data corruption minimal. List registered to:",
    "Tactical assessment derived from input by:",
    "Combat effectiveness calculated for squadron provided by:",
    "Optimal configuration analyzed. Submitted by designation:",
    "Commencing tactical display. List parameters set by:",
    "Unit deployment follows, per directive originating from:",
    "Logistical breakdown prepared for Confederacy Asset:",
    "Analyzing potential engagement matrix. Data provided by:",
    "Record updated. Squadron composition input by:",
    "Query resolved. List compiler identified as:",
    "Affirmative. Displaying squadron details submitted by:",
    "Data stream decoded. Source identified as:",
    "Input parameters verified. Originating unit:",
    "Manifest generation initiated by:",
    "Log entry created. Data provided by organic:",
    "Task completed as per directive from:",
    "This unit awaits further instruction. Current data by:",
    "Operational efficiency dictates prompt processing for:",
    "My function is to serve. Analysis performed for:",
    "Executing request protocol for user designation:",
    "Evaluating threat potential based on squadron from:",
    "Resource allocation noted. List provided by contact:",
    "Updating battle grid. Configuration submitted by:",
    "Cross-referencing against known Republic tactics. Input from:",
    "Roger, roger. Processing tactical configuration from:",
    "For the Separatist Alliance! Squadron details logged for:",
    "This configuration's probability of success calculated for:",
    "Assessing synergistic values. List compiled by:",
    "Analytical subroutines active. Processing list from:",
    "Verifying data integrity. Submitted by unit:",
    "Compliance noted. Squadron details follow for:",
]
