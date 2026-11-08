from __future__ import annotations

import copy
from typing import Any
import unittest
from unittest.mock import patch

from engine.action_dispatcher import ActionDispatcher
from engine.access import is_directly_reachable
from engine.analysis import validate_quest_state_graph
from engine.constants import FILTER_ROOM, LOC_INVENTORY, MATTER_LIQUID, TYPE_CONTAINER, TYPE_SURFACE
from engine.game_state import GameState
from engine.handlers.exploration import ExplorationHandler
from engine.handlers.inventory import InventoryHandler
from engine.handlers.mechanics import MechanicsHandler
from engine.handlers.movement import MovementHandler
from engine.resolver import Resolver
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
from engine.systems.llm_grounding import (
    build_prompts,
    build_world_context,
    preserves_core_facts,
    sanitize_reply,
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
        self.game = GameState(copy.deepcopy(self.game_config), silent=False)
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
        self.game = GameState(copy.deepcopy(self.game_config), silent=False)
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

    def test_connecting_door_two_way_resolution_and_blocking(self) -> None:
        self.game.location = "briefing_anteroom"
        # 1. Vorraum-Tür muss im Vorraum auffindbar sein, obwohl location == central_hub
        resolved = Resolver.resolve_target(self.game, ["vorraum-tür"], location_filter=FILTER_ROOM)
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved["id"], "anteroom_door")

        # 2. Wenn Vorraum-Tür geschlossen ist, muss Rückweg nach Osten blockiert sein
        self.game.objects["anteroom_door"]["is_open"] = False
        MovementHandler.handle(self.game, ["east"])
        self.assertEqual(self.game.location, "briefing_anteroom")
        error_logs = [entry["text"] for entry in self.game.logs if entry["type"] == "error"]
        self.assertTrue(any("Vorraum-Tür" in msg for msg in error_logs))

    def test_custom_locked_msg_on_open(self) -> None:
        self.game.location = "briefing_anteroom"
        MechanicsHandler.open(self.game, ["schallschutztür"])
        error_logs = [entry["text"] for entry in self.game.logs if entry["type"] == "error"]
        self.assertTrue(any("Hydraulikfeder" in msg for msg in error_logs))


class LLMGroundingAndDialogueTests(unittest.TestCase):
    game_config: dict[str, Any]

    @classmethod
    def setUpClass(cls) -> None:
        config = StoryLoader.load_chapter(EP1, raise_on_error=True)
        assert config is not None
        cls.game_config = config

    def setUp(self) -> None:
        self.game = GameState(copy.deepcopy(self.game_config), silent=False)
        self.game.config["use_llm_dialogue"] = True
        self.npc = self.game.npcs[0]
        self.game.location = self.npc["location"]

    def test_english_prompts_and_central_language_config(self) -> None:
        self.game.config["language"] = "de"
        sys_de, user_de = build_prompts(
            self.game, self.npc, core_text="Der Code lautet 4210."
        )
        self.assertIn("WORLD FACTS (authoritative, complete):", sys_de)
        self.assertIn("Respond ONLY in German (language code: 'de').", sys_de)
        self.assertEqual(user_de, "Core statement: Der Code lautet 4210.")

        self.game.config["language"] = "en"
        sys_en, user_en = build_prompts(
            self.game, self.npc, player_text="Where is the reactor?"
        )
        self.assertIn("Respond ONLY in English (language code: 'en').", sys_en)
        self.assertNotIn("Where is the reactor?", sys_en)
        self.assertEqual(user_en, "The player says: Where is the reactor?")

    def test_world_context_tracks_inventory_and_stability(self) -> None:
        first_obj = next(iter(self.game.objects.values()))
        first_obj["location"] = "inventory"
        self.game.stability = 35
        ctx = build_world_context(self.game, self.npc, known_facts=["Sektor B ist kalt."])
        self.assertIn(first_obj["name"], ctx)
        self.assertIn("stress level: HIGH", ctx)
        self.assertIn("- Sektor B ist kalt.", ctx)

    def test_sanitize_and_numeric_fact_guardrails(self) -> None:
        self.assertEqual(
            sanitize_reply("<think>internal</think> Dr. Sato: \"Alles ruhig.\"", "Dr. Sato"),
            "Alles ruhig.",
        )
        self.assertIsNone(sanitize_reply("Als KI kann ich das nicht beantworten."))
        self.assertTrue(preserves_core_facts("Code 4210 für Sektor 7.", "Nutze 4210 in Sektor 7!"))
        self.assertFalse(preserves_core_facts("Code 4210.", "Ich kenne den Code nicht."))

    def test_dialogue_falls_back_when_llm_drops_numbers_or_fails(self) -> None:
        with patch("engine.systems.dialogue_system.LLMBridge.call", return_value="Gehe zum Schott."):
            self.game.dialogue_system.print_dialogue(
                self.npc, "Der Zugangscode ist 7741."
            )
        self.assertIn("7741", self.game.logs[-1]["text"])

        with patch("engine.systems.dialogue_system.LLMBridge.call", return_value=None):
            self.game.dialogue_system.print_dialogue(
                self.npc, "LLM_AUTO_REPLY", prompt_context="Test?"
            )
        self.assertNotIn("LLM_AUTO_REPLY", self.game.logs[-1]["text"])


class QuestBranchingAndStateTreeTests(unittest.TestCase):
    game_config: dict[str, Any]

    @classmethod
    def setUpClass(cls) -> None:
        config = StoryLoader.load_chapter(EP0, raise_on_error=True)
        assert config is not None
        cls.game_config = config

    def setUp(self) -> None:
        cfg = copy.deepcopy(self.game_config)
        cfg["quests"]["branching_crisis"] = {
            "title": "Krise im Sektor",
            "start_stage": 0,
            "stages": {
                0: "Entscheide über das Vorgehen.",
                10: "Diplomatischer Pfad gewählt.",
                20: "Sabotage-Pfad gewählt.",
                30: "Abschlussphase.",
            },
            "transitions": {
                0: [10, 20],
                10: [30],
                20: [30],
                30: [],
            },
            "outcomes": {
                "peaceful": "Krise friedlich gelöst.",
                "sabotaged": "Sektor durch Sabotage gesichert.",
                "compromised": "Mission enttarnt.",
            },
            "exclusive_with": ["rival_protocol"],
        }
        cfg["quests"]["rival_protocol"] = {
            "title": "Konkurrenz-Protokoll",
            "start_stage": 0,
            "stages": {0: "Folge dem Sicherheitsprotokoll."},
            "exclusive_with": ["branching_crisis"],
        }
        self.game = GameState(cfg, silent=False)

    def test_branching_transitions_history_and_outcomes(self) -> None:
        self.assertTrue(self.game.quests.start_quest("branching_crisis"))
        # Direkter Sprung auf 30 ist laut transitions nicht erlaubt
        self.assertFalse(self.game.quests.update_quest("branching_crisis", 30))
        # Wahl von Pfad 10 ist erlaubt
        self.assertTrue(self.game.quests.update_quest("branching_crisis", 10))
        # Wechsel auf den exklusiven Nachbarzweig 20 ist von 10 aus gesperrt
        self.assertFalse(self.game.quests.update_quest("branching_crisis", 20))
        # Weiter zu 30 ist erlaubt
        self.assertTrue(self.game.quests.update_quest("branching_crisis", 30))
        self.assertEqual(
            self.game.quests.states["branching_crisis"]["history"], [0, 10, 30]
        )

        # Abschluss mit benanntem Outcome
        self.game.effects.process(
            {"type": "quest_complete", "id": "branching_crisis", "outcome": "peaceful"}
        )
        state = self.game.quests.states["branching_crisis"]
        self.assertEqual(state["status"], "completed")
        self.assertEqual(state["outcome"], "peaceful")

        # Komposite State-Tree-Bedingung prüft visited_stage + outcome + Negation
        tree_cond: dict[str, Any] = {
            "type": "all",
            "conditions": [
                {
                    "type": "quest_state",
                    "quest": "branching_crisis",
                    "status": "completed",
                    "outcome": "peaceful",
                    "visited_stage": 10,
                },
                {
                    "type": "quest_state",
                    "quest": "branching_crisis",
                    "visited_stage": 20,
                    "not": True,
                },
            ],
        }
        self.assertTrue(self.game.events.evaluate_condition(tree_cond))

    def test_mutually_exclusive_quests_auto_fail_and_block(self) -> None:
        self.assertTrue(self.game.quests.start_quest("rival_protocol"))
        self.assertEqual(self.game.quests.states["rival_protocol"]["status"], "active")
        # Start der exklusiven Gegen-Quest lässt rival_protocol fehlschlagen
        self.assertTrue(self.game.quests.start_quest("branching_crisis"))
        self.assertEqual(self.game.quests.states["rival_protocol"]["status"], "failed")
        self.game.quests.complete_quest("branching_crisis", outcome="sabotaged")

    def test_state_graph_validator_on_chapters_and_broken_graphs(self) -> None:
        self.assertEqual(validate_quest_state_graph(self.game.config), [])

        broken = copy.deepcopy(self.game.config)
        broken["quests"]["broken_quest"] = {
            "title": "Defekte Quest",
            "start_stage": 0,
            "stages": {0: "Start", 1: "Schleife A", 2: "Schleife B", 99: "Waisen-Stage"},
            "transitions": {0: [1], 1: [2], 2: [1]},
            "outcomes": {"ok": "Okay"},
            "exclusive_with": ["rival_protocol"],
        }
        broken["events"].append(
            {
                "id": "bad_cond_ev",
                "trigger": "condition",
                "condition": {
                    "type": "all",
                    "conditions": [
                        {"type": "quest_state", "quest": "broken_quest", "stage": 99},
                        {"type": "quest_state", "quest": "broken_quest", "outcome": "missing"},
                    ],
                },
            }
        )
        issues = validate_quest_state_graph(broken)
        self.assertTrue(any("Nicht erreichbare Stages" in msg for msg in issues))
        self.assertTrue(any("Endlosschleife" in msg for msg in issues))
        self.assertTrue(any("Asymmetrische exclusive_with" in msg for msg in issues))
        self.assertTrue(any("unerreichbar" in msg for msg in issues))
        self.assertTrue(any("kein Outcome 'missing'" in msg for msg in issues))


class PhysicsAndSimulationStressTests(unittest.TestCase):
    game_config: dict[str, Any]

    @classmethod
    def setUpClass(cls) -> None:
        config = StoryLoader.load_chapter(EP0, raise_on_error=True)
        assert config is not None
        cls.game_config = config

    def setUp(self) -> None:
        self.game = GameState(copy.deepcopy(self.game_config), silent=False)
        room_id = self.game.location
        self.game.objects["test_scale"] = {
            "id": "test_scale",
            "name": "Präzisionswaage",
            "desc": "Eine digitale Waage.",
            "type": TYPE_SURFACE,
            "is_scale": True,
            "location": room_id,
            "weight": float("inf"),
            "level": 0,
        }
        self.game.objects["small_pouch"] = {
            "id": "small_pouch",
            "name": "Lederbeutel",
            "desc": "Ein kleiner Beutel.",
            "type": TYPE_CONTAINER,
            "is_open": True,
            "location": LOC_INVENTORY,
            "weight": 0.5,
            "max_weight": 3.0,
            "level": 0,
        }
        self.game.objects["inner_case"] = {
            "id": "inner_case",
            "name": "Metallkassette",
            "desc": "Eine robuste Kassette.",
            "type": TYPE_CONTAINER,
            "is_open": True,
            "location": LOC_INVENTORY,
            "weight": 1.0,
            "max_weight": 10.0,
            "level": 0,
        }
        self.game.objects["lead_ingot"] = {
            "id": "lead_ingot",
            "name": "Bleibarren",
            "desc": "Schweres Blei.",
            "type": "item",
            "location": LOC_INVENTORY,
            "weight": 2.0,
            "level": 0,
        }
        self.game.objects["heavy_anvil"] = {
            "id": "heavy_anvil",
            "name": "Stahlblock",
            "desc": "Extrem schwer.",
            "type": "item",
            "location": LOC_INVENTORY,
            "weight": 25.0,
            "level": 0,
        }
        self.game.objects["raw_acid"] = {
            "id": "raw_acid",
            "name": "Säurepfütze",
            "desc": "Ätzende Flüssigkeit.",
            "type": "item",
            "matter": MATTER_LIQUID,
            "location": room_id,
            "weight": 1.0,
            "level": 0,
        }

    def test_nested_container_scale_weight_and_cyclic_guard(self) -> None:
        # Bleibarren (2kg) in Lederbeutel (0.5kg), Lederbeutel in Metallkassette (1kg)
        MechanicsHandler.put(self.game, ["Bleibarren", "in", "Lederbeutel"])
        self.assertEqual(self.game.objects["lead_ingot"]["location"], "small_pouch")
        MechanicsHandler.put(self.game, ["Lederbeutel", "in", "Metallkassette"])
        self.assertEqual(self.game.objects["small_pouch"]["location"], "inner_case")

        # Zyklische Verschachtelung (Metallkassette in Lederbeutel) muss scheitern
        self.game.objects["small_pouch"]["location"] = LOC_INVENTORY
        self.game.objects["inner_case"]["location"] = "small_pouch"
        MechanicsHandler.put(self.game, ["Lederbeutel", "in", "Metallkassette"])
        self.assertEqual(self.game.objects["small_pouch"]["location"], LOC_INVENTORY)

        # Korrekte Schachtelung auf die Waage legen -> 1.0 + 0.5 + 2.0 = 3.5 kg
        self.game.objects["inner_case"]["location"] = LOC_INVENTORY
        self.game.objects["small_pouch"]["location"] = "inner_case"
        self.game.objects["lead_ingot"]["location"] = "small_pouch"
        MechanicsHandler.put(self.game, ["Metallkassette", "auf", "Präzisionswaage"])
        self.assertEqual(self.game.objects["inner_case"]["location"], "test_scale")

        self.assertTrue(
            self.game.events.evaluate_condition(
                {"type": "scale_weight", "id": "test_scale", "value": 3.5}
            )
        )
        ExplorationHandler.look(self.game, ["Präzisionswaage"])
        self.assertIn("3.50 kg", self.game.logs[-1]["text"])

    def test_container_capacity_and_liquid_surface_constraints(self) -> None:
        # 25kg Stahlblock passt nicht in 3kg-Lederbeutel
        MechanicsHandler.put(self.game, ["Stahlblock", "in", "Lederbeutel"])
        self.assertEqual(self.game.objects["heavy_anvil"]["location"], LOC_INVENTORY)

        # Flüssigkeit im Raum nicht mit bloßen Händen nehmbar
        InventoryHandler.take(self.game, ["Säurepfütze"])
        self.assertNotEqual(self.game.objects["raw_acid"]["location"], LOC_INVENTORY)

        # Flüssigkeit im Inventar darf nicht auf flache Oberfläche (Waage) gelegt werden,
        # wohl aber in einen offenen Behälter (Metallkassette)
        self.game.objects["raw_acid"]["location"] = LOC_INVENTORY
        MechanicsHandler.put(self.game, ["Säurepfütze", "auf", "Präzisionswaage"])
        self.assertEqual(self.game.objects["raw_acid"]["location"], LOC_INVENTORY)
        MechanicsHandler.put(self.game, ["Säurepfütze", "in", "Metallkassette"])
        self.assertEqual(self.game.objects["raw_acid"]["location"], "inner_case")

    def test_elevation_and_closed_container_reachability_invariants(self) -> None:
        # Kassette steht im Raum auf Ebene 0, Bleibarren liegt darin
        self.game.objects["inner_case"]["location"] = self.game.location
        self.game.objects["lead_ingot"]["location"] = "inner_case"
        self.assertTrue(is_directly_reachable(self.game, self.game.objects["lead_ingot"]))

        # Kassette schließen -> Inhalt ist physisch nicht mehr direkt greifbar
        self.game.objects["inner_case"]["is_open"] = False
        self.assertFalse(is_directly_reachable(self.game, self.game.objects["lead_ingot"]))

        # Kassette wieder öffnen, aber auf Ebene 3 verschieben -> vom Boden (Ebene 0) unerreichbar
        self.game.objects["inner_case"]["is_open"] = True
        self.game.objects["inner_case"]["level"] = 3
        self.assertFalse(is_directly_reachable(self.game, self.game.objects["lead_ingot"]))
        MechanicsHandler.put(self.game, ["Lederbeutel", "in", "Metallkassette"])
        self.assertEqual(self.game.objects["small_pouch"]["location"], LOC_INVENTORY)


if __name__ == "__main__":
    unittest.main()
