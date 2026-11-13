# data/modules/deep_zero/chapters/ep3_reactor_core/events.py
from __future__ import annotations

from engine.schema import EventData, QuestDefinitionData

QUESTS: dict[str, QuestDefinitionData] = {
    "reactor_overdrive": {
        "title": "Kritische Resonanz",
        "desc": "Kühle den überhitzten Reaktorkern und stabilisiere das Magnetische Containment.",
        "stages": {
            0: "Melde dich bei Dr. Sato im Reaktor-Leitstand.",
            1: "Isolierhandschuhe im Leitstand und Kühlkanister aus dem Kühllager holen, dann auf Ebene 2 anschließen.",
            2: "Magnetfeld an der Steuerkonsole mit dem Omni-Tool kalibrieren.",
            3: "Station gerettet. Erstatte Dr. Sato Bericht.",
            4: "Abgeschlossen.",
        },
        "completion_stage": 4,
    },
}

NARRATIVE_MATRIX: list[EventData] = [
    {
        "id": "core_intro",
        "trigger": "time",
        "trigger_time": 0,
        "description": (
            "Die Panzerschleuse zum Reaktor-Sektor schwingt auf. Ein tiefes, pulsierendes "
            "Resonanzdröhnen vibriert durch die Gitterroste unter deinen Stiefeln."
        ),
        "effects": [
            {"type": "learn", "fact": "ep3_reactor_crisis_active"},
            {"type": "set_npc_state", "npc": "core_ai", "value": "glitched"},
            {
                "type": "message",
                "log_type": "character",
                "message": (
                    "C.O.R.E. (Headset): 'Kritische Warnung: Reaktortemperatur bei 140%. "
                    "Dr. Sato erwartet Sie im Reaktor-Leitstand östlich der Brücke.'"
                ),
            },
        ],
    },
]

EVENTS: list[EventData] = [
    {
        "id": "event_quest_start",
        "trigger": "manual",
        "quest_start": "reactor_overdrive",
        "effects": [
            {"type": "learn", "fact": "ep3_quest_started"},
            {"type": "set_npc_state", "npc": "sato", "value": "waiting"},
            {"type": "quest_update", "quest_update": {"id": "reactor_overdrive", "stage": 1}},
        ],
    },
    {
        "id": "reactor_hum_loop",
        "trigger": "time",
        "trigger_time": 0,
        "repeat": True,
        "origin_id": "reactor_chamber",
        "condition": {"type": "knowledge", "value": "core_stabilized", "not": True},
        "sound_msg": "Ein bedrohlich anschwellendes, tiefes Resonanzdröhnen aus der Reaktorkammer.",
        "volume": 2.2,
    },
    {
        "id": "event_core_cooled",
        "trigger": "manual",
        "effects": [
            {"type": "learn", "fact": "core_cooled"},
            {"type": "update_object", "target": "dark_matter_core", "updates": {"desc": "Der Dunkle-Materie-Kern ist auf sichere Betriebstemperatur abgekühlt."}},
            {"type": "quest_update", "quest_update": {"id": "reactor_overdrive", "stage": 2}},
            {"type": "message", "message": "Die Überhitzungswarnung erlischt! Das Containment-Magnetfeld muss nun an der Steuerkonsole kalibriert werden."},
        ],
    },
    {
        "id": "event_core_stabilized",
        "trigger": "manual",
        "effects": [
            {"type": "learn", "fact": "core_stabilized"},
            {"type": "set_npc_state", "npc": "sato", "value": "celebrating"},
            {"type": "quest_update", "quest_update": {"id": "reactor_overdrive", "stage": 3}},
            {"type": "message", "message": "Die Resonanzfrequenz schwingt ein. Der Kern pulsiert in vollkommener Stabilität!"},
        ],
    },
    {
        "id": "event_station_saved",
        "trigger": "manual",
        "effects": [
            {"type": "quest_complete", "id": "reactor_overdrive"},
            {"type": "message", "message": "Du nimmst den Generalschlüssel von Deep Zero entgegen. Die Station ist gerettet!"},
            {"type": "game_over", "reason": "KAMPAGNE ERFOLGREICH BEENDET - Deep Zero ist stabilisiert und bereit für neue Entdeckungen!"},
        ],
    },
]
