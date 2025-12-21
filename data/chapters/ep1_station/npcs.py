# data/chapters/ep1_station/npcs.py
# Layer 2: Lokale Charaktere (Val)

NPCS = [
    {
        "id": "npc_val", 
        "name": "Val", 
        "aliases": ["commander", "frau"], 
        "is_global": False, # Sie bleibt in diesem Kapitel zurück
        
        "start_loc": "bridge", 
        "location": "bridge", 
        
        # Neue Struktur: Top-Level "states"
        "initial_state": "injured",
        "states": {
            "injured": {
                "behavior": {
                    "movement_chance": 0, # Zu schwer verletzt
                    "affinity": ["bridge"],
                    "route": []
                },
                "visuals": {
                    "img": "face_val_pain", 
                    "desc": "Sie liegt über der Konsole. Das Gravitationsfeld des Schwarzen Lochs zerrt bereits an der Station.",
                    "personality": "Schmerzerfüllt"
                },
                "dialogue": {
                    "greeting": "Gehen Sie... zum Schiff... ich kann die Station nicht mehr... halten...",
                    "medikit": {
                        "condition": {"type": "knowledge", "value": "received_medikit"},
                        "text": "(Keucht) Das Stimulanz... wirkt. Ich kann mich fokussieren.",
                        "effect": {"type": "set_state", "value": "sacrifice"}
                    }
                }
            },
            "sacrifice": {
                "behavior": {
                    "movement_chance": 0, # Sie bleibt auf der Brücke für das Manöver
                    "affinity": ["bridge"],
                    "route": []
                },
                "visuals": {
                    "img": "face_val_stern", 
                    "desc": "Ihre Hände fliegen über die Konsole, obwohl sie kaum stehen kann.",
                    "personality": "Entschlossen"
                },
                "dialogue": {
                    "greeting": "Verschwinden Sie! Ich stabilisiere den Orbit für den Start der Kestrel.",
                    "chip": {
                        "text": "Nehmen Sie den Chip für K.A.R.L.! Aris braucht ihn für den Hyperantrieb. Und jetzt RUNTER VON MEINER BRÜCKE!",
                        "effect": [
                            {"type": "receive_item", "item_id": "access_chip"},
                            {"type": "learn", "fact": "val_sacrifice_ready"}
                        ]
                    },
                    "default": "Keine Zeit für Sentimentalitäten. Fliegen Sie!"
                }
            }
        }
    }
]
