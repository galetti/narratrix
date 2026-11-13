# data/modules/deep_zero/chapters/ep2_habitat_sector/events.py
from __future__ import annotations

from engine.schema import EventData, QuestDefinitionData

QUESTS: dict[str, QuestDefinitionData] = {
    "biosphere_pressure": {
        "title": "Kritischer Druckabfall",
        "desc": "Stabilisiere das Überdruckventil und versiegele die Dampfleitung in der Biosphäre.",
        "stages": {
            0: "Dr. Elena Vance braucht dringend Hilfe in der Biosphäre.",
            1: "Die Reparatur auf Ebene 1 läuft. Ventil und Dampfleitung müssen versorgt werden.",
            2: "Die Lebenshaltung ist gerettet. Erstatte Dr. Vance Bericht.",
            3: "Abgeschlossen.",
        },
        "completion_stage": 3,
    },
}

NARRATIVE_MATRIX: list[EventData] = [
    {
        "id": "habitat_intro",
        "trigger": "time",
        "trigger_time": 0,
        "description": (
            "Das Schott schließt sich hinter dir. Du stehst in der Habitat-Schleuse von Deep Zero. "
            "Die Luft riecht hier süßlicher nach feuchter Erde und Algenkulturen."
        ),
        "effects": [
            {
                "type": "message",
                "log_type": "character",
                "message": (
                    "C.O.R.E. (Headset): 'Dr. Thorne, Ihr persönliches Quartier 4B ist freigeschaltet. "
                    "Achtung: Im Biosphären-Trakt liegt eine Überdruckwarnung der Stufe 2 vor.'"
                ),
            },
        ],
    },
]

EVENTS: list[EventData] = [
    {
        "id": "event_quest_start",
        "trigger": "manual",
        "quest_start": "biosphere_pressure",
        "effects": [
            {"type": "learn", "fact": "ep2_quest_started"},
            {"type": "set_npc_state", "npc": "dr_vance", "value": "waiting"},
        ],
    },
    {
        "id": "steam_hiss_loop",
        "trigger": "time",
        "trigger_time": 0,
        "repeat": True,
        "origin_id": "hydroponics_bay",
        "condition": {"type": "knowledge", "value": "steam_fixed", "not": True},
        "sound_msg": "Ein schrilles Pfeifen und Zischen von entweichendem Heißdampf.",
        "volume": 1.8,
    },
    {
        "id": "event_valve_calibrated",
        "trigger": "manual",
        "effects": [
            {"type": "learn", "fact": "valve_calibrated"},
            {"type": "update_object", "target": "pressure_valve", "updates": {"desc": "Das Ventil ist freigängig und der Stellmotor sauber kalibriert."}},
            {"type": "quest_update", "quest_update": {"id": "biosphere_pressure", "stage": 1}},
            {"type": "message", "message": "Der Überdruck im Rohrsystem fällt ab. Das Ventil arbeitet wieder vorschriftsmäßig."},
        ],
    },
    {
        "id": "event_steam_sealed",
        "trigger": "manual",
        "effects": [
            {"type": "learn", "fact": "steam_fixed"},
            {"type": "update_object", "target": "steam_pipe", "updates": {"desc": "Die Dampfleitung ist mit dem hitzefesten Nanopolymer-Band nahtlos abgedichtet."}},
            {"type": "set_npc_state", "npc": "dr_vance", "value": "relieved"},
            {"type": "quest_update", "quest_update": {"id": "biosphere_pressure", "stage": 2}},
            {"type": "message", "message": "Das Leck ist vollständig versiegelt. Endlich kehrt Ruhe im Biosphären-Trakt ein."},
        ],
    },
    {
        "id": "event_chapter_end",
        "trigger": "manual",
        "effects": [
            {"type": "quest_complete", "id": "biosphere_pressure"},
            {"type": "message", "message": "Du nimmst den Reaktorkern-Zugangschip entgegen und eilst weiter zum Reaktor-Sektor."},
            {
                "type": "load_chapter",
                "chapter": "data.modules.deep_zero.chapters.ep3_reactor_core.config",
            },
        ],
    },
]
