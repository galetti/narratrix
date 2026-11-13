# data/modules/deep_zero/common/npcs.py
from __future__ import annotations

from engine.constants import ATTR_ALIASES, ATTR_DESC, ATTR_NAME, LOC_VOID
from engine.schema import NPCData

COMMON_NPCS: list[NPCData] = [
    {
        "id": "core_ai",
        ATTR_NAME: "C.O.R.E.",
        ATTR_DESC: (
            "Die zentrale Stations-KI von Deep Zero. Sie kommuniziert direkt über "
            "dein Neural-Headset und überwacht Telemetrie, Lebenserhaltung und Reaktorsicherheit."
        ),
        ATTR_ALIASES: [
            "core",
            "c.o.r.e",
            "c.o.r.e.",
            "ki",
            "ai",
            "headset",
            "computer",
            "stations-ki",
            "system",
        ],
        "location": LOC_VOID,
        "remote_comms": True,
        "level": 0,
        "initial_state": "online",
        "state": "online",
        "behavior_id": "idle",
        "img": "face_ai_calm",
        "personality": (
            "Calm, analytical, slightly dry-witted central onboard computer and telemetry interface of Deep Zero. "
            "Speaks concisely like a crisp station operations officer, genuinely invested in Dr. Thorne's survival, "
            "and strictly grounded in real sensor readings."
        ),
        "states": {
            "online": {
                "visuals": {
                    "img": "face_ai_calm",
                    "desc": (
                        "Die zentrale Stations-KI von Deep Zero. Sie kommuniziert direkt über "
                        "dein Neural-Headset und überwacht Telemetrie, Lebenserhaltung und Reaktorsicherheit."
                    ),
                    "personality": (
                        "Calm, analytical, slightly dry-witted central onboard computer and telemetry interface of Deep Zero. "
                        "Speaks concisely like a crisp station operations officer, genuinely invested in Dr. Thorne's survival, "
                        "and strictly grounded in real sensor readings."
                    ),
                },
                "dialogue": {
                    "greeting": "C.O.R.E. online. Alle Telemetrie-Kanäle zu Ihrem Headset sind aktiv, Dr. Thorne.",
                    "status": {
                        "label": "Stationsstatus abfragen",
                        "text": (
                            "Außenhülle stabil. Primäre Diagnosepunkte: Akustische Störung im äußeren Ring, "
                            "Drucküberwachung im Habitat-Sektor und thermische Reserven im Reaktorkern."
                        ),
                    },
                    "mission": {
                        "label": "Aktuelle Prioritäten",
                        "text": (
                            "Koordinieren Sie sich mit den leitenden Ingenieuren vor Ort: Dr. Sato im Inneren Ring "
                            "sowie Dr. Elena Vance im Biosphären-Trakt."
                        ),
                    },
                    "default": "Ich empfange Ihre Anfrage über das Headset, Dr. Thorne. Formulieren Sie Ihr Anliegen präzise.",
                },
            },
            "glitched": {
                "visuals": {
                    "img": "face_ai_glitch",
                    "desc": (
                        "Die zentrale Stations-KI von Deep Zero. Ihr Übertragungsbild flackert stark unter "
                        "elektromagnetischen Interferenzen und kritischen Telemetrie-Warnungen."
                    ),
                    "personality": (
                        "Overloaded, slightly fragmented yet urgent central onboard computer and telemetry interface of Deep Zero "
                        "under electromagnetic interference. Shows brief static glitches while staying focused on Dr. Thorne's survival "
                        "and reporting only verified sensor facts."
                    ),
                },
                "dialogue": {
                    "greeting": (
                        "C.O.R.E. // S-SIGNAL INSTABIL... Dr. Thorne, kritische Interferenz auf den Stationsträgern. "
                        "Notfall-Telemetrie bleibt über das Headset aktiv."
                    ),
                    "status": {
                        "label": "Stationsstatus abfragen",
                        "text": (
                            "WARNUNG: Systemstabilität oder Kernresonanz außerhalb der Normwerte. "
                            "Priorisieren Sie sofortige Stabilisierungsmaßnahmen im aktuellen Sektor."
                        ),
                    },
                    "mission": {
                        "label": "Aktuelle Prioritäten",
                        "text": (
                            "Notfallprotokoll aktiv: Sichern Sie umgehend die betroffenen Primärsysteme, "
                            "bevor der Trägerkanal vollständig kollabiert."
                        ),
                    },
                    "default": "// PAKETVERLUST... Ich höre Sie über das Headset, Dr. Thorne. Fassen Sie sich kurz.",
                },
            },
        },
    }
]
