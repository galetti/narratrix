# narratrix_engine/data/chapters/ep0_test_lab/rooms.py
from __future__ import annotations

from engine.constants import ATTR_DESC, ATTR_ID, ATTR_NAME
from engine.schema import RoomData

ROOMS: dict[str, RoomData] = {
    "central_hub": {
        ATTR_ID: "central_hub",
        ATTR_NAME: "Zentrale Ebene",
        ATTR_DESC: (
            "Ein großer, runder Raum. In der Mitte steht das {central_terminal}. "
            "Eine Leiter führt nach {upper_deck} und eine Luke nach {lower_deck}."
        ),
        "img": "hub_main",
        "exits": {
            "up": "upper_deck",
            "down": "lower_deck",
            "north": "test_chamber",
        },
        "acoustics": {
            # Direkte akustische Verbindung nach oben (z.B. offenes Gitter)
            "upper_deck": 0.8,
        },
        "_editor": {"x": 0, "y": 0, "z": 0},
    },
    "upper_deck": {
        ATTR_ID: "upper_deck",
        ATTR_NAME: "Oberes Deck (Wartung)",
        ATTR_DESC: "Ein Laufsteg direkt über der Zentrale. Du kannst durch das Gitter nach unten sehen.",
        "img": "deck_upper",
        "exits": {
            "down": "central_hub",
        },
        "acoustics": {
            "central_hub": 0.8,
        },
        "_editor": {"x": 0, "y": 0, "z": 1},
    },
    "lower_deck": {
        ATTR_ID: "lower_deck",
        ATTR_NAME: "Unterdecks (Maschinenraum)",
        ATTR_DESC: "Es ist dunkel und eng hier. Rohre verlaufen an den Wänden.",
        "img": "deck_lower",
        "exits": {
            "up": "central_hub",
        },
        "_editor": {"x": 0, "y": 0, "z": -1},
    },
    "test_chamber": {
        ATTR_ID: "test_chamber",
        ATTR_NAME: "Testkammer",
        ATTR_DESC: (
            "Ein steriler Raum für physikalische Experimente. "
            "Nach Osten führt ein massives {security_door} zum Tresorbereich."
        ),
        "img": "lab_white",
        "exits": {
            "south": "central_hub",
            "east": "vault_room",
        },
        "_editor": {"x": 0, "y": -150, "z": 0},
    },
    "vault_room": {
        ATTR_ID: "vault_room",
        ATTR_NAME: "Akustik-Tresorraum",
        ATTR_DESC: (
            "Eine schallisolierte Kammer. In der Wand ist der {resonance_vault} eingelassen, "
            "daneben steht eine hochpräzise {precision_scale}."
        ),
        "exits": {
            "west": "test_chamber",
        },
        "_editor": {"x": 150, "y": -150, "z": 0},
    },
}
