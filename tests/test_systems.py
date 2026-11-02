from __future__ import annotations

import copy
from typing import Any
import unittest

from engine.action_dispatcher import ActionDispatcher
from engine.game_state import GameState
from engine.handlers.exploration import ExplorationHandler
from engine.parser.rule_based import RuleBasedParser
from engine.story_loader import StoryLoader
from engine.systems.acoustics import AcousticsSystem
from engine.systems.ai import (
    Action,
    AISystem,
    Condition,
    Selector,
    Sequence,
)


EP0: str = "data.chapters.ep0_test_lab.config"
EP1: str = "data.chapters.ep1_deep_zero.config"


class RuleBasedParserTests(unittest.TestCase):
    game_config: dict[str, Any]

    @classmethod
    def setUpClass(cls) -> None:
        config = StoryLoader.load_chapter(EP0, raise_on_error=True)
        assert config is not None
        cls.game_config = config

    def setUp(self) -> None:
        self.game = GameState(copy.deepcopy(self.game_config))
        self.parser = RuleBasedParser(self.game)

    def test_empty_and_punctuation_inputs_are_safe(self) -> None:
        self.parser.parse("")
        self.parser.parse("   ")
        self.parser.parse("...,,,!?;;")
        self.assertEqual(self.game.location, "central_hub")

    def test_short_direction_commands_navigate(self) -> None:
        self.parser.parse("n")
        self.assertEqual(self.game.location, "test_chamber")
        self.parser.parse("s")
        self.assertEqual(self.game.location, "central_hub")

    def test_canonical_and_synonym_verbs(self) -> None:
        self.parser.parse("schaue")
        self.assertTrue(any("Zentraler Test-Hub" in entry["text"] for entry in self.game.logs))

        self.parser.parse("nimm Greifzange")
        self.assertEqual(self.game.objects["grabber"]["location"], "inventory")

    def test_fuzzy_verb_matching_handles_minor_typos(self) -> None:
        # "inwentar" -> "inventar"
        self.parser.parse("inwentar")
        self.assertTrue(any("Inventar" in entry["text"] for entry in self.game.logs))

        # "nehme" -> "nehmen" -> "take"
        self.parser.parse("nehme Greifzange")
        self.assertEqual(self.game.objects["grabber"]["location"], "inventory")

    def test_pending_interaction_and_disambiguation_forwarding(self) -> None:
        self.game.pending_interaction = {"verb": "use", "args": ["Greifzange"]}
        self.parser.parse("mit Wartungsleiter")
        self.assertIsNone(self.game.pending_interaction)


class AcousticsSystemTests(unittest.TestCase):
    game_config: dict[str, Any]

    @classmethod
    def setUpClass(cls) -> None:
        config = StoryLoader.load_chapter(EP1, raise_on_error=True)
        assert config is not None
        cls.game_config = config

    def setUp(self) -> None:
        self.game = GameState(copy.deepcopy(self.game_config), silent=True)
        self.acoustics = AcousticsSystem(self.game)

    def test_same_room_audibility_is_maximum(self) -> None:
        volume, direction = self.acoustics.get_audibility_info(
            "room_outer_docking", "room_outer_docking"
        )
        self.assertEqual(volume, 1.0)
        self.assertEqual(direction, "hier")

    def test_adjacent_room_audibility_and_direction(self) -> None:
        # room_outer_docking hat Exit "east" -> room_inner_corridor_north
        # Aus Sicht von room_inner_corridor_north kommt der Schall von room_outer_docking
        volume, direction = self.acoustics.get_audibility_info(
            source_room_id="room_outer_docking",
            listener_room_id="room_inner_corridor_north",
        )
        self.assertGreater(volume, 0.0)
        self.assertIn("Westen", direction)

    def test_door_damping_reduces_transmission(self) -> None:
        # Schott zur Luftschleuse/Hangar mit Tür-Dämpfung
        self.game.objects["docking_airlock_door"] = {
            "id": "docking_airlock_door",
            "name": "Schott",
            "location": "room_inner_corridor_north",
            "linked_exit": "west",
            "is_open": False,
            "acoustic_damping": 0.2,
        }
        vol_closed, _ = self.acoustics.get_audibility_info(
            "room_outer_docking", "room_inner_corridor_north", use_player_tools=False
        )

        self.game.objects["docking_airlock_door"]["is_open"] = True
        vol_open, _ = self.acoustics.get_audibility_info(
            "room_outer_docking", "room_inner_corridor_north", use_player_tools=False
        )

        self.assertGreater(vol_open, vol_closed)

    def test_player_tool_bonus_amplifies_faint_sound(self) -> None:
        self.game.objects["test_scanner"] = {
            "id": "test_scanner",
            "name": "Verstärker",
            "location": "inventory",
            "acoustic_boost": 0.3,
        }
        vol_boosted, _ = self.acoustics.get_audibility_info(
            "room_outer_waste", "room_inner_corridor_north", use_player_tools=True
        )
        vol_raw, _ = self.acoustics.get_audibility_info(
            "room_outer_waste", "room_inner_corridor_north", use_player_tools=False
        )
        self.assertGreaterEqual(vol_boosted, vol_raw)

    def test_symmetric_exit_transmission_with_door(self) -> None:
        self.game.rooms["room_test_a"] = {
            "id": "room_test_a",
            "name": "Raum A",
            "exits": {"east": "room_test_b"},
            "acoustics": {},
        }
        self.game.rooms["room_test_b"] = {
            "id": "room_test_b",
            "name": "Raum B",
            "exits": {"west": "room_test_a"},
            "acoustics": {},
        }
        self.game.objects["test_door"] = {
            "id": "test_door",
            "name": "Schott",
            "location": "room_test_a",
            "linked_exit": "east",
            "is_open": False,
            "acoustic_damping": 0.15,
        }
        vol_a_to_b, _ = self.acoustics.get_audibility_info(
            "room_test_a", "room_test_b", use_player_tools=False
        )
        vol_b_to_a, _ = self.acoustics.get_audibility_info(
            "room_test_b", "room_test_a", use_player_tools=False
        )
        self.assertAlmostEqual(vol_a_to_b, vol_b_to_a, places=2)


class AISystemTests(unittest.TestCase):
    game_config: dict[str, Any]

    @classmethod
    def setUpClass(cls) -> None:
        config = StoryLoader.load_chapter(EP0, raise_on_error=True)
        assert config is not None
        cls.game_config = config

    def setUp(self) -> None:
        self.game = GameState(copy.deepcopy(self.game_config), silent=True)
        self.ai = AISystem(self.game)

    def test_behavior_tree_primitives(self) -> None:
        test_npc = self.game.npcs[0]

        # Action Node
        action_true = Action(lambda npc, ai: True)
        action_false = Action(lambda npc, ai: False)
        self.assertTrue(action_true.execute(test_npc, self.ai))
        self.assertFalse(action_false.execute(test_npc, self.ai))

        # Condition Node
        cond = Condition(lambda npc, ai, val: val == 42, 42)
        self.assertTrue(cond.execute(test_npc, self.ai))

        # Selector: erstes True bricht ab
        selector = Selector([action_false, action_true, action_false])
        self.assertTrue(selector.execute(test_npc, self.ai))

        # Sequence: erstes False bricht ab
        sequence = Sequence([action_true, action_false])
        self.assertFalse(sequence.execute(test_npc, self.ai))

    def test_idle_npc_does_not_wander(self) -> None:
        drone = next(npc for npc in self.game.npcs if npc["id"] == "shy_drone")
        start_loc = drone["location"]
        drone["behavior_id"] = "idle"

        self.ai.process_all_npcs(minutes=5)
        self.assertEqual(drone["location"], start_loc)

    def test_fearful_npc_flees_from_player_presence(self) -> None:
        drone = next(npc for npc in self.game.npcs if npc["id"] == "shy_drone")
        self.game.location = "test_chamber"
        drone["location"] = "test_chamber"
        drone["behavior_id"] = "fearful"

        # Tick 1: AI registriert Spieler und plant Fluchtweg
        self.ai.process_all_npcs(minutes=1)
        self.assertIsNotNone(drone.get("target_location"))

        # Tick 2: Bewegung wird ausgeführt -> Drohne hat Raum verlassen
        self.ai.process_all_npcs(minutes=1)
        self.assertNotEqual(drone["location"], "test_chamber")


class EffectProcessorAndListenTests(unittest.TestCase):
    game_config: dict[str, Any]

    @classmethod
    def setUpClass(cls) -> None:
        config = StoryLoader.load_chapter(EP0, raise_on_error=True)
        assert config is not None
        cls.game_config = config

    def setUp(self) -> None:
        self.game = GameState(copy.deepcopy(self.game_config), silent=False)

    def test_move_player_effect(self) -> None:
        self.assertEqual(self.game.location, "central_hub")
        self.game.effects.process({"type": "move_player", "target": "lower_deck"})
        self.assertEqual(self.game.location, "lower_deck")

    def test_listen_bare_and_with_glass(self) -> None:
        # 1. Zu Beginn: Schutztür zu, kein Laut dringt durch
        ExplorationHandler.listen(self.game, ["an", "Vorraum-Tür"])
        logs_before = [entry["text"] for entry in self.game.logs if entry["type"] == "info"]
        self.assertTrue(any("vollkommen still" in msg for msg in logs_before))

        # 2. Schutztür verkeilt, Vorraum-Tür verriegelt
        self.game.quests.start_quest("investigate_sabotage")
        self.game.objects["soundproof_door"]["is_open"] = True
        self.game.objects["soundproof_door"]["jammed"] = True
        self.game.objects["anteroom_door"]["is_open"] = False
        self.game.objects["anteroom_door"]["is_locked"] = True
        self.game.add_knowledge("soundproof_door_wedged")

        # Lauschen ohne Glas: gedämpftes Gemurmel
        ExplorationHandler.listen(self.game, ["an", "Vorraum-Tür"])
        logs_muffled = [entry["text"] for entry in self.game.logs if entry["type"] == "info"]
        self.assertTrue(any("gedämpftes Gemurmel" in msg for msg in logs_muffled))

        # Lauschen mit Akustik-Glas: glasklares Belauschen der Sabotage
        self.game.objects["amplifying_glass"]["location"] = "inventory"
        ExplorationHandler.listen(self.game, ["an", "Vorraum-Tür", "mit", "Akustik-Glas"])
        self.assertIn("sabotage_plan_uncovered", self.game.knowledge)
        self.assertEqual(
            self.game.quests.states["investigate_sabotage"]["status"], "completed"
        )


if __name__ == "__main__":
    unittest.main()
