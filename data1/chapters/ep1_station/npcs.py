# data/chapters/ep1_station/npcs.py
# Layer 2: Lokale Charaktere (Val)

NPCS = [
    {
        "id": "npc_val", 
        "name": "Val", 
        "aliases": ["commander", "frau"], 
        "is_global": False, 
        
        "start_loc": "bridge", 
        "location": "bridge", 
        
        "initial_state": "injured",
        "states": {
            "injured": {
                "behavior": {
                    "movement_chance": 0,
                    "affinity": ["bridge"],
                    "route": []
                },
                "visuals": {
                    "img": "face_val_pain", 
                    "desc": "Sie liegt über der Konsole, eine Hand auf eine klaffende Wunde an ihrer Seite gepresst. Das Gravitationsfeld des Schwarzen Lochs zerrt bereits spürbar an der Station.",
                    "personality": "Schmerzerfüllt"
                },
                "dialogue": {
                    "greeting": "Gehen Sie... zum Schiff... ich kann die Station nicht mehr... halten...",
                    "medikit": {
                        "condition": {"type": "knowledge", "value": "received_medikit"},
                        "text": "(Keucht) Das Stimulanz... wirkt. Der Schmerz lässt nach. Ich kann mich wieder fokussieren.",
                        "effect": {"type": "set_state", "value": "sacrifice"}
                    },
                    "hilfe": "Ich brauche... medizinisches Gel... und Verbände... In der Medbay...",
                    "status": "Der Reaktor... instabil... Aris muss ihn kühlen..."
                }
            },
            "sacrifice": {
                "behavior": {
                    "movement_chance": 0,
                    "affinity": ["bridge"],
                    "route": []
                },
                "visuals": {
                    "img": "face_val_stern", 
                    "desc": "Ihre Hände fliegen über die Konsole, obwohl sie kaum stehen kann. Ihr Blick ist starr auf den Ereignishorizont gerichtet.",
                    "personality": "Entschlossen"
                },
                "dialogue": {
                    "greeting": "Verschwinden Sie! Ich stabilisiere den Orbit für den Start der Kestrel.",
                    "chip": {
                        "text": "Nehmen Sie den Chip für K.A.R.L.! Aris braucht ihn für den Hyperantrieb. Und jetzt RUNTER VON MEINER BRÜCKE! Wenn die Schleuse klemmt, nutzen Sie Gewalt!",
                        "effect": [
                            {"type": "receive_item", "item_id": "access_chip"},
                            {"type": "learn", "fact": "val_sacrifice_ready"}
                        ]
                    },
                    "default": "Keine Zeit für Sentimentalitäten. Fliegen Sie! Retten Sie die Crew!"
                }
            }
        }
    }
]
