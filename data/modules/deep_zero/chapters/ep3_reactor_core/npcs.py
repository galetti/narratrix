# data/modules/deep_zero/chapters/ep3_reactor_core/npcs.py
from __future__ import annotations

from engine.constants import ATTR_ALIASES, ATTR_DESC, ATTR_NAME
from engine.schema import NPCData

NPCS: list[NPCData] = [
    {
        "id": "sato",
        ATTR_NAME: "Dr. Sato",
        ATTR_DESC: "Chefingenieur Sato steht vor den Reaktor-Monitoren im Leitstand. Seine Stirn liegt in tiefen Sorgenfalten.",
        ATTR_ALIASES: ["sato", "dr", "doktor", "chefingenieur", "ingenieur"],
        "location": "control_room",
        "level": 0,
        "state": "urgent",
        "behavior_id": "idle",
        "personality": "Focused, urgent chief engineer fighting against time to save the dark-matter reactor.",
        "dialogue": {
            "urgent": {
                "greeting": "Thorne! Zum Glück bist du hier! Die thermische Resonanz des Kerns gerät außer Kontrolle!",
                "problem": {
                    "label": "Wie ist die Lage?",
                    "text": (
                        "Die Temperatur im Dunkle-Materie-Kern steigt exponentiell! Wir müssen den Notkühlkanister "
                        "aus dem Kryo-Lager holen und oben auf Ebene 2 an den Injektor-Verteiler anschließen. "
                        "Nimm unbedingt die Isolierhandschuhe aus dem Wandfach hier! Danach müssen wir das Magnetfeld "
                        "über die Steuerkonsole kalibrieren!"
                    ),
                    "effect": {"type": "trigger_event", "id": "event_quest_start"},
                },
                "solution": {
                    "label": "Ich starte die Notkühlung.",
                    "text": (
                        "Beeil dich! Hol die Isolierhandschuhe aus dem Wandfach und den Kryo-Kühlkanister aus dem Kühllager im Norden. "
                        "Klettere in der Reaktorkammer die Leiter auf Ebene 2 hoch und kuppele ihn an den Verteiler an. "
                        "Danach stimmst du hier die Steuerkonsole mit deinem Omni-Tool ab!"
                    ),
                    "condition": "ep3_quest_started",
                },
            },
            "waiting": {
                "greeting": "Die Reaktortemperatur ist immer noch im roten Bereich! Bring den Kühlkanister mit den Isolierhandschuhen auf Ebene 2!",
                "default": "Isolierhandschuhe aus dem Wandfach, Kühlkanister aus dem Lager holen, in die Reaktorkammer gehen, auf Ebene 2 klettern und einkoppeln!",
            },
            "celebrating": {
                "greeting": "Unglaublich, Thorne! Die Temperatur fällt rapide und das Magnetfeld steht felsenfest!",
                "reward": {
                    "label": "Einsatz beenden",
                    "text": (
                        "Du hast nicht nur den Reaktor gerettet, sondern die gesamte Station und die Besatzung. "
                        "Im Namen der gesamten Crew: Danke! Hiermit überreiche ich dir den Generalschlüssel von Deep Zero."
                    ),
                    "effect": [
                        {"type": "receive_item", "item": "master_station_key"},
                        {"type": "trigger_event", "id": "event_station_saved"},
                    ],
                },
            },
        },
    },
    {
        "id": "aegis",
        ATTR_NAME: "Aegis (MK-3)",
        ATTR_DESC: "Ein schwer gepanzerter Sicherheits- und Gefahrengut-Droide mit gelben Warnsignalen.",
        ATTR_ALIASES: ["aegis", "drohne", "bot", "mk-3", "sicherheitsdrohne", "schutzbot"],
        "location": "reactor_bridge",
        "level": 0,
        "state": "alert",
        "behavior_id": "idle",
        "dialogue": {
            "alert": {
                "greeting": "BEEP. WARNUNG: Reaktor-Containment aktiv. Autorisierungschip von Dr. Vance bestätigt. Zutritt gewährt.",
                "default": "BEEP. Halten Sie Sicherheitsabstand zu Plasma-Entladungen. Schutzprotokoll 7 aktiv.",
            },
        },
    },
]
