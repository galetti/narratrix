# narratrix_engine/data/chapters/ep1_deep_zero/npcs.py
from engine.constants import *

NPCS = [
    {
        "id": "sato",
        ATTR_NAME: "Dr. Sato",
        ATTR_DESC: "Der leitende Ingenieur. Er wirkt müde.",
        "location": "room_corridor_quarters", # Startet im Gang (Murmeln)
        "state": "mumbling",
        "behavior_id": "guard", # Patrouille als Basis
        "waypoints": ["room_mess", "room_control", "room_lab"],
        "speed": 0.5, # Langsam
        "dialogue": {
            "mumbling": {
                "greeting": "(Er bemerkt dich nicht, murmelt über Messwerte)",
                "default": "Hm? Oh, hi Aris. Gleich, ich muss das hier verstehen..."
            },
            "coffee_craving": {
                "greeting": "Morgen, Aris. Die Pumpe ist hin. Ohne Kaffee arbeite ich nicht.",
                "default": "Hast du die Dichtungen gesehen?"
            },
            "coffee_happy": {
                "greeting": "Du bist ein Lebensretter! Das nenne ich Service.",
                "mars": {
                    "label": "Wie gehts der Familie?",
                    "text": "Lena hat mir ein Bild vom Mars geschickt. Sie wachsen so schnell... hier draußen verpasst man alles."
                }
            },
            "evening": {
                "greeting": "Sorry, hab die Zeit vergessen. War gerade so ruhig.",
                "check": {
                    "label": "Lass uns den Check machen.",
                    "text": "Lass uns nur schnell die Grav-Daten abzeichnen, dann gehört die Station mir."
                }
            }
        }
    },
    {
        "id": "core",
        ATTR_NAME: "C.O.R.E.",
        ATTR_DESC: "Die Stations-KI. Überall und nirgends.",
        "location": "room_control", # Virtuell überall erreichbar via Funk?
        "state": "active",
        "dialogue": {
            "active": {
                "greeting": "Guten Morgen, Dr. Thorne. Systeme nominal.",
                "schach": {
                    "label": "Eine Partie Schach?",
                    "text": "Gerne. Ich werde meine Prozessorkapazität auf 5% drosseln, um es fair zu gestalten... Schachmatt in 4 Zügen."
                }
            }
        }
    }
]