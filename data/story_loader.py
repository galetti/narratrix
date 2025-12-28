import importlib
import copy
import sys

# FIX: Importiere aus 'common', nicht 'global'
try:
    from data.common.config import COMMON_CONFIG
except ImportError as e:
    print(f"[CRITICAL] Konnte Common-Layer nicht laden: {e}")
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
            # WICHTIG: Reload erzwingen, damit Änderungen im laufenden Prozess übernommen werden!
            importlib.reload(module)
            
            # Auch die Sub-Module (rooms, items, etc.) müssen evtl. neu geladen werden,
            # wenn sie im Config-Modul importiert wurden.
            # Da Config meistens 'from .rooms import ROOMS' macht, reicht reload(module) oft nicht,
            # wenn module.ROOMS eine direkte Referenz ist.
            # Wir müssen rekursiv reloaden oder die Struktur der Configs ändern.
            # Einfacher Hack: Wir verlassen uns darauf, dass Config bei Reload die Imports neu ausführt.
            # Besser: Wir reloaden explizit die bekannten Submodule des Kapitels.
            
            base_package = module.__package__
            if base_package:
                for sub in ['rooms', 'items', 'npcs', 'events', 'events_flavor']:
                    try:
                        sub_mod = importlib.import_module(f"{base_package}.{sub}")
                        importlib.reload(sub_mod)
                    except ImportError:
                        pass # Nicht jedes Kapitel hat alle Submodule
            
            # Config Modul selbst nochmal reloaden, um die aktualisierten Dicts zu holen
            importlib.reload(module)
            
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
            
            # 3. Dynamische Verknüpfung (Link System)
            links = chapter_data.get('links', [])
            
            if links:
                for link in links:
                    from_id = link.get('from_common')
                    direction = link.get('dir')
                    to_tag = link.get('to_chapter_tag')
                    
                    if from_id and direction and to_tag:
                        target_room_id = None
                        for r_id, room_data in final_rooms.items():
                            if to_tag in room_data.get("tags", []):
                                target_room_id = r_id
                                break
                        
                        if target_room_id and from_id in final_rooms:
                            if 'exits' not in final_rooms[from_id]: final_rooms[from_id]['exits'] = {}
                            final_rooms[from_id]['exits'][direction] = target_room_id
                            
                            if 'exits' not in final_rooms[target_room_id]: final_rooms[target_room_id]['exits'] = {}
                            final_rooms[target_room_id]['exits'][direction] = from_id
                            
                            print(f"[SYSTEM] Link erstellt: {from_id} --({direction})--> {target_room_id}")
                            
                            desc = final_rooms[target_room_id].get('desc', "")
                            if direction not in desc.lower():
                                final_rooms[target_room_id]['desc'] = desc + f" Ein Weg führt nach '{direction}'."

            else:
                docking_room_id = None
                for r_id, room_data in final_rooms.items():
                    if "common_dock" in room_data.get("tags", []):
                        docking_room_id = r_id
                        break
                
                if not docking_room_id:
                    docking_room_id = chapter_data['meta'].get('start_room')

                if docking_room_id and 'ship_cockpit' in final_rooms:
                    final_rooms['ship_cockpit']['exits']['out'] = docking_room_id
                    if 'exits' not in final_rooms[docking_room_id]: final_rooms[docking_room_id]['exits'] = {}
                    final_rooms[docking_room_id]['exits']['out'] = 'ship_cockpit'
                    
                    desc = final_rooms[docking_room_id].get('desc', "")
                    if "dock" not in desc.lower() and "schleuse" not in desc.lower():
                        final_rooms[docking_room_id]['desc'] = desc + " Die Luftschleuse zum Dock (out/dock) ist aktiv."

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
                "put": ["put", "legen", "stecken", "tun", "platziere", "stell", "packe", "fülle", "stellen", "stelle"],
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
                "hack": ["hack", "hacken", "zugriff", "system", "override"],
                "help": ["hilfe", "help", "h", "?", "commands", "befehle"]
            },
            "directions": {
                "north": ["n", "nord", "norden", "brücke"],
                "south": ["s", "süd", "süden", "kantine"],
                "east": ["e", "ost", "osten", "reaktor"],
                "west": ["w", "west", "westen", "schleuse"],
                "up": ["u", "up", "oben", "deck1"],
                "down": ["d", "down", "unten", "wartung"],
                "out": ["raus", "out", "ausgang", "dock", "schiff", "kestrel"] 
            },
            "skip_words": []
        }