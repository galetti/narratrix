"""Validation helpers for Narratrix chapter data.

The runtime deliberately uses plain dictionaries for author-friendly content,
but all modules share this single contract. Invalid references are rejected
while a chapter is loaded instead of failing much later during play.
"""

from __future__ import annotations

from typing import Any, Iterable, TypedDict

from engine.constants import LOC_INVENTORY, LOC_VOID


class ConditionDict(TypedDict, total=False):
    type: str
    value: Any
    item: str
    location: str
    npc: str
    state: str
    is_open: bool
    is_locked: bool
    quest: str
    status: str
    stage: int | str
    op: str
    id: str
    # "not" is a reserved keyword in class syntax, accessed via dict syntax at runtime


ConditionSpec = str | dict[str, Any]


class EffectData(TypedDict, total=False):
    type: str
    npc: str
    room: str
    target: str
    value: Any
    fact: str
    item: str
    item_id: str
    location: str
    updates: dict[str, Any]
    reason: str
    id: str
    message: str
    log_type: str
    quest: str
    stage: int | str
    quest_update: dict[str, Any]
    chapter: str


class AcousticConnectionData(TypedDict, total=False):
    transmission: float
    direction_text: str


class EditorPositionData(TypedDict, total=False):
    x: float
    y: float
    z: int


class RoomData(TypedDict, total=False):
    id: str
    name: str
    desc: str
    img: str
    exits: dict[str, str]
    acoustics: dict[str, float | AcousticConnectionData]
    climb_targets: dict[str, str]
    tags: list[str]
    visited: bool
    state: str
    _editor: EditorPositionData


class ObjectBehaviorData(TypedDict, total=False):
    type: str
    chance: float


class ObjectData(TypedDict, total=False):
    id: str
    name: str
    desc: str
    aliases: list[str]
    location: str
    type: str
    state: str
    weight: float
    temp: float
    matter: str
    level: int
    climbable: bool
    target_elevation: int
    destination: str
    is_open: bool
    is_locked: bool
    key_id: str
    linked_exit: str
    acoustic_damping: float
    acoustic_boost: float
    is_tool: bool
    reach: int
    damage: int
    toughness: int
    fragile: bool
    hot: bool
    usable: bool
    movable: bool
    is_scale: bool
    is_resource: bool
    resource_id: str
    count: int
    behavior: ObjectBehaviorData


class DialogueOptionData(TypedDict, total=False):
    label: str
    text: str
    condition: ConditionSpec
    effect: EffectData | list[EffectData]
    effects: EffectData | list[EffectData]
    hidden: bool


DialogueEntry = str | DialogueOptionData


class NPCStateDefinition(TypedDict, total=False):
    behavior: dict[str, Any]
    visuals: dict[str, Any]
    dialogue: dict[str, DialogueEntry]


class NPCMemoryData(TypedDict, total=False):
    last_noise_loc: str | None


class NPCData(TypedDict, total=False):
    id: str
    name: str
    desc: str
    aliases: list[str]
    location: str
    level: int
    state: str
    initial_state: str
    states: dict[str, NPCStateDefinition]
    behavior_id: str
    speed: float
    waypoints: list[str]
    waypoint_index: int
    path: list[str]
    target_location: str | None
    move_acc: float
    has_greeted: bool
    memory: NPCMemoryData
    toughness: int
    personality: str
    img: str
    dialogue: dict[str, dict[str, DialogueEntry]]
    _state_managed_keys: list[str]
    _state_base_values: dict[str, Any]
    _state_missing_keys: list[str]


EntityData = ObjectData | NPCData | dict[str, Any]


class EventData(TypedDict, total=False):
    id: str
    trigger: str
    trigger_time: int
    repeat: bool
    triggered: bool
    last_triggered_at: int | None
    location: str
    value: str
    origin_id: str
    title: str
    description: str
    sound_msg: str
    volume: float
    message: str
    condition: ConditionSpec
    conditions: list[ConditionSpec]
    operator: str
    quest_start: str
    quest_update: dict[str, Any]
    quest_complete: str
    effects: EffectData | list[EffectData]


class QuestDefinitionData(TypedDict, total=False):
    title: str
    desc: str
    stages: dict[int, str]
    start_stage: int
    completion_stage: int


class QuestStateData(TypedDict):
    status: str
    stage: int | None


class ActiveQuestInfo(TypedDict):
    id: str
    title: str
    stage: int | None
    stage_desc: str


class RecipeData(TypedDict, total=False):
    verb: str
    items: list[str]
    ingredients: dict[str, int]
    tools: list[str]
    station: str
    blueprint: str
    result: str
    spawn_item: str
    condition: ConditionSpec
    message: str
    effect: EffectData | list[EffectData]
    effects: EffectData | list[EffectData]


class LogEntry(TypedDict):
    type: str
    text: str
    turn: int


class GameSnapshot(TypedDict):
    time: int
    stability: float
    game_over: bool
    pending_chapter_load: str | None
    room_name: str
    room_img: str
    dialogue_active: bool
    dialogue_header: str
    dialogue_img: str
    logs: list[LogEntry]
    elevation: int
    present_npcs: list[str]


class VocabularyData(TypedDict, total=False):
    verbs: dict[str, list[str]]
    directions: dict[str, list[str]]
    skip_words: list[str]


class GameConfigData(TypedDict, total=False):
    meta: dict[str, Any]
    settings: dict[str, Any]
    vocabulary: VocabularyData
    rooms: dict[str, RoomData]
    objects: dict[str, ObjectData]
    npcs: list[NPCData]
    combinations: list[RecipeData]
    narrative_matrix: list[EventData]
    matrix: list[EventData]
    events: list[EventData]
    quests: dict[str, QuestDefinitionData]
    links: list[dict[str, str]]
    use_llm_dialogue: bool
    llm_url: str | None
    llm_model: str | None


SUPPORTED_TRIGGERS: set[str] = {"time", "location", "condition", "complex", "manual"}
SUPPORTED_CONDITIONS: set[str] = {
    "knowledge",
    "location",
    "item_location",
    "object_state",
    "scale_weight",
    "npc_state",
    "quest_state",
    "stability",
    "event_triggered",
    "inventory",
}
SUPPORTED_EFFECTS: set[str] = {
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

    def validate_effect_references(effect: dict[str, Any], context: str) -> None:
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

    def walk_content(node: Any, context: str) -> None:
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
