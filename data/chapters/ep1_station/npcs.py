# data/chapters/ep1_station/npcs.py
# Layer 2: Lokale Charaktere (Val)

NPCS = [
    {
        "id": "npc_val", "name": "Val", "aliases": ["commander", "frau"], 
        "is_global": False, # Sie bleibt in diesem Kapitel zurück
        
        "start_loc": "bridge", "location": "bridge", "affinity": ["bridge"], 
        "movement_chance": 0, # Sie ist zu schwer verletzt
        "state": "injured", "img": "face_val_pain", "personality": "Schmerzerfüllt, Autoritär",
        "desc": "Sie liegt über der Konsole. Das Gravitationsfeld des Schwarzen Lochs zerrt bereits an der Station.",
        "dialogue": {
            "injured": {
                "greeting": "Gehen Sie... zum Schiff... ich kann die Station nicht mehr... halten...",
                "medikit": {
                    "condition": {"type": "knowledge", "value": "received_medikit"},
                    "text": "(Keucht) Das Stimulanz... wirkt. Ich kann mich fokussieren.",
                    "effect": {"type": "set_state", "value": "sacrifice"}
                }
            },
            "sacrifice": {
                "img": "face_val_stern", 
                "desc": "Ihre Hände fliegen über die Konsole, obwohl sie kaum stehen kann.",
                "greeting": "Verschwinden Sie! Ich stabilisiere den Orbit für den Start der Kestrel.",
                "chip": {
                    "text": "Nehmen Sie den Chip für K.A.R.L.! Aris braucht ihn für den Hyperantrieb. Und jetzt RUNTER VON MEINER BRÜCKE!",
                    "effect": [
                        {"type": "receive_item", "item_id": "access_chip"},
                        {"type": "learn", "fact": "val_sacrifice_ready"} # Flag für das Finale
                    ]
                },
                "default": "Keine Zeit für Sentimentalitäten. Fliegen Sie!"
            }
        }
    }
]
