# data/story_config.py
# -*- coding: utf-8 -*-

from data.rooms import ROOMS
from data.items import ITEMS, COMBINATIONS
from data.npcs import NPCS
from data.events import NARRATIVE_MATRIX

CONFIG = {
    "meta": {
        "title": "Echo der Station Omega-9",
        "author": "Galetti & AI",
        "version": "4.3 (Refactored)",
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
        # NEU: System- und Parsing-Befehle zentralisiert
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
        "skip_words": []
    },

    "narrative_matrix": NARRATIVE_MATRIX,
    "combinations": COMBINATIONS,
    "rooms": ROOMS,
    "objects": ITEMS,
    "npcs": NPCS
}
