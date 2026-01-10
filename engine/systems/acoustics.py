# narratrix_engine/engine/systems/acoustics.py
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
        direction_text: z.B. "Norden", "der Wand zum Reaktor" oder "oben"
        """
        if source_room_id == listener_room_id:
            return 1.0, "hier"

        # Wir berechnen die Lautstärke aus Sicht des Hörers (Rückwärts-Suche),
        # um direkt bestimmen zu können, aus welcher Richtung das Geräusch kommt.
        return self._calculate_sound_from_listener_perspective(listener_room_id, source_room_id)

    def _calculate_sound_from_listener_perspective(self, listener_id, source_id):
        # Wir schauen uns alle Nachbarn des Hörers an und prüfen, wie laut die Quelle von dort zu hören wäre.
        # + Wir prüfen, wie laut es ist, wenn wir durch eine Wand/Decke/Boden lauschen.
        
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
        
        listener_room = self.game.rooms.get(listener_id)
        if not listener_room: return 0.0, ""

        trans_map = {
            "north": "Norden", "south": "Süden", "east": "Osten", "west": "Westen", 
            "up": "Oben", "down": "Unten", "out": "Draußen"
        }

        # --- A. Exits (Offene/Geschlossene Türen/Treppen) ---
        # Das deckt auch normale vertikale Bewegung ab (Treppen, Leitern)
        for direction, neighbor_id in listener_room.get('exits', {}).items():
            # Wie durchlässig ist dieser Ausgang?
            trans_local = self._calculate_exit_transmission(listener_id, direction)
            
            # Wie laut ist es im Nachbarraum?
            vol_at_neighbor = self._get_volume_at_room(source_id, neighbor_id, visited={listener_id})
            
            total_vol = vol_at_neighbor * trans_local
            
            # Tool-Bonus wirkt auf geschlossene Barrieren
            if trans_local < 0.5 and tool_bonus > 0:
                total_vol = vol_at_neighbor * min(1.0, trans_local + tool_bonus)

            if total_vol > max_vol:
                max_vol = total_vol
                direction_str = trans_map.get(direction, direction)

        # --- B. Wände & Vertikale Schächte (Acoustics Definition) ---
        # 'acoustics' Dictionary im Raum definiert direkte Schallverbindungen ohne Weg.
        # Format: { "room_id": transmission_float }
        # NEU: Wir prüfen auch implizite vertikale Nachbarn, wenn nicht explizit definiert.
        
        acoustics = listener_room.get('acoustics', {}).copy()
        
        # Automatische Erkennung vertikaler Nachbarn über Koordinaten (falls vorhanden)
        # Annahme: Räume haben 'z' Koordinate oder explizite 'up'/'down' exits, die wir schon prüften.
        # Aber manchmal gibt es Löcher im Boden ohne Exit. Das muss über 'acoustics' manuell definiert sein.
        
        for neighbor_id, data in acoustics.items():
            # data kann float (transmission) oder dict sein
            wall_trans = data if isinstance(data, float) else data.get('transmission', 0.0)
            custom_dir_text = data.get('direction_text') if isinstance(data, dict) else None
            
            if neighbor_id not in self.game.rooms: continue
            
            vol_at_neighbor = self._get_volume_at_room(source_id, neighbor_id, visited={listener_id})
            
            effective_trans = wall_trans
            if tool_bonus > 0:
                effective_trans = min(1.0, wall_trans + tool_bonus)
            
            total_vol = vol_at_neighbor * effective_trans
            
            if total_vol > max_vol:
                max_vol = total_vol
                
                if custom_dir_text:
                    direction_str = custom_dir_text
                else:
                    # Versuche Richtung abzuleiten
                    n_room = self.game.rooms.get(neighbor_id)
                    
                    # Checke ob es Oben/Unten ist (basierend auf Exits des Nachbarn zurück zu uns?)
                    # Einfacher: Wenn neighbor 'down' exit zu uns hat, ist er 'oben'.
                    n_exits = n_room.get('exits', {})
                    if n_exits.get('down') == listener_id: direction_str = "Oben (durch die Decke)"
                    elif n_exits.get('up') == listener_id: direction_str = "Unten (durch den Boden)"
                    else: direction_str = f"der Wand zu {n_room[ATTR_NAME]}"

        return max_vol, direction_str

    def _get_volume_at_room(self, source_id, current_id, visited):
        """
        Berechnet rekursiv (via Pathfinder), wie laut die Quelle 'source_id' im Raum 'current_id' ist.
        """
        if source_id == current_id:
            return 1.0
        
        if current_id in visited:
            return 0.0
        
        # WICHTIG: Pathfinder sucht normalerweise begehbare Wege. 
        # Für Schall wollen wir aber auch "Hör-Wege" (durch Wände/Decken).
        # Wir bräuchten einen speziellen 'AcousticPathfinder'. 
        # Da wir den nicht haben, nutzen wir den normalen Pathfinder als Approximation für die Distanz,
        # ABER wir checken direkte 'acoustics' Links als Abkürzungen.
        
        # Da eine volle Schall-Simulation zu teuer ist (Dijkstra auf Schall), 
        # machen wir hier eine Vereinfachung: Wir nutzen den normalen Pfad.
        # Das limitiert Schall durch Wände auf *direkte* Nachbarn.
        # Für Schall über 2 Räume hinweg durch 2 Wände bräuchten wir einen Graph-Search.
        
        path = self.game.pathfinder.find_path(source_id, current_id)
        if not path:
            # Fallback: Check direkte akustische Verbindung
            s_room = self.game.rooms.get(source_id)
            if s_room and current_id in s_room.get('acoustics', {}):
                # Direkter Schall-Link existiert!
                trans = self._get_transmission_between(source_id, current_id)
                return trans
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
        if not room_a: return 0.0
        
        # 1. Suche nach Exit (Luftschall)
        for direction, target_id in room_a.get('exits', {}).items():
            if target_id == room_b_id:
                return self._calculate_exit_transmission(room_a_id, direction)
        
        # 2. Suche nach Acoustic Link (Körperschall / Wand / Decke)
        acoustics = room_a.get('acoustics', {})
        if room_b_id in acoustics:
            val = acoustics[room_b_id]
            return val if isinstance(val, float) else val.get('transmission', 0.0)
            
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