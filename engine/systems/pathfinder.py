# engine/systems/pathfinder.py
from collections import deque

class Pathfinder:
    def __init__(self, game):
        self.game = game

    def find_path(self, start_room_id, target_room_id):
        if start_room_id == target_room_id: return []
        
        # Breadth-First Search (BFS) für kürzesten Weg
        queue = deque([[start_room_id]])
        visited = set([start_room_id])
        
        while queue:
            path = queue.popleft()
            current = path[-1]
            
            if current == target_room_id:
                return path[1:] # Ersten Raum (Start) weglassen
            
            room_data = self.game.rooms.get(current)
            if room_data:
                for exit_id in room_data['exits'].values():
                    if exit_id not in visited and exit_id in self.game.rooms:
                        visited.add(exit_id)
                        new_path = list(path)
                        new_path.append(exit_id)
                        queue.append(new_path)
        return None
        
    def get_direction_to(self, start_room, target_room_id):
        if start_room == target_room_id: return "hier"
        
        path = self.find_path(start_room, target_room_id)
        if not path: return None
        
        next_step = path[0]
        current_room_data = self.game.rooms[start_room]
        
        for direction, r_id in current_room_data['exits'].items():
            if r_id == next_step:
                trans = {
                    "north": "Norden", "south": "Süden", "east": "Osten", "west": "Westen", 
                    "up": "Oben", "down": "Unten", "out": "Ausgang"
                }
                return trans.get(direction, direction)
        
        return "irgendwo"