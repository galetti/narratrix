import importlib
import copy
from data.global.npcs import GLOBAL_NPCS

class StoryLoader:
    """
    Verwaltet das Laden und Zusammenführen von Globalen Daten (Layer 1)
    und Kapitel-Daten (Layer 2).
    """
    
    @staticmethod
    def load_chapter(chapter_module_path):
        """
        Lädt ein Kapitel basierend auf dem Modul-Pfad (z.B. 'data.chapters.ep1_station.config').
        Gibt ein vollständiges Config-Dictionary zurück, wie es GameState erwartet.
        """
        try:
            # 1. Dynamischer Import des Kapitel-Configs
            module = importlib.import_module(chapter_module_path)
            chapter_data = module.CHAPTER_CONFIG
            
            print(f"[SYSTEM] Lade Kapitel: {chapter_data['meta']['title']}")
            
            # 2. Globale Daten (Layer 1) laden (Klonen, damit Original sauber bleibt)
            global_npcs = copy.deepcopy(GLOBAL_NPCS)
            
            # 3. Merging (Zusammenführen)
            # Hier könnten wir später Logik einbauen, um Global NPCs in Räume zu 'teleportieren',
            # falls ihre 'start_loc' im neuen Kapitel nicht existiert.
            
            final_npcs = global_npcs + copy.deepcopy(chapter_data.get('npcs', []))
            
            # 4. Config Struktur bauen
            full_config = {
                "meta": chapter_data['meta'],
                "vocabulary": StoryLoader._get_default_vocabulary(), # TODO: Auslagern
                "rooms": copy.deepcopy(chapter_data['rooms']),
                "objects": copy.deepcopy(chapter_data['objects']),
                "combinations": copy.deepcopy(chapter_data.get('combinations', [])),
                "narrative_matrix": copy.deepcopy(chapter_data.get('matrix', [])),
                "npcs": final_npcs
            }
            
            return full_config

        except ImportError as e:
            print(f"[ERROR] Konnte Kapitel '{chapter_module_path}' nicht laden: {e}")
            return None
        except Exception as e:
            print(f"[CRITICAL] Fehler im StoryLoader: {e}")
            return None

    @staticmethod
    def _get_default_vocabulary():
        # Temporär: Vocabulary hier hardcoden oder aus einer globalen Datei laden
        return {
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
            "skip_words": []
        }
