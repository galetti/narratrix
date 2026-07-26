import copy
import contextlib
import io
import os
import unittest
from unittest.mock import patch

from engine.analysis import generate_future_matrix
from engine.game_state import GameState
from engine.handlers.dialogue import DialogueHandler
from engine.handlers.mechanics import MechanicsHandler
from engine.handlers.movement import MovementHandler
from engine.handlers.system import SystemHandler
from engine.schema import ConfigurationError, validate_game_config
from engine.story_loader import StoryLoader


EP0 = "data.chapters.ep0_test_lab.config"
EP1 = "data.chapters.ep1_deep_zero.config"


class NarratrixEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ep0 = StoryLoader.load_chapter(EP0, raise_on_error=True)
        cls.ep1 = StoryLoader.load_chapter(EP1, raise_on_error=True)

    def test_chapters_validate_and_intro_is_loaded(self):
        validate_game_config(copy.deepcopy(self.ep0))
        validate_game_config(copy.deepcopy(self.ep1))
        game = GameState(self.ep1)
        texts = [entry["text"] for entry in game.logs]
        self.assertTrue(any("Andockklammern" in text for text in texts))
        self.assertTrue(any("C.O.R.E." in text for text in texts))

    def test_json_chapter_from_world_editor_is_loadable(self):
        fixture = os.path.join(
            os.path.dirname(__file__), "fixtures", "minimal_chapter.json"
        )
        config = StoryLoader.load_chapter(fixture, raise_on_error=True)
        self.assertEqual(config["meta"]["name"], "JSON Fixture")
        self.assertIn("json_room", config["rooms"])

    def test_crafting_consumes_resources_and_spawns_result(self):
        game = GameState(self.ep0, silent=True)
        game.location = "lower_deck"
        game.objects["scrap_metal_1"]["location"] = "inventory"
        game.objects["wire_coil"]["location"] = "inventory"

        result = game.perform_combine("Metallschrott", "Werkbank")

        self.assertTrue(result.success)
        self.assertEqual(game.objects["scrap_metal_1"]["count"], 1)
        self.assertEqual(game.objects["wire_coil"]["count"], 1)
        self.assertEqual(
            game.objects["improvised_shiv"]["location"], "inventory"
        )
        second = game.perform_combine("Metallschrott", "Werkbank")
        self.assertFalse(second.success)
        self.assertEqual(game.objects["scrap_metal_1"]["count"], 1)

    def test_rusty_flow_respects_height_updates_quest_and_stops_noise(self):
        game = GameState(self.ep1)
        game.events.trigger_event_by_id("quest_start_rusty")
        game.location = "room_outer_waste"
        game.objects["tool_wrench"]["location"] = "inventory"
        rusty = next(npc for npc in game.npcs if npc["id"] == "rusty")

        MechanicsHandler.break_(game, ["Rusty", "mit", "Rohrzange"])
        self.assertEqual(rusty["state"], "malfunction")
        self.assertIn("Ebene 2", game.logs[-1]["text"])

        game.elevation = 2
        MechanicsHandler.break_(game, ["Rusty", "mit", "Rohrzange"])
        self.assertEqual(rusty["state"], "disabled")
        self.assertEqual(game.quests.states["noise_pollution"]["stage"], 1)
        state_logs = [
            entry
            for entry in game.logs
            if "Rusty" in entry["text"] and "wirkt verändert" in entry["text"]
        ]
        self.assertEqual(len(state_logs), 1)

        log_start = len(game.logs)
        game.tick(1)
        self.assertFalse(
            any("KRK-KLONG" in entry["text"] for entry in game.logs[log_start:])
        )

    def test_reward_items_and_explicit_quest_completion(self):
        game = GameState(self.ep1)
        game.events.trigger_event_by_id("quest_start_rusty")
        game.events.trigger_event_by_id("rusty_shutdown")
        sato = next(npc for npc in game.npcs if npc["id"] == "sato")
        reward = sato["dialogue"]["grateful"]["reward"]["effect"]

        game.effects.process(reward, context_npc=sato)

        self.assertEqual(game.objects["keycard_quarters"]["location"], "inventory")
        self.assertEqual(game.objects["tool_omni"]["location"], "inventory")
        self.assertEqual(
            game.quests.states["noise_pollution"]["status"], "completed"
        )
        self.assertTrue(game.game_over)

    def test_map_tracks_visited_rooms_and_empty_move_is_safe(self):
        game = GameState(self.ep1)
        MovementHandler.handle(game, [])
        self.assertEqual(game.logs[-1]["text"], "Wohin willst du gehen?")
        MovementHandler.handle(game, ["east"])
        SystemHandler.map(game, [])

        self.assertTrue(game.rooms["room_outer_docking"]["visited"])
        self.assertTrue(game.rooms["room_inner_corridor_north"]["visited"])
        map_output = "\n".join(entry["text"] for entry in game.logs)
        self.assertIn("Hangar Bay 4", map_output)
        self.assertIn("Innerer Ring (Nord)", map_output)

    def test_object_behavior_is_connected_to_tick(self):
        config = copy.deepcopy(self.ep0)
        config["objects"]["red_key"]["behavior"] = {
            "type": "random_open_close",
            "chance": 100,
        }
        config["objects"]["red_key"]["is_open"] = False
        game = GameState(config, silent=True)

        with patch("engine.systems.object_behavior.rng.chance", return_value=True):
            game.tick(1)

        self.assertTrue(game.objects["red_key"]["is_open"])

    def test_idle_npc_does_not_investigate_noise(self):
        game = GameState(self.ep1, silent=True)
        sato = next(npc for npc in game.npcs if npc["id"] == "sato")
        for _ in range(5):
            game.tick(1)
        self.assertEqual(sato["location"], "room_inner_corridor_north")

    def test_hidden_dialogue_topic_cannot_bypass_visibility(self):
        game = GameState(self.ep1)
        sato = next(npc for npc in game.npcs if npc["id"] == "sato")
        sato["dialogue"]["working"]["secret"] = {
            "hidden": True,
            "text": "Geheimnis",
            "effect": {"type": "learn", "fact": "secret_learned"},
        }
        game.dialogue_system.start_dialogue(sato)

        DialogueHandler.step(game, "secret")

        self.assertNotIn("secret_learned", game.knowledge)

    def test_save_roundtrip_and_chapter_guard(self):
        game = GameState(self.ep1)
        MovementHandler.handle(game, ["east"])
        game.events.trigger_event_by_id("quest_start_rusty")
        saved = game.serialize_state()

        restored = GameState(self.ep1, silent=True)
        self.assertTrue(restored.deserialize_state(saved))
        self.assertEqual(restored.location, game.location)
        self.assertEqual(restored.time, game.time)
        self.assertEqual(restored.quests.states, game.quests.states)

        other_chapter = GameState(self.ep0, silent=True)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertFalse(other_chapter.deserialize_state(saved))
        with self.assertRaises(ValueError):
            SystemHandler._save_filename(["../../outside"])

    def test_future_matrix_uses_event_manager_timestamps(self):
        config = copy.deepcopy(self.ep1)
        config["events"].append(
            {
                "id": "future_test",
                "trigger": "time",
                "trigger_time": 10,
                "origin_id": "room_outer_docking",
                "title": "Zukunft",
            }
        )
        validate_game_config(config)
        game = GameState(config, silent=True)

        timeline = generate_future_matrix(game, minutes_to_simulate=10, step_size=5)

        self.assertIn(
            "Zukunft",
            timeline[-1]["rooms"]["room_outer_docking"]["events"],
        )

    def test_schema_rejects_key_id_mismatch(self):
        config = copy.deepcopy(self.ep1)
        config["objects"]["tool_wrench"]["id"] = "wrong_id"
        with self.assertRaises(ConfigurationError):
            validate_game_config(config)


if __name__ == "__main__":
    unittest.main()
