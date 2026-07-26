import copy
import importlib
import json
import os
from typing import Any

from engine.schema import ConfigurationError, validate_game_config


class StoryLoader:
    """Load and merge common and chapter content into one validated config."""

    @staticmethod
    def _load_common_config() -> dict[str, Any]:
        try:
            module = importlib.import_module("data.common.config")
            importlib.reload(module)
            return copy.deepcopy(module.COMMON_CONFIG)
        except ImportError as exc:
            print(f"[WARN] StoryLoader: Common-Layer nicht verfügbar: {exc}")
            return {
                "rooms": {},
                "objects": {},
                "npcs": [],
                "matrix": [],
                "events": [],
                "combinations": [],
                "quests": {},
            }

    @staticmethod
    def _load_chapter_data(chapter_source: str) -> tuple[dict[str, Any], str]:
        if os.path.isfile(chapter_source) or chapter_source.lower().endswith(".json"):
            with open(chapter_source, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            module_id = os.path.abspath(chapter_source)
            return data, module_id

        module = importlib.import_module(chapter_source)
        module = importlib.reload(module)
        return copy.deepcopy(module.CHAPTER_CONFIG), chapter_source

    @staticmethod
    def _merge_by_id(base: list[dict], overlay: list[dict]) -> list[dict]:
        """Merge entity lists; chapter entries replace common entries by ID."""

        merged: list[dict] = []
        positions: dict[str, int] = {}
        for entry in copy.deepcopy(base) + copy.deepcopy(overlay):
            entry_id = entry.get("id")
            if entry_id and entry_id in positions:
                merged[positions[entry_id]] = entry
            else:
                if entry_id:
                    positions[entry_id] = len(merged)
                merged.append(entry)
        return merged

    @staticmethod
    def load_chapter(chapter_source: str, raise_on_error: bool = False):
        try:
            common_data = StoryLoader._load_common_config()
            chapter_data, module_id = StoryLoader._load_chapter_data(chapter_source)

            rooms = copy.deepcopy(common_data.get("rooms", {}))
            rooms.update(copy.deepcopy(chapter_data.get("rooms", {})))

            objects = copy.deepcopy(common_data.get("objects", {}))
            objects.update(copy.deepcopy(chapter_data.get("objects", {})))

            combinations = copy.deepcopy(common_data.get("combinations", []))
            combinations.extend(copy.deepcopy(chapter_data.get("combinations", [])))

            common_matrix = common_data.get("narrative_matrix", common_data.get("matrix", []))
            chapter_matrix = chapter_data.get("narrative_matrix", chapter_data.get("matrix", []))
            matrix = StoryLoader._merge_by_id(common_matrix, chapter_matrix)
            events = StoryLoader._merge_by_id(
                common_data.get("events", []), chapter_data.get("events", [])
            )
            npcs = StoryLoader._merge_by_id(
                common_data.get("npcs", []), chapter_data.get("npcs", [])
            )

            quests = copy.deepcopy(common_data.get("quests", {}))
            quests.update(copy.deepcopy(chapter_data.get("quests", {})))

            meta = copy.deepcopy(chapter_data.get("meta", {}))
            meta["module"] = module_id
            StoryLoader._process_links(chapter_data.get("links", []), rooms)

            full_config = {
                "meta": meta,
                "settings": copy.deepcopy(chapter_data.get("settings", {})),
                "vocabulary": StoryLoader._get_default_vocabulary(),
                "rooms": rooms,
                "objects": objects,
                "combinations": combinations,
                "narrative_matrix": matrix,
                "events": events,
                "npcs": npcs,
                "quests": quests,
            }
            return validate_game_config(full_config)

        except (ImportError, OSError, json.JSONDecodeError, AttributeError, ConfigurationError) as exc:
            print(f"[ERROR] StoryLoader: Kapitel '{chapter_source}' ist ungültig: {exc}")
            if raise_on_error:
                raise
            return None
        except Exception as exc:
            print(f"[FATAL] StoryLoader: Unerwarteter Fehler: {exc}")
            if raise_on_error:
                raise
            return None

    @staticmethod
    def _process_links(links: list[dict], rooms: dict[str, dict]) -> None:
        for link in links:
            from_id = link.get("from_common")
            direction = link.get("dir")
            to_tag = link.get("to_chapter_tag")
            if not (from_id and direction and to_tag):
                continue

            target_room_id = next(
                (room_id for room_id, room in rooms.items() if to_tag in room.get("tags", [])),
                None,
            )
            if not target_room_id or from_id not in rooms:
                raise ConfigurationError(
                    f"Layer-Link '{from_id}:{direction}' kann Tag '{to_tag}' nicht auflösen."
                )

            rooms[from_id].setdefault("exits", {})[direction] = target_room_id
            reverse_direction = link.get("reverse_dir")
            if reverse_direction:
                rooms[target_room_id].setdefault("exits", {})[reverse_direction] = from_id

    @staticmethod
    def _get_default_vocabulary():
        return {
            "verbs": {
                "inventory": ["i", "inv", "tasche", "rucksack", "ausrüstung", "inventar"],
                "look": ["schau", "l", "x", "untersuche", "betrachte", "lies", "scan", "status", "ansehen"],
                "move": ["gehe", "go", "lauf", "schwebe", "wandere", "steig", "bewege"],
                "take": ["nimm", "greif", "einstecken", "sammle", "aufheben", "nehmen"],
                "drop": ["drop", "fallenlassen", "abwerfen", "hinlegen", "ablegen", "entferne", "lass"],
                "put": ["put", "legen", "stecken", "tun", "platziere", "stell", "packe", "stellen", "stelle"],
                "give": ["gib", "geben", "reich", "schenke", "give", "versorge"],
                "use": ["benutze", "opfere", "anwenden", "kombiniere", "fülle", "injiziere", "nutze"],
                "talk": ["rede", "sprich", "frag", "befrage", "kommuniziere", "funk", "sagen"],
                "open": ["öffne", "aufmachen"],
                "close": ["schließe", "zumachen", "schliess", "close"],
                "break": ["brich", "zerstöre", "eintreten", "force", "zerschlage"],
                "fix": ["repariere", "reinige", "patch", "löte", "fix", "flicken", "verbinde"],
                "wait": ["warte", "bete", "z", "ruhen"],
                "save": ["speichern", "sichern", "save"],
                "load": ["laden", "load"],
                "oracle": ["orakel", "vorhersage", "vision", "prognose", "sehe", "log"],
                "map": ["map", "karte", "plan", "radar"],
                "hack": ["hack", "hacken", "system", "override"],
                "help": ["hilfe", "help", "h", "?", "commands", "befehle"],
                "hide": ["verstecke", "hide", "krieche", "duck"],
                "journal": ["journal", "logbuch", "aufgaben", "quests", "ziele", "j"],
                "climb": ["klettere", "climb", "steige", "erklimme"],
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
                "southwest": ["sw", "südwest", "südwesten"],
                "out": ["raus", "draußen", "hinaus"],
            },
            "skip_words": [
                "der",
                "die",
                "das",
                "dem",
                "den",
                "ein",
                "eine",
                "einen",
                "mit",
                "zum",
                "zur",
                "im",
                "am",
                "auf",
                "in",
                "aus",
            ],
        }
