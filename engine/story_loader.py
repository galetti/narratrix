import importlib
import copy
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class StoryLoader:
    
    @staticmethod
    def _load_common_config():
        try:
            module = importlib.import_module("data.common.config")
            importlib.reload(module)
            return module.COMMON_CONFIG
        except ImportError as e:
            print(f"[WARN] StoryLoader: Konnte Common-Layer nicht laden: {e}")
            return {"rooms": {}, "objects": {}, "npcs": [], "matrix": [], "events": [], "combinations": [], "quests": {}}

    @staticmethod
    def load_chapter(chapter_module_path):
        try:
            common_data = StoryLoader._load_common_config()
            module = importlib.import_module(chapter_module_path)
            importlib.reload(module)
            
            base_package = module.__package__
            if base_package:
                for sub in ['rooms', 'items', 'npcs', 'events', 'events_flavor', 'config', 'quests']:
                    try:
                        sub_mod = importlib.import_module(f"{base_package}.{sub}")
                        importlib.reload(sub_mod)
                    except ImportError: pass
            
            chapter_data = module.CHAPTER_CONFIG
            
            final_rooms = copy.deepcopy(common_data.get('rooms', {}))
            final_rooms.update(copy.deepcopy(chapter_data.get('rooms', {})))
            
            final_objects = copy.deepcopy(common_data.get('objects', {}))
            final_objects.update(copy.deepcopy(chapter_data.get('objects', {})))
            
            final_combinations = copy.deepcopy(common_data.get('combinations', []))
            final_combinations.extend(copy.deepcopy(chapter_data.get('combinations', [])))
            
            final_matrix = copy.deepcopy(common_data.get('matrix', []))
            final_matrix.extend(copy.deepcopy(chapter_data.get('matrix', [])))

            final_events = copy.deepcopy(common_data.get('events', []))
            final_events.extend(copy.deepcopy(chapter_data.get('events', [])))

            final_npcs = copy.deepcopy(common_data.get('npcs', [])) + copy.deepcopy(chapter_data.get('npcs', []))
            
            final_quests = copy.deepcopy(common_data.get('quests', {}))
            final_quests.update(copy.deepcopy(chapter_data.get('quests', {})))

            StoryLoader._process_links(chapter_data.get('links', []), final_rooms, chapter_data.get('meta', {}))

            full_config = {
                "meta": chapter_data.get('meta', {}),
                "vocabulary": StoryLoader._get_default_vocabulary(),
                "rooms": final_rooms,
                "objects": final_objects,
                "combinations": final_combinations,
                "narrative_matrix": final_matrix,
                "events": final_events,
                "npcs": final_npcs,
                "quests": final_quests
            }
            
            return full_config

        except ImportError as e:
            print(f"[ERROR] StoryLoader: Konnte Kapitel '{chapter_module_path}' nicht importieren: {e}")
            return None
        except Exception as e:
            print(f"[FATAL] StoryLoader: Fehler: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def _process_links(links, rooms, meta):
        if links:
            for link in links:
                from_id = link.get('from_common')
                direction = link.get('dir')
                to_tag = link.get('to_chapter_tag')
                if from_id and direction and to_tag:
                    target_room_id = None
                    for r_id, room_data in rooms.items():
                        if to_tag in room_data.get("tags", []):
                            target_room_id = r_id; break
                    if target_room_id and from_id in rooms:
                        if 'exits' not in rooms[from_id]: rooms[from_id]['exits'] = {}
                        rooms[from_id]['exits'][direction] = target_room_id
                        if 'exits' not in rooms[target_room_id]: rooms[target_room_id]['exits'] = {}

    @staticmethod
    def _get_default_vocabulary():
        return {
            "verbs": {
                "inventory": ["i", "inv", "tasche", "rucksack", "ausrüstung", "inventar"],
                "look": ["schau", "l", "x", "untersuche", "betrachte", "lies", "scan", "status", "ansehen"],
                # WICHTIG: "klettere" hier entfernt!
                "move": ["gehe", "go", "lauf", "schwebe", "wandere", "steig", "bewege"],
                "take": ["nimm", "greif", "einstecken", "sammle", "aufheben", "nehmen"],
                "drop": ["drop", "fallenlassen", "abwerfen", "hinlegen", "ablegen", "entferne", "lass"],
                "put": ["put", "legen", "stecken", "tun", "platziere", "stell", "packe", "fülle", "stellen", "stelle"],
                "give": ["gib", "geben", "reich", "schenke", "give", "versorge"],
                "use": ["benutze", "opfere", "anwenden", "kombiniere", "fülle", "injiziere", "nutze"],
                "talk": ["rede", "sprich", "frag", "befrage", "kommuniziere", "funk", "sagen"],
                "open": ["öffne", "aufmachen", "zugriff"],
                "break": ["brich", "zerstöre", "eintreten", "force", "zerschlage"],
                "fix": ["repariere", "reinige", "patch", "löte", "fix", "flicken", "verbinde"],
                "wait": ["warte", "bete", "z", "ruhen"],
                "save": ["speichern", "sichern", "save"],
                "load": ["laden", "load"],
                "oracle": ["orakel", "vorhersage", "vision", "prognose", "sehe", "log"],
                "map": ["map", "karte", "plan", "radar"],
                "hack": ["hack", "hacken", "zugriff", "system", "override"],
                "help": ["hilfe", "help", "h", "?", "commands", "befehle"],
                "hide": ["verstecke", "hide", "krieche", "duck"],
                "journal": ["journal", "logbuch", "aufgaben", "quests", "ziele", "j"],
                # WICHTIG: "klettere" hier hinzugefügt!
                "climb": ["klettere", "climb", "steige", "erklimme"]
            },
            "directions": {
                "north": ["n", "nord", "norden"],
                "south": ["s", "süd", "süden"],
                "east": ["e", "ost", "osten"],
                "west": ["w", "west", "westen"],
                "up": ["u", "up", "oben", "rauf"],
                "down": ["d", "down", "unten", "runter"],
                "northeast": ["ne", "no", "nordost", "nordosten"],
                "northwest": ["nw", "nordwest", "nordwesten"],
                "southeast": ["se", "so", "südost", "südosten"],
                "southwest": ["sw", "südwest", "südwesten"]
            },
            "skip_words": ["der", "die", "das", "dem", "den", "ein", "eine", "einen", "mit", "zum", "zur", "im", "am", "auf", "in", "aus", "out"]
        }