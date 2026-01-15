from engine.constants import *
from collections import deque
import math

class AcousticsSystem:
    def __init__(self, game):
        self.game = game
        # Konfigurierbare Reichweite für Optimierung
        # Angenommen: Transmission ist im Schnitt 0.9 pro Raum.
        # 0.9^x < 0.05 (Hörschwelle) -> x ≈ 28 Räume.
        # Bei geschlossenen Türen (0.2) -> 0.2^x < 0.05 -> x ≈ 2 Räume.
        self.max_propagation_distance = 20 # Sicherheitslimit für Pathfinder

    def get_audibility_info(self, source_room_id, listener_room_id):
        """
        Berechnet die Hörbarkeit und die Richtung des Schalls.
        Returns: (volume, direction_text)
        """
        if source_room_id == listener_room_id:
            return 1.0, "hier"

        # Optimierung: Distanz-Check VOR teurer Pfadsuche
        if not self._is_potentially_audible(source_room_id, listener_room_id):
            return 0.0, ""

        return self._calculate_sound_from_listener_perspective(listener_room_id, source_room_id)

    def _is_potentially_audible(self, source_id, listener_id):
        """
        Schneller Check, ob es sich überhaupt lohnt, Pfade zu berechnen.
        Nutzt Koordinaten (falls vorhanden) für Heuristik.
        """
        room_s = self.game.rooms.get(source_id)
        room_l = self.game.rooms.get(listener_id)
        
        if not room_s or not room_l: return False
        
        # Koordinaten aus Editor-Daten nutzen (falls vorhanden)
        ed_s = room_s.get('_editor', {})
        ed_l = room_l.get('_editor', {})
        
        if 'x' in ed_s and 'x' in ed_l:
            # Einfache Euklidische Distanz im Grid (Skalierung beachten!)
            # Annahme: Grid Size im Editor ist ca. 100-150px pro Raum.
            # Wir normalisieren das grob auf "Raum-Einheiten".
            dx = (ed_s['x'] - ed_l['x']) / 100.0
            dy = (ed_s['y'] - ed_l['y']) / 100.0
            dz = (ed_s.get('z', 0) - ed_l.get('z', 0)) * 2 # Z zählt mehr (Decken dämpfen stark)
            
            dist = math.sqrt(dx*dx + dy*dy + dz*dz)
            
            # Wenn Distanz > Max Reichweite -> Abbruch
            if dist > self.max_propagation_distance:
                return False
                
        return True

    def _calculate_sound_from_listener_perspective(self, listener_id, source_id):
        tool_bonus = 0.0
        inv_items = [o for o in self.game.objects.values() if o['location'] == LOC_INVENTORY]
        for item in inv_items:
            boost = item.get('acoustic_boost', 0.0)
            if boost > tool_bonus: tool_bonus = boost
            
        if listener_id == source_id: return 1.0, "hier"

        max_vol = 0.0
        direction_str = "irgendwo"
        
        listener_room = self.game.rooms.get(listener_id)
        if not listener_room: return 0.0, ""

        trans_map = {
            "north": ("Norden", "aus"), 
            "south": ("Süden", "aus"), 
            "east": ("Osten", "aus"), 
            "west": ("Westen", "aus"), 
            "up": ("Oben", "von"), 
            "down": ("Unten", "von"), 
            "out": ("Draußen", "von"),
            "northeast": ("Nordosten", "aus"), 
            "northwest": ("Nordwesten", "aus"),
            "southeast": ("Südosten", "aus"), 
            "southwest": ("Südwesten", "aus")
        }

        # --- A. Exits ---
        for direction, neighbor_id in listener_room.get('exits', {}).items():
            trans_local = self._calculate_exit_transmission(listener_id, direction)
            
            # WICHTIG: Wenn der Ausgang schon fast dicht ist, brechen wir diesen Zweig ab
            if trans_local <= 0.01: continue

            vol_at_neighbor = self._get_volume_at_room(source_id, neighbor_id, visited={listener_id})
            
            total_vol = vol_at_neighbor * trans_local
            
            if trans_local < 0.5 and tool_bonus > 0:
                total_vol = vol_at_neighbor * min(1.0, trans_local + tool_bonus)

            if total_vol > max_vol:
                max_vol = total_vol
                name, prep = trans_map.get(direction, (direction, "aus"))
                direction_str = f"{prep} {name}"

        # --- B. Wände & Acoustics ---
        acoustics = listener_room.get('acoustics', {}).copy()
        for neighbor_id, data in acoustics.items():
            wall_trans = data if isinstance(data, float) else data.get('transmission', 0.0)
            custom_dir_text = data.get('direction_text') if isinstance(data, dict) else None
            
            # WICHTIG: Wanddichte Check
            if wall_trans <= 0.01: continue

            if neighbor_id not in self.game.rooms: continue
            
            vol_at_neighbor = self._get_volume_at_room(source_id, neighbor_id, visited={listener_id})
            effective_trans = wall_trans
            if tool_bonus > 0: effective_trans = min(1.0, wall_trans + tool_bonus)
            
            total_vol = vol_at_neighbor * effective_trans
            
            if total_vol > max_vol:
                max_vol = total_vol
                if custom_dir_text: 
                    direction_str = custom_dir_text 
                else:
                    n_room = self.game.rooms.get(neighbor_id)
                    n_exits = n_room.get('exits', {})
                    if n_exits.get('down') == listener_id: direction_str = "von Oben (durch die Decke)"
                    elif n_exits.get('up') == listener_id: direction_str = "von Unten (durch den Boden)"
                    else: direction_str = f"hinter der Wand zu {n_room[ATTR_NAME]}"

        # Cutoff: Wenn Lautstärke mikroskopisch klein ist, betrachte es als 0
        if max_vol < 0.01: return 0.0, ""
        
        return max_vol, direction_str

    def _get_volume_at_room(self, source_id, current_id, visited):
        if source_id == current_id: return 1.0
        if current_id in visited: return 0.0
        
        # Performance: Nutze limitierte Pfadsuche (nicht unendlich tief)
        # Wir modifizieren find_path aber nicht, da er BFS ist (kürzester Weg zuerst).
        # Aber wir können prüfen, ob der Weg zu lang ist.
        
        path = self.game.pathfinder.find_path(source_id, current_id)
        
        # Optimierung: Wenn Weg zu lang für Akustik, brich ab.
        # Annahme: Selbst bei offener Tür (0.9) ist nach 30 Räumen Stille (0.9^30 = 0.04)
        if path and len(path) > 30: 
            return 0.0

        if not path:
            s_room = self.game.rooms.get(source_id)
            if s_room and current_id in s_room.get('acoustics', {}):
                trans = self._get_transmission_between(source_id, current_id)
                return trans
            return 0.0
        
        volume = 1.0
        trace_room = source_id
        for step_room in path:
            trans = self._get_transmission_between(trace_room, step_room)
            volume *= trans
            trace_room = step_room
            # WICHTIG: Early Exit während der Berechnung
            if volume <= 0.01: return 0.0
            
        return volume

    def _get_transmission_between(self, room_a_id, room_b_id):
        room_a = self.game.rooms.get(room_a_id)
        if not room_a: return 0.0
        
        for direction, target_id in room_a.get('exits', {}).items():
            if target_id == room_b_id:
                return self._calculate_exit_transmission(room_a_id, direction)
        
        acoustics = room_a.get('acoustics', {})
        if room_b_id in acoustics:
            val = acoustics[room_b_id]
            return val if isinstance(val, float) else val.get('transmission', 0.0)
            
        return 0.0 

    def _calculate_exit_transmission(self, room_id, direction):
        transmission = ACOUSTIC_OPEN_AIR
        local_objs = [o for o in self.game.objects.values() if o['location'] == room_id]
        
        for obj in local_objs:
            if obj.get('linked_exit') == direction:
                if obj.get('is_open'): transmission = ACOUSTIC_OPEN_DOOR
                else: transmission = obj.get('acoustic_damping', ACOUSTIC_CLOSED_DOOR)
                break
        return transmission