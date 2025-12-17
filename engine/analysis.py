# engine/analysis.py
import copy
from engine.constants import *

def generate_future_matrix(initial_state, minutes_to_simulate=60, step_size=5):
    """
    Simuliert die Zukunft des Spiels und erstellt eine Matrix.
    """
    # 1. Klonen des IST-Zustands
    sim_state = initial_state.clone()
    
    timeline = []
    
    # 2. Schleife durch die Zukunft
    for tick in range(0, minutes_to_simulate, step_size):
        # Simulation vorantreiben
        sim_state.tick(step_size)
        
        # Snapshot erstellen
        snapshot = {
            "time": sim_state.time,
            "rooms": {}
        }
        
        # Räume initialisieren
        for room_id in sim_state.rooms:
            snapshot["rooms"][room_id] = {
                "npcs": [],
                "events": []
            }
            
        # NPCs zuordnen
        for npc in sim_state.npcs:
            loc = npc['location']
            if loc in snapshot["rooms"]:
                snapshot["rooms"][loc]["npcs"].append(npc[ATTR_NAME])
                
        # Events zuordnen (die gerade gefeuert haben)
        for node in sim_state.matrix:
            # Wir prüfen 'triggered_at', das vom GameState gesetzt wird, wenn ein Event feuert.
            # Wenn triggered_at im aktuellen Zeitfenster liegt, nehmen wir es auf.
            triggered_at = node.get('triggered_at')
            
            if triggered_at is not None:
                # Prüfen, ob das Event in DIESEM Schritt (oder knapp davor) passiert ist
                if triggered_at > (sim_state.time - step_size) and triggered_at <= sim_state.time:
                    origin = node.get('origin_id', 'unknown')
                    if origin in snapshot["rooms"]:
                        snapshot["rooms"][origin]["events"].append(node['title'])
                    
        timeline.append(snapshot)
        
    return timeline