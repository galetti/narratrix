NPCS = [
    {
        "id": "npc_aris",
        "name": "ARIS",
        "location": "ship_workshop",
        "state": "offline",
        "desc": "Ein humanoider Android der älteren Baureihe. Zynisch, beschädigt, unentbehrlich.",
        "aliases": ["drohne", "roboter", "bot", "android"],
        "states": {
            "offline": {
                "visuals": {"desc": "ARIS hängt schlaff in seiner Halterung."},
                "dialogue": {}
            },
            "online": {
                "visuals": {"desc": "ARIS steht etwas krumm da. Seine Optiken flackern gelb."},
                "behavior": {"roam": True}, 
                "dialogue": {
                    "greeting": "System-Reboot... Oh. Du lebst noch. Statistisch gesehen unwahrscheinlich.",
                    "status": {
                        "text": "Hüllenintegrität bei 12%. Lebenserhaltung im Notbetrieb.",
                        "label": "Statusbericht"
                    },
                    "tuer_problem": {
                        "condition": "knows_bio_lock", # Wenn Spieler Tür gesehen hat
                        "text": "Die Bio-Verriegelung im Korridor? Vergiss es. Das Sicherheitsprotokoll denkt, wir seien tot. Ich kann es von hier nicht hacken.",
                        "label": "Die Schleuse ist versiegelt."
                    },
                    "alternative": {
                        "condition": "knows_bio_lock",
                        "text": "Es gibt einen Wartungsschacht hier hinter dem Gitter. Er führt um die Schleuse herum. Eng, schmutzig, gefährlich. Genau dein Stil.",
                        "label": "Gibt es einen anderen Weg?",
                        "effect": [
                            {"type": "trigger_event", "id": "start_shaft_sequence"},
                            {"type": "set_npc_state", "npc": "ARIS", "value": "scouting"} 
                        ]
                    }
                }
            },
            "scouting": {
                # ARIS begleitet den Spieler nicht direkt, sondern taucht auf und ab
                "visuals": {"desc": "ARIS klettert geschickt voraus in den Schacht."},
                "behavior": {"roam": False},
                "dialogue": {
                    "greeting": "Nicht trödeln. Meine Sensoren messen einen Temperaturabfall.",
                    "weg": {
                        "text": "Ich gehe vor und scanne die Struktur. Warte hier, wenn du nicht abstürzen willst.",
                        "label": "Wo lang?"
                    }
                }
            }
        }
    }
]