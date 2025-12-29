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
                    "desc": "Eine junge Frau mit wilden roten Haaren und einem Laborkittel. Sie wirkt etwas chaotisch, aber sympathisch.",
                    "personality": "Quirlig"
                },
                "dialogue": {
                    "greeting": "Oh, hallo! Du bist der neue Ingenieur vom USC, oder? Ich bin Fiona! Willkommen auf der Omega-9.",
                    "arbeit": {
                        "label": "Nach ihrer Arbeit fragen",
                        "text": "Ich untersuche die Flora des nahen Planeten. Faszinierend, sag ich dir! Aber auch gefährlich."
                    },
                    "aris": {
                        "label": "Über Aris reden",
                        "condition": {"type": "knowledge", "value": "aris_friend"},
                        "text": "Aris? Er ist ein Schatz. Er repariert mir immer den Extraktor, auch wenn er eigentlich Wichtigeres zu tun hat.",
                        "effect": {"type": "learn", "fact": "knows_aris_crush"}
                    },
                    "frucht": {
                        "label": "Die Frucht ansehen",
                        "text": "Ist sie nicht hübsch? Aber ich kriege das Gewicht nicht bestimmt, meine Hände zittern heute so."
                    },
                    "waage": {
                        "label": "Hilfe anbieten",
                        "text": "Kannst du mir helfen? Leg die Frucht einfach auf die Waage und sag mir, was sie wiegt."
                    },
                    "gewicht": {
                        "hidden": True,
                        "condition": {"type": "item_location", "item": "alien_fruit", "location": "scale"}, 
                        "text": "0.35 kg? Perfekt! Danke dir! Du bist ein Schatz.", 
                        "effect": {"type": "learn", "fact": "fiona_helped"}
                    }
                }
            },
            "dinner": {
                "behavior": {"movement_chance": 0, "affinity": ["cantina"]},
                "visuals": {
                    "img": "face_fiona_happy", 
                    "desc": "Sie sitzt am Tisch und genießt ihr Curry.",
                    "personality": "Entspannt"
                },
                "dialogue": {
                    "greeting": "Das Essen ist heute gar nicht übel! Setz dich zu uns.",
                    "default": "Hoffentlich schlafe ich heute gut. Morgen wird ein großer Tag."
                }
            },
            # NEU: Nacht-Zustand (Vor der Konfrontation)
            "night_conspiracy": {
                "behavior": {
                    "movement_chance": 0, 
                    "affinity": ["maintenance"], # Sie schleicht zum Treffpunkt
                    "route": ["medbay", "hub", "maintenance"], # Sie geht dorthin
                    "route_behavior": "once"
                },
                "visuals": {
                    "img": "face_fiona_happy", # 
                    "desc": "Sie wirkt gehetzt und schaut sich ständig um. Sie hält einen kleinen Behälter fest umklammert.",
                    "personality": "Nervös"
                },
                "dialogue": {
                    "greeting": "Was... was machst du hier? Du solltest schlafen!",
                    "behälter": "Das? Das ist... nichts. Nur ein Experiment. Geh zurück ins Bett, bitte!",
                    "default": "Ich habe zu tun. Gute Nacht."
                }
            }
        }
    }
]