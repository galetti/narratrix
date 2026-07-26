# data/common/events.py
# Layer 1: Globale Events (z.B. Hunger, Funksprüche vom Hauptquartier)

COMMON_MATRIX = [
    # Beispiel: Ein kosmisches Hintergrundrauschen alle 100 Ticks
     {
         "id": "evt_global_ambience",
         "trigger": "time", "trigger_time": 100,
         "title": "Subraum-Echo",
         "description": "Ein fernes Subraum-Echo lässt die Umgebung leicht vibrieren."
     }
]
