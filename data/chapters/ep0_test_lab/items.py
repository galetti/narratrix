# narratrix_engine/data/chapters/ep0_test_lab/items.py
from engine.constants import *

ITEMS = {
    "red_key": {
        ATTR_ID: "red_key",
        ATTR_NAME: "roter Schlüssel",
        ATTR_DESC: "Ein kleiner Schlüssel mit rotem Griff.",
        ATTR_ALIASES: ["schlüssel", "rot", "key"],
        "location": "test_chamber",
        "type": TYPE_ITEM,
        ATTR_WEIGHT: 1
    },
    "blue_key": {
        ATTR_ID: "blue_key",
        ATTR_NAME: "blauer Schlüssel",
        ATTR_DESC: "Ein schwerer Schlüssel aus blauem Metall.",
        ATTR_ALIASES: ["schlüssel", "blau", "key"],
        "location": "test_chamber",
        "type": TYPE_ITEM,
        ATTR_WEIGHT: 1
    },
    "noisy_machine": {
        ATTR_ID: "noisy_machine",
        ATTR_NAME: "Lärmmaschine",
        ATTR_DESC: "Eine Maschine, die Krach macht.",
        "location": "lower_deck",
        "type": TYPE_FIXTURE,
        "state": "off"
    }
}

COMBINATIONS = []