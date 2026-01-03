import importlib
import copy
import sys
import os

# Wir stellen sicher, dass das Root-Verzeichnis im Pfad ist
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class StoryLoader:
    """
    Zentrale Klasse zum Laden und Zusammenführen von Spieldaten.
    Ersetzt die alte Version in data/story_loader.py.
    """
    
    @staticmethod
    def _load_common_config():
        """Lädt die Basiskonfiguration (Layer 1)."""
        try:
            # Versuche, das Modul neu zu laden, falls es bereits im Cache ist
            module = importlib.import_module("data.common.config")
            importlib.reload(module)
            return module.COMMON_CONFIG
        except ImportError as e:
            print(f"[CRITICAL] StoryLoader: Konnte Common-Layer nicht laden: {e}")
            # Fallback: Leeres Gerüst, damit das Spiel nicht sofort abstürzt
            return {"rooms": {}, "objects": {}, "npcs": [], "matrix": [], "combinations": []}

    @staticmethod
    def load_chapter(chapter_module_path):
        """
        Lädt ein Kapitel (Layer 2) und führt es mit dem Common Layer (Layer 1) zusammen.
        
        Args:
            chapter_module_path (str): Python-Pfad zum Kapitel-Config (z.B. "data.chapters.ep1.config")
        """
        try:
            # 1. Common Layer laden
            common_data = StoryLoader._load_common_config()

            # 2. Kapitel-Modul laden
            module = importlib.import_module(chapter_module_path)
            importlib.reload(module) # Wichtig für Hot-Reloading während der Entwicklung
            
            # Auch Sub-Module (Rooms, Items etc.) neu laden, falls sie importiert wurden
            base_package = module.__package__
            if base_package:
                for sub in ['rooms', 'items', 'npcs', 'events', 'events_flavor', 'config']:
                    try:
                        sub_mod = importlib.import_module(f"{base_package}.{sub}")
                        importlib.reload(sub_mod)
                    except ImportError:
                        pass # Nicht jedes Kapitel hat alle Sub-Dateien
            
            chapter_data = module.CHAPTER_CONFIG
            print(f"[SYSTEM] StoryLoader: Lade Kapitel '{chapter_data.get('meta', {}).get('title', 'Unbekannt')}'")
            
            # 3. Daten Zusammenführen (Deep Copy ist wichtig, um Originaldaten nicht zu verändern)
            
            # A. Räume (Dict Update)
            final_rooms = copy.deepcopy(common_data.get('rooms', {}))
            final_rooms.update(copy.deepcopy(chapter_data.get('rooms', {})))
            
            # B. Objekte (Dict Update)
            final_objects = copy.deepcopy(common_data.get('objects', {}))
            final_objects.update(copy.deepcopy(chapter_data.get('objects', {})))
            
            # C. Listen (Append)
            final_combinations = copy.deepcopy(common_data.get('combinations', []))
            final_combinations.extend(copy.deepcopy(chapter_data.get('combinations', [])))
            
            final_matrix = copy.deepcopy(common_data.get('matrix', []))
            final_matrix.extend(copy.deepcopy(chapter_data.get('matrix', [])))

            final_npcs = copy.deepcopy(common_data.get('npcs', [])) + copy.deepcopy(chapter_data.get('npcs', []))
            
            # 4. Verknüpfungen (Links) verarbeiten
            StoryLoader._process_links(chapter_data.get('links', []), final_rooms, chapter_data.get('meta', {}))

            # 5. Finales Config-Objekt erstellen
            full_config = {
                "meta": chapter_data.get('meta', {}),
                "vocabulary": StoryLoader._get_default_vocabulary(),
                "rooms": final_rooms,
                "objects": final_objects,
                "combinations": final_combinations,
                "narrative_matrix": final_matrix,
                "npcs": final_npcs
            }
            
            return full_config

        except ImportError as e:
            print(f"[ERROR] StoryLoader: Konnte Kapitel '{chapter_module_path}' nicht importieren: {e}")
            return None
        except Exception as e:
            print(f"[FATAL] StoryLoader: Unerwarteter Fehler: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def _process_links(links, rooms, meta):
        """Verarbeitet die Verbindungen zwischen Common- und Chapter-Räumen."""
        if links:
            for link in links:
                from_id = link.get('from_common')
                direction = link.get('dir')
                to_tag = link.get('to_chapter_tag')
                
                if from_id and direction and to_tag:
                    # Zielraum im Kapitel suchen (basierend auf Tag)
                    target_room_id = None
                    for r_id, room_data in rooms.items():
                        if to_tag in room_data.get("tags", []):
                            target_room_id = r_id
                            break
                    
                    if target_room_id and from_id in rooms:
                        # Hinweg
                        if 'exits' not in rooms[from_id]: rooms[from_id]['exits'] = {}
                        rooms[from_id]['exits'][direction] = target_room_id
                        
                        # Rückweg (wir nutzen denselben Key, Synonyme regelt der Parser)
                        if 'exits' not in rooms[target_room_id]: rooms[target_room_id]['exits'] = {}
                        rooms[target_room_id]['exits'][direction] = from_id
                        
                        print(f"[SYSTEM] Link etabliert: {from_id} <-> {target_room_id}")
        else:
            # Legacy Fallback Logic (falls keine expliziten Links definiert sind)
            docking_id = None
            for r_id, room_data in rooms.items():
                if "common_dock" in room_data.get("tags", []):
                    docking_id = r_id
                    break
            
            if not docking_id:
                docking_id = meta.get('start_room')

            if docking_id and 'ship_cockpit' in rooms:
                # Verbindung Kestrel <-> Station
                if 'exits' not in rooms['ship_cockpit']: rooms['ship_cockpit']['exits'] = {}
                rooms['ship_cockpit']['exits']['out'] = docking_id
                
                if 'exits' not in rooms[docking_id]: rooms[docking_id]['exits'] = {}
                rooms[docking_id]['exits']['out'] = 'ship_cockpit'

    @staticmethod
    def _get_default_vocabulary():
        return {
            "verbs": {
                "look": ["schau", "l", "x", "untersuche", "betrachte", "lies", "scan", "status", "ansehen"],
                "move": ["gehe", "go", "lauf", "klettere", "schwebe", "wandere", "steig", "bewege"],
                "take": ["nimm", "greif", "einstecken", "sammle", "aufheben", "nehmen"],
                "drop": ["drop", "fallenlassen", "abwerfen", "hinlegen", "ablegen", "entferne", "lass"],
                "put": ["put", "legen", "stecken", "tun", "platziere", "stell", "packe", "fülle", "stellen", "stelle"],
                "give": ["gib", "geben", "reich", "schenke", "give", "versorge"],
                "use": ["benutze", "opfere", "anwenden", "kombiniere", "fülle", "injiziere", "nutze"],
                "talk": ["rede", "sprich", "frag", "befrage", "kommuniziere", "funk", "sagen"],
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
                "help": ["hilfe", "help", "h", "?", "commands", "befehle"],
                "hide": ["verstecke", "hide", "krieche", "duck"]
            },
            "directions": {
                "north": ["n", "nord", "norden"],
                "south": ["s", "süd", "süden"],
                "east": ["e", "ost", "osten"],
                "west": ["w", "west", "westen"],
                "up": ["u", "up", "oben", "rauf"],
                "down": ["d", "down", "unten", "runter"],
                "out": ["raus", "out", "ausgang", "dock", "schiff", "kestrel", "weg"]
            },
            "skip_words": ["der", "die", "das", "dem", "den", "ein", "eine", "einen", "mit", "zum", "zur", "in", "im", "am", "auf"]
        }