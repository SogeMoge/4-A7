"""Variables for xws_dict conversion to pretty format."""


def convert_xws(string):
    """Convert xws faction name to readable format."""
    mapping = {
        'rebelalliance': 'Rebel Alliance',
        'rebels': 'Rebel Alliance',
        'rebel': 'Rebel Alliance',
        'galacticempire': 'Galactic Empire',
        'imperial': 'Galactic Empire',
        'scumandvillainy': 'Scum and Villainy',
        'firstorder': 'First Order',
        'resistance': 'Resistance',
        'galacticrepublic': 'Galactic Republic',
        'separatistalliance': 'Separatist Alliance'
    }
    return mapping.get(string.lower(), string)

# exportObj.fromXWSUpgrade =
#     'amd': 'Astromech'
#     'astromechdroid': 'Astromech'
#     'ept': 'Talent'
#     'elitepilottalent': 'Talent'
#     'system': 'Sensor'
#     'mod': 'Modification'
#     'force-power':'Force'
#     'tactical-relay':'Tactical Relay'