# narratrix_engine/data/chapters/ep0_test_lab/events.py
from engine.constants import *

# Narrative Matrix (Story Flow)
NARRATIVE_MATRIX = [
    # Wir könnten hier Kapitel-Events definieren
]

# Dynamische Events
EVENTS = [
    {
        "id": "machine_noise",
        "trigger": "time",
        "trigger_time": 1, # Startet fast sofort
        "repeat": True,    # Wiederholt sich (simuliert Loop)
        "origin_id": "lower_deck", # Schallquelle
        "sound_msg": "Ein tiefes Wummern von Maschinen.",
        # Trigger Condition: Immer wahr für Testzwecke, oder wir togglen es via Maschine
    }
]