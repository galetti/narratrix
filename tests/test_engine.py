from __future__ import annotations

import ast
import copy
import os
from pathlib import Path
from typing import Any
import unittest
from unittest.mock import patch

from engine.action_dispatcher import ActionDispatcher
from engine.analysis import generate_future_matrix
from engine.game_state import GameState
from engine.handlers.dialogue import DialogueHandler
from engine.handlers.exploration import ExplorationHandler
from engine.handlers.inventory import InventoryHandler
from engine.handlers.mechanics import MechanicsHandler
from engine.handlers.movement import MovementHandler
from engine.handlers.system import SystemHandler
from engine.parser.spacy_parser import SpacyParser
from engine.schema import ConfigurationError, validate_game_config
from engine.story_loader import StoryLoader
from engine.ui import RichTextRenderer, load_system_config


EP0: str = "data.chapters.ep0_test_lab.config"
EP1: str = "data.chapters.ep1_deep_zero.config"
EP2: str = "data.chapters.ep2_habitat_sector.config"
EP3: str = "data.chapters.ep3_reactor_core.config"


class NarratrixEngineTests(unittest.TestCase):
    ep0: dict[str, Any]
    ep1: dict[str, Any]
    ep2: dict[str, Any]
    ep3: dict[str, Any]

    @classmethod
    def setUpClass(cls) -> None:
        ep0 = StoryLoader.load_chapter(EP0, raise_on_error=True)
        ep1 = StoryLoader.load_chapter(EP1, raise_on_error=True)
        ep2 = StoryLoader.load_chapter(EP2, raise_on_error=True)
        ep3 = StoryLoader.load_chapter(EP3, raise_on_error=True)
        assert ep0 is not None and ep1 is not None and ep2 is not None and ep3 is not None
        cls.ep0 = ep0
        cls.ep1 = ep1
        cls.ep2 = ep2
        cls.ep3 = ep3

    def test_chapters_validate_and_intro_is_loaded(self) -> None:
        validate_game_config(copy.deepcopy(self.ep0))
        validate_game_config(copy.deepcopy(self.ep1))
        validate_game_config(copy.deepcopy(self.ep2))
        validate_game_config(copy.deepcopy(self.ep3))
        game = GameState(self.ep1)
        texts = [entry["text"] for entry in game.logs]
        self.assertTrue(any("Andockklammern" in text for text in texts))
        self.assertTrue(any("C.O.R.E." in text for text in texts))

    def test_json_chapter_from_world_editor_is_loadable(self) -> None:
        fixture = os.path.join(
            os.path.dirname(__file__), "fixtures", "minimal_chapter.json"
        )
        config = StoryLoader.load_chapter(fixture, raise_on_error=True)
        assert config is not None
        self.assertEqual(config["meta"]["name"], "JSON Fixture")
        self.assertIn("json_room", config["rooms"])

    def test_crafting_consumes_resources_and_spawns_result(self) -> None:
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

    def test_rusty_flow_respects_height_updates_quest_and_stops_noise(self) -> None:
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

    def test_reward_items_and_explicit_quest_completion(self) -> None:
        game = GameState(self.ep1)
        game.events.trigger_event_by_id("quest_start_rusty")
        game.events.trigger_event_by_id("rusty_shutdown")
        sato = next(npc for npc in game.npcs if npc["id"] == "sato")
        reward_entry = sato["dialogue"]["grateful"]["reward"]
        assert isinstance(reward_entry, dict)
        reward = reward_entry["effect"]

        game.effects.process(reward, context_npc=sato)

        self.assertEqual(game.objects["keycard_quarters"]["location"], "inventory")
        self.assertEqual(game.objects["tool_omni"]["location"], "inventory")
        self.assertEqual(
            game.quests.states["noise_pollution"]["status"], "completed"
        )
        self.assertTrue(game.game_over)

    def test_map_tracks_visited_rooms_and_empty_move_is_safe(self) -> None:
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

    def test_object_behavior_is_connected_to_tick(self) -> None:
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

    def test_idle_npc_does_not_investigate_noise(self) -> None:
        game = GameState(self.ep1, silent=True)
        sato = next(npc for npc in game.npcs if npc["id"] == "sato")
        for _ in range(5):
            game.tick(1)
        self.assertEqual(sato["location"], "room_inner_corridor_north")

    def test_hidden_dialogue_topic_cannot_bypass_visibility(self) -> None:
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

    def test_save_roundtrip_and_chapter_guard(self) -> None:
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
        with self.assertLogs("engine.game_state", level="ERROR"):
            self.assertFalse(other_chapter.deserialize_state(saved))
        with self.assertRaises(ValueError):
            SystemHandler._save_filename(["../../outside"])

    def test_future_matrix_uses_event_manager_timestamps(self) -> None:
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

    def test_schema_rejects_key_id_mismatch(self) -> None:
        config = copy.deepcopy(self.ep1)
        config["objects"]["tool_wrench"]["id"] = "wrong_id"
        with self.assertRaises(ConfigurationError):
            validate_game_config(config)

    def test_ep0_resonance_puzzle_end_to_end(self) -> None:
        game = GameState(self.ep0)
        self.assertEqual(game.quests.states["core_calibration"]["status"], "active")
        self.assertEqual(game.quests.states["core_calibration"]["stage"], 0)

        # 1. Greifzange & Akustik-Stethoskop im central_hub nehmen
        InventoryHandler.take(game, ["Greifzange"])
        InventoryHandler.take(game, ["Akustik-Stethoskop"])
        self.assertEqual(game.objects["grabber"]["location"], "inventory")
        self.assertEqual(game.objects["acoustic_scanner"]["location"], "inventory")

        # 2. In die Testkammer gehen; Zugangskarte mit Greifzange von Ebene 2 holen
        MovementHandler.handle(game, ["north"])
        self.assertEqual(game.location, "test_chamber")
        InventoryHandler.take(game, ["Zugangskarte", "mit", "Greifzange"])
        self.assertEqual(game.objects["access_card"]["location"], "inventory")

        # 3. Flüssigkeit kann nicht genommen werden; Glasphiole ist zerbrechlich
        InventoryHandler.take(game, ["Kühlmittel-Pfütze"])
        self.assertNotEqual(game.objects["coolant_pool"]["location"], "inventory")
        MechanicsHandler.break_(game, ["Glasphiole"])
        self.assertEqual(game.objects["glass_vial"]["state"], "broken")

        # 4. Schlüssel nehmen, Gefahrgut-Spind öffnen, Verstecken testen
        InventoryHandler.take(game, ["roter", "Schlüssel"])
        InventoryHandler.take(game, ["blauer", "Schlüssel"])
        MechanicsHandler.open(game, ["Gefahrgut-Spind"])
        self.assertTrue(game.objects["hazard_locker"]["is_open"])

        ExplorationHandler.hide(game, ["Gefahrgut-Spind"])
        self.assertEqual(game.hidden_in, "hazard_locker")
        MovementHandler.handle(game, ["raus"])
        self.assertIsNone(game.hidden_in)

        # 5. Kryo-Kapsel & Energiezelle aus dem Spind nehmen; Kapsel im Schmelzofen auftauen
        InventoryHandler.take(game, ["Kryo-Kapsel"])
        InventoryHandler.take(game, ["Energiezelle"])
        MechanicsHandler.use(game, ["Kryo-Kapsel", "mit", "Schmelzofen"])
        self.assertEqual(game.objects["calibration_weight"]["location"], "inventory")
        self.assertEqual(game.quests.states["core_calibration"]["stage"], 1)

        # 6. Scheue Wartungsdrohne mit Energiezelle füttern -> Resonanz-Frequenz lernen
        shy_drone = next(npc for npc in game.npcs if npc["id"] == "shy_drone")
        game.location = shy_drone["location"]
        InventoryHandler.give(game, ["Energiezelle", "an", "Wartungsdrohne"])
        self.assertIn("knows_resonance_tuning", game.knowledge)
        self.assertEqual(shy_drone["state"], "friendly")
        self.assertEqual(game.quests.states["core_calibration"]["stage"], 2)

        # 7. Zurück in die Testkammer, Sicherheits-Schott öffnen und Tresorraum betreten
        game.location = "test_chamber"
        MechanicsHandler.open(game, ["Sicherheits-Schott"])
        self.assertTrue(game.objects["security_door"]["is_open"])
        MovementHandler.handle(game, ["east"])
        self.assertEqual(game.location, "vault_room")

        # 8. Präzisionswaage mit exakt 2.50 kg (1.50 kg Eichgewicht + 1.00 kg blauer Schlüssel) beladen
        MechanicsHandler.put(game, ["Eichgewicht", "auf", "Präzisionswaage"])
        self.assertFalse(game.objects["resonance_vault"]["is_open"])
        MechanicsHandler.put(game, ["blauer", "Schlüssel", "auf", "Präzisionswaage"])
        self.assertTrue(game.objects["resonance_vault"]["is_open"])
        self.assertEqual(game.objects["resonance_core"]["location"], "vault_room")
        self.assertEqual(game.quests.states["core_calibration"]["stage"], 3)

        # 9. Resonanz-Kern nehmen, reparieren und im Zentral-Terminal einsetzen
        InventoryHandler.take(game, ["Resonanz-Kern"])
        MechanicsHandler.fix(game, ["Resonanz-Kern", "mit", "Greifzange"])
        self.assertEqual(game.objects["resonance_core"]["state"], "normal")

        game.location = "central_hub"
        MechanicsHandler.use(game, ["Resonanz-Kern", "mit", "Zentral-Terminal"])
        self.assertEqual(
            game.quests.states["core_calibration"]["status"], "completed"
        )
        self.assertIn("lab_stabilized", game.knowledge)

    def test_ep0_sabotage_eavesdropping_puzzle_end_to_end(self) -> None:
        game = GameState(self.ep0)

        # 1. Akustik-Glas im central_hub nehmen
        InventoryHandler.take(game, ["Akustik-Glas"])
        self.assertEqual(game.objects["amplifying_glass"]["location"], "inventory")

        # 2. In den Maschinenraum (lower_deck) gehen und den schweren Türkeil holen
        MovementHandler.handle(game, ["down"])
        self.assertEqual(game.location, "lower_deck")
        InventoryHandler.take(game, ["Schwerer", "Türkeil"])
        self.assertEqual(game.objects["door_wedge"]["location"], "inventory")

        # 3. Zurück in den Hub und nach Westen in den Sicherheits-Vorraum gehen
        MovementHandler.handle(game, ["up"])
        self.assertEqual(game.location, "central_hub")
        MovementHandler.handle(game, ["west"])
        self.assertEqual(game.location, "briefing_anteroom")
        self.assertIn("investigate_sabotage", game.quests.states)
        self.assertEqual(game.quests.states["investigate_sabotage"]["stage"], 0)

        # 4. Versuch, an der geschlossenen Schallschutztür zu lauschen (Schallisolierung dämpft 100%)
        ExplorationHandler.listen(game, ["an", "Schallschutztür", "mit", "Akustik-Glas"])
        self.assertNotIn("sabotage_plan_uncovered", game.knowledge)

        # 5. Türkeil an der Schallschutztür anwenden -> Tür verkeilt sich offen, Alarm feuert, Rauswurf in den Hub!
        MechanicsHandler.use(game, ["Schwerer", "Türkeil", "an", "Schallschutztür"])
        self.assertTrue(game.objects["soundproof_door"]["is_open"])
        self.assertTrue(game.objects["soundproof_door"]["jammed"])
        self.assertEqual(game.location, "central_hub")
        self.assertFalse(game.objects["anteroom_door"]["is_open"])
        self.assertTrue(game.objects["anteroom_door"]["is_locked"])
        self.assertEqual(game.quests.states["investigate_sabotage"]["stage"], 1)

        # 6. Versuch, wieder in den Vorraum zu gehen: versperrt!
        MovementHandler.handle(game, ["west"])
        self.assertEqual(game.location, "central_hub")

        # 7. An der Vorraum-Tür lauschen mit dem Akustik-Glas -> Sabotagepläne aufgedeckt!
        ActionDispatcher.dispatch(game, "lausche", ["an", "Vorraum-Tür", "mit", "Akustik-Glas"])
        self.assertIn("sabotage_plan_uncovered", game.knowledge)
        self.assertEqual(
            game.quests.states["investigate_sabotage"]["status"], "completed"
        )

    def test_parser_handles_short_direction_and_hyphenated_commands(self) -> None:
        game = GameState(self.ep0, silent=True)
        parser = SpacyParser(game)
        parser.parse("n")
        self.assertEqual(game.location, "test_chamber")
        parser.parse("s")
        self.assertEqual(game.location, "central_hub")
        parser.parse("gehe nach norden")
        self.assertEqual(game.location, "test_chamber")
        parser.parse("gehe nach süden")
        self.assertEqual(game.location, "central_hub")
        self.assertFalse(any("--" in entry["text"] for entry in game.logs))

    def test_ep1_npcs_and_maintenance_shaft_visible_and_interactive(self) -> None:
        game = GameState(self.ep1)
        parser = SpacyParser(game)

        parser.parse("e")
        self.assertEqual(game.location, "room_inner_corridor_north")
        self.assertIn("Dr. Sato", game.get_snapshot()["present_npcs"])
        self.assertTrue(any("Personen: Dr. Sato" in e["text"] for e in game.logs))

        parser.parse("nimm rohrzange")
        parser.parse("e")
        parser.parse("e")
        self.assertEqual(game.location, "room_outer_waste")
        self.assertIn(
            "Rusty (MK-1 Bot) (oben auf Ebene 2)",
            game.get_snapshot()["present_npcs"],
        )

        parser.parse("klettere wartungsleiter")
        self.assertEqual(game.elevation, 2)
        self.assertIn("Rusty (MK-1 Bot)", game.get_snapshot()["present_npcs"])
        parser.parse("untersuche wartungsschacht")
        self.assertTrue(
            any("Wartungsbot 'Rusty'" in e["text"] for e in game.logs[-3:])
        )
        parser.parse("betrete schacht")
        self.assertEqual(game.elevation, 2)

    def test_ep2_habitat_sector_end_to_end(self) -> None:
        game = GameState(self.ep2)
        parser = SpacyParser(game)

        # 1. Start in der Schleuse; Intro-Meldung empfangen
        self.assertEqual(game.location, "quarters_airlock")
        self.assertTrue(any("Habitat-Schleuse" in e["text"] for e in game.logs))

        # 2. In die Lounge gehen; Scrubber MK-2 sehen
        parser.parse("o")
        self.assertEqual(game.location, "living_commons")
        self.assertIn("Scrubber (MK-2)", game.get_snapshot()["present_npcs"])

        # 3. Ins Quartier 4B gehen, Spind öffnen und Dichtungsband nehmen
        parser.parse("s")
        self.assertEqual(game.location, "crew_cabin_thorne")
        parser.parse("nimm dichtungsband")
        self.assertEqual(game.objects["sealant_tape"]["location"], "inventory")

        # 4. In die Biosphäre gehen
        parser.parse("n")
        self.assertEqual(game.location, "living_commons")
        parser.parse("n")
        self.assertEqual(game.location, "hydroponics_bay")
        self.assertIn("Dr. Elena Vance", game.get_snapshot()["present_npcs"])

        # 5. Quest starten via Dialog
        game.events.trigger_event_by_id("event_quest_start")
        self.assertEqual(game.quests.states["biosphere_pressure"]["status"], "active")

        # 6. Auf Ebene 1 klettern
        parser.parse("klettere service-leiter")
        self.assertEqual(game.elevation, 1)

        # 7. Ventil kalibrieren & Dampfleitung versiegeln
        parser.parse("benutze omni-tool mit ventil")
        self.assertIn("valve_calibrated", game.knowledge)
        parser.parse("benutze dichtungsband mit dampfleitung")
        self.assertIn("steam_fixed", game.knowledge)

        # 8. Hinabsteigen und Belohnung erhalten
        parser.parse("klettere runter")
        self.assertEqual(game.elevation, 0)

        vance = next(npc for npc in game.npcs if npc["id"] == "dr_vance")
        reward_entry = vance["dialogue"]["relieved"]["reward"]
        assert isinstance(reward_entry, dict)
        game.effects.process(reward_entry["effect"], context_npc=vance)

        self.assertEqual(game.objects["core_access_chip"]["location"], "inventory")
        self.assertEqual(game.quests.states["biosphere_pressure"]["status"], "completed")
        self.assertTrue(game.game_over)

    def test_ep3_reactor_core_end_to_end(self) -> None:
        game = GameState(self.ep3)
        parser = SpacyParser(game)

        # 1. Start auf der Zugangsbrücke; Intro-Log und Drohne Aegis
        self.assertEqual(game.location, "reactor_bridge")
        self.assertIn("Aegis (MK-3)", game.get_snapshot()["present_npcs"])

        # 2. In den Leitstand gehen und mit Dr. Sato sprechen
        parser.parse("o")
        self.assertEqual(game.location, "control_room")
        self.assertIn("Dr. Sato", game.get_snapshot()["present_npcs"])

        # Quest starten
        game.events.trigger_event_by_id("event_quest_start")
        self.assertEqual(game.quests.states["reactor_overdrive"]["status"], "active")

        # 3. Zurück zur Brücke, dann nach Norden ins Kryo-Kühllager
        parser.parse("w")
        self.assertEqual(game.location, "reactor_bridge")
        parser.parse("n")
        self.assertEqual(game.location, "coolant_depot")

        # Kryo-Kühlkanister nehmen
        parser.parse("nimm kühlkanister")
        self.assertEqual(game.objects["cryo_canister"]["location"], "inventory")

        # 4. Nach Süden zur Brücke, dann nach Süden in die Reaktorkammer
        parser.parse("s")
        self.assertEqual(game.location, "reactor_bridge")
        parser.parse("s")
        self.assertEqual(game.location, "reactor_chamber")

        # 5. Auf Ebene 2 klettern
        parser.parse("klettere injektor-leiter")
        self.assertEqual(game.elevation, 2)

        # 6. Kühlkanister an den Injektor-Verteiler anschließen
        parser.parse("benutze kühlkanister mit verteiler")
        self.assertIn("core_cooled", game.knowledge)

        # 7. Hinabsteigen, zurück zur Brücke und in den Leitstand
        parser.parse("klettere runter")
        self.assertEqual(game.elevation, 0)
        parser.parse("n")
        self.assertEqual(game.location, "reactor_bridge")
        parser.parse("o")
        self.assertEqual(game.location, "control_room")

        # 8. Steuerkonsole mit dem Omni-Tool kalibrieren
        parser.parse("benutze omni-tool mit steuerkonsole")
        self.assertIn("core_stabilized", game.knowledge)
        self.assertEqual(game.quests.states["reactor_overdrive"]["stage"], 3)

        # 9. Dr. Sato überreicht den Generalschlüssel und das Spiel endet siegreich
        sato = next(npc for npc in game.npcs if npc["id"] == "sato")
        reward_entry = sato["dialogue"]["celebrating"]["reward"]
        assert isinstance(reward_entry, dict)
        game.effects.process(reward_entry["effect"], context_npc=sato)

        self.assertEqual(game.objects["master_station_key"]["location"], "inventory")
        self.assertEqual(game.quests.states["reactor_overdrive"]["status"], "completed")
        self.assertTrue(game.game_over)

    def test_ui_helpers_work_headless(self) -> None:
        class _DummyFont:
            def size(self, text: str) -> tuple[int, int]:
                return (len(text) * 8, 16)

        renderer = RichTextRenderer(_DummyFont(), (200, 200, 200))  # type: ignore[arg-type]
        wrapped = renderer.parse_and_wrap("Hallo <alert>Welt!</alert>", max_width=200)
        self.assertEqual(len(wrapped), 1)
        self.assertEqual([seg["text"] for seg in wrapped[0]], ["Hallo", " ", "Welt!"])
        self.assertEqual(wrapped[0][2]["color"], renderer.color_map["alert"])

        sys_conf = load_system_config()
        self.assertIn("game", sys_conf)
        self.assertIn("system", sys_conf)

    def test_codebase_hygiene_and_type_annotations(self) -> None:
        root = Path(__file__).resolve().parent.parent
        issues: list[str] = []

        for py_file in sorted(root.rglob("*.py")):
            if ".git" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            rel = py_file.relative_to(root)
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(rel))

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.returns is None:
                        issues.append(f"{rel}:{node.lineno} {node.name} missing return type")
                    all_args = (
                        node.args.posonlyargs
                        + node.args.args
                        + node.args.kwonlyargs
                        + ([node.args.vararg] if node.args.vararg else [])
                        + ([node.args.kwarg] if node.args.kwarg else [])
                    )
                    for arg in all_args:
                        if arg.arg not in ("self", "cls") and arg.annotation is None:
                            issues.append(
                                f"{rel}:{node.lineno} {node.name}({arg.arg}) missing type"
                            )
                elif isinstance(node, ast.ImportFrom):
                    if any(alias.name == "*" for alias in node.names):
                        issues.append(f"{rel}:{node.lineno} wildcard import")
                elif isinstance(node, ast.ExceptHandler) and node.type is None:
                    issues.append(f"{rel}:{node.lineno} bare except")
                elif (
                    rel.parts[0] == "engine"
                    and isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "print"
                ):
                    issues.append(f"{rel}:{node.lineno} print() in engine/")

        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
