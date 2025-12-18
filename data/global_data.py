# data/global_data.py
# Enthält Daten, die in ALLEN Kapiteln verfügbar sind.
# KEINE IMPORTE aus items.py, rooms.py etc. mehr!

from engine.constants import (
    TYPE_ITEM, LOC_INVENTORY, ATTR_MOVABLE
)

# --- GLOBALE ITEMS ---
# Dinge, die der Spieler immer hat oder die kapitelübergreifend sind.
GLOBAL_ITEMS = {
    "player_pda": {
        "id": "player_pda", 
        "name": "Datapad", 
        "aliases": ["pda", "tablet", "logbuch"],
        "location": LOC_INVENTORY, 
        "type": TYPE_ITEM, 
        "movable": True,
        "desc": "Dein persönliches Terminal. Es enthält Missionslogs.",
        "weight": 0.5
    }
}

# --- GLOBALE NPCS ---
# Z.B. eine KI im Kopf des Spielers oder ein Begleiter.
GLOBAL_NPCS = []

# --- GLOBALE KONFIGURATION ---
GLOBAL_CONFIG = {
    "meta": {
        "title": "Narratrix: Omega-9",
        "author": "Galetti & AI",
        "version": "6.0 (Chapter Isolation)",
        "start_room": "hub" # Startraum des aktuellen Kapitels (überschreibbar)
    },

    "system": {
        "llm_api_url": "http://localhost:1234/v1/chat/completions",
        "llm_timeout": 5
    },

    # Vokabular ist global
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
    
    # Platzhalter für Merge (werden vom ChapterManager gefüllt)
    "narrative_matrix": [],
    "combinations": [],
    "rooms": {},
    "objects": GLOBAL_ITEMS, 
    "npcs": GLOBAL_NPCS
}
