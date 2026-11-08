from __future__ import annotations

from typing import TYPE_CHECKING, Any

from engine.access import is_directly_reachable, reach_error
from engine.constants import (
    ATTR_ID,
    ATTR_MATTER,
    ATTR_NAME,
    ATTR_WEIGHT,
    FILTER_INVENTORY,
    FILTER_RECURSIVE,
    FILTER_ROOM,
    LOC_VOID,
    MATTER_LIQUID,
    STATE_BROKEN,
    STATE_NORMAL,
    STATE_SABOTAGED,
    TYPE_CONTAINER,
    TYPE_FIXTURE,
    TYPE_SURFACE,
)
from engine.handlers.common import CommonHandler
from engine.resolver import ResolutionError, Resolver
from engine.strings import Texts

if TYPE_CHECKING:
    from engine.game_state import GameState


class MechanicsHandler:
    @staticmethod
    def put(game: GameState, args: list[str]) -> None:
        if game.hidden_in:
            return game.log("error", Texts.ERR_HIDDEN)
        separators = {"in", "into", "auf", "on", "an"}
        index = next((i for i, word in enumerate(args) if word.lower() in separators), None)
        if index is None:
            return game.log("error", Texts.PUT_MISSING_PREP)

        try:
            item = Resolver.resolve_target(
                game, args[:index], location_filter=FILTER_INVENTORY, verb="put_item"
            )
            target = Resolver.resolve_target(
                game, args[index + 1 :], location_filter=FILTER_RECURSIVE, verb="put_container"
            )
            if not item or not target:
                return
            if item not in game.objects.values():
                return game.log("error", Texts.PUT_ONLY_OBJECTS)
            if item[ATTR_ID] == target[ATTR_ID]:
                return game.log("error", Texts.PUT_PHYSICALLY_IMPOSSIBLE)
            if not is_directly_reachable(game, target):
                return game.log("error", reach_error(game, target))
            if target.get("type") not in {TYPE_CONTAINER, TYPE_SURFACE, TYPE_FIXTURE}:
                return game.log("error", Texts.PUT_CANNOT_PLACE.format(target=target[ATTR_NAME]))
            if target.get("type") == TYPE_CONTAINER and not target.get("is_open", False):
                return game.log("error", Texts.PUT_CONTAINER_CLOSED.format(target=target[ATTR_NAME]))
            if item.get(ATTR_MATTER) == MATTER_LIQUID and target.get("type") != TYPE_CONTAINER:
                return game.log(
                    "error",
                    Texts.PUT_LIQUID_ON_SURFACE.format(target=target[ATTR_NAME]),
                )
            if CommonHandler.is_contained_in(game, target, item[ATTR_ID]):
                return game.log("error", Texts.PUT_CYCLIC_CONTAINER)

            item_weight = CommonHandler.get_total_weight(game, item)
            current_load = CommonHandler.get_contained_weight(game, target[ATTR_ID])
            explicit_cap = target.get("max_weight", target.get("capacity"))
            if explicit_cap is not None:
                max_capacity = float(explicit_cap)
            elif (
                target.get("type") == TYPE_CONTAINER
                and float(target.get(ATTR_WEIGHT, float("inf"))) < float("inf")
            ):
                # Portable containers cannot hold objects heavier than 10x their own mass
                max_capacity = max(10.0, float(target.get(ATTR_WEIGHT, 1.0)) * 10.0)
            else:
                max_capacity = float("inf")

            if current_load + item_weight > max_capacity:
                return game.log(
                    "error",
                    Texts.PUT_TOO_HEAVY_FOR_CONTAINER.format(
                        item=item[ATTR_NAME], target=target[ATTR_NAME]
                    ),
                )

            item["location"] = target[ATTR_ID]
            item["level"] = target.get("level", 0)
            game.log(
                "success",
                Texts.PUT_SUCCESS.format(item=item[ATTR_NAME], target=target[ATTR_NAME]),
            )
            game.tick(1)
        except ResolutionError as exc:
            game.log("error", str(exc))

    @staticmethod
    def use(game: GameState, args: list[str]) -> None:
        if game.hidden_in:
            return game.log("error", Texts.ERR_HIDDEN)
        separators = {"mit", "with", "an", "on", "in"}
        indices = [i for i, word in enumerate(args) if word.lower() in separators]

        if indices:
            index = indices[-1]
            first_words, second_words = args[:index], args[index + 1 :]
            result = game.perform_combine(
                " ".join(first_words), " ".join(second_words), verb="use"
            )
            if result.success:
                game.log("success", result.message)
                game.tick(2)
                return
            if result.code == "not_reachable":
                return game.log("error", result.message)

            if result.code in {"no_recipe", "not_found"}:
                if MechanicsHandler._try_reach_tool(
                    game, first_words, second_words
                ):
                    return
            game.log("info", result.message)
            return

        try:
            target = Resolver.resolve_target(
                game, args, location_filter=FILTER_RECURSIVE, verb="use"
            )
            if not target:
                return
            if not is_directly_reachable(game, target):
                return game.log("error", reach_error(game, target))
            if target.get("type") == TYPE_FIXTURE or target.get("usable", False):
                if "state" in target:
                    target["state"] = "on" if target["state"] == "off" else "off"
                    game.log(
                        "success",
                        Texts.USE_STATE_TOGGLED.format(
                            target=target[ATTR_NAME], state=target["state"]
                        ),
                    )
                else:
                    game.log(
                        "info",
                        Texts.USE_NOTHING_HAPPENS.format(target=target[ATTR_NAME]),
                    )
                game.tick(1)
            else:
                game.pending_interaction = {"verb": "use", "args": args}
                game.log(
                    "info",
                    Texts.USE_ASK_WHAT_WITH.format(target=target[ATTR_NAME]),
                )
        except ResolutionError as exc:
            game.log("error", str(exc))

    @staticmethod
    def open(game: GameState, args: list[str]) -> None:
        if game.hidden_in:
            return game.log("error", Texts.ERR_HIDDEN)
        try:
            target = Resolver.resolve_target(
                game, args, location_filter=FILTER_RECURSIVE, verb="open"
            )
            if not target:
                return
            if target.get("type") != TYPE_CONTAINER:
                return game.log("error", Texts.OPEN_NOT_CONTAINER)
            if not is_directly_reachable(game, target):
                return game.log("error", reach_error(game, target))
            if target.get("is_open"):
                return game.log(
                    "info",
                    Texts.OPEN_ALREADY_OPEN.format(target=target[ATTR_NAME]),
                )
            if target.get("is_locked", False):
                key_id = target.get("key_id")
                key = game.objects.get(key_id) if isinstance(key_id, str) else None
                if not key or not CommonHandler.is_held_by_player(game, key):
                    locked_msg = target.get("locked_msg")
                    if isinstance(locked_msg, str) and locked_msg:
                        try:
                            msg = locked_msg.format(target=target[ATTR_NAME])
                        except KeyError:
                            msg = locked_msg
                    else:
                        msg = Texts.OPEN_LOCKED.format(target=target[ATTR_NAME])
                    return game.log("error", msg)
                target["is_locked"] = False
                game.log(
                    "info",
                    Texts.OPEN_UNLOCK_WITH_KEY.format(
                        target=target[ATTR_NAME], key=key[ATTR_NAME]
                    ),
                )

            target["is_open"] = True
            game.log("success", Texts.OPEN_SUCCESS.format(target=target[ATTR_NAME]))
            contents = [
                obj[ATTR_NAME]
                for obj in game.objects.values()
                if obj.get("location") == target[ATTR_ID]
            ]
            if contents:
                game.log("info", Texts.OPEN_CONTAINS.format(', '.join(contents)))
            game.tick(1)
        except ResolutionError as exc:
            game.log("error", str(exc))

    @staticmethod
    def close(game: GameState, args: list[str]) -> None:
        if game.hidden_in:
            return game.log("error", Texts.ERR_HIDDEN)
        try:
            target = Resolver.resolve_target(
                game, args, location_filter=FILTER_RECURSIVE, verb="close"
            )
            if not target:
                return
            if target.get("type") != TYPE_CONTAINER:
                return game.log("error", Texts.CLOSE_NOT_CONTAINER)
            if not is_directly_reachable(game, target):
                return game.log("error", reach_error(game, target))
            if not target.get("is_open"):
                return game.log(
                    "info",
                    Texts.CLOSE_ALREADY_CLOSED.format(target=target[ATTR_NAME]),
                )
            if target.get("jammed"):
                return game.log(
                    "error",
                    Texts.CLOSE_JAMMED.format(target=target[ATTR_NAME]),
                )
            target["is_open"] = False
            game.log("success", Texts.CLOSE_SUCCESS.format(target=target[ATTR_NAME]))
            game.tick(1)
        except ResolutionError as exc:
            game.log("error", str(exc))

    @staticmethod
    def break_(game: GameState, args: list[str]) -> None:
        if game.hidden_in:
            return game.log("error", Texts.ERR_HIDDEN)
        separators = {"mit", "with", "in", "using", "an", "gegen"}
        index = next((i for i, word in enumerate(args) if word.lower() in separators), None)
        target_words = args if index is None else args[:index]
        tool_words = [] if index is None else args[index + 1 :]
        separator = "" if index is None else args[index].lower()

        try:
            target = Resolver.resolve_target(
                game, target_words, location_filter=FILTER_RECURSIVE, verb="break_target"
            )
            if not target:
                return
            if not is_directly_reachable(game, target):
                return game.log("error", reach_error(game, target))
            if target.get("state") == STATE_BROKEN:
                return game.log("info", Texts.BREAK_ALREADY_BROKEN.format(target=target[ATTR_NAME]))

            if tool_words:
                tool_filter = FILTER_ROOM if separator == "in" else FILTER_INVENTORY
                tool = Resolver.resolve_target(
                    game, tool_words, location_filter=tool_filter, verb="break_tool"
                )
                if not tool:
                    return
                if not is_directly_reachable(game, tool):
                    return game.log("error", reach_error(game, tool))

                result = game.perform_combine(
                    " ".join(target_words), " ".join(tool_words), verb="break"
                )
                if result.success:
                    game.log("success", result.message)
                    game.tick(1)
                    return
                if result.code == "not_reachable":
                    return game.log("error", result.message)

                if separator == "in" and (
                    tool.get("state") == "on" or tool.get("hot", False)
                ):
                    target["location"] = LOC_VOID
                    game.log(
                        "success",
                        Texts.BREAK_IN_CONTAINER_SUCCESS.format(
                            target=target[ATTR_NAME], tool=tool[ATTR_NAME]
                        ),
                    )
                    game.tick(1)
                    return

                if tool.get("damage", 1) >= target.get("toughness", 1):
                    MechanicsHandler._mark_broken(target)
                    game.log(
                        "success",
                        Texts.BREAK_WITH_TOOL_SUCCESS.format(
                            tool=tool[ATTR_NAME], target=target[ATTR_NAME]
                        ),
                    )
                    game.tick(1)
                else:
                    game.log(
                        "info",
                        Texts.BREAK_TOOL_NOT_STRONG.format(
                            tool=tool[ATTR_NAME], target=target[ATTR_NAME]
                        ),
                    )
                return

            if target.get("fragile", False) or target.get("toughness", 1) == 0:
                MechanicsHandler._mark_broken(target)
                game.log(
                    "success",
                    Texts.BREAK_BARE_HANDS_SUCCESS.format(target=target[ATTR_NAME]),
                )
                game.tick(1)
            else:
                game.log("info", Texts.BREAK_NEED_TOOL)
        except ResolutionError as exc:
            game.log("error", str(exc))

    @staticmethod
    def fix(game: GameState, args: list[str]) -> None:
        if game.hidden_in:
            return game.log("error", Texts.ERR_HIDDEN)
        separators = {"mit", "with", "using"}
        index = next((i for i, word in enumerate(args) if word.lower() in separators), None)
        target_words = args if index is None else args[:index]
        tool_words = [] if index is None else args[index + 1 :]
        try:
            target = Resolver.resolve_target(
                game, target_words, location_filter=FILTER_RECURSIVE, verb="fix"
            )
            if not target:
                return
            if not is_directly_reachable(game, target):
                return game.log("error", reach_error(game, target))
            if target.get("state") == STATE_SABOTAGED:
                return game.log("info", Texts.FIX_SABOTAGED_HINT)
            if target.get("state") != STATE_BROKEN:
                return game.log(
                    "info",
                    Texts.FIX_NOT_BROKEN.format(target=target[ATTR_NAME]),
                )

            if tool_words:
                tool = Resolver.resolve_target(
                    game, tool_words, location_filter=FILTER_INVENTORY, verb="fix_tool"
                )
                has_tool = bool(tool and tool.get("is_tool"))
            else:
                has_tool = any(
                    obj.get("is_tool") and CommonHandler.is_held_by_player(game, obj)
                    for obj in game.objects.values()
                )
            if not has_tool:
                return game.log("error", Texts.FIX_NEED_TOOL)

            target["state"] = STATE_NORMAL
            target["name"] = target["name"].removeprefix(Texts.BROKEN_PREFIX)
            game.log("success", Texts.FIX_SUCCESS.format(target=target[ATTR_NAME]))
            game.tick(5)
        except ResolutionError as exc:
            game.log("error", str(exc))

    @staticmethod
    def wait(game: GameState, args: list[str]) -> None:
        minutes = 10
        if args and args[0].isdigit():
            minutes = max(1, min(60, int(args[0])))
        game.log("info", Texts.WAIT_MINUTES.format(minutes=minutes))
        game.tick(minutes)

    @staticmethod
    def _try_reach_tool(
        game: GameState, first_words: list[str], second_words: list[str]
    ) -> bool:
        try:
            first = Resolver.resolve_target(game, first_words, location_filter=FILTER_RECURSIVE)
            second = Resolver.resolve_target(game, second_words, location_filter=FILTER_RECURSIVE)
        except ResolutionError:
            return False
        if not first or not second:
            return False
        if first.get("is_tool") and first.get("reach", 0) > 0:
            tool, target, target_words, tool_words = first, second, second_words, first_words
        elif second.get("is_tool") and second.get("reach", 0) > 0:
            tool, target, target_words, tool_words = second, first, first_words, second_words
        else:
            return False
        if not CommonHandler.is_held_by_player(game, tool):
            return False
        from engine.handlers.inventory import InventoryHandler

        game.log(
            "info",
            Texts.TRY_TAKE_WITH_TOOL.format(
                target=target[ATTR_NAME], tool=tool[ATTR_NAME]
            ),
        )
        InventoryHandler.take(game, target_words + ["mit"] + tool_words)
        return True

    @staticmethod
    def _mark_broken(target: dict[str, Any]) -> None:
        target["state"] = STATE_BROKEN
        if not target["name"].startswith(Texts.BROKEN_PREFIX):
            target["name"] = f"{Texts.BROKEN_PREFIX}{target['name']}"
        target["desc"] = Texts.BROKEN_DESC

