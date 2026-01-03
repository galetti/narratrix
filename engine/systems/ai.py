import random
from engine.constants import *
from engine.action_dispatcher import ActionDispatcher
from engine.systems.pathfinder import Pathfinder

# Restauriertes AI System: Behält alte Methoden bei und integriert neue Logik.

class AISystem:
    """
    Steuert NPCs, ihre Bewegungen und autonomes Handeln.
    Integriert Pathfinding und komplexe Verhaltensmuster.
    """
    
    def __init__(self, game):
        self.game = game
        self.pathfinder = Pathfinder(game)

    def process_all_npcs(self):
        """Wird jeden Tick aufgerufen. (Früher update)"""
        for npc in self.game.npcs:
            self._process_npc(npc)

    # --- CORE PROCESS ---

    def _process_npc(self, npc):
        # 1. State Management (einfacher State Machine Ansatz)
        current_state = npc.get('state', 'idle')
        
        # 2. Priorität: Pathfinding (hat der NPC ein Ziel?)
        target_room = npc.get('target_room')
        if target_room and npc['location'] != target_room:
            self._move_towards_target(npc, target_room)
            return

        # 3. Verhalten basierend auf Rolle/State
        if npc.get('roam') and random.random() < 0.1: 
            self._roam(npc)
            
        # 4. Reaktives Verhalten (z.B. Engineer repariert sabotierte Räume)
        self._check_environment_triggers(npc)

    # --- MOVEMENT LOGIC ---

    def move_npc(self, npc_id, target_room_id):
        """
        Öffentliche Methode zum direkten Bewegen eines NPCs (z.B. durch Events).
        Dies entspricht der alten Funktionalität, die Events genutzt haben könnten.
        """
        npc = next((n for n in self.game.npcs if n['id'] == npc_id), None)
        if npc:
            self._execute_move(npc, "teleport", target_room_id)
            npc['target_room'] = None # Ziel löschen, da angekommen

    def _move_towards_target(self, npc, target_room_id):
        """Nutzt den Pathfinder, um den nächsten Schritt zum Ziel zu finden."""
        path = self.pathfinder.find_path(npc['location'], target_room_id)
        
        if path and len(path) > 1:
            next_step = path[1] # [0] ist start, [1] ist nächster Raum
            
            # Finde die Richtung (Direction) für diesen Schritt
            current_room = self.game.rooms.get(npc['location'])
            exits = current_room.get('exits', {})
            direction = None
            for d, r_id in exits.items():
                if r_id == next_step:
                    direction = d
                    break
            
            if direction:
                self._execute_move(npc, direction, next_step)
            else:
                # Fallback: Teleport oder Fehler (Pfad existiert, aber kein Exit?)
                # Wir teleportieren sicherheitshalber zum nächsten Schritt
                self._execute_move(npc, "path_link", next_step)
        else:
            # Ziel erreicht oder kein Pfad
            if npc['location'] == target_room_id:
                npc['target_room'] = None # Ziel löschen
                if self.game.location == npc['location']:
                    self.game.log('character', f"{npc['name']} ist angekommen.")

    def _execute_move(self, npc, direction, target_id):
        old_loc = npc['location']
        npc['location'] = target_id
        
        # Logs nur wenn Spieler relevant
        if self.game.location == old_loc:
            if direction in ["teleport", "path_link"]:
                self.game.log('character', f"{npc['name']} verlässt den Raum.")
            else:
                self.game.log('character', f"{npc['name']} geht nach {direction}.")
        elif self.game.location == target_id:
            if direction in ["teleport", "path_link"]:
                self.game.log('character', f"{npc['name']} betritt den Raum.")
            else:
                self.game.log('character', f"{npc['name']} kommt aus {self._inverse_dir(direction)}.")

    def _roam(self, npc):
        """Zufällige Bewegung."""
        current_loc_id = npc['location']
        room = self.game.rooms.get(current_loc_id)
        if not room: return
        exits = room.get('exits', {})
        if not exits: return
        
        direction = random.choice(list(exits.keys()))
        target_id = exits[direction]
        self._execute_move(npc, direction, target_id)

    # --- INTERACTION LOGIC ---

    def npc_look(self, npc):
        """
        Simuliert Wahrnehmung des NPCs.
        Kann von Events genutzt werden, um zu prüfen, was der NPC sieht.
        """
        local_objs = [o for o in self.game.objects.values() if o['location'] == npc['location']]
        return local_objs

    def _check_environment_triggers(self, npc):
        """Spezifische Interaktionen je nach Rolle."""
        current_room = self.game.rooms.get(npc['location'])
        if not current_room: return

        # Engineer Logic
        if npc.get('role') == 'engineer' and current_room.get('state') == STATE_SABOTAGED:
            # 50% Chance zu reparieren wenn im Raum
            if random.random() < 0.5:
                # Wir rufen die Aktion direkt auf
                if self.game.location == npc['location']:
                    self.game.log('character', f"{npc['name']} beginnt Reparaturen an den Systemen...")
                    
                # Fix durchführen
                current_room['state'] = STATE_NORMAL
                
                if self.game.location == npc['location']:
                    self.game.log('success', f"{npc['name']} hat die Systeme stabilisiert!")

    def _inverse_dir(self, direction):
        mapping = {"north": "Süden", "south": "Norden", "east": "Westen", "west": "Osten", "up": "Unten", "down": "Oben", "out": "Drinnen"}
        return mapping.get(direction, "irgendwo")

    def _perform_action(self, npc, verb, args):
        """Generische Aktion (Platzhalter für komplexere Interaktionen)."""
        if self.game.location == npc['location']:
            # Detaillierte Logs für den Spieler
            item_name = args[0] if args else "etwas"
            
            if verb == 'take':
                self.game.log('character', f"{npc['name']} steckt {item_name} ein.")
            elif verb == 'drop':
                self.game.log('character', f"{npc['name']} legt {item_name} ab.")
            elif verb == 'open':
                self.game.log('character', f"{npc['name']} öffnet {item_name}.")
            elif verb == 'close':
                self.game.log('character', f"{npc['name']} schließt {item_name}.")
            elif verb == 'use':
                self.game.log('character', f"{npc['name']} benutzt {item_name}.")
            elif verb == 'fix':
                self.game.log('character', f"{npc['name']} repariert {item_name}.")
            else:
                self.game.log('character', f"{npc['name']} macht etwas mit {item_name}.")