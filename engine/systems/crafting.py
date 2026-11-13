from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Sequence

from engine.access import _root_entity_and_location, is_directly_reachable, reach_error
from engine.constants import ATTR_NAME, FILTER_RECURSIVE, LOC_INVENTORY, LOC_VOID
from engine.resolver import AmbiguityError, ResolutionError, Resolver
from engine.schema import EntityData, ObjectData, RecipeData
from engine.strings import Texts

if TYPE_CHECKING:
    from engine.game_state import GameState


@dataclass(frozen=True)
class CraftResult:
    success: bool
    message: str
    code: str = "ok"

    def __str__(self) -> str:
        return self.message


class CraftingSystem:
    def __init__(self, game: GameState) -> None:
        self.game: GameState = game

    @staticmethod
    def _identifiers(entity: EntityData) -> set[str]:
        return {
            value
            for value in (entity.get("id"), entity.get("resource_id"))
            if isinstance(value, str) and value
        }

    def perform_combine(
        self, item1_name: str, item2_name: str, verb: str = "use"
    ) -> CraftResult:
        item1 = self._find_obj_or_npc_by_name(item1_name)
        item2 = self._find_obj_or_npc_by_name(item2_name)
        if not item1 or not item2:
            return CraftResult(False, Texts.CRAFT_NOT_FOUND, "not_found")

        for entity in (item1, item2):
            if not is_directly_reachable(self.game, entity):
                return CraftResult(False, reach_error(self.game, entity), "not_reachable")

        possible = [
            recipe
            for recipe in self.game.combinations
            if recipe.get("verb", "use") == verb
            and self._matches_interaction(recipe, (item1, item2))
        ]
        if not possible:
            return CraftResult(False, Texts.CRAFT_NO_RECIPE, "no_recipe")

        failures: list[CraftResult] = []
        for recipe in possible:
            result = self._try_craft(recipe, (item1, item2))
            if result.success:
                return result
            failures.append(result)
        return failures[0] if failures else CraftResult(False, Texts.CRAFT_FAILED, "failed")

    def _matches_interaction(
        self, recipe: RecipeData, entities: Sequence[EntityData]
    ) -> bool:
        requested = set(recipe.get("items", []))
        identifiers = [self._identifiers(entity) for entity in entities]
        if requested:
            return all(any(item_id in values for values in identifiers) for item_id in requested)

        station = recipe.get("station")
        ingredients = set(recipe.get("ingredients", {}))
        tools = set(recipe.get("tools", []))
        relevant = ingredients | tools | ({station} if station else set())
        return any(identifier in relevant for values in identifiers for identifier in values)

    def _try_craft(
        self, recipe: RecipeData, interacting_items: Sequence[EntityData]
    ) -> CraftResult:
        if "condition" in recipe and not self.game.events.evaluate_condition(
            recipe["condition"]
        ):
            return CraftResult(False, Texts.CRAFT_CONDITION_FAILED, "condition")

        station_id = recipe.get("station")
        if station_id:
            station = self._find_entity_by_identifier(station_id)
            if not station or not is_directly_reachable(self.game, station):
                return CraftResult(
                    False,
                    Texts.CRAFT_STATION_UNREACHABLE.format(station=station_id),
                    "station",
                )

        blueprint = recipe.get("blueprint")
        if blueprint and blueprint not in self.game.knowledge:
            return CraftResult(False, Texts.CRAFT_MISSING_BLUEPRINT, "blueprint")

        for tool_id in recipe.get("tools", []):
            tool = self._find_inventory_entity(tool_id)
            if not tool:
                return CraftResult(
                    False,
                    Texts.CRAFT_MISSING_TOOL.format(tool=tool_id),
                    "tool",
                )

        result_id = recipe.get("result") or recipe.get("spawn_item")
        result_obj: ObjectData | None = None
        if result_id:
            result_obj = self.game.objects.get(result_id)
            if not result_obj:
                raise ValueError(f"Rezept-Ergebnis '{result_id}' fehlt trotz Validierung.")
            if result_obj.get("location") != LOC_VOID:
                return CraftResult(
                    False,
                    Texts.CRAFT_RESULT_EXISTS.format(name=result_obj[ATTR_NAME]),
                    "result_exists",
                )

        ingredient_plan: dict[str, tuple[int, list[ObjectData]]] = {}
        missing: list[str] = []
        for ingredient_id, required_count in recipe.get("ingredients", {}).items():
            stacks = self._inventory_entities(ingredient_id)
            available = sum(
                int(entity.get("count", 1)) if entity.get("is_resource") else 1
                for entity in stacks
            )
            if available < required_count:
                missing.append(f"{required_count}x {ingredient_id}")
            ingredient_plan[ingredient_id] = (required_count, stacks)
        if missing:
            return CraftResult(
                False,
                Texts.CRAFT_MISSING_INGREDIENTS.format(missing=", ".join(missing)),
                "ingredients",
            )

        # Validation is complete; all following mutations form one atomic action.
        for _, (required_count, stacks) in ingredient_plan.items():
            remaining = required_count
            for entity in stacks:
                available = int(entity.get("count", 1)) if entity.get("is_resource") else 1
                consumed = min(remaining, available)
                remaining -= consumed
                if entity.get("is_resource") and consumed < available:
                    entity["count"] = available - consumed
                else:
                    entity["location"] = LOC_VOID
                if remaining == 0:
                    break

        effects = recipe.get("effects", recipe.get("effect"))
        if effects:
            context_npc = next(
                (entity for entity in interacting_items if entity in self.game.npcs),
                None,
            )
            self.game.effects.process(effects, context_npc)  # type: ignore[arg-type]

        result_name = None
        if result_id and result_obj:
            result_obj["location"] = LOC_INVENTORY
            result_name = result_obj[ATTR_NAME]

        message = recipe.get("message")
        if not message and result_name:
            message = Texts.CRAFT_SUCCESS_DEFAULT.format(name=result_name)
        return CraftResult(True, message or Texts.CRAFT_ACTION_DONE)

    def _inventory_entities(self, identifier: str) -> list[ObjectData]:
        results: list[ObjectData] = []
        for entity in self.game.objects.values():
            if identifier not in self._identifiers(entity):
                continue
            _, root_loc, blocked = _root_entity_and_location(self.game, entity)
            if root_loc == LOC_INVENTORY and not blocked:
                results.append(entity)
        return results

    def _find_inventory_entity(self, identifier: str) -> ObjectData | None:
        return next(iter(self._inventory_entities(identifier)), None)

    def _find_entity_by_identifier(self, identifier: str) -> dict[str, Any] | None:
        for entity in list(self.game.objects.values()) + list(self.game.npcs):
            if identifier in self._identifiers(entity):
                return entity  # type: ignore[return-value]
        return None

    def _find_obj_or_npc_by_name(self, name: str) -> dict[str, Any] | None:
        try:
            return Resolver.resolve_target(
                self.game, name.split(), location_filter=FILTER_RECURSIVE, verb="craft"
            )
        except (ResolutionError, AmbiguityError):
            return None
