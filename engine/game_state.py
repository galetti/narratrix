import copy
import re
import threading
import traceback

from engine.constants import (
    ATTR_DESC,
    ATTR_MATTER,
    ATTR_NAME,
    ATTR_TEMP,
    LOC_VOID,
    MATTER_SOLID,
    STATE_BROKEN,
    STATE_SABOTAGED,
)
from engine.systems.acoustics import AcousticsSystem
from engine.systems.ai import AISystem
from engine.systems.crafting import CraftingSystem
from engine.systems.dialogue_system import DialogueSystem
from engine.systems.effect_processor import EffectProcessor
from engine.systems.event_manager import EventManager
from engine.systems.object_behavior import ObjectBehaviorSystem
from engine.systems.pathfinder import Pathfinder
from engine.systems.quest_manager import QuestManager


SAVE_SCHEMA_VERSION = 2


class GameState:
    def __init__(self, config, silent=False):
        self.config = config
        self.silent = silent
        self.lock = threading.RLock()

        self.time = 0
        self.logs = []
        self.pending_chapter_load = None
        self.hidden_in = None
        self.elevation = 0
        self.stability = 100
        self.game_over = False
        self.last_subject_id = None
        self.disambiguation = None
        self.pending_interaction = None
        self.dialogue_active = False
        self.dialogue_partner = None
        self.knowledge = set()

        self.rooms = copy.deepcopy(config["rooms"])
        self.npcs = copy.deepcopy(config["npcs"])
        self.matrix = copy.deepcopy(config.get("narrative_matrix", []))
        self.dynamic_events = copy.deepcopy(config.get("events", []))
        self.objects = copy.deepcopy(config["objects"])
        self.combinations = copy.deepcopy(config.get("combinations", []))

        start_room = config.get("meta", {}).get("start_room")
        self.location = start_room if start_room in self.rooms else LOC_VOID
        self.visit_room(self.location)

        for npc in self.npcs:
            self._prepare_npc_state(npc)
        for obj in self.objects.values():
            obj.setdefault(ATTR_TEMP, 20)
            obj.setdefault(ATTR_MATTER, MATTER_SOLID)

        self.effects = EffectProcessor(self)
        self.dialogue_system = DialogueSystem(self)
        self.crafting = CraftingSystem(self)
        self.pathfinder = Pathfinder(self)
        self.ai = AISystem(self)
        self.object_behavior = ObjectBehaviorSystem(self)
        self.acoustics = AcousticsSystem(self)
        self.quests = QuestManager(self)
        self.quests.load_definitions(config.get("quests", {}))
        self.events = EventManager(self)
        self.events.load_events(self.matrix + self.dynamic_events)

        if not self.silent:
            self.events.update()

    def _prepare_npc_state(self, npc):
        states = npc.get("states", {})
        if not states:
            return
        if "state" not in npc:
            npc["state"] = npc.get("initial_state", next(iter(states)))

        managed_keys = set()
        for state_data in states.values():
            managed_keys.update(state_data.get("behavior", {}))
            managed_keys.update(state_data.get("visuals", {}))
        npc["_state_managed_keys"] = sorted(managed_keys)
        npc["_state_base_values"] = {
            key: copy.deepcopy(npc[key]) for key in managed_keys if key in npc
        }
        npc["_state_missing_keys"] = [key for key in managed_keys if key not in npc]
        self._hydrate_npc(npc)

    def _hydrate_npc(self, npc):
        states = npc.get("states", {})
        if not states:
            return
        state = npc.get("state")
        if state not in states:
            raise ValueError(f"NPC '{npc.get('id')}' hat unbekannten Zustand '{state}'.")

        for key in npc.get("_state_managed_keys", []):
            if key in npc.get("_state_base_values", {}):
                npc[key] = copy.deepcopy(npc["_state_base_values"][key])
            else:
                npc.pop(key, None)
        state_data = states[state]
        for section in ("behavior", "visuals"):
            for key, value in state_data.get(section, {}).items():
                npc[key] = copy.deepcopy(value)

    def set_npc_state(self, npc, new_state):
        if npc.get("states") and new_state not in npc["states"]:
            raise ValueError(f"NPC '{npc.get('id')}': Zustand '{new_state}' fehlt.")
        npc["state"] = new_state
        self._hydrate_npc(npc)

    def clone(self):
        clone = GameState(self.config, silent=True)
        if not clone.deserialize_state(self.serialize_state(), allow_chapter_mismatch=False):
            raise ValueError("GameState konnte nicht geklont werden.")
        clone.silent = True
        return clone

    def visit_room(self, room_id):
        if room_id in self.rooms:
            self.rooms[room_id]["visited"] = True

    def render_room_desc(self, room_id):
        if self.hidden_in:
            container = self.objects.get(self.hidden_in)
            name = container[ATTR_NAME] if container else "einem Versteck"
            return f"Du bist versteckt in {name}. Durch einen Spalt siehst du den Raum."

        room = self.rooms.get(room_id)
        if not room:
            return f"ERROR: Raum '{room_id}' nicht gefunden."

        def replace_match(match):
            key = match.group(1)
            obj = self.objects.get(key)
            if obj:
                display = obj[ATTR_NAME]
                if obj.get("state") == STATE_SABOTAGED:
                    display += " [SABOTIERT]"
                elif obj.get("state") == STATE_BROKEN:
                    display += " [DEFEKT]"
                elif obj.get("type") == "container":
                    display += " [OFFEN]" if obj.get("is_open") else " [VERSCHLOSSEN]"
                return display
            target_room = self.rooms.get(key)
            return target_room[ATTR_NAME] if target_room else f"ERROR:{key}"

        description = re.sub(r"\{(\w+)\}", replace_match, room[ATTR_DESC])
        if self.elevation > 0:
            description += f"\n(Du befindest dich auf Ebene {self.elevation}.)"
        return description

    def log(self, type_str, text):
        if self.silent:
            return
        with self.lock:
            self.logs.append({"type": type_str, "text": str(text), "turn": self.time})

    def get_logs(self):
        with self.lock:
            return list(self.logs)

    def get_snapshot(self):
        with self.lock:
            room = self.rooms.get(self.location)
            partner_name = None
            partner_img = None
            if self.dialogue_active and self.dialogue_partner:
                partner_name = self.dialogue_partner[ATTR_NAME]
                partner_img = self.dialogue_partner.get("img")
            return {
                "time": self.time,
                "stability": self.stability,
                "game_over": self.game_over,
                "pending_chapter_load": self.pending_chapter_load,
                "room_name": room[ATTR_NAME] if room else "Unbekannt",
                "room_img": room.get("img", "???") if room else "???",
                "dialogue_active": self.dialogue_active,
                "dialogue_header": (
                    f"GESPRÄCH: {partner_name.upper()}" if partner_name else ""
                ),
                "dialogue_img": partner_img or partner_name or "???",
                "logs": list(self.logs),
                "elevation": self.elevation,
            }

    def get_room(self, room_id):
        return self.rooms.get(room_id)

    def add_knowledge(self, fact_id):
        if fact_id in self.knowledge:
            return False
        self.knowledge.add(fact_id)
        return True

    def perform_combine(self, item1_name, item2_name, verb="use"):
        return self.crafting.perform_combine(item1_name, item2_name, verb)

    def find_path(self, start, target):
        return self.pathfinder.find_path(start, target)

    def get_direction_to(self, target_room_id):
        return self.pathfinder.get_direction_to(self.location, target_room_id)

    def tick(self, minutes):
        if minutes <= 0:
            return
        with self.lock:
            self.time += minutes
            ambient_factor = 1 - (0.9 ** minutes)
            for obj in self.objects.values():
                current = float(obj.get(ATTR_TEMP, 20))
                if current != 20:
                    updated = current + (20 - current) * ambient_factor
                    obj[ATTR_TEMP] = 20 if abs(updated - 20) < 0.5 else updated

            try:
                self.events.update()
                self.object_behavior.update(minutes)
                self.ai.process_all_npcs(minutes)
            except Exception as exc:
                print(f"[FATAL] Simulationsfehler: {exc}")
                traceback.print_exc()
                self.log("error", f"Systemfehler (Simulation): {exc}")

            if self.stability <= 0 and not self.game_over:
                self.log("alarm", "GAME OVER: STATION KRITISCH.")
                self.game_over = True

    @staticmethod
    def _clean_npc_for_save(npc):
        cleaned = copy.deepcopy(npc)
        for key in cleaned.get("_state_managed_keys", []):
            if key in cleaned.get("_state_base_values", {}):
                cleaned[key] = copy.deepcopy(cleaned["_state_base_values"][key])
            else:
                cleaned.pop(key, None)
        for key in (
            "_state_managed_keys",
            "_state_base_values",
            "_state_missing_keys",
        ):
            cleaned.pop(key, None)
        return cleaned

    def serialize_state(self):
        with self.lock:
            return {
                "meta": {
                    "schema_version": SAVE_SCHEMA_VERSION,
                    "chapter": self.config.get("meta", {}).get("module"),
                },
                "location": self.location,
                "time": self.time,
                "stability": self.stability,
                "elevation": self.elevation,
                "knowledge": sorted(self.knowledge),
                "hidden_in": self.hidden_in,
                "game_over": self.game_over,
                "rooms": copy.deepcopy(self.rooms),
                "objects": copy.deepcopy(self.objects),
                "npcs": [self._clean_npc_for_save(npc) for npc in self.npcs],
                "quests": copy.deepcopy(self.quests.get_save_data()),
                "events": copy.deepcopy(self.events.events),
                "combinations": copy.deepcopy(self.combinations),
            }

    def deserialize_state(self, data, allow_chapter_mismatch=False):
        try:
            meta = data.get("meta", {})
            if meta.get("schema_version") != SAVE_SCHEMA_VERSION:
                raise ValueError(
                    f"Saveformat {meta.get('schema_version')} wird nicht unterstützt "
                    f"(erwartet: {SAVE_SCHEMA_VERSION})."
                )
            saved_chapter = meta.get("chapter")
            current_chapter = self.config.get("meta", {}).get("module")
            if (
                not allow_chapter_mismatch
                and saved_chapter
                and current_chapter
                and saved_chapter != current_chapter
            ):
                raise ValueError(
                    f"Spielstand gehört zu '{saved_chapter}', nicht zu '{current_chapter}'."
                )

            rooms = copy.deepcopy(data["rooms"])
            location = data["location"]
            if location not in rooms:
                raise ValueError(f"Gespeicherter Raum '{location}' fehlt.")

            self.rooms = rooms
            self.objects = copy.deepcopy(data["objects"])
            self.npcs = copy.deepcopy(data["npcs"])
            self.combinations = copy.deepcopy(data.get("combinations", self.combinations))
            self.location = location
            self.time = int(data.get("time", 0))
            self.stability = float(data.get("stability", 100))
            self.elevation = int(data.get("elevation", 0))
            self.knowledge = set(data.get("knowledge", []))
            self.hidden_in = data.get("hidden_in")
            self.game_over = bool(data.get("game_over", False))
            self.pending_chapter_load = None
            self.pending_interaction = None
            self.disambiguation = None
            self.dialogue_active = False
            self.dialogue_partner = None

            for npc in self.npcs:
                self._prepare_npc_state(npc)
            for obj in self.objects.values():
                obj.setdefault(ATTR_TEMP, 20)
                obj.setdefault(ATTR_MATTER, MATTER_SOLID)

            self.quests.load_save_data(data.get("quests", {}))
            saved_events = {
                event["id"]: event
                for event in data.get("events", [])
                if isinstance(event, dict) and "id" in event
            }
            for event in self.events.events:
                saved = saved_events.get(event.get("id"))
                if saved:
                    event["triggered"] = bool(saved.get("triggered", False))
                    event["last_triggered_at"] = saved.get("last_triggered_at")
            self.visit_room(self.location)
            return True
        except Exception as exc:
            print(f"[ERROR] Laden fehlgeschlagen: {exc}")
            return False
