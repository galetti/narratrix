# data/chapters/chapter_1.py
from data.npcs import NPCS as ALL_NPCS

CHAPTER_META = {
    "chapter_title": "Kapitel 1: Init",
    "chapter_id": 1
}

# --- LOKALE RÄUME ---
ROOMS = {}

# --- LOKALE ITEMS ---
ITEMS = {}

# --- LOKALE NPCS ---
# Hier filtern wir NUR VAL heraus
NPCS = []
for npc in ALL_NPCS:
    is_val = (
        npc.get('id', '').lower() == 'npc_val' or 
        npc.get('name', '').upper() == 'VAL' or
        'val' in npc.get('aliases', [])
    )
    if is_val:
        NPCS.append(npc)

# --- LOKALE EVENTS ---
NARRATIVE_MATRIX = []

# WICHTIG: Liste statt Dict, um zum globalen Format zu passen
COMBINATIONS = []
