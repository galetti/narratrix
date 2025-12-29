# data/common/npcs.py
# Layer 1: Die permanente Crew (Aris & K.A.R.L.)

COMMON_NPCS = [
    {
        "id": "npc_aris", 
        "name": "Aris", 
        "aliases": ["chief", "aris", "ingenieur"], 
        "is_global": True,
        "start_loc": "cantina", 
        "location": "cantina", 
        
        "initial_state": "panic",
        "states": {
            "relaxed": {
                "behavior": {
                    "movement_chance": 20, 
                    "affinity": ["reactor", "hub", "cantina"], 
                    "route": []
                },
                "visuals": {
                    "img": "face_aris_alert", 
                    "desc": "Der Chefingenieur wirkt zufrieden. Er summt leise vor sich hin.",
                    "personality": "Freundlich, Jovial"
                },
                "dialogue": {
                    "greeting": "Hey! Gut, dass du da bist. Der Hyperantrieb macht zwar Zicken, aber das hat bis morgen Zeit.",
                    "fiona": "Die Neue? Sie ist nett. Ein bisschen verrückt nach Pflanzen, aber wer ist hier draußen schon normal?",
                    "essen": "Ich hoffe, der Replikator spuckt heute Abend was Essbares aus. Ich hab einen Bärenhunger.",
                    "geschenk": {
                        "condition": {"type": "knowledge", "value": "received_gift"}, 
                        "text": "Oh, Pralinen von der Erde? Du bist der Beste! Die hebe ich mir für nach dem Dienst auf.", 
                        "effect": {"type": "learn", "fact": "aris_friend"}
                    }
                }
            },
            # NEU: Schlafenszeit
            "sleeping": {
                "behavior": {
                    "movement_chance": 100, # Er geht sofort ins Bett
                    "affinity": ["crew_quarters"],
                    "route": []
                },
                "visuals": {
                    "img": "face_aris_alert", # Wir haben kein 'sleeping' face, also neutral
                    "desc": "Aris ist auf dem Weg in seine Koje.",
                    "personality": "Müde"
                },
                "dialogue": {
                    "greeting": "Gute Nacht. Morgen ist auch noch ein Tag."
                }
            },
            "panic": {
                "behavior": {
                    "movement_chance": 40, 
                    "affinity": ["cantina", "reactor"], 
                    "route": []
                },
                "visuals": {
                    "img": "face_aris_tired", 
                    "desc": "Er zittert am ganzen Leib. Öl verschmiert sein Gesicht.",
                    "personality": "Gestresst"
                },
                "dialogue": {
                    "greeting": "Verdammt! Ich brauche einen Stim!",
                    "stim": {"text": "Misch Pulver und Wasser! Schnell!"},
                    "kaffee": {"condition": {"type": "knowledge", "value": "received_stim_caf"}, "text": "Danke.", "effect": {"type": "set_state", "value": "focused"}}
                }
            },
            "focused": {
                "behavior": {
                    "movement_chance": 80, 
                    "affinity": ["cantina", "reactor"],
                    "route": ["cantina", "hub", "reactor", "maintenance", "reactor", "hub"], 
                    "route_behavior": "loop"
                },
                "visuals": {
                    "img": "face_aris_alert", 
                    "desc": "Er wirkt ruhig und kompetent.",
                    "personality": "Kompetent"
                },
                "dialogue": {
                    "greeting": "Wir müssen das Schiff retten.",
                    "chip": {"condition": {"type": "knowledge", "value": "received_access_chip"}, "text": "Ich starte K.A.R.L. neu!", "effect": [{"type": "move_npc", "target": "hub"}, {"type": "set_state", "value": "hacking"}, {"type": "set_npc_state", "npc": "K.A.R.L.", "value": "online"}]}
                }
            },
            "hacking": {
                "behavior": {
                    "movement_chance": 0,
                    "affinity": ["hub"],
                    "route": []
                },
                "visuals": {
                    "img": "face_aris_alert",
                    "desc": "Er tippt wild auf dem Terminal herum.",
                    "personality": "Fokussiert"
                },
                "dialogue": {
                    "greeting": "Nicht jetzt!", 
                    "default": "Keine Zeit!"
                }
            }
        }
    },
    {
        "id": "npc_val", "name": "Val", "aliases": ["commander", "frau"], "is_global": True, 
        "start_loc": "bridge", "location": "bridge",
        "initial_state": "injured",
        "states": {
            "relaxed": {
                "behavior": {"movement_chance": 10, "affinity": ["bridge", "hub"]},
                "visuals": {
                    "img": "face_val_stern", 
                    "desc": "Commander Val strahlt natürliche Autorität aus. Sie wirkt entspannt, aber wachsam.",
                    "personality": "Professionell"
                },
                "dialogue": {
                    "greeting": "Willkommen an Bord, Spezialist. Wir schätzen die Unterstützung des USC.",
                    "status": "Alle Systeme nominal. Genießen Sie den Abend, morgen früh geht die Wartung los.",
                    "fiona": "Dr. Hellman leistet gute Arbeit, auch wenn ihre Methoden etwas... unkonventionell sind."
                }
            },
            # NEU: Schlafenszeit
            "sleeping": {
                "behavior": {
                    "movement_chance": 100,
                    "affinity": ["crew_quarters"],
                    "route": []
                },
                "visuals": {
                    "img": "face_val_stern",
                    "desc": "Sie ist auf dem Weg in die Quartiere.",
                    "personality": "Müde"
                },
                "dialogue": {
                    "greeting": "Der Dienst ist beendet. Ruhen Sie sich aus."
                }
            },
            "injured": {
                "behavior": {"movement_chance": 0},
                "visuals": {"img": "face_val_pain", "desc": "Sie blutet stark."},
                "dialogue": {"greeting": "Bericht..."}
            }
        }
    },
    {
        "id": "npc_karl", 
        "name": "K.A.R.L.", 
        "aliases": ["ki"], 
        "is_global": True,
        "start_loc": "hub", 
        "location": "hub", 
        
        "initial_state": "offline",
        "states": {
            "offline": {
                "behavior": {"movement_chance": 0, "affinity": ["hub"], "route": []},
                "visuals": {"img": "face_ai_glitch", "desc": "Das Hologramm flackert rot.", "personality": "Defekt"},
                "dialogue": {"greeting": "S-S-Systemfehler."}
            },
            "online": {
                "behavior": {"movement_chance": 0, "affinity": ["hub"]},
                "visuals": {"img": "face_ai_calm", "desc": "Das Hologramm leuchtet ruhig blau.", "personality": "Hilfsbereit"},
                "dialogue": {"greeting": "Systeme online."}
            },
            "service": {
                "behavior": {"movement_chance": 0, "affinity": ["hub"]},
                "visuals": {
                    "img": "face_ai_calm", 
                    "desc": "Das Hologramm projeziert ein freundliches Lächeln.",
                    "personality": "Höflich"
                },
                "dialogue": {
                    "greeting": "Guten Abend, Sir. Kann ich Ihnen behilflich sein?",
                    "essen": "Das Abendmenü heute ist 'Reis-Variationen'. Ich habe die Kalorien für die Crew bereits optimiert."
                }
            }
        }
    }
]