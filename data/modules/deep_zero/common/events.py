# data/modules/deep_zero/common/events.py
# Kampagnen-Layer für Deep Zero: Globale Sci-Fi-Umgebungsereignisse
from __future__ import annotations

from engine.schema import EventData

COMMON_MATRIX: list[EventData] = [
    {
        "id": "evt_global_ambience",
        "trigger": "time",
        "trigger_time": 100,
        "title": "Subraum-Echo",
        "description": "Ein fernes Subraum-Echo lässt die Stationshülle von Deep Zero leicht vibrieren.",
    },
    {
        "id": "evt_core_glitch_stability",
        "trigger": "condition",
        "repeat": True,
        "condition": {
            "type": "all",
            "conditions": [
                {"type": "stability", "op": "<", "value": 50},
                {"type": "npc_state", "npc": "core_ai", "state": "online"},
            ],
        },
        "effects": [
            {"type": "set_npc_state", "npc": "core_ai", "value": "glitched"},
            {
                "type": "message",
                "log_type": "character",
                "message": "C.O.R.E. (Headset): '// WARNUNG: Interferenz erkannt. Telemetrie-Kanal schaltet auf Notfallpuffer.'",
            },
        ],
    },
    {
        "id": "evt_core_recover_stability",
        "trigger": "condition",
        "repeat": True,
        "condition": {
            "type": "all",
            "conditions": [
                {"type": "stability", "op": ">=", "value": 50},
                {"type": "npc_state", "npc": "core_ai", "state": "glitched"},
                {
                    "type": "any",
                    "conditions": [
                        {"type": "knowledge", "value": "ep3_reactor_crisis_active", "not": True},
                        {"type": "knowledge", "value": "core_stabilized"},
                    ],
                },
            ],
        },
        "effects": [
            {"type": "set_npc_state", "npc": "core_ai", "value": "online"},
            {
                "type": "message",
                "log_type": "character",
                "message": "C.O.R.E. (Headset): 'Signalträger stabilisiert. Reguläre Telemetrie wiederhergestellt.'",
            },
        ],
    },
]
