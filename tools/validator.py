import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from engine.schema import ConfigurationError, validate_game_config
from engine.story_loader import StoryLoader


DEFAULT_CHAPTER = "data.chapters.ep1_deep_zero.config"


def validate_integrity(chapter_source=DEFAULT_CHAPTER):
    print(f"--- Narratrix-Validierung: {chapter_source} ---")
    try:
        config = StoryLoader.load_chapter(chapter_source, raise_on_error=True)
        validate_game_config(config)
    except (ConfigurationError, ImportError, OSError, ValueError) as exc:
        print(f"❌ DATENFEHLER: {exc}")
        return 1

    warnings = []
    asset_dir = os.path.join(PROJECT_ROOT, "data", "assets", "images")
    for room_id, room in config["rooms"].items():
        image_id = room.get("img")
        if image_id and not any(
            os.path.exists(os.path.join(asset_dir, image_id + extension))
            for extension in (".png", ".jpg", ".jpeg")
        ):
            warnings.append(f"Raum '{room_id}': Bild '{image_id}' fehlt.")
    for npc in config["npcs"]:
        image_ids = []
        if npc.get("img"):
            image_ids.append(npc["img"])
        for state in npc.get("states", {}).values():
            image_id = state.get("visuals", {}).get("img")
            if image_id:
                image_ids.append(image_id)
        for image_id in image_ids:
            if not any(
                os.path.exists(os.path.join(asset_dir, image_id + extension))
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


if __name__ == "__main__":
    source = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CHAPTER
    raise SystemExit(validate_integrity(source))
