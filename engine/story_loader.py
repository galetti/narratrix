from __future__ import annotations

import copy
import importlib
import importlib.util
import json
import logging
import os
from pathlib import Path
from typing import Any

from engine.schema import (
    ConfigurationError,
    ModuleConfigData,
    VocabularyData,
    validate_game_config,
)

logger = logging.getLogger(__name__)
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
DEFAULT_MODULES_DIR: Path = PROJECT_ROOT / "data" / "modules"


def _empty_common_config() -> dict[str, Any]:
    return {
        "rooms": {},
        "objects": {},
        "npcs": [],
        "matrix": [],
        "events": [],
        "combinations": [],
        "quests": {},
    }


class StoryLoader:
    """Load and merge module-scoped common and chapter content into one validated config."""

    @staticmethod
    def discover_modules(modules_dir: Path | None = None) -> dict[str, ModuleConfigData]:
        """Discover all game modules under data/modules/<id>/module.py."""

        target_dir = modules_dir or DEFAULT_MODULES_DIR
        if not target_dir.is_dir():
            return {}

        discovered: dict[str, ModuleConfigData] = {}
        is_default_dir = target_dir.resolve() == DEFAULT_MODULES_DIR.resolve()
        for entry in sorted(target_dir.iterdir(), key=lambda p: p.name):
            if not entry.is_dir() or entry.name.startswith((".", "_")):
                continue
            manifest_path = entry / "module.py"
            if not manifest_path.is_file():
                continue
            try:
                if is_default_dir:
                    mod = importlib.import_module(f"data.modules.{entry.name}.module")
                    mod = importlib.reload(mod)
                else:
                    spec = importlib.util.spec_from_file_location(
                        f"_narratrix_module_{entry.name}", manifest_path
                    )
                    if spec is None or spec.loader is None:
                        continue
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                raw_cfg = getattr(mod, "MODULE_CONFIG", getattr(mod, "MODULE_META", None))
                if not isinstance(raw_cfg, dict):
                    continue
                cfg: ModuleConfigData = copy.deepcopy(raw_cfg)  # type: ignore[assignment]
                mod_id = str(cfg.get("id") or entry.name)
                cfg["id"] = mod_id
                if isinstance(cfg.get("start_chapter"), str) and cfg["start_chapter"]:
                    discovered[mod_id] = cfg
            except (ImportError, OSError, AttributeError, TypeError, ValueError) as exc:
                logger.warning("StoryLoader: Modul '%s' konnte nicht geladen werden: %s", entry.name, exc)
        return discovered

    @staticmethod
    def get_module(
        module_id: str, modules_dir: Path | None = None
    ) -> ModuleConfigData | None:
        return StoryLoader.discover_modules(modules_dir).get(module_id)

    @staticmethod
    def resolve_start_chapter(
        module_or_chapter: str, modules_dir: Path | None = None
    ) -> str:
        modules = StoryLoader.discover_modules(modules_dir)
        if module_or_chapter in modules:
            return str(modules[module_or_chapter]["start_chapter"])
        return module_or_chapter

    @staticmethod
    def _infer_module_meta(chapter_source: str) -> ModuleConfigData | None:
        if chapter_source.startswith("data.modules."):
            parts = chapter_source.split(".")
            if len(parts) >= 3:
                return StoryLoader.get_module(parts[2])
        return None

    @staticmethod
    def _load_common_config(common_source: str | None = None) -> dict[str, Any]:
        if not common_source:
            return _empty_common_config()
        try:
            module = importlib.import_module(common_source)
            importlib.reload(module)
            return copy.deepcopy(module.COMMON_CONFIG)
        except ImportError as exc:
            logger.warning("StoryLoader: Common-Layer '%s' nicht verfügbar: %s", common_source, exc)
            return _empty_common_config()

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
    def _merge_by_id(base: list[dict[str, Any]], overlay: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Merge entity lists; chapter entries replace common entries by ID."""

        merged: list[dict[str, Any]] = []
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
    def load_chapter(
        chapter_source: str, raise_on_error: bool = False
    ) -> dict[str, Any] | None:
        try:
            chapter_data, module_id = StoryLoader._load_chapter_data(chapter_source)
            parent_module = StoryLoader._infer_module_meta(chapter_source)

            if "common_module" in chapter_data:
                common_source = chapter_data.get("common_module")
            elif parent_module is not None:
                common_source = parent_module.get("common_module")
            else:
                common_source = None

            common_data = StoryLoader._load_common_config(common_source)

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

            theme_spec = (
                chapter_data.get("theme")
                or meta.get("theme")
                or (parent_module.get("theme") if parent_module else None)
                or "default"
            )
            asset_dir = (
                chapter_data.get("asset_dir")
                or (parent_module.get("asset_dir") if parent_module else None)
            )

            full_config = {
                "meta": meta,
                "settings": copy.deepcopy(chapter_data.get("settings", {})),
                "theme": copy.deepcopy(theme_spec),
                "common_module": common_source,
                "asset_dir": asset_dir,
                "module_id": parent_module.get("id") if parent_module else None,
                "language": str(
                    chapter_data.get("settings", {}).get("language")
                    or meta.get("language")
                    or "de"
                ),
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

        except (
            ImportError,
            OSError,
            json.JSONDecodeError,
            AttributeError,
            TypeError,
            ValueError,
            ConfigurationError,
        ) as exc:
            logger.error("StoryLoader: Kapitel '%s' ist ungültig: %s", chapter_source, exc)
            if raise_on_error:
                raise
            return None

    @staticmethod
    def _process_links(links: list[dict[str, Any]], rooms: dict[str, dict[str, Any]]) -> None:
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
    def _get_default_vocabulary() -> VocabularyData:
        return {
            "verbs": {
                "inventory": ["i", "inv", "tasche", "rucksack", "ausrüstung", "inventar"],
                "look": ["schau", "l", "x", "untersuche", "betrachte", "lies", "scan", "status", "ansehen"],
                "move": ["gehe", "go", "lauf", "schwebe", "wandere", "steig", "bewege", "betrete", "betreten"],
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
                "listen": ["lausche", "lauschen", "horche", "horchen", "listen", "höre", "hören", "belausche", "belauschen"],
                "journal": ["journal", "logbuch", "aufgaben", "quests", "ziele", "j"],
                "climb": ["klettere", "climb", "steige", "erklimme"],
            },
            "directions": {
                "north": ["n", "nord", "norden"],
                "south": ["s", "süd", "süden"],
                "east": ["e", "o", "ost", "osten"],
                "west": ["w", "west", "westen"],
                "up": ["u", "up", "oben", "rauf", "hoch"],
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
