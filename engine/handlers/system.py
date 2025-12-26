import os
import json
import threading
from engine.handlers.interaction import InteractionHandler
from engine.analysis import generate_future_matrix
from engine.constants import *

class SystemHandler:
    
    @staticmethod
    def help(game, args):
        game.log('info', "--- HILFE & BEFEHLE ---")
        game.log('info', "Bewegung:     gehe [nord/süd/ost/west/oben/unten/raus] (n, s, o, w, u, d)")
        game.log('info', "Exploration:  schau [objekt] (l, x), nimm [objekt]")
        game.log('info', "Interaktion:  benutze [objekt] mit [objekt]")
        game.log('info', "Inventar:     i, inv, inventar")
        game.log('info', "Gespräch:     rede mit [person], gib [item] an [person]")
        game.log('info', "System:       save, load, map, quit, help (h)")
        game.log('info', "Tipp:         Pfeiltasten für Korrekturen & History.")

    @staticmethod
    def save(game, args):
        save_dir = "saves"
        if not os.path.exists(save_dir): os.makedirs(save_dir)
        
        filename = None
        
        # Fall 1: Argument angegeben (Quick Save)
        if args:
            filename = f"{''.join(x for x in args[0] if x.isalnum())}.json"
            filepath = os.path.join(save_dir, filename)
        else:
            # Fall 2: Datei-Dialog
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw() # Hauptfenster verstecken
                root.attributes('-topmost', True) # Über Pygame legen
                
                # Absoluter Pfad für den Dialog-Start
                start_dir = os.path.abspath(save_dir)
                
                selected_path = filedialog.asksaveasfilename(
                    initialdir=start_dir,
                    title="Spielstand speichern",
                    defaultextension=".json",
                    filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
                )
                root.destroy()
                
                if not selected_path: return # Abgebrochen
                filepath = selected_path
                filename = os.path.basename(filepath)
            except Exception as e:
                # Fallback für Headless oder Fehler
                print(f"[WARN] GUI Dialog fehlgeschlagen: {e}")
                filename = "savegame.json"
                filepath = os.path.join(save_dir, filename)

        # Speichern Logik
        state = {
            "time": game.time, "location": game.location, "stability": game.stability, "game_over": game.game_over,
            "knowledge": list(game.knowledge), "objects": game.objects, "npcs": game.npcs, "matrix": game.matrix, "logs": game.logs[-50:]
        }
        try:
            with open(filepath, 'w', encoding='utf-8') as f: 
                json.dump(state, f, indent=2, ensure_ascii=False)
            game.log('success', f"Gespeichert: {filename}")
        except Exception as e:
            game.log('error', f"Fehler beim Speichern: {e}")

    @staticmethod
    def load(game, args):
        save_dir = "saves"
        filepath = None
        
        if args:
            filename = f"{''.join(x for x in args[0] if x.isalnum())}.json"
            filepath = os.path.join(save_dir, filename)
        else:
            # Datei-Dialog
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                
                start_dir = os.path.abspath(save_dir)
                
                selected_path = filedialog.askopenfilename(
                    initialdir=start_dir,
                    title="Spielstand laden",
                    filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
                )
                root.destroy()
                
                if not selected_path: return
                filepath = selected_path
            except Exception as e:
                game.log('error', f"GUI Dialog Fehler: {e}")
                return

        if not os.path.exists(filepath): 
            return game.log('error', "Spielstand nicht gefunden.")
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f: state = json.load(f)
            
            # State wiederherstellen
            game.time = state.get("time"); game.location = state.get("location"); game.stability = state.get("stability")
            game.game_over = state.get("game_over"); game.knowledge = set(state.get("knowledge"))
            game.objects = state.get("objects"); game.npcs = state.get("npcs"); game.matrix = state.get("matrix"); game.logs = state.get("logs")
            game.disambiguation = None; game.dialogue_active = False 
            
            game.log('success', f"Geladen: {os.path.basename(filepath)}")
            InteractionHandler.look(game, [])
        except Exception as e:
            game.log('error', f"Ladefehler: {e}")

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