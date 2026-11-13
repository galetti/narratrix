# data/modules/test_lab/chapters/sandbox/events.py
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
    },
    "investigate_sabotage": {
        "title": "Abgekartetes Spiel",
        "desc": "Im abhörsicheren Besprechungstrakt planen zwei Gestalten etwas Finsteres. Finde einen Weg, ihr Gespräch zu belauschen.",
        "stages": {
            0: "Verschaffe dir Zugang zum Vorraum des Besprechungstrakts und finde einen Weg, die Schallschutztür offen zu halten.",
            1: "Die Schallschutztür ist verkeilt! Nutze ein akustisches Verstärkerglas an der verschlossenen Vorraum-Tür, um das Gespräch zu belauschen.",
            2: "Du hast die Sabotagepläne aufgedeckt und weißt nun über den geplanten Anschlag auf den Reaktor Bescheid!",
        },
        "completion_stage": 2,
    },
}

NARRATIVE_MATRIX: list[EventData] = [
    {
        "id": "intro_test_lab",
        "trigger": "time",
        "trigger_time": 0,
        "description": (
            "=== SYSTEM-TESTGELÄNDE (SANDBOX) ===\n"
            "Willkommen in der modularen Narratrix-Testumgebung zur Demonstration von Spielmechaniken:\n"
            "• [NORDEN] Physikrätsel: Aggregatzustände & Wiegetest (verzweigt zum Tresor)\n"
            "• [WESTEN] Physikrätsel: Akustikdämpfung & Belauschen (verzweigt zur Schallschutzkammer)\n"
            "• [OSTEN] Gesprächslabor: Dialogbäume & Wissensprüfungen\n"
            "• [OBEN] Kletterparcours: Höhenebenen & Drohnen-KI\n"
            "• [UNTEN] Maschinendeck: Lärmsimulation & Werkbank-Crafting\n"
            "Sieh dir die Sektorschilder an oder nutze das Zentral-Terminal, um die Testabläufe zu starten."
        ),
        "quest_start": "core_calibration",
    },
    {
        "id": "enter_anteroom",
        "trigger": "location",
        "location": "briefing_anteroom",
        "quest_start": "investigate_sabotage",
        "description": "Als du den Sicherheits-Vorraum betrittst, siehst du durch die dicke Glasscheibe der Schallschutztür Chefingenieur Vance und Techniker Ray hastig über einem Bauplan gestikulieren.",
    },
]

EVENTS: list[EventData] = [
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
    {
        "id": "sabotage_discussion",
        "trigger": "time",
        "trigger_time": 0,
        "repeat": True,
        "origin_id": "soundproof_office",
        "condition": {
            "type": "object_state",
            "item": "soundproof_door",
            "is_open": True,
        },
        "sound_msg": "Die Sabotage ist beschlossene Sache. Sobald die Schicht wechselt, kappen wir die Energiekopplung des Reaktors und legen die Station lahm!",
        "muffled_msg": "Gedämpfte Stimmen und unklares Gemurmel hinter der Vorraum-Tür.",
        "volume": 1.0,
        "listen_effects": [
            {"type": "learn", "fact": "sabotage_plan_uncovered"},
            {
                "type": "quest_update",
                "quest_update": {"id": "investigate_sabotage", "stage": 2},
            },
            {"type": "quest_complete", "id": "investigate_sabotage"},
        ],
    },
]
