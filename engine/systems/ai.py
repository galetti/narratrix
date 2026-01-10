# narratrix_engine/engine/systems/ai.py
from engine.constants import *

class AISystem:
    def __init__(self, game):
        self.game = game

    def process_all_npcs(self, minutes=1):
        """
        Wird jeden Tick aufgerufen.
        minutes: Die vergangene Zeit in Minuten (wichtig für Geschwindigkeit).
        """
        for npc in self.game.npcs:
            self._handle_movement(npc, minutes)
            # Hier könnte später komplexe Behavior-Tree Logik folgen
            # self._handle_behavior(npc)

    def move_npc(self, npc_id, target_room_id, instant=False):
        """
        Befiehlt einem NPC, sich zu einem Ziel zu bewegen.
        instant=True erzwingt Teleportation.
        """
        npc = self._find_npc(npc_id)
        if not npc: 
            print(f"[AI] Warnung: NPC {npc_id} nicht gefunden.")
            return

        if instant:
            # Teleportation (für Debugging oder SciFi-Tech)
            old_loc = npc.get('location')
            npc['location'] = target_room_id
            npc['path'] = [] # Alten Pfad löschen
            npc['target_location'] = None
            if old_loc != target_room_id:
                # Logik für Spieler-Feedback beim Teleport könnte hier rein
                pass
            return

        # Echte Bewegung berechnen
        start_room = npc.get('location')
        if start_room == target_room_id:
            return # Schon da

        # Pfad finden
        path = self.game.pathfinder.find_path(start_room, target_room_id)
        if path:
            # Pathfinder gibt Liste exklusive Start, inklusive Ziel zurück (z.B. ['flur', 'keller'])
            npc['path'] = path
            npc['target_location'] = target_room_id
            
            # Bewegungsspeicher initialisieren falls nicht vorhanden
            if 'move_acc' not in npc: npc['move_acc'] = 0.0
            
            # Optional: Feedback, dass er losläuft (nur wenn Spieler dabei ist)
            if self.game.location == start_room:
                # Wohin geht der erste Schritt?
                first_step = path[0]
                direction = self._get_exit_direction(start_room, first_step)
                dir_str = f" nach {direction}" if direction else ""
                self.game.log('character', f"{npc[ATTR_NAME]} macht sich auf den Weg{dir_str}.")
        else:
            print(f"[AI] Kein Weg gefunden für {npc[ATTR_NAME]} von {start_room} nach {target_room_id}")

    def _handle_movement(self, npc, minutes):
        """Verarbeitet die Bewegung eines NPCs basierend auf Zeit und Geschwindigkeit."""
        path = npc.get('path')
        if not path: return

        # Geschwindigkeit: Default 1.0 (1 Raum pro Minute)
        # 2.0 = Doppelt so schnell, 0.5 = Halb so schnell
        speed = npc.get('speed', 1.0)
        
        # Bewegungs-Akku aufladen
        current_acc = npc.get('move_acc', 0.0) + (speed * minutes)
        
        # Schritte abarbeiten
        steps_taken = 0
        
        # Solange genug "Energie" für einen Schritt (Kosten: 1.0) da ist
        while current_acc >= 1.0 and path:
            next_room_id = path.pop(0)
            old_room_id = npc['location']
            
            # Bewegung ausführen
            npc['location'] = next_room_id
            current_acc -= 1.0
            steps_taken += 1
            
            # Spieler-Feedback generieren (Begegnungen)
            self._broadcast_movement(npc, old_room_id, next_room_id)
            
        npc['move_acc'] = current_acc
        
        # Ziel erreicht?
        if not path and steps_taken > 0:
            npc['target_location'] = None
            npc['move_acc'] = 0.0 # Rest-Energie verfällt bei Ankunft (oder behalten?)
            # Hier könnte man ein "Arrived" Event triggern

    def _broadcast_movement(self, npc, old_room, new_room):
        """Erzeugt Textausgaben, wenn der Spieler die Bewegung sieht."""
        player_loc = self.game.location
        npc_name = npc[ATTR_NAME]

        # Fall A: Spieler ist im Raum, den der NPC verlässt
        if player_loc == old_room:
            direction = self._get_exit_direction(old_room, new_room)
            dir_text = f" nach {direction}" if direction else ""
            self.game.log('character', f"{npc_name} verlässt den Bereich{dir_text}.")
        
        # Fall B: Spieler ist im Raum, den der NPC betritt
        elif player_loc == new_room:
            # Wir brauchen die Richtung, aus der er kommt (Exit vom NEUEN zum ALTEN Raum)
            direction = self._get_exit_direction(new_room, old_room)
            dir_text = f" aus {direction}" if direction else ""
            self.game.log('character', f"{npc_name} betritt den Bereich{dir_text}.")

    def _get_exit_direction(self, source_id, target_id):
        """Hilfsfunktion: Findet den Namen des Exits zu einem Raum."""
        room = self.game.rooms.get(source_id)
        if not room: return None
        
        trans_map = {
            "north": "Norden", "south": "Süden", "east": "Osten", "west": "Westen", 
            "up": "Oben", "down": "Unten", "out": "Draußen"
        }
        
        for direction, dest in room.get('exits', {}).items():
            if dest == target_id:
                return trans_map.get(direction, direction)
        return None

    def _find_npc(self, identifier):
        return next((n for n in self.game.npcs if n.get('id') == identifier or n.get('name') == identifier), None)