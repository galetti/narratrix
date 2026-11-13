# data/modules/deep_zero/chapters/ep3_reactor_core/rooms.py
from __future__ import annotations

from engine.constants import ATTR_DESC, ATTR_ID, ATTR_NAME
from engine.schema import RoomData

ROOMS: dict[str, RoomData] = {
    "reactor_bridge": {
        ATTR_ID: "reactor_bridge",
        ATTR_NAME: "Reaktor-Zugangsbrücke",
        ATTR_DESC: (
            "Ein schmaler Gittersteg überspannt die dunkle Kluft des inneren Rings. "
            "Nach Osten führt der Weg in den {control_room}. Nach Norden liegt das {coolant_depot}, "
            "gesichert durch ein schweres {security_gate}. Nach Süden führt das {radiation_blast_door} "
            "direkt in die Herzkammer des Reaktors."
        ),
        "exits": {
            "east": "control_room",
            "north": "coolant_depot",
            "south": "reactor_chamber",
        },
        "acoustics": {
            "control_room": 0.7,
            "coolant_depot": 0.5,
            "reactor_chamber": {"transmission": 0.4, "direction_text": "hinter dem Strahlenschutz-Schott"},
        },
    },
    "control_room": {
        ATTR_ID: "control_room",
        ATTR_NAME: "Reaktor-Leitstand",
        ATTR_DESC: (
            "Pulte voller flackernder Warnleuchten und holografischer Statusdiagramme. "
            "In der Mitte dominiert die {control_console} zur Stabilisierung des Magnetfelds. "
            "An der Wand steht ein {storage_locker}. Durch ein dickes Bleiglasfenster blickst du auf die Reaktorkammer. "
            "Nach Westen führt der Ausgang zurück zur Brücke."
        ),
        "exits": {
            "west": "reactor_bridge",
        },
        "acoustics": {
            "reactor_bridge": 0.7,
        },
    },
    "coolant_depot": {
        ATTR_ID: "coolant_depot",
        ATTR_NAME: "Kryo-Kühllager",
        ATTR_DESC: (
            "Eisiger weißer Reif bedeckt die Metallwände dieses Hochsicherheitslagers. "
            "Ein mechanischer {crane} hängt über den Kühlmittelbehältern. "
            "Auf einer gummierten Ladefläche steht ein tragbarer {cryo_canister}. "
            "Nach Süden führt der Ausgang zurück zur Zugangsbrücke."
        ),
        "exits": {
            "south": "reactor_bridge",
        },
        "acoustics": {
            "reactor_bridge": 0.5,
        },
    },
    "reactor_chamber": {
        ATTR_ID: "reactor_chamber",
        ATTR_NAME: "Reaktorkammer (Containment)",
        ATTR_DESC: (
            "Die gigantische Herzkammer von Deep Zero. In der Mitte schwebt der {dark_matter_core}, "
            "umgeben von violett pulsierenden Energiebögen und Hitzeflimmern. "
            "Eine massive {coolant_gantry_ladder} führt hinauf zur Injektorbühne auf Ebene 2, "
            "wo der {coolant_manifold} für das Notkühlsystem angebracht ist. "
            "Am Boden summt der {containment_generator}. Nach Norden führt das Strahlenschutz-Schott zurück zur Brücke."
        ),
        "exits": {
            "north": "reactor_bridge",
        },
        "acoustics": {
            "reactor_bridge": {"transmission": 0.4, "direction_text": "aus dem Reaktorkern"},
        },
    },
}
