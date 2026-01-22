# narratrix_engine/data/chapters/ep1_deep_zero/rooms.py
from engine.constants import *

ROOMS = {
    "room_quarters_aris": {
        ATTR_ID: "room_quarters_aris",
        ATTR_NAME: "Aris' Quartier",
        # Fix: Uhrzeit entfernt, da sie statisch wäre.
        ATTR_DESC: "Der Wecker hat aufgehört zu summen. Ein weiterer Tag in der Leere. Die {ventilation} über dir gibt ein unregelmäßiges, nerviges Klappern von sich. Neben dem Bett liegt das {tablet}.",
        "exits": {
            "out": "room_corridor_quarters",
            "east": "room_corridor_quarters"
        },
        "acoustics": {
            "room_corridor_quarters": {"transmission": 0.3, "direction_text": "gedämpft vom Gang"}
        }
    },
    "room_corridor_quarters": {
        ATTR_ID: "room_corridor_quarters",
        ATTR_NAME: "Wohnkorridor",
        ATTR_DESC: "Ein schmaler Gang mit grauen Panelen. Hier liegen die Quartiere der Crew.",
        "exits": {
            "west": "room_quarters_aris",
            "east": "room_quarters_sato",
            "north": "room_mess"
        },
        "acoustics": {
            "room_quarters_aris": 0.3,
            "room_quarters_sato": 0.2
        }
    },
    "room_quarters_sato": {
        ATTR_ID: "room_quarters_sato",
        ATTR_NAME: "Satos Quartier",
        ATTR_DESC: "Verschlossen. Sato mag seine Privatsphäre.",
        "exits": {
            "west": "room_corridor_quarters"
        },
        "acoustics": {
            "room_corridor_quarters": 0.2
        }
    },
    "room_mess": {
        ATTR_ID: "room_mess",
        ATTR_NAME: "Die Messe",
        ATTR_DESC: "Der soziale Mittelpunkt der Station. Es riecht normalerweise nach Kaffee, heute eher nach verbranntem Plastik. In der Ecke steht ein Kühlschrank, der leise summt.",
        "exits": {
            "south": "room_corridor_quarters",
            "north": "room_corridor_main"
        }
    },
    "room_corridor_main": {
        ATTR_ID: "room_corridor_main",
        ATTR_NAME: "Hauptkorridor (Wartung)",
        ATTR_DESC: "Der Gang ist hier etwa 4 Meter hoch und voller offener Leitungen an der Decke. Ein {emitter_relay} hängt weit oben an der Decke (Ebene 2) und blinkt rot.",
        "exits": {
            "south": "room_mess",
            "east": "room_lab",
            "west": "room_control"
        },
        "climb_targets": {}, 
        "acoustics": {
            "room_control": 0.5
        }
    },
    "room_lab": {
        ATTR_ID: "room_lab",
        ATTR_NAME: "Forschungslabor",
        ATTR_DESC: "Regale voller Gesteinsproben und Terminals. Ein Schachbrett steht auf einem Tisch.",
        "exits": {
            "west": "room_corridor_main"
        }
    },
    "room_control": {
        ATTR_ID: "room_control",
        ATTR_NAME: "Kontrollraum",
        ATTR_DESC: "Das Herz der Station. Monitore zeigen endlose Sternenfelder und Statusberichte.",
        "exits": {
            "east": "room_corridor_main"
        },
        "acoustics": {
            "exterior_hull": {"transmission": 0.9, "direction_text": "von der Außenhülle"}
        }
    },
    "exterior_hull": {
        ATTR_ID: "exterior_hull",
        ATTR_NAME: "Außenhülle",
        ATTR_DESC: "Das kalte Vakuum.",
        "exits": {},
        "acoustics": {
            "room_control": 0.1
        }
    }
}