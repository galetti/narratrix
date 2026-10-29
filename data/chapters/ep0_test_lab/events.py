# narratrix_engine/data/chapters/ep0_test_lab/events.py
from __future__ import annotations

from engine.schema import EventData, QuestDefinitionData

QUESTS: dict[str, QuestDefinitionData] = {
    "core_calibration": {
        "title": "Operation Resonanz-Kern",
        "desc": "Birg den Resonanz-Kern aus dem Akustik-Tresorraum, repariere ihn und setze ihn im Zentral-Terminal ein.",
        "stages": {
            0: "Verschaffe dir Zugang zum Tresorraum östlich der Testkammer und öffne den Gefahrgut-Spind.",
            1: "Das Eichgewicht (1.50 kg) ist aufgetaut. Finde den Frequenz-Code der Wartungsdrohne und kalibriere die Präzisionswaage auf exakt 2.50 kg.",
            2: "Du kennst die Resonanz-Frequenz. Kalibriere die Präzisionswaage im Tresorraum auf exakt 2.50 kg, um den Tresor zu öffnen.",
            3: "Der Resonanz-Kern ist geborgen! Repariere ihn mit einem Werkzeug und setze ihn in das Zentral-Terminal ein.",
            4: "Der Resonanz-Kern läuft stabil. Testlabor-Protokoll erfolgreich abgeschlossen!",
        },
        "completion_stage": 4,
    }
}

NARRATIVE_MATRIX: list[EventData] = [
    {
        "id": "intro_test_lab",
        "trigger": "time",
        "trigger_time": 0,
        "description": (
            "Willkommen im Testlabor (Episode 0). Das Zentral-Terminal meldet: "
            "'Resonanz-Kern fehlt. Bitte aus dem Akustik-Tresorraum bergen, kalibrieren und einsetzen.'"
        ),
        "quest_start": "core_calibration",
    }
]

EVENTS: list[EventData] = [
    # 1. Maschinenlärm: Feuert nur noch, wenn die Lärmmaschine im Unterdeck eingeschaltet ist!
    {
        "id": "machine_noise",
        "trigger": "time",
        "trigger_time": 0,
        "repeat": True,
        "origin_id": "lower_deck",
        "condition": {
            "type": "object_state",
            "item": "noisy_machine",
            "state": "on",
        },
        "sound_msg": "Ein tiefes, dröhnendes Wummern der Lärmmaschine.",
        "volume": 1.5,
    },
    # 2. Subtiles Summen aus dem Tresorraum (demonstriert Dämpfung durch geschlossenes Schott + Akustik-Stethoskop)
    {
        "id": "vault_hum",
        "trigger": "time",
        "trigger_time": 0,
        "repeat": True,
        "origin_id": "vault_room",
        "condition": {
            "type": "knowledge",
            "value": "vault_opened",
            "not": True,
        },
        "sound_msg": "Ein hochfrequentes Pulsieren hinter dem Tresor-Schott.",
        "volume": 0.4,
    },
    # 3. Kryo-Kapsel im Schmelzofen geschmolzen
    {
        "id": "capsule_melted",
        "trigger": "manual",
        "effects": [
            {"type": "learn", "fact": "weight_recovered"},
            {
                "type": "quest_update",
                "quest_update": {"id": "core_calibration", "stage": 1},
            },
        ],
    },
    # 4. Präzisionswaage erreicht exakt 2.50 kg -> Tresor entriegelt sich automatisch!
    {
        "id": "vault_unlocked",
        "trigger": "condition",
        "condition": {
            "type": "scale_weight",
            "item": "precision_scale",
            "value": 2.5,
        },
        "effects": [
            {"type": "learn", "fact": "vault_opened"},
            {
                "type": "update_object",
                "target": "resonance_vault",
                "updates": {"is_locked": False, "is_open": True},
            },
            {
                "type": "spawn_item",
                "item": "resonance_core",
                "location": "vault_room",
            },
            {
                "type": "quest_update",
                "quest_update": {"id": "core_calibration", "stage": 3},
            },
            {
                "type": "message",
                "log_type": "success",
                "message": (
                    "KLICK-ZISCH! Die Präzisionswaage zeigt exakt 2.50 kg an. "
                    "Der Resonanz-Tresor springt auf und gibt den beschädigten Resonanz-Kern frei!"
                ),
            },
        ],
    },
    # 5. Abschluss des mehrstufigen Rätsels
    {
        "id": "protocol_complete",
        "trigger": "manual",
        "effects": [
            {"type": "learn", "fact": "lab_stabilized"},
            {"type": "quest_complete", "id": "core_calibration"},
            {
                "type": "message",
                "log_type": "success",
                "message": (
                    "Das Zentral-Terminal fährt mit einem harmonischen Summen hoch. "
                    "Alle Systeme des Testlabors sind kalibriert!"
                ),
            },
        ],
    },
]
