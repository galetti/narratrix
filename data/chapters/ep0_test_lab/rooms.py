# narratrix_engine/data/chapters/ep0_test_lab/rooms.py
from engine.constants import *

ROOMS = {
    "central_hub": {
        ATTR_NAME: "Zentrale Ebene",
        ATTR_DESC: "Ein großer, runder Raum. In der Mitte steht ein Terminal. Eine Leiter führt nach {upper_deck} und eine Luke nach {lower_deck}.",
        "img": "hub_main",
        "exits": {
            "up": "upper_deck",
            "down": "lower_deck",
            "north": "test_chamber"
        },
        "acoustics": {
            # Direkte akustische Verbindung nach oben (z.B. offenes Gitter)
            "upper_deck": 0.8 
        },
        "_editor": {"x": 0, "y": 0, "z": 0}
    },
    "upper_deck": {
        ATTR_NAME: "Oberes Deck (Wartung)",
        ATTR_DESC: "Ein Laufsteg direkt über der Zentrale. Du kannst durch das Gitter nach unten sehen.",
        "img": "deck_upper",
        "exits": {
            "down": "central_hub"
        },
        "acoustics": {
            "central_hub": 0.8
        },
        "_editor": {"x": 0, "y": 0, "z": 1}
    },
    "lower_deck": {
        ATTR_NAME: "Unterdecks (Maschinenraum)",
        ATTR_DESC: "Es ist dunkel und eng hier. Rohre verlaufen an den Wänden.",
        "img": "deck_lower",
        "exits": {
            "up": "central_hub"
        },
        # Keine direkte akustische Verbindung außer durch den Exit definiert
        "_editor": {"x": 0, "y": 0, "z": -1}
    },
    "test_chamber": {
        ATTR_NAME: "Testkammer",
        ATTR_DESC: "Ein steriler Raum für Experimente.",
        "img": "lab_white",
        "exits": {
            "south": "central_hub"
        },
        "_editor": {"x": 0, "y": -150, "z": 0}
    }
}