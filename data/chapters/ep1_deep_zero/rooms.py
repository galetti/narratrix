# narratrix_engine/data/chapters/ep1_arrival/rooms.py
from engine.constants import *

ROOMS = {
    # 1. Hangar (Start)
    "room_outer_docking": {
        ATTR_ID: "room_outer_docking",
        ATTR_NAME: "Hangar Bay 4",
        # FIX: "nach Osten" statt "{east}"
        ATTR_DESC: "Die riesige Schleusenhalle riecht nach Ozon und kaltem Metall. Dein Shuttle, die 'Charon', steht angedockt hinter dir. Grüne Markierungen am Boden führen nach Osten zum 'Inner Ring'.",
        "exits": {
            "east": "room_inner_corridor_north"
        },
        "acoustics": {
            "room_inner_corridor_north": 0.5 
        }
    },

    # 2. Innerer Korridor
    "room_inner_corridor_north": {
        ATTR_ID: "room_inner_corridor_north",
        ATTR_NAME: "Innerer Ring (Nord)",
        ATTR_DESC: "Ein gebogener Korridor, der den Kern der Station umläuft. Leitungen hängen von der Decke.",
        "exits": {
            "west": "room_outer_docking",
            "east": "room_inner_greenhouse",
            "south": "room_inner_labs"
        },
        "acoustics": {
            "room_inner_greenhouse": 0.8, 
            "room_inner_labs": 0.4        
        }
    },

    # 3. Labore
    "room_inner_labs": {
        ATTR_ID: "room_inner_labs",
        ATTR_NAME: "Server-Labor",
        ATTR_DESC: "Reihen von schwarzen Monolithen summen leise vor sich hin. Die Luft ist staubtrocken und kühl.",
        "exits": {
            "north": "room_inner_corridor_north"
        }
    },

    # 4. Gewächshaus
    "room_inner_greenhouse": {
        ATTR_ID: "room_inner_greenhouse",
        ATTR_NAME: "Hydroponik Sektor",
        # FIX: "nach Osten" statt "{east}"
        ATTR_DESC: "Das UV-Licht brennt in den Augen. Reihen von Algen-Tanks blubbern hier. Ein Schott führt nach Osten zur Müllverarbeitung.",
        "exits": {
            "west": "room_inner_corridor_north",
            "east": "room_outer_waste"
        },
        "acoustics": {
            "room_outer_waste": {"transmission": 0.7, "direction_text": "hinter dem Schott"}
        }
    },

    # 5. Müllverarbeitung
    "room_outer_waste": {
        ATTR_ID: "room_outer_waste",
        ATTR_NAME: "Müllverarbeitung",
        ATTR_DESC: "Es stinkt nach verbranntem Plastik. In der Mitte steht eine Schrottpresse. An der Wand führt eine {ladder} zu einem offenen Wartungsschacht hoch.",
        "exits": {
            "west": "room_inner_greenhouse"
        },
        "climb_targets": {},
        "acoustics": {}
    }
}