from dataclasses import dataclass

from engine.access import is_directly_reachable, reach_error
from engine.constants import ATTR_ALIASES, ATTR_ID, ATTR_NAME, LOC_INVENTORY, LOC_VOID


@dataclass(frozen=True)
class CraftResult:
    success: bool
    message: str
    code: str = "ok"

    def __str__(self):
        return self.message


class CraftingSystem:
    def __init__(self, game):
        self.game = game

    @staticmethod
    def _identifiers(entity):
        return {
            value
            for value in (entity.get("id"), entity.get("resource_id"))
            if value
        }

    def perform_combine(self, item1_name, item2_name, verb="use"):
        item1 = self._find_obj_or_npc_by_name(item1_name)
        item2 = self._find_obj_or_npc_by_name(item2_name)
        if not item1 or not item2:
            return CraftResult(False, "Ich weiß nicht, was du kombinieren willst.", "not_found")

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
            return CraftResult(False, "Das scheint nicht zu funktionieren.", "no_recipe")

        failures = []
        for recipe in possible:
            result = self._try_craft(recipe, (item1, item2))
            if result.success:
                return result
            failures.append(result)
        return failures[0] if failures else CraftResult(False, "Das funktioniert so nicht.", "failed")

    def _matches_interaction(self, recipe, entities):
        requested = set(recipe.get("items", []))
        identifiers = [self._identifiers(entity) for entity in entities]
        if requested:
            return all(any(item_id in values for values in identifiers) for item_id in requested)

        station = recipe.get("station")
        ingredients = set(recipe.get("ingredients", {}))
        tools = set(recipe.get("tools", []))
        relevant = ingredients | tools | ({station} if station else set())
        return any(identifier in relevant for values in identifiers for identifier in values)

    def _try_craft(self, recipe, interacting_items):
        if "condition" in recipe and not self.game.events.evaluate_condition(
            recipe["condition"]
        ):
            return CraftResult(False, "Diese Aktion ist bereits erledigt.", "condition")

        station_id = recipe.get("station")
        if station_id:
            station = self._find_entity_by_identifier(station_id)
            if not station or not is_directly_reachable(self.game, station):
                return CraftResult(False, f"Die benötigte Station '{station_id}' ist nicht erreichbar.", "station")

        blueprint = recipe.get("blueprint")
        if blueprint and blueprint not in self.game.knowledge:
            return CraftResult(False, "Dir fehlt das Wissen für dieses Rezept.", "blueprint")

        for tool_id in recipe.get("tools", []):
            tool = self._find_inventory_entity(tool_id)
            if not tool:
                return CraftResult(False, f"Dir fehlt das Werkzeug '{tool_id}'.", "tool")

        result_id = recipe.get("result") or recipe.get("spawn_item")
        if result_id:
            result_obj = self.game.objects.get(result_id)
            if not result_obj:
                raise ValueError(f"Rezept-Ergebnis '{result_id}' fehlt trotz Validierung.")
            if result_obj.get("location") != LOC_VOID:
                return CraftResult(
                    False,
                    f"{result_obj[ATTR_NAME]} wurde bereits hergestellt.",
                    "result_exists",
                )

        ingredient_plan = {}
        missing = []
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
            return CraftResult(False, f"Dir fehlt noch: {', '.join(missing)}.", "ingredients")

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
            self.game.effects.process(effects, context_npc)

        result_name = None
        if result_id:
            result_obj["location"] = LOC_INVENTORY
            result_name = result_obj[ATTR_NAME]

        message = recipe.get("message")
        if not message and result_name:
            message = f"Hergestellt: {result_name}"
        return CraftResult(True, message or "Aktion ausgeführt.")

    def _inventory_entities(self, identifier):
        return [
            entity
            for entity in self.game.objects.values()
            if entity.get("location") == LOC_INVENTORY
            and identifier in self._identifiers(entity)
        ]

    def _find_inventory_entity(self, identifier):
        return next(iter(self._inventory_entities(identifier)), None)

    def _find_entity_by_identifier(self, identifier):
        for entity in list(self.game.objects.values()) + list(self.game.npcs):
            if identifier in self._identifiers(entity):
                return entity
        return None

    def _find_obj_or_npc_by_name(self, name):
        normalized = name.lower().strip()
        candidates = [
            obj
            for obj in self.game.objects.values()
            if obj.get("location") in {LOC_INVENTORY, self.game.location}
        ]
        candidates.extend(
            npc for npc in self.game.npcs if npc.get("location") == self.game.location
        )

        for entity in candidates:
            if entity[ATTR_NAME].lower() == normalized:
                return entity
        for entity in candidates:
            if any(alias.lower() == normalized for alias in entity.get(ATTR_ALIASES, [])):
                return entity
        matches = [
            entity
            for entity in candidates
            if normalized and normalized in entity[ATTR_NAME].lower()
        ]
        return matches[0] if len(matches) == 1 else None
