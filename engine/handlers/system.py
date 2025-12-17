import os
import json
from engine.handlers.interaction import InteractionHandler
from engine.analysis import generate_future_matrix
from engine.constants import *

class SystemHandler:
    @staticmethod
    def save(game, args):
        save_dir = "saves"
        if not os.path.exists(save_dir): os.makedirs(save_dir)
        filename = f"{''.join(x for x in args[0] if x.isalnum())}.json" if args else "savegame.json"
        filepath = os.path.join(save_dir, filename)
        state = {
            "time": game.time, "location": game.location, "stability": game.stability, "game_over": game.game_over,
            "knowledge": list(game.knowledge), "objects": game.objects, "npcs": game.npcs, "matrix": game.matrix, "logs": game.logs[-50:]
        }
        with open(filepath, 'w', encoding='utf-8') as f: json.dump(state, f, indent=2, ensure_ascii=False)
        game.log('success', f"Gespeichert: {filename}")

    @staticmethod
    def load(game, args):
        save_dir = "saves"
        filename = f"{''.join(x for x in args[0] if x.isalnum())}.json" if args else "savegame.json"
        filepath = os.path.join(save_dir, filename)
        if not os.path.exists(filepath): return game.log('error', "Spielstand nicht gefunden.")
        with open(filepath, 'r', encoding='utf-8') as f: state = json.load(f)
        game.time = state.get("time"); game.location = state.get("location"); game.stability = state.get("stability")
        game.game_over = state.get("game_over"); game.knowledge = set(state.get("knowledge"))
        game.objects = state.get("objects"); game.npcs = state.get("npcs"); game.matrix = state.get("matrix"); game.logs = state.get("logs")
        game.disambiguation = None; game.dialogue_active = False 
        game.log('success', f"Geladen: {filename}")
        InteractionHandler.look(game, [])

    @staticmethod
    def oracle(game, args):
        game.log('event', "Zugriff auf interne Sensoren... Berechne Prognosen...")
        timeline = generate_future_matrix(game, minutes_to_simulate=60, step_size=5)
        found_vision = False
        for snap in timeline:
            time_offset = snap['time'] - game.time
            if time_offset <= 0: continue
            for r_id, r_data in snap['rooms'].items():
                room_name = game.rooms[r_id][ATTR_NAME]
                if r_data['events']:
                    events = ", ".join(r_data['events'])
                    game.log('story', f"[ALERT T+{time_offset}m] Sektor '{room_name}': {events}")
                    found_vision = True
                if r_data['events'] and r_data['npcs']:
                    names = ", ".join(r_data['npcs'])
                    game.log('alarm', f"WARNUNG: Lebenszeichen ({names}) im Gefahrenbereich!")
                    found_vision = True
        if not found_vision: game.log('info', "Sensoren: Keine Anomalien in den nächsten 60 Minuten.")

    @staticmethod
    def map(game, args):
        game.log('info', "--- SYSTEM ÜBERSICHT ---")
        min_x, max_x = 0, 0; min_y, max_y = 0, 0
        grid = {} 
        for r_id, room in game.rooms.items():
            x = room.get('map_x', 0); y = room.get('map_y', 0)
            grid[(x,y)] = r_id
            min_x = min(min_x, x); max_x = max(max_x, x); min_y = min(min_y, y); max_y = max(max_y, y)

        for y in range(min_y, max_y + 1):
            line1 = ""; line2 = "" 
            for x in range(min_x, max_x + 1):
                r_id = grid.get((x, y))
                if r_id:
                    symbol = "[ ]" 
                    if r_id == game.location: symbol = "[@]" 
                    npcs_here = [n for n in game.npcs if n['location'] == r_id]
                    if npcs_here: symbol = "[N]" if r_id != game.location else "[@N]"
                    cell = f"{symbol}".center(12)
                    exits = game.rooms[r_id]['exits']
                    has_east = 'east' in exits or (grid.get((x+1, y)) and 'west' in game.rooms[grid.get((x+1, y))]['exits'])
                    conn = "--" if has_east else "  "
                    line1 += cell + conn
                    has_south = 'south' in exits or (grid.get((x, y+1)) and 'north' in game.rooms[grid.get((x, y+1))]['exits'])
                    v_conn = "  |  " if has_south else "     "
                    line2 += v_conn.center(12) + "  "
                else: line1 += " " * 14; line2 += " " * 14
            game.log('info', line1)
            if y < max_y: game.log('info', line2)
        game.log('info', "Legende: [@] Pos, [N] Bio-Signatur")