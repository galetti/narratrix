import importlib
import copy
import sys

# FIX: Importiere aus 'common', nicht 'global'
try:
    from data.common.config import COMMON_CONFIG
except ImportError as e:
    print(f"[CRITICAL] Konnte Common-Layer nicht laden: {e}")
    # Fallback, damit das Spiel startet (wenn auch leer)
    COMMON_CONFIG = {"rooms": {}, "objects": {}, "npcs": [], "matrix": [], "combinations": []}

class StoryLoader:
    """
    Verwaltet das Laden und Zusammenführen von Common Daten (Layer 1)
    und Kapitel-Daten (Layer 2).
    """
    
    @staticmethod
    def load_chapter(chapter_module_path):
        try:
            # 1. Dynamischer Import des Kapitel-Configs (Layer 2)
            module = importlib.import_module(chapter_module_path)
            chapter_data = module.CHAPTER_CONFIG
            
            print(f"[SYSTEM] Lade Kapitel: {chapter_data['meta']['title']}")
            
            # 2. Daten Mergen (Layer 1 + Layer 2)
            
            # Räume zusammenführen (Dictionary Update)
            final_rooms = copy.deepcopy(COMMON_CONFIG.get('rooms', {}))
            final_rooms.update(copy.deepcopy(chapter_data.get('rooms', {})))
            
            # Objekte/Items zusammenführen (Dictionary Update)
            final_objects = copy.deepcopy(COMMON_CONFIG.get('objects', {}))
            final_objects.update(copy.deepcopy(chapter_data.get('objects', {})))
            
            # Kombinationen zusammenführen (Listen addieren)
            final_combinations = copy.deepcopy(COMMON_CONFIG.get('combinations', []))
            final_combinations.extend(copy.deepcopy(chapter_data.get('combinations', [])))
            
            # Matrix/Events zusammenführen (Listen addieren)
            final_matrix = copy.deepcopy(COMMON_CONFIG.get('matrix', []))
            final_matrix.extend(copy.deepcopy(chapter_data.get('matrix', [])))

            # NPCs zusammenführen (Listen addieren)
            final_npcs = copy.deepcopy(COMMON_CONFIG.get('npcs', [])) + copy.deepcopy(chapter_data.get('npcs', []))
            
            # 3. Verknüpfungspunkte (Hardcoded Logic für den Übergang)
            # Verbindet das Schiff (ship_cockpit) mit dem Startraum des Kapitels
            start_room = chapter_data['meta']['start_room']
            
            # Prüfen, ob Schiff und Startraum existieren, dann verbinden
            if 'ship_cockpit' in final_rooms and start_room in final_rooms:
                # A. Ausgang vom Schiff zur Station
                final_rooms['ship_cockpit']['exits']['out'] = start_room
                
                # B. Ausgang von der Station zum Schiff (FIX: Damit man die Kestrel findet)
                if 'exits' not in final_rooms[start_room]:
                    final_rooms[start_room]['exits'] = {}
                
                # Wir nennen den Ausgang 'dock' (im Vokabular unter 'out'/'dock' gemappt)
                final_rooms[start_room]['exits']['dock'] = 'ship_cockpit'
                
                # Optional: Hinweis in der Raumbeschreibung ergänzen, damit der Spieler es sieht
                # (Nur wenn noch nicht erwähnt)
                desc = final_rooms[start_room].get('desc', "")
                if "dock" not in desc.lower() and "schleuse" not in desc.lower():
                    final_rooms[start_room]['desc'] = desc + " Die Luftschleuse zum Dock (dock) ist grün beleuchtet."

            # 4. Finales Config bauen
            full_config = {
                "meta": chapter_data['meta'],
                "vocabulary": StoryLoader._get_default_vocabulary(),
                "rooms": final_rooms,
                "objects": final_objects,
                "combinations": final_combinations,
                "narrative_matrix": final_matrix,
                "npcs": final_npcs
            }
            
            return full_config

        except ImportError as e:
            print(f"[ERROR] Konnte Kapitel '{chapter_module_path}' nicht laden: {e}")
            return None
        except Exception as e:
            print(f"[CRITICAL] Fehler im StoryLoader: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def _get_default_vocabulary():
        # Zentrales Vokabular für alle Kapitel
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
                "down": ["d", "down", "unten", "wartung"],
                "out": ["raus", "out", "ausgang", "dock"] # Wichtig für das Schiff
            },
            "skip_words": []
        }
