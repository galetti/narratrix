from engine.constants import LOC_INVENTORY


def is_directly_reachable(game, entity, upward_reach=1, allow_below=False):
    """Return whether the player can physically interact with an entity."""

    if entity.get("location") == LOC_INVENTORY:
        return True
    if entity.get("location") != game.location:
        return False
    level = int(entity.get("level", 0))
    if level < game.elevation:
        return allow_below
    return level <= game.elevation + upward_reach


def reach_error(game, entity):
    level = int(entity.get("level", 0))
    if level > game.elevation:
        return (
            f"{entity.get('name', 'Das Ziel')} ist auf Ebene {level}. "
            "Du kommst von hier nicht heran."
        )
    return f"{entity.get('name', 'Das Ziel')} ist von hier nicht erreichbar."
