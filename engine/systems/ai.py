# narratrix_engine/engine/systems/ai.py
from engine.constants import *
import random

class BTNode:
    """Basisklasse für Behavior Tree Nodes."""
    def execute(self, npc, ai_system):
        return False # Fail

class Selector(BTNode):
    """Führt Kinder aus, bis eines SUCCESS (True) zurückgibt."""
    def __init__(self, children):
        self.children = children
    
    def execute(self, npc, ai_system):
        for child in self.children:
            if child.execute(npc, ai_system):
                return True
        return False

class Sequence(BTNode):
    """Führt Kinder aus, solange sie SUCCESS zurückgeben."""
    def __init__(self, children):
        self.children = children
        
    def execute(self, npc, ai_system):
        for child in self.children:
            if not child.execute(npc, ai_system):
                return False
        return True

class Action(BTNode):
    """Führt eine konkrete Aktion aus."""
    def __init__(self, action_func, *args):
        self.func = action_func
        self.args = args
        
    def execute(self, npc, ai_system):
        return self.func(npc, ai_system, *self.args)

class Condition(BTNode):
    """Prüft eine Bedingung."""
    def __init__(self, condition_func, *args):
        self.func = condition_func
        self.args = args
        
    def execute(self, npc, ai_system):
        return self.func(npc, ai_system, *self.args)

class AISystem:
    def __init__(self, game):
        self.game = game
        self.trees = {} # Cache für Behavior Trees
        self._init_default_behaviors()

    def _init_default_behaviors(self):
        # Standard-Verhalten: "Wache"
        self.trees['guard'] = Selector([
            Sequence([
                Condition(self._cond_hear_noise),
                Action(self._act_investigate_noise)
            ]),
            Sequence([
                Condition(self._cond_player_visible),
                Condition(self._cond_not_greeted),
                Action(self._act_greet_player)
            ]),
            Action(self._act_patrol)
        ])
        
        # Standard-Verhalten: "Ängstlich"
        self.trees['fearful'] = Selector([
            Sequence([
                Condition(self._cond_player_near),
                Action(self._act_flee)
            ]),
            Action(self._act_idle_nervous)
        ])

    def process_all_npcs(self, minutes=1):
        """Wird jeden Tick aufgerufen."""
        for npc in self.game.npcs:
            self._handle_movement(npc, minutes)
            
            behavior_id = npc.get('behavior_id', 'guard') 
            tree = self.trees.get(behavior_id)
            
            if tree:
                tree.execute(npc, self)

    # --- CONDITIONS ---

    def _cond_player_visible(self, npc, sys):
        return sys.game.location == npc['location']

    def _cond_player_near(self, npc, sys):
        if sys.game.location == npc['location']: return True
        path = sys.game.pathfinder.find_path(npc['location'], sys.game.location)
        return path and len(path) == 1

    def _cond_not_greeted(self, npc, sys):
        return not npc.get('has_greeted', False)

    def _cond_hear_noise(self, npc, sys):
        return npc.get('memory', {}).get('last_noise_loc') is not None

    # --- ACTIONS ---

    def _act_greet_player(self, npc, sys):
        sys.game.log('character', f"{npc[ATTR_NAME]} nickt dir zu.")
        npc['has_greeted'] = True
        return True

    def _act_idle_nervous(self, npc, sys):
        if random.random() < 0.1:
            sys.game.log('character', f"{npc[ATTR_NAME]} schaut sich nervös um.")
        return True

    def _act_flee(self, npc, sys):
        current = npc['location']
        player_loc = sys.game.location
        room = sys.game.rooms.get(current)
        best_exit = None
        for direction, target in room.get('exits', {}).items():
            if target != player_loc:
                best_exit = target
                break
        if best_exit:
            sys.move_npc(npc['id'], best_exit)
            return True
        return False 

    def _act_patrol(self, npc, sys):
        waypoints = npc.get('waypoints', [])
        if not waypoints: return False
        if npc.get('target_location'): return True
        
        idx = npc.get('waypoint_index', 0)
        target = waypoints[idx]
        
        if npc['location'] == target:
            idx = (idx + 1) % len(waypoints)
            npc['waypoint_index'] = idx
            target = waypoints[idx]
            
        sys.move_npc(npc['id'], target)
        return True

    def _act_investigate_noise(self, npc, sys):
        target = npc.get('memory', {}).get('last_noise_loc')
        if not target: return False
        
        if npc['location'] == target:
            sys.game.log('character', f"{npc[ATTR_NAME]} sieht sich suchend um.")
            npc['memory']['last_noise_loc'] = None 
            return True
            
        sys.move_npc(npc['id'], target)
        return True

    # --- MOVEMENT LOGIC ---

    def move_npc(self, npc_id, target_room_id, instant=False):
        npc = self._find_npc(npc_id)
        if not npc: return

        if instant:
            npc['location'] = target_room_id
            npc['path'] = []
            npc['target_location'] = None
            return

        start_room = npc.get('location')
        if start_room == target_room_id: return

        if npc.get('target_location') == target_room_id and npc.get('path'):
            return

        path = self.game.pathfinder.find_path(start_room, target_room_id)
        if path:
            npc['path'] = path
            npc['target_location'] = target_room_id
            if 'move_acc' not in npc: npc['move_acc'] = 0.0
            
            if self.game.location == start_room:
                first_step = path[0]
                direction = self._get_exit_direction(start_room, first_step)
                dir_str = f" nach {direction}" if direction else ""
                self.game.log('character', f"{npc[ATTR_NAME]} bricht auf{dir_str}.")

    def _handle_movement(self, npc, minutes):
        path = npc.get('path')
        if not path: return

        speed = npc.get('speed', 1.0)
        current_acc = npc.get('move_acc', 0.0) + (speed * minutes)
        
        steps_taken = 0
        while current_acc >= 1.0 and path:
            next_room_id = path.pop(0)
            old_room_id = npc['location']
            
            npc['location'] = next_room_id
            current_acc -= 1.0
            steps_taken += 1
            
            self._broadcast_movement(npc, old_room_id, next_room_id)
            
        npc['move_acc'] = current_acc
        
        if not path and steps_taken > 0:
            npc['target_location'] = None
            npc['move_acc'] = 0.0

    def _broadcast_movement(self, npc, old_room, new_room):
        player_loc = self.game.location
        npc_name = npc[ATTR_NAME]

        if player_loc == old_room:
            direction = self._get_exit_direction(old_room, new_room)
            dir_text = f" nach {direction}" if direction else ""
            self.game.log('character', f"{npc_name} verlässt den Bereich{dir_text}.")
        elif player_loc == new_room:
            direction = self._get_exit_direction(new_room, old_room)
            dir_text = f" aus {direction}" if direction else ""
            self.game.log('character', f"{npc_name} betritt den Bereich{dir_text}.")

    def _get_exit_direction(self, source_id, target_id):
        room = self.game.rooms.get(source_id)
        if not room: return None
        trans_map = {
            "north": "Norden", "south": "Süden", "east": "Osten", "west": "Westen", 
            "up": "Oben", "down": "Unten",
            "northeast": "Nordosten", "northwest": "Nordwesten",
            "southeast": "Südosten", "southwest": "Südwesten"
        }
        for direction, dest in room.get('exits', {}).items():
            if dest == target_id: return trans_map.get(direction, direction)
        return None

    def _find_npc(self, identifier):
        return next((n for n in self.game.npcs if n.get('id') == identifier or n.get('name') == identifier), None)
    
    def notify_noise(self, origin_id, volume):
        for npc in self.game.npcs:
            vol, _ = self.game.acoustics.get_audibility_info(origin_id, npc['location'])
            if vol > 0.2: 
                if 'memory' not in npc: npc['memory'] = {}
                npc['memory']['last_noise_loc'] = origin_id