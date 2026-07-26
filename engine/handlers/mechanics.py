from engine.access import is_directly_reachable, reach_error
from engine.constants import (
    ATTR_ID,
    ATTR_NAME,
    FILTER_INVENTORY,
    FILTER_RECURSIVE,
    FILTER_ROOM,
    LOC_VOID,
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


class MechanicsHandler:
    @staticmethod
    def put(game, args):
        if game.hidden_in:
            return game.log("error", Texts.ERR_HIDDEN)
        separators = {"in", "into", "auf", "on", "an"}
        index = next((i for i, word in enumerate(args) if word.lower() in separators), None)
        if index is None:
            return game.log("error", "Wo willst du das hintun? (Benutze 'in' oder 'auf')")

        try:
            item = Resolver.resolve_target(
                game, args[:index], location_filter=FILTER_INVENTORY, verb="put_item"
            )
            target = Resolver.resolve_target(
                game, args[index + 1 :], location_filter=FILTER_ROOM, verb="put_container"
            )
            if item not in game.objects.values():
                return game.log("error", "Nur Gegenstände lassen sich ablegen.")
            if item[ATTR_ID] == target[ATTR_ID]:
                return game.log("error", "Das geht physikalisch nicht.")
            if target.get("type") not in {TYPE_CONTAINER, TYPE_SURFACE, TYPE_FIXTURE}:
                return game.log("error", f"Auf/in {target[ATTR_NAME]} lässt sich nichts legen.")
            if target.get("type") == TYPE_CONTAINER and not target.get("is_open", False):
                return game.log("error", f"{target[ATTR_NAME]} ist geschlossen.")
            if MechanicsHandler._is_descendant(game, target, item[ATTR_ID]):
                return game.log("error", "Container können nicht zyklisch verschachtelt werden.")

            item["location"] = target[ATTR_ID]
            item["level"] = target.get("level", 0)
            game.log("success", f"Du legst {item[ATTR_NAME]} in/auf {target[ATTR_NAME]}.")
            game.tick(1)
        except ResolutionError as exc:
            game.log("error", str(exc))

    @staticmethod
    def use(game, args):
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
            if not is_directly_reachable(game, target):
                return game.log("error", reach_error(game, target))
            if target.get("type") == TYPE_FIXTURE or target.get("usable", False):
                if "state" in target:
                    target["state"] = "on" if target["state"] == "off" else "off"
                    game.log(
                        "success",
                        f"Du benutzt {target[ATTR_NAME]}. (Zustand: {target['state']})",
                    )
                else:
                    game.log("info", f"Du benutzt {target[ATTR_NAME]}, aber nichts passiert.")
                game.tick(1)
            else:
                game.pending_interaction = {"verb": "use", "args": args}
                game.log("info", f"Was willst du mit {target[ATTR_NAME]} benutzen?")
        except ResolutionError as exc:
            game.log("error", str(exc))

    @staticmethod
    def open(game, args):
        if game.hidden_in:
            return game.log("error", Texts.ERR_HIDDEN)
        try:
            target = Resolver.resolve_target(
                game, args, location_filter=FILTER_RECURSIVE, verb="open"
            )
            if target.get("type") != TYPE_CONTAINER:
                return game.log("error", "Das kann man nicht öffnen.")
            if not is_directly_reachable(game, target):
                return game.log("error", reach_error(game, target))
            if target.get("is_open"):
                return game.log("info", f"{target[ATTR_NAME]} ist bereits offen.")
            if target.get("is_locked", False):
                key_id = target.get("key_id")
                key = game.objects.get(key_id)
                if not key or not CommonHandler.is_held_by_player(game, key):
                    return game.log("error", f"{target[ATTR_NAME]} ist verschlossen.")
                target["is_locked"] = False
                game.log("info", f"Du schließt {target[ATTR_NAME]} mit {key[ATTR_NAME]} auf.")

            target["is_open"] = True
            game.log("success", f"Du öffnest {target[ATTR_NAME]}.")
            contents = [
                obj[ATTR_NAME]
                for obj in game.objects.values()
                if obj.get("location") == target[ATTR_ID]
            ]
            if contents:
                game.log("info", f"Darin befindet sich: {', '.join(contents)}")
            game.tick(1)
        except ResolutionError as exc:
            game.log("error", str(exc))

    @staticmethod
    def close(game, args):
        if game.hidden_in:
            return game.log("error", Texts.ERR_HIDDEN)
        try:
            target = Resolver.resolve_target(
                game, args, location_filter=FILTER_RECURSIVE, verb="close"
            )
            if target.get("type") != TYPE_CONTAINER:
                return game.log("error", "Das kann man nicht schließen.")
            if not is_directly_reachable(game, target):
                return game.log("error", reach_error(game, target))
            if not target.get("is_open"):
                return game.log("info", f"{target[ATTR_NAME]} ist bereits geschlossen.")
            target["is_open"] = False
            game.log("success", f"Du schließt {target[ATTR_NAME]}.")
            game.tick(1)
        except ResolutionError as exc:
            game.log("error", str(exc))

    @staticmethod
    def break_(game, args):
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
            if not is_directly_reachable(game, target):
                return game.log("error", reach_error(game, target))
            if target.get("state") == STATE_BROKEN:
                return game.log("info", f"{target[ATTR_NAME]} ist bereits kaputt.")

            if tool_words:
                tool_filter = FILTER_ROOM if separator == "in" else FILTER_INVENTORY
                tool = Resolver.resolve_target(
                    game, tool_words, location_filter=tool_filter, verb="break_tool"
                )
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
                        f"Du zerstörst {target[ATTR_NAME]} in {tool[ATTR_NAME]}.",
                    )
                    game.tick(1)
                    return

                if tool.get("damage", 1) >= target.get("toughness", 1):
                    MechanicsHandler._mark_broken(target)
                    game.log(
                        "success",
                        f"Mit {tool[ATTR_NAME]} zerstörst du {target[ATTR_NAME]}!",
                    )
                    game.tick(1)
                else:
                    game.log(
                        "info",
                        f"{tool[ATTR_NAME]} ist nicht stark genug für {target[ATTR_NAME]}.",
                    )
                return

            if target.get("fragile", False) or target.get("toughness", 1) == 0:
                MechanicsHandler._mark_broken(target)
                game.log("success", f"Du zerstörst {target[ATTR_NAME]} mit bloßen Händen.")
                game.tick(1)
            else:
                game.log("info", "Du brauchst dafür ein passendes Werkzeug.")
        except ResolutionError as exc:
            game.log("error", str(exc))

    @staticmethod
    def fix(game, args):
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
            if not is_directly_reachable(game, target):
                return game.log("error", reach_error(game, target))
            if target.get("state") == STATE_SABOTAGED:
                return game.log("info", "Das sieht nach Sabotage aus. Dafür brauchst du einen Plan.")
            if target.get("state") != STATE_BROKEN:
                return game.log("info", f"{target[ATTR_NAME]} scheint in Ordnung zu sein.")

            if tool_words:
                tool = Resolver.resolve_target(
                    game, tool_words, location_filter=FILTER_INVENTORY, verb="fix_tool"
                )
                has_tool = bool(tool.get("is_tool"))
            else:
                has_tool = any(
                    obj.get("is_tool") and CommonHandler.is_held_by_player(game, obj)
                    for obj in game.objects.values()
                )
            if not has_tool:
                return game.log("error", "Du hast kein geeignetes Werkzeug dabei.")

            target["state"] = STATE_NORMAL
            target["name"] = target["name"].removeprefix("kaputte(s) ")
            game.log("success", f"Du hast {target[ATTR_NAME]} repariert.")
            game.tick(5)
        except ResolutionError as exc:
            game.log("error", str(exc))

    @staticmethod
    def wait(game, args):
        minutes = 10
        if args and args[0].isdigit():
            minutes = max(1, min(60, int(args[0])))
        game.log("info", f"Du wartest {minutes} Minuten...")
        game.tick(minutes)

    @staticmethod
    def _try_reach_tool(game, first_words, second_words):
        try:
            first = Resolver.resolve_target(game, first_words, location_filter=FILTER_RECURSIVE)
            second = Resolver.resolve_target(game, second_words, location_filter=FILTER_RECURSIVE)
        except ResolutionError:
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

        game.log("info", f"(Versuche, {target[ATTR_NAME]} mit {tool[ATTR_NAME]} zu nehmen...)")
        InventoryHandler.take(game, target_words + ["mit"] + tool_words)
        return True

    @staticmethod
    def _mark_broken(target):
        target["state"] = STATE_BROKEN
        if not target["name"].startswith("kaputte(s) "):
            target["name"] = f"kaputte(s) {target['name']}"
        target["desc"] = "Völlig zerstört."

    @staticmethod
    def _is_descendant(game, candidate, ancestor_id):
        current = candidate
        seen = set()
        while current.get("location") in game.objects:
            location = current["location"]
            if location == ancestor_id:
                return True
            if location in seen:
                return True
            seen.add(location)
            current = game.objects[location]
        return False
