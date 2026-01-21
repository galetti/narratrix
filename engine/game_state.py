import copy
import re
import threading
import traceback
from engine.constants import *

from engine.systems.crafting import CraftingSystem
from engine.systems.pathfinder import Pathfinder
from engine.systems.ai import AISystem
from engine.systems.object_behavior import ObjectBehaviorSystem
from engine.systems.acoustics import AcousticsSystem
from engine.systems.quest_manager import QuestManager
from engine.systems.event_manager import EventManager

from engine.systems.effect_processor import EffectProcessor
from engine.systems.dialogue_system import DialogueSystem

class GameState:
    def __init__(self, config, silent=False):
        self.config = config
        self.silent = silent
        
        self.time = 0
        self.logs = []
        self.lock = threading.RLock()
        
        self.persistent_flags = set() 
        self.pending_chapter_load = None 
        self.hidden_in = None 
        
        start_room = config.get('meta', {}).get('start_room')
        if not start_room and 'start' in config['rooms']: start_room = 'start'
        if not start_room or start_room not in config['rooms']:
            start_room = list(config['rooms'].keys())[0] if config['rooms'] else LOC_VOID

        self.location = start_room
        self.elevation = 0 # NEU: Vertikale Ebene im Raum (0 = Boden)
        
        self.inventory = []
        self.stability = 100
        self.game_over = False
        self.last_subject_id = None
        self.disambiguation = None 
        self.pending_interaction = None
        self.dialogue_active = False
        self.dialogue_partner = None
        self.knowledge = set()

        self.rooms = copy.deepcopy(config['rooms'])
        self.npcs = copy.deepcopy(config['npcs'])
        self.matrix = copy.deepcopy(config.get('narrative_matrix', []))
        self.dynamic_events = copy.deepcopy(config.get('events', []))
        
        self.objects = copy.deepcopy(config['objects'])
        self.combinations = copy.deepcopy(config.get('combinations', []))
        
        for npc in self.npcs:
            if 'states' in npc:
                if 'state' not in npc:
                    npc['state'] = npc.get('initial_state', list(npc['states'].keys())[0])
                self._hydrate_npc(npc)
                npc['_last_hydrated_state'] = npc['state']

        for obj in self.objects.values():
            if ATTR_TEMP not in obj: obj[ATTR_TEMP] = 20
            if ATTR_MATTER not in obj: obj[ATTR_MATTER] = MATTER_SOLID

        self.effects = EffectProcessor(self)
        self.dialogue_system = DialogueSystem(self)
        
        self.crafting = CraftingSystem(self)
        self.pathfinder = Pathfinder(self)
        self.ai = AISystem(self)
        self.object_behavior = ObjectBehaviorSystem(self)
        self.acoustics = AcousticsSystem(self)
        self.quests = QuestManager(self)
        self.quests.load_definitions(config.get('quests', {}))
        
        self.events = EventManager(self)
        
        all_events = self.matrix + self.dynamic_events
        self.events.load_events(all_events)
        
        if not self.silent:
            self.events.update()

    def _hydrate_npc(self, npc):
        current_state = npc.get('state')
        state_data = npc.get('states', {}).get(current_state)
        if not state_data: return
        if 'behavior' in state_data:
            for k, v in state_data['behavior'].items(): npc[k] = v 
        if 'visuals' in state_data:
            for k, v in state_data['visuals'].items(): npc[k] = v 
        if 'dialogue' in state_data:
            if 'dialogue' not in npc: npc['dialogue'] = {}
            npc['dialogue'][current_state] = state_data['dialogue']

    def _synchronize_npcs(self):
        for npc in self.npcs:
            if 'states' in npc:
                current = npc.get('state')
                last = npc.get('_last_hydrated_state')
                if current != last:
                    self._hydrate_npc(npc)
                    npc['_last_hydrated_state'] = current

    def clone(self):
        new_state = GameState(self.config, silent=True)
        with self.lock:
            new_state.time = self.time
            new_state.location = self.location
            new_state.elevation = self.elevation # NEU
            new_state.stability = self.stability
            new_state.game_over = self.game_over
            new_state.knowledge = copy.deepcopy(self.knowledge)
            new_state.persistent_flags = copy.deepcopy(self.persistent_flags)
            new_state.hidden_in = self.hidden_in 
            new_state.rooms = copy.deepcopy(self.rooms)
            new_state.npcs = copy.deepcopy(self.npcs)
            new_state.matrix = copy.deepcopy(self.matrix)
            new_state.dynamic_events = copy.deepcopy(self.dynamic_events)
            
            new_state.objects = copy.deepcopy(self.objects)
            new_state.inventory = copy.deepcopy(self.inventory)
            new_state.combinations = copy.deepcopy(self.combinations)
            new_state.events.events = copy.deepcopy(self.events.events) 
        return new_state

    def render_room_desc(self, room_id):
        if self.hidden_in:
            container = self.objects.get(self.hidden_in)
            c_name = container[ATTR_NAME] if container else "einem Versteck"
            return f"Du bist versteckt in {c_name}. Durch einen Spalt siehst du den Raum."

        room = self.rooms.get(room_id)
        if not room: return f"ERROR: Raum '{room_id}' nicht gefunden."
        
        text = room[ATTR_DESC]
        
        # NEU: Spezielle Beschreibung abhängig von der Ebene/Höhe?
        # Man könnte hier prüfen, ob der Raum unterschiedliche Beschreibungen pro Level hat.
        # Für jetzt belassen wir es beim Standardtext.
        
        def replace_match(match):
            key = match.group(1)
            obj = self.objects.get(key)
            if obj:
                display_text = obj[ATTR_NAME]
                if obj.get('state') == STATE_SABOTAGED: display_text += " [SABOTIERT]"
                elif obj.get('state') == STATE_BROKEN: display_text += " [DEFEKT]"
                elif obj.get('is_container'):
                    if obj.get('is_open'): display_text += " [OFFEN]"
                    else: display_text += " [VERSCHLOSSEN]"
                return display_text
            
            target_room = self.rooms.get(key)
            if target_room:
                return target_room[ATTR_NAME]
                
            return f"ERROR:{key}"
            
        desc = re.sub(r"\{(\w+)\}", replace_match, text)
        
        # Zusatzinfo für Elevation
        if self.elevation > 0:
            desc += f"\n(Du befindest dich auf Ebene {self.elevation}.)"
            
        return desc

    def log(self, type_str, text):
        if self.silent: return 
        
        with self.lock:
            self.logs.append({"type": type_str, "text": text, "turn": self.time})

    def get_logs(self):
        with self.lock: return list(self.logs)

    def get_snapshot(self):
        with self.lock:
            self._synchronize_npcs()
            room = self.rooms.get(self.location)
            partner_name = None; partner_img = None
            if self.dialogue_active and self.dialogue_partner:
                partner_name = self.dialogue_partner[ATTR_NAME]; partner_img = self.dialogue_partner.get('img')
                
            return {
                "time": self.time, "stability": self.stability, "game_over": self.game_over,
                "pending_chapter_load": self.pending_chapter_load,
                "room_name": room[ATTR_NAME] if room else "Unbekannt",
                "room_img": room.get('img', '???') if room else '???',
                "dialogue_active": self.dialogue_active,
                "dialogue_header": f"GESPRÄCH: {partner_name.upper()}" if partner_name else "",
                "dialogue_img": partner_img if partner_img else (partner_name if partner_name else "???"),
                "logs": list(self.logs),
                # NEU: Info für GUI (könnte man z.B. im Sensor Log anzeigen)
                "elevation": self.elevation
            }

    def get_room(self, room_id): return self.rooms.get(room_id)
    def add_knowledge(self, fact_id): 
        if fact_id not in self.knowledge: self.knowledge.add(fact_id)

    def perform_combine(self, item1_name, item2_name, verb="use"):
        return self.crafting.perform_combine(item1_name, item2_name, verb)

    def find_path(self, start, target): return self.pathfinder.find_path(start, target)
    def get_direction_to(self, target_room_id): return self.pathfinder.get_direction_to(self.location, target_room_id)

    def tick(self, minutes):
        self.time += minutes
        
        for obj in self.objects.values():
            if ATTR_TEMP in obj:
                current = obj[ATTR_TEMP]; target = 20
                if current != target:
                    diff = target - current
                    if abs(change := diff * 0.1) < 0.5: obj[ATTR_TEMP] = target
                    else: obj[ATTR_TEMP] += change
        
        try:
            self.events.update()
        except Exception as e:
            print(f"[FATAL] EventManager Update Error: {e}")
            traceback.print_exc()
            self.log('error', f"Systemfehler (Events): {e}")

        if hasattr(self.ai, 'process_all_npcs'): 
            try:
                self.ai.process_all_npcs(minutes)
            except TypeError:
                self.ai.process_all_npcs()

        if hasattr(self.object_behavior, 'update'): self.object_behavior.update()

        if self.stability <= 0: 
            self.log('alarm', "GAME OVER: STATION KRITISCH.")
            self.game_over = True

    def serialize_state(self):
        return {
            "location": self.location, "time": self.time, "stability": self.stability,
            "elevation": self.elevation, # NEU
            "knowledge": list(self.knowledge), "rooms": self.rooms,   
            "objects": self.objects, "npcs": self.npcs,     
            "quests": self.quests.get_save_data(), 
            "events": self.events.events, 
            "combinations": self.combinations,
            "meta": {"version": "1.4"} 
        }

    def deserialize_state(self, data):
        try:
            self.location = data.get("location", "start_room")
            self.time = data.get("time", 0)
            self.stability = data.get("stability", 100)
            self.elevation = data.get("elevation", 0) # NEU
            self.knowledge = set(data.get("knowledge", []))
            
            if "rooms" in data: self.rooms = data["rooms"]
            if "objects" in data: self.objects = data["objects"]
            if "npcs" in data: self.npcs = data["npcs"]
            if "combinations" in data: self.combinations = data["combinations"]
            if "quests" in data: self.quests.load_save_data(data["quests"])
                
            if "events" in data:
                saved_events = {e['id']: e for e in data['events'] if 'id' in e}
                for ev in self.events.events:
                    if ev['id'] in saved_events:
                        saved = saved_events[ev['id']]
                        ev['triggered'] = saved.get('triggered', False)
                        ev['triggered_at'] = saved.get('triggered_at')
            return True
        except Exception as e:
            print(f"[ERROR] Load failed: {e}"); return False