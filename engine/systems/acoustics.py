from engine.constants import *
from collections import deque

class AcousticsSystem:
    def __init__(self, game):
        self.game = game

    def get_audibility_info(self, source_room_id, listener_room_id):
        """
        Berechnet die Hörbarkeit und die Richtung des Schalls.
        Returns: (volume, direction_text)
        volume: 0.0 bis 1.0
        direction_text: z.B. "Norden" oder "der Wand zum Reaktor"
        """
        if source_room_id == listener_room_id:
            return 1.0, "hier"

        # Wir berechnen die Lautstärke aus Sicht des Hörers (Rückwärts-Suche),
        # um direkt bestimmen zu können, aus welcher Richtung das Geräusch kommt.
        return self._calculate_sound_from_listener_perspective(listener_room_id, source_room_id)

    def _calculate_sound_from_listener_perspective(self, listener_id, source_id):
        # Wir schauen uns alle Nachbarn des Hörers an und prüfen, wie laut die Quelle von dort zu hören wäre.
        # + Wir prüfen, wie laut es ist, wenn wir durch eine Wand lauschen.
        
        # 1. Tool-Bonus prüfen
        tool_bonus = 0.0
        # Prüfe Inventar auf Items mit 'acoustic_boost'
        inv_items = [o for o in self.game.objects.values() if o['location'] == LOC_INVENTORY]
        for item in inv_items:
            boost = item.get('acoustic_boost', 0.0)
            if boost > tool_bonus: tool_bonus = boost
            
        # Wenn wir direkt im gleichen Raum sind
        if listener_id == source_id:
            return 1.0, "hier"

        max_vol = 0.0
        direction_str = "irgendwo"

        # Wir scannen die Umgebung des Listeners
        listener_room = self.game.rooms.get(listener_id)
        if not listener_room: return 0.0, ""

        # A. Exits (Offene/Geschlossene Türen)
        for direction, neighbor_id in listener_room.get('exits', {}).items():
            # Wie durchlässig ist dieser Ausgang?
            trans_local = self._calculate_exit_transmission(listener_id, direction)
            
            # Wie laut ist es im Nachbarraum? (Rekursiver Check der Quelle dort)
            vol_at_neighbor = self._get_volume_at_room(source_id, neighbor_id, visited={listener_id})
            
            total_vol = vol_at_neighbor * trans_local
            
            # Tool-Bonus wirkt auf geschlossene Barrieren
            if trans_local < 0.5 and tool_bonus > 0:
                total_vol = vol_at_neighbor * min(1.0, trans_local + tool_bonus)

            if total_vol > max_vol:
                max_vol = total_vol
                trans_map = {"north": "Norden", "south": "Süden", "east": "Osten", "west": "Westen", "up": "Oben", "down": "Unten", "out": "Draußen"}
                direction_str = trans_map.get(direction, direction)

        # B. Wände (Acoustics Definition)
        acoustics = listener_room.get('acoustics', {})
        for neighbor_id, wall_trans in acoustics.items():
            if neighbor_id not in self.game.rooms: continue
            
            vol_at_neighbor = self._get_volume_at_room(source_id, neighbor_id, visited={listener_id})
            
            # Tool Bonus wirkt stark bei Wänden
            effective_trans = wall_trans
            if tool_bonus > 0:
                effective_trans = min(1.0, wall_trans + tool_bonus)
            
            total_vol = vol_at_neighbor * effective_trans
            
            if total_vol > max_vol:
                max_vol = total_vol
                n_room = self.game.rooms.get(neighbor_id)
                direction_str = f"der Wand zu {n_room[ATTR_NAME]}"

        return max_vol, direction_str

    def _get_volume_at_room(self, source_id, current_id, visited):
        """
        Berechnet rekursiv (via Pathfinder), wie laut die Quelle 'source_id' im Raum 'current_id' ist.
        """
        if source_id == current_id:
            return 1.0
        
        if current_id in visited:
            return 0.0
        
        path = self.game.pathfinder.find_path(source_id, current_id)
        if not path:
            return 0.0
        
        # Pfad gefunden. Dämpfung berechnen.
        volume = 1.0
        trace_room = source_id
        for step_room in path:
            trans = self._get_transmission_between(trace_room, step_room)
            volume *= trans
            trace_room = step_room
            
            if volume <= 0.01: return 0.0
            
        return volume

    def _get_transmission_between(self, room_a_id, room_b_id):
        """Berechnet Transmission zwischen zwei direkt benachbarten Räumen."""
        room_a = self.game.rooms.get(room_a_id)
        
        # 1. Suche nach Exit
        for direction, target_id in room_a.get('exits', {}).items():
            if target_id == room_b_id:
                return self._calculate_exit_transmission(room_a_id, direction)
        
        # 2. Suche nach Acoustic Link (Wand)
        acoustics = room_a.get('acoustics', {})
        if room_b_id in acoustics:
            return acoustics[room_b_id]
            
        return 0.0 

    def _calculate_exit_transmission(self, room_id, direction):
        """Prüft, ob eine Tür den Ausgang blockiert."""
        transmission = ACOUSTIC_OPEN_AIR
        
        local_objs = [o for o in self.game.objects.values() if o['location'] == room_id]
        
        for obj in local_objs:
            if obj.get('linked_exit') == direction:
                if obj.get('is_open'):
                    transmission = ACOUSTIC_OPEN_DOOR
                else:
                    transmission = obj.get('acoustic_damping', ACOUSTIC_CLOSED_DOOR)
                break
        
        return transmission