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

WELCOME_GIFS = [
    "https://tenor.com/view/the-book-of-boba-fett-slave1-firespray-boba-fett-ship-firing-gif-24574050",
    "https://tenor.com/view/teehee-gif-23758487",
    "https://tenor.com/view/star-wars-opening-scene-star-wars-opening-scene-tantive-iv-star-destroyer-gif-3315182254245272060",
    "https://tenor.com/view/battle-of-endor-gif-9693422465872747809",
    "https://tenor.com/view/star-wars-rebels-space-battle-star-wars-battle-atollon-battle-of-atollon-gif-23976475",
    "https://tenor.com/view/rebellions-are-built-on-hope-jyn-erso-felicity-jones-star-wars-rogue-one-gif-26233408",
    "https://tenor.com/view/baby-yoda-the-mandalorian-star-wars-cute-hi-gif-16737494",
    "https://tenor.com/view/bossk-star-wars-empire-strikes-back-bounty-hunter-scum-gif-12841322",
    "https://tenor.com/view/star-wars-corridor-death-star-gif-17480766",
    "https://tenor.com/view/x-wing-poe-dameron-resistance-star-wars-the-force-awakens-gif-18784380",
    "https://tenor.com/view/the-millennium-falcon-planet-jakku-star-wars-episode-vii-the-force-awakens-2015-sci-fi-film-han-solo-gif-17956956054864084627",
    "https://tenor.com/view/star-wars-rogue-one-star-destroyer-devastator-gif-21042471",
    "https://tenor.com/view/firing-attack-shot-shooting-star-destroyer-gif-9394419841825674730",
    "https://tenor.com/view/andor-laser-spin-cantwell-cruiser-imperial-gif-27101696",
    "https://tenor.com/view/itano-circus-tie-fighter-pilot-anime-cockpit-gif-24987125",
    "https://tenor.com/view/mandalorian-razorcrest-star-wars-gif-19310589",
    "https://tenor.com/view/rogue-one-battle-of-scarif-scarif-star-wars-gif-19761980",
    "https://tenor.com/view/star-wars-celebration-bespin-gif-15492932804125968948",
    "https://tenor.com/view/star-wars-gif-22096470",
    "https://tenor.com/view/star-wars-x-wing-rebel-alliance-rebellion-rogue-one-gif-17098723",
    "https://tenor.com/view/star-wars-poe-dameron-you-need-a-pilot-pilot-oscar-isaac-gif-27051289",
    "https://tenor.com/view/the-mandalorian-the-mando-mando-star-wars-razor-crest-gif-15689506",
    "https://tenor.com/view/star-wars-tie-fighter-tie-fighters-the-rise-of-skywalker-first-order-gif-21441670",
    "https://tenor.com/view/itano-circus-tie-fighter-pilot-anime-cockpit-gif-24987125",
    "https://tenor.com/view/seismic-charge-the-mandalorian-star-wars-the-believer-boba-fett-gif-19531689",
    "https://tenor.com/view/purge-purge-mandalore-mandalore-purge-star-wars-mandalorian-gif-3740060489136577632",
    "https://tenor.com/view/star-wars-battle-gif-17469101",
    "https://tenor.com/view/star-wars-clone-wars-spaceships-gif-16294755",
    "https://tenor.com/view/slave1takeoff-mando-slave1-mandalorian-slave1-mando-slave1takeoff-mandalorian-slave1takeoff-gif-19535452",
    "https://tenor.com/view/y-wing-bomber-republicbomber-clone-wars-grand-army-of-the-republic-republic-gif-23771349",
    "https://tenor.com/view/star-wars-gif-22561568",
    "https://tenor.com/view/star-wars-star-wars-squadrons-x-wing-tie-fighter-chase-gif-17576758",
]

THE_WAY_GIFS = [
    "https://tenor.com/view/the-mandalorian-bo-katan-kryze-this-is-the-way-mandalorian-katee-sackhoff-gif-15366759469985897837",
    "https://tenor.com/view/game-of-thrones-tormund-giantsbane-this-is-the-way-gif-6920601626819058768",
    "https://tenor.com/view/the-mandalorian-this-is-the-way-the-way-mandalorian-star-wars-gif-18999449",
    "https://tenor.com/view/star-wars-the-mandalorian-this-is-the-way-din-djarin-gif-15916889",
    "https://tenor.com/view/bo-katan-this-is-the-way-the-mandalorian-star-wars-katee-sackhoff-gif-19179876",
    "https://tenor.com/view/this-is-the-way-din-djarin-the-mandalorian-the-only-way-no-other-choice-gif-22927061",
    "https://tenor.com/view/star-wars-the-mandalorian-this-is-the-way-the-armorer-gif-15639793",
    "https://tenor.com/view/this-is-the-way-mandalorian-star-wars-gif-19631947",
    "https://tenor.com/view/dis-is-da-wae-this-is-da-wae-this-is-the-way-da-wae-ugandan-knuckles-gif-25797533",
    "https://tenor.com/view/mandalorian-this-is-the-way-gif-24826742",
    "https://tenor.com/view/the-book-of-boba-fett-this-is-the-way-the-armorer-mandalorian-gif-25545276",
]
