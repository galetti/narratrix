# data/chapters/ep0_arrival/npcs.py

NPCS = [
    {
        "id": "npc_fiona", 
        "name": "Fiona", 
        "aliases": ["biologin", "fiona", "doktor"], 
        "is_global": False,
        "start_loc": "medbay", 
        "location": "medbay",
        
        "initial_state": "working",
        "states": {
            "working": {
                "behavior": {"movement_chance": 10, "affinity": ["medbay"]},
                "visuals": {
                    "img": "face_fiona_happy", 
                    "desc": "Eine junge Frau mit wilden roten Haaren und einem Laborkittel.",
                    "personality": "Quirlig"
                },
                "dialogue": {
                    "greeting": "Oh, hallo! Du bist der neue Ingenieur, oder? Ich bin Fiona! Willkommen auf der Omega-9.",
                    
                    "arbeit": {
                        "label": "Nach ihrer Arbeit fragen", # Schöner Label im Menü
                        "text": "Ich untersuche die Flora des nahen Planeten. Faszinierend, sag ich dir! Aber auch gefährlich."
                    },
                    
                    # Dieses Thema erscheint erst, wenn man Aris Pralinen gegeben hat (aris_friend)
                    "aris": {
                        "label": "Über Aris reden",
                        "condition": {"type": "knowledge", "value": "aris_friend"},
                        "text": "Aris? Er ist ein Schatz. Er repariert mir immer den Extraktor, auch wenn er eigentlich Wichtigeres zu tun hat.",
                        "effect": {"type": "learn", "fact": "knows_aris_crush"} # Neues Wissen!
                    },
                    
                    "frucht": {
                        "label": "Die Frucht ansehen",
                        "text": "Ist sie nicht hübsch? Aber ich kriege das Gewicht nicht bestimmt, meine Hände zittern heute so."
                    },
                    
                    "waage": {
                        "label": "Hilfe anbieten",
                        "text": "Kannst du mir helfen? Leg die Frucht einfach auf die Waage und sag mir, was sie wiegt."
                    },
                    
                    # Verstecktes Thema (kein Label = muss getippt werden, oder hidden=True)
                    "geheimnis": {
                        "hidden": True,
                        "text": "Pscht! Nicht so laut. Ich habe illegale Proben an Bord. Aber sag's nicht Val!"
                    },

                    "gewicht": {
                        "hidden": True, # Soll nicht im Menü auftauchen, wird getriggert durch Keyword
                        "condition": {"type": "item_location", "item": "alien_fruit", "location": "scale"}, 
                        "text": "0.35 kg? Perfekt! Danke dir! Du bist ein Schatz.", 
                        "effect": {"type": "learn", "fact": "fiona_helped"}
                    }
                }
            },
            "dinner": {
                "behavior": {"movement_chance": 0, "affinity": ["cantina"]},
                "visuals": {"img": "face_fiona_happy", "desc": "Sie isst herzhaft."},
                "dialogue": {
                    "greeting": "Das Essen ist heute gar nicht übel!",
                    "default": "Hoffentlich schlafe ich heute gut."
                }
            }
        }
    }
]