# engine/systems/ai.py
from engine.constants import *
from utils import rng

class AISystem:
    def __init__(self, game):
        self.game = game

    def process_all_npcs(self):
        """Haupt-Loop für alle NPCs."""
        for npc in self.game.npcs:
            # Wenn NPC gerade spricht, pausiert seine KI (damit er nicht wegrennt)
            if not self.game.silent and npc == self.game.dialogue_partner and self.game.dialogue_active:
                continue
            self._process_single_npc(npc)

    def _process_single_npc(self, npc):
        # 1. Wahrscheinlichkeit ermitteln (Hierarchie)
        chance_to_move = AI_CHANCE_MOVE_DEFAULT
        
        # Override NPC Level
        if 'movement_chance' in npc:
            chance_to_move = npc['movement_chance']
            
        # Override State Level
        current_state = npc.get('state', 'default')
        dialogue_conf = npc.get('dialogue', {})
        state_conf = dialogue_conf.get(current_state, {})
        
        if 'movement_chance' in state_conf:
            chance_to_move = state_conf['movement_chance']
            
        # 2. Würfeln
        if not rng.chance(chance_to_move): 
            return 

        # 3. Ziel ermitteln
        affinity_rooms = npc.get(ATTR_AFFINITY, [])
        current_loc = npc['location']
        
        if not affinity_rooms: return 
        
        # Wenn schon am Ziel, vielleicht bleiben?
        if current_loc in affinity_rooms:
            if rng.chance(AI_CHANCE_STAY): return 
            
        # Neues Ziel wählen
        target = rng.pick(affinity_rooms)
        
        # Wenn das Ziel der aktuelle Raum ist und es Alternativen gibt, wähle Alternative
        if target == current_loc and len(affinity_rooms) > 1:
            target = rng.pick([r for r in affinity_rooms if r != current_loc])
            
        # 4. Bewegen
        # Wir nutzen den Pathfinder vom Game (via System Access)
        path = self.game.pathfinder.find_path(current_loc, target)
        
        if path:
            self.move_npc(npc, path[0])

    def move_npc(self, npc, next_room):
        player_sees_movement = (self.game.location == npc['location']) or (self.game.location == next_room)
        old_loc = npc['location']
        npc['location'] = next_room
        
        if player_sees_movement and not self.game.silent:
            direction = "davon"
            room_data = self.game.rooms.get(old_loc)
            
            # Versuche Richtung zu ermitteln
            if room_data:
                for d, r_id in room_data['exits'].items():
                    if r_id == next_room: 
                        direction = d
                        break
            
            trans = {"north": "Norden", "south": "Süden", "east": "Osten", "west": "Westen", "up": "Oben", "down": "Unten", "out": "Raus"}
            dir_de = trans.get(direction, direction)
            
            if self.game.location == old_loc:
                self.game.log('character', f"{npc[ATTR_NAME]} verlässt den Raum nach {dir_de}.")
            elif self.game.location == next_room:
                self.game.log('character', f"{npc[ATTR_NAME]} betritt den Raum.")