from __future__ import annotations

from pathlib import Path
import sys

from engine.schema import ConfigurationError, validate_game_config
from engine.story_loader import StoryLoader


PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
DEFAULT_CHAPTER: str = "data.chapters.ep1_deep_zero.config"


def validate_integrity(chapter_source: str = DEFAULT_CHAPTER) -> int:
    print(f"--- Narratrix-Validierung: {chapter_source} ---")
    try:
        config = StoryLoader.load_chapter(chapter_source, raise_on_error=True)
        if config is None:
            raise ConfigurationError("Kapitel konnte nicht geladen werden.")
        validate_game_config(config)
    except (ConfigurationError, ImportError, OSError, ValueError) as exc:
        print(f"❌ DATENFEHLER: {exc}")
        return 1

    warnings: list[str] = []
    asset_dir = PROJECT_ROOT / "data" / "assets" / "images"
    for room_id, room in config["rooms"].items():
        image_id = room.get("img")
        if image_id and not any(
            (asset_dir / f"{image_id}{extension}").exists()
            for extension in (".png", ".jpg", ".jpeg")
        ):
            warnings.append(f"Raum '{room_id}': Bild '{image_id}' fehlt.")
    for npc in config["npcs"]:
        image_ids: list[str] = []
        if npc.get("img"):
            image_ids.append(npc["img"])
        for state in npc.get("states", {}).values():
            image_id = state.get("visuals", {}).get("img")
            if image_id:
                image_ids.append(image_id)
        for image_id in image_ids:
            if not any(
                (asset_dir / f"{image_id}{extension}").exists()
                for extension in (".png", ".jpg", ".jpeg")
            ):
                warnings.append(f"NPC '{npc['id']}': Bild '{image_id}' fehlt.")

    meta = config["meta"]
    print(
        f"✅ {meta.get('name', chapter_source)}: "
        f"{len(config['rooms'])} Räume, {len(config['objects'])} Objekte, "
        f"{len(config['npcs'])} NPCs, "
        f"{len(config['narrative_matrix']) + len(config['events'])} Events, "
        f"{len(config['combinations'])} Rezepte."
    )
    for warning in warnings:
        print(f"⚠️  {warning}")
    return 0


def main() -> int:
    source = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CHAPTER
    return validate_integrity(source)


if __name__ == "__main__":
    raise SystemExit(main())
