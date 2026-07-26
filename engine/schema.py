"""Validation helpers for Narratrix chapter data.

The runtime deliberately uses plain dictionaries for author-friendly content,
but all modules share this single contract. Invalid references are rejected
while a chapter is loaded instead of failing much later during play.
"""

from __future__ import annotations

from typing import Any, Iterable

from engine.constants import LOC_INVENTORY, LOC_VOID


SUPPORTED_TRIGGERS = {"time", "location", "condition", "complex", "manual"}
SUPPORTED_CONDITIONS = {
    "knowledge",
    "location",
    "item_location",
    "npc_state",
    "quest_state",
    "stability",
    "event_triggered",
    "inventory",
}
SUPPORTED_EFFECTS = {
    "move_npc",
    "teleport_npc",
    "set_state",
    "set_npc_state",
    "learn",
    "spawn_item",
    "receive_item",
    "update_object",
    "damage_stability",
    "game_over",
    "trigger_event",
    "message",
    "quest_start",
    "quest_update",
    "quest_complete",
    "quest_fail",
    "load_chapter",
}


class ConfigurationError(ValueError):
    """Raised when chapter data violates the shared engine contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ConfigurationError(message)


def _unique_ids(entries: Iterable[dict[str, Any]], label: str) -> set[str]:
    ids: set[str] = set()
    for entry in entries:
        entry_id = entry.get("id")
        _require(isinstance(entry_id, str) and entry_id, f"{label} ohne gültige ID.")
        _require(entry_id not in ids, f"Doppelte {label}-ID '{entry_id}'.")
        ids.add(entry_id)
    return ids


def _validate_condition(condition: Any, context: str) -> None:
    if isinstance(condition, str):
        _require(bool(condition), f"{context}: Leere Wissensbedingung.")
        return
    _require(isinstance(condition, dict), f"{context}: Bedingung muss String oder Dict sein.")
    condition_type = condition.get("type")
    _require(
        condition_type in SUPPORTED_CONDITIONS,
        f"{context}: Unbekannter Bedingungstyp '{condition_type}'.",
    )


def _validate_effect(effect: Any, context: str) -> None:
    _require(isinstance(effect, dict), f"{context}: Effekt muss ein Dict sein.")
    effect_type = effect.get("type")
    _require(
        effect_type in SUPPORTED_EFFECTS,
        f"{context}: Unbekannter Effekttyp '{effect_type}'.",
    )


def validate_game_config(config: dict[str, Any]) -> dict[str, Any]:
    """Validate and return a normalized runtime configuration."""

    _require(isinstance(config, dict), "Konfiguration muss ein Dict sein.")
    rooms = config.get("rooms")
    objects = config.get("objects")
    npcs = config.get("npcs")
    _require(isinstance(rooms, dict) and rooms, "Kapitel benötigt mindestens einen Raum.")
    _require(isinstance(objects, dict), "'objects' muss ein Dict sein.")
    _require(isinstance(npcs, list), "'npcs' muss eine Liste sein.")

    room_ids = set(rooms)
    for room_id, room in rooms.items():
        _require(isinstance(room, dict), f"Raum '{room_id}' muss ein Dict sein.")
        _require(room.get("id") == room_id, f"Raum-Schlüssel und ID weichen ab: '{room_id}'.")
        _require(bool(room.get("name")), f"Raum '{room_id}' hat keinen Namen.")
        _require(isinstance(room.get("exits", {}), dict), f"Raum '{room_id}': exits muss Dict sein.")
        for direction, target in room.get("exits", {}).items():
            _require(target in room_ids, f"Raum '{room_id}': Exit '{direction}' -> '{target}' fehlt.")

    object_ids = set(objects)
    resource_ids: set[str] = set()
    for object_id, obj in objects.items():
        _require(isinstance(obj, dict), f"Objekt '{object_id}' muss ein Dict sein.")
        _require(obj.get("id") == object_id, f"Objekt-Schlüssel und ID weichen ab: '{object_id}'.")
        _require(bool(obj.get("name")), f"Objekt '{object_id}' hat keinen Namen.")
        if obj.get("resource_id"):
            resource_ids.add(obj["resource_id"])

    npc_ids = _unique_ids(npcs, "NPC")
    valid_locations = room_ids | object_ids | {LOC_INVENTORY, LOC_VOID}
    for object_id, obj in objects.items():
        _require(
            obj.get("location") in valid_locations,
            f"Objekt '{object_id}' hat ungültige Location '{obj.get('location')}'.",
        )
    for npc in npcs:
        _require(
            npc.get("location") in room_ids,
            f"NPC '{npc['id']}' hat ungültige Location '{npc.get('location')}'.",
        )

    quests = config.get("quests", {})
    _require(isinstance(quests, dict), "'quests' muss ein Dict sein.")
    for quest_id, quest in quests.items():
        _require(isinstance(quest, dict), f"Quest '{quest_id}' muss ein Dict sein.")
        stages = quest.get("stages", {})
        _require(isinstance(stages, dict) and stages, f"Quest '{quest_id}' benötigt Stages.")
        normalized_stages: dict[int, str] = {}
        for stage, description in stages.items():
            try:
                normalized_stage = int(stage)
            except (TypeError, ValueError) as exc:
                raise ConfigurationError(
                    f"Quest '{quest_id}' hat ungültige Stage '{stage}'."
                ) from exc
            normalized_stages[normalized_stage] = str(description)
        quest["stages"] = normalized_stages

    events = list(config.get("narrative_matrix", [])) + list(config.get("events", []))
    event_ids = _unique_ids(events, "Event")
    for event in events:
        event_id = event["id"]
        trigger = event.get("trigger", "manual")
        _require(trigger in SUPPORTED_TRIGGERS, f"Event '{event_id}': Trigger '{trigger}' unbekannt.")
        if "origin_id" in event:
            _require(
                event["origin_id"] in room_ids,
                f"Event '{event_id}': Origin '{event['origin_id']}' fehlt.",
            )
        if trigger == "location":
            target = event.get("location", event.get("value"))
            _require(target in room_ids, f"Event '{event_id}': Zielraum '{target}' fehlt.")
        if trigger == "condition":
            _validate_condition(event.get("condition"), f"Event '{event_id}'")
        elif "condition" in event:
            _validate_condition(event["condition"], f"Event '{event_id}'")
        if trigger == "complex":
            conditions = event.get("conditions")
            _require(isinstance(conditions, list) and conditions, f"Event '{event_id}': conditions fehlen.")
            for index, condition in enumerate(conditions):
                _validate_condition(condition, f"Event '{event_id}' Bedingung #{index}")
        effects = event.get("effects", [])
        if not isinstance(effects, list):
            effects = [effects]
        for index, effect in enumerate(effects):
            _validate_effect(effect, f"Event '{event_id}' Effekt #{index}")

    known_entity_ids = object_ids | npc_ids | resource_ids
    combinations = config.get("combinations", [])
    _require(isinstance(combinations, list), "'combinations' muss eine Liste sein.")
    for index, recipe in enumerate(combinations):
        context = f"Rezept #{index}"
        _require(isinstance(recipe, dict), f"{context} muss ein Dict sein.")
        _require(recipe.get("verb", "use") in {"use", "break"}, f"{context}: Verb unbekannt.")
        ingredients = recipe.get("ingredients", {})
        _require(isinstance(ingredients, dict), f"{context}: ingredients muss Dict sein.")
        for ingredient, count in ingredients.items():
            _require(ingredient in known_entity_ids, f"{context}: Zutat '{ingredient}' fehlt.")
            _require(isinstance(count, int) and count > 0, f"{context}: Menge für '{ingredient}' ungültig.")
        for tool_id in recipe.get("tools", []):
            _require(tool_id in known_entity_ids, f"{context}: Werkzeug '{tool_id}' fehlt.")
        if recipe.get("station"):
            _require(recipe["station"] in known_entity_ids, f"{context}: Station fehlt.")
        if recipe.get("result"):
            _require(recipe["result"] in object_ids, f"{context}: Ergebnis '{recipe['result']}' fehlt.")
        for item_id in recipe.get("items", []):
            _require(item_id in known_entity_ids, f"{context}: Interaktionsziel '{item_id}' fehlt.")
        if "condition" in recipe:
            _validate_condition(recipe["condition"], context)
        effects = recipe.get("effects", recipe.get("effect", []))
        if not isinstance(effects, list):
            effects = [effects]
        for effect_index, effect in enumerate(effects):
            _validate_effect(effect, f"{context} Effekt #{effect_index}")

    meta = config.setdefault("meta", {})
    start_room = meta.get("start_room")
    _require(start_room in room_ids, f"Start-Raum '{start_room}' fehlt.")

    def validate_effect_references(effect, context):
        effect_type = effect.get("type")
        if effect_type in {"move_npc", "teleport_npc"}:
            _require(effect.get("npc") in npc_ids, f"{context}: NPC fehlt.")
            target = effect.get("room") or effect.get("target")
            _require(target in room_ids, f"{context}: Zielraum '{target}' fehlt.")
        elif effect_type in {"set_state", "set_npc_state"} and effect.get("npc"):
            _require(effect["npc"] in npc_ids, f"{context}: NPC '{effect['npc']}' fehlt.")
        elif effect_type in {"spawn_item", "receive_item"}:
            item_id = effect.get("item") or effect.get("item_id")
            _require(item_id in object_ids, f"{context}: Item '{item_id}' fehlt.")
        elif effect_type == "update_object":
            _require(
                effect.get("target") in object_ids | npc_ids,
                f"{context}: Update-Ziel '{effect.get('target')}' fehlt.",
            )
        elif effect_type == "trigger_event":
            _require(effect.get("id") in event_ids, f"{context}: Event '{effect.get('id')}' fehlt.")
        elif effect_type in {"quest_start", "quest_complete", "quest_fail"}:
            quest_id = effect.get("id") or effect.get("quest")
            _require(quest_id in quests, f"{context}: Quest '{quest_id}' fehlt.")
        elif effect_type == "quest_update":
            payload = effect.get("quest_update", effect)
            quest_id = payload.get("id") or payload.get("quest")
            _require(quest_id in quests, f"{context}: Quest '{quest_id}' fehlt.")
            try:
                stage = int(payload.get("stage"))
            except (TypeError, ValueError):
                raise ConfigurationError(f"{context}: Quest-Stage fehlt.")
            _require(stage in quests[quest_id]["stages"], f"{context}: Quest-Stage {stage} fehlt.")

    def walk_content(node, context):
        if isinstance(node, dict):
            if "condition" in node:
                _validate_condition(node["condition"], context)
            for key in ("effect", "effects"):
                if key in node:
                    effects_to_check = node[key]
                    if not isinstance(effects_to_check, list):
                        effects_to_check = [effects_to_check]
                    for effect_index, effect in enumerate(effects_to_check):
                        _validate_effect(effect, f"{context} Effekt #{effect_index}")
                        validate_effect_references(
                            effect, f"{context} Effekt #{effect_index}"
                        )
            for key, value in node.items():
                if key not in {"effect", "effects", "condition"}:
                    walk_content(value, f"{context}.{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk_content(value, f"{context}[{index}]")

    for event in events:
        effects = event.get("effects", [])
        if not isinstance(effects, list):
            effects = [effects]
        for effect_index, effect in enumerate(effects):
            validate_effect_references(
                effect, f"Event '{event['id']}' Effekt #{effect_index}"
            )
    for recipe_index, recipe in enumerate(combinations):
        effects = recipe.get("effects", recipe.get("effect", []))
        if not isinstance(effects, list):
            effects = [effects]
        for effect_index, effect in enumerate(effects):
            validate_effect_references(
                effect, f"Rezept #{recipe_index} Effekt #{effect_index}"
            )
    for npc in npcs:
        walk_content(npc.get("dialogue", {}), f"NPC '{npc['id']}'.dialogue")
        walk_content(npc.get("states", {}), f"NPC '{npc['id']}'.states")

    return config
