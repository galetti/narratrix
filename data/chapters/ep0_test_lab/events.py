# narratrix_engine/data/chapters/ep0_test_lab/events.py
from engine.constants import *

# Narrative Matrix (Story Flow) - Kann leer sein für Tests
NARRATIVE_MATRIX = []

# Dynamische Events
EVENTS = [
    {
        "id": "machine_noise",
        "trigger": "time",
        "trigger_time": 0, # Sofort ab Start
        "repeat": True,    # Wiederholt sich jeden Tick
        "origin_id": "lower_deck", # Schallquelle
        "sound_msg": "Ein tiefes Wummern von Maschinen.",
    }
]