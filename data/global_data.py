# data/global_data.py

from data.rooms import ROOMS
from data.items import ITEMS, COMBINATIONS
from data.events import NARRATIVE_MATRIX
from data.npcs import NPCS as ALL_NPCS
# Wir brauchen hier keine Constants importieren, wenn wir sie nicht direkt nutzen,
# aber da ITEMS sie nutzt, muss ITEMS.py sie importieren (Schritt 1).

# --- NPC FILTERUNG ---
GLOBAL_NPCS = []
for npc in ALL_NPCS:
    is_val = (
        npc.get('id', '').lower() == 'npc_val' or 
        npc.get('name', '').upper() == 'VAL' or
        'val' in npc.get('aliases', [])
    )
    if not is_val:
        GLOBAL_NPCS.append(npc)

# ITEMS UPDATEN MIT GEWICHT (Patching der bestehenden Items)
for item in ITEMS.values():
    if 'weight' not in item:
        name = item.get('name', '').lower()
        if 'pda' in name or 'datapad' in name: item['weight'] = 0.5
        elif 'brecheisen' in name: item['weight'] = 2.5
        elif 'schlüssel' in name: item['weight'] = 0.1
        else: item['weight'] = 1.0 

if 'player_pda' in ITEMS:
    ITEMS['player_pda']['weight'] = 0.3

# --- GLOBALE KONFIGURATION ---
GLOBAL_CONFIG = {
    "meta": {
        "title": "Narratrix: Omega-9",
        "author": "Galetti & AI",
        "version": "5.1 (Weight System)",
        "start_room": "hub" 
    },

    "system": {
        "llm_api_url": "http://localhost:1234/v1/chat/completions",
        "llm_timeout": 5
    },

    "vocabulary": {
        "verbs": {
            "look": ["schau", "l", "x", "untersuche", "betrachte", "lies", "scan", "status"],
            "move": ["gehe", "go", "lauf", "klettere", "schwebe", "wandere", "steig", "bewege"],
            "take": ["nimm", "greif", "einstecken", "sammle", "aufheben"],
            "drop": ["drop", "fallenlassen", "abwerfen", "hinlegen", "ablegen", "entferne", "lass"],
            "put": ["put", "legen", "stecken", "tun", "platziere", "stell", "packe", "fülle"],
            "give": ["gib", "geben", "reich", "schenke", "give", "versorge"],
            "use": ["benutze", "opfere", "anwenden", "kombiniere", "fülle", "injiziere"],
            "talk": ["rede", "sprich", "frag", "befrage", "kommuniziere", "funk"],
            "open": ["öffne", "aufmachen", "zugriff"],
            "break": ["brich", "zerstöre", "eintreten", "force", "zerschlage"],
            "fix": ["repariere", "reinige", "patch", "löte", "fix", "flicken", "verbinde"],
            "inventory": ["i", "inv", "tasche", "rucksack", "ausrüstung"],
            "wait": ["warte", "bete", "z", "ruhen"],
            "save": ["speichern", "sichern", "save"],
            "load": ["laden", "load"],
            "oracle": ["orakel", "vorhersage", "vision", "prognose", "sehe", "log"],
            "map": ["map", "karte", "plan", "radar"],
            "hack": ["hack", "hacken", "zugriff", "system", "override"]
        },
        "directions": {
            "north": ["n", "nord", "norden", "brücke"],
            "south": ["s", "süd", "süden", "kantine"],
            "east": ["e", "ost", "osten", "reaktor"],
            "west": ["w", "west", "westen", "schleuse"],
            "up": ["u", "up", "oben", "deck1"],
            "down": ["d", "down", "unten", "wartung"]
        },
        "system_commands": {
            "cancel": ["stop", "abbrechen", "nein", "cancel", "zurück", "n"]
        },
        "dialogue_exits": ["bye", "ende", "tschüss", "weg", "stop", "exit", "leave"],
        "prepositions": {
            "give": ["an", "to", "dem", "der"],
            "put": ["in", "auf", "on", "into", "an"],
            "use": ["mit", "with", "und", "an"],
            "general": ["in", "im", "an", "am", "auf", "mit", "bei", "zu", "nach", "den", "die", "das", "dem", "der"]
        },
        "skip_words": ["der", "die", "das", "ein", "eine", "einen"]
    },
    
    "narrative_matrix": NARRATIVE_MATRIX,
    "combinations": COMBINATIONS,
    "rooms": ROOMS,
    "objects": ITEMS,
    "npcs": GLOBAL_NPCS
}
