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
            
            # 3. Dynamische Verknüpfung (Docking System)
            # Wir suchen einen Raum im Kapitel, der das Tag "common_dock" besitzt.
            
            docking_room_id = None
            
            # Suche nach Tag
            for r_id, room_data in final_rooms.items():
                if "common_dock" in room_data.get("tags", []):
                    docking_room_id = r_id
                    print(f"[SYSTEM] Docking-Punkt gefunden: {r_id}")
                    break
            
            # Fallback: Startraum (falls kein Dock definiert wurde, damit man nicht festsitzt)
            if not docking_room_id:
                docking_room_id = chapter_data['meta'].get('start_room')
                print(f"[SYSTEM] Kein Dock-Tag gefunden. Nutze Startraum als Fallback: {docking_room_id}")

            # Verbindung herstellen
            if docking_room_id and 'ship_cockpit' in final_rooms:
                
                # A. Ausgang vom Schiff zur Station (out -> Docking Room)
                final_rooms['ship_cockpit']['exits']['out'] = docking_room_id
                
                # B. Ausgang von der Station zum Schiff
                # WICHTIG: Wir nutzen den Key 'out', da unser Parser 'dock' zu 'out' übersetzt.
                if 'exits' not in final_rooms[docking_room_id]:
                    final_rooms[docking_room_id]['exits'] = {}
                
                final_rooms[docking_room_id]['exits']['out'] = 'ship_cockpit'
                
                # C. Flavor Text hinzufügen (damit der Spieler den Ausgang bemerkt)
                desc = final_rooms[docking_room_id].get('desc', "")
                # Wir prüfen, ob schon ein Hinweis existiert, um Doppelungen zu vermeiden
                if "dock" not in desc.lower() and "schleuse" not in desc.lower():
                    final_rooms[docking_room_id]['desc'] = desc + " Die Luftschleuse zum Dock (Befehl: dock/out) ist aktiv."

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
                "out": ["raus", "out", "ausgang", "dock", "schiff", "kestrel"] # Erweitert um Schiff/Kestrel
            },
            "skip_words": []
        }