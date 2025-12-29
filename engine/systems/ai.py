# engine/systems/ai.py
from engine.constants import *
from utils import rng

class AISystem:
    """
    Steuert das Verhalten aller NPCs im Spiel.
    Umfasst Bewegung, Pfadfindung und zustandsabhängige Routinen.
    """
    def __init__(self, game):
        self.game = game

    def process_all_npcs(self):
        """Haupt-Schleife: Wird jeden Tick aufgerufen, um alle NPCs zu aktualisieren."""
        for npc in self.game.npcs:
            # Pausiere KI, wenn der NPC gerade mit dem Spieler spricht.
            # Das verhindert, dass der Gesprächspartner mitten im Dialog wegrennt.
            if not self.game.silent and npc == self.game.dialogue_partner and self.game.dialogue_active:
                continue
            self._process_single_npc(npc)

    def _process_single_npc(self, npc):
        """Entscheidungslogik für einen einzelnen NPC."""
        
        # 1. Ermittlung der Bewegungswahrscheinlichkeit
        # Hierarchie: State-Level > NPC-Level > Global Default
        chance_to_move = AI_CHANCE_MOVE_DEFAULT
        
        if 'movement_chance' in npc: 
            chance_to_move = npc['movement_chance']
        
        # Prüfe den aktuellen Zustand (z.B. 'panic', 'relaxed')
        current_state = npc.get('state', 'default')
        # Hole Config für diesen State (unterstützt alte und neue Datenstruktur)
        state_conf = {}
        if 'states' in npc:
            state_conf = npc['states'].get(current_state, {}).get('behavior', {})
        else:
            # Fallback für alte Struktur
            dialogue_conf = npc.get('dialogue', {})
            state_conf = dialogue_conf.get(current_state, {})
        
        if 'movement_chance' in state_conf: 
            chance_to_move = state_conf['movement_chance']
            
        # Wenn Chance <= 0, bewegt er sich gar nicht (z.B. verletzt oder am Terminal).
        if chance_to_move <= 0: return

        # 2. Bestehendes Ziel verfolgen (Intent Persistence)
        destination = npc.get('destination')
        
        if destination:
            # Sind wir schon da?
            if npc['location'] == destination:
                npc['destination'] = None # Ziel erreicht
                # Chance zu verweilen, bevor ein neues Ziel gesucht wird
                if rng.chance(AI_CHANCE_STAY): return
            else:
                # Noch unterwegs. 
                # Wenn nicht in Panik (<50%), würfeln wir trotzdem, ob er trödelt.
                if chance_to_move < 50 and not rng.chance(chance_to_move): return
                
                # Nächsten Schritt berechnen
                path = self.game.pathfinder.find_path(npc['location'], destination)
                if path:
                    self.move_npc(npc, path[0])
                    return
                else:
                    # Weg blockiert oder nicht gefunden -> Ziel verwerfen
                    npc['destination'] = None

        # 3. Neues Ziel wählen (nur wenn kein aktives Ziel)
        # Wir würfeln für den Start einer neuen Reise
        if not rng.chance(chance_to_move): return 

        # 4. Routen-Logik (Patrouillen)
        route = None
        behavior = "loop"
        
        # Lese Route aus State oder NPC Config
        if 'route' in state_conf:
            route = state_conf['route']
            behavior = state_conf.get('route_behavior', 'loop')
        elif 'route' in npc:
            route = npc['route']
            behavior = npc.get('route_behavior', 'loop')
            
        if route and len(route) > 0:
            idx = npc.get('route_index', 0)
            
            # Prüfen, ob Index valide ist
            if idx < len(route):
                next_target = route[idx]
                
                # Wenn wir den Wegpunkt erreicht haben -> Nächster Punkt
                if npc['location'] == next_target:
                    idx += 1
                    # Verhalten am Ende der Route
                    if idx >= len(route):
                        if behavior == 'loop': idx = 0
                        elif behavior == 'pingpong': pass # TODO: Pingpong Logik
                        elif behavior == 'once': route = None 
                    
                    npc['route_index'] = idx
                    if route: next_target = route[idx]
                
                # Wenn wir ein valides Ziel haben, loslaufen
                if route and next_target != npc['location']:
                    path = self.game.pathfinder.find_path(npc['location'], next_target)
                    if path:
                        npc['destination'] = next_target
                        self.move_npc(npc, path[0])
                        return

        # 5. Zufalls-Logik (Affinity / Random Walk)
        # Wird nur ausgeführt, wenn keine Route aktiv ist
        affinity_rooms = npc.get(ATTR_AFFINITY, [])
        current_loc = npc['location']
        
        if not affinity_rooms: return 
        
        target = rng.pick(affinity_rooms)
        
        # Versuche, den Raum zu wechseln (nicht stehenbleiben), wenn möglich
        if target == current_loc and len(affinity_rooms) > 1:
            target = rng.pick([r for r in affinity_rooms if r != current_loc])
            
        if target and target != current_loc:
            path = self.game.pathfinder.find_path(current_loc, target)
            if path:
                npc['destination'] = target
                self.move_npc(npc, path[0])

    def move_npc(self, npc, next_room):
        """Führt die Bewegung aus und generiert Log-Nachrichten für den Spieler."""
        player_sees_movement = (self.game.location == npc['location']) or (self.game.location == next_room)
        old_loc = npc['location']
        npc['location'] = next_room
        
        # STEALTH CHECK: 
        # Wenn Spieler versteckt ist (hidden_in), sieht er den NPC, aber der NPC ihn nicht.
        # Der Log-Text wird angepasst, um das Versteck widerzuspiegeln.
        
        if player_sees_movement and not self.game.silent:
            room_data_old = self.game.rooms.get(old_loc)
            room_data_new = self.game.rooms.get(next_room)
            
            # Fall A: Spieler sieht NPC gehen (aus dem aktuellen Raum)
            if self.game.location == old_loc:
                direction = "davon"
                if room_data_old:
                    for d, r_id in room_data_old['exits'].items():
                        if r_id == next_room: direction = d; break
                
                trans = {
                    "north": "Norden", "south": "Süden", "east": "Osten", "west": "Westen", 
                    "up": "Oben", "down": "Unten", "out": "Raus", "dock": "zum Dock"
                }
                dir_de = trans.get(direction, direction)
                
                msg = f"{npc[ATTR_NAME]} verlässt den Raum nach {dir_de}."
                if self.game.hidden_in: msg = f"(Versteckt) {msg}"
                self.game.log('character', msg)
            
            # Fall B: Spieler sieht NPC kommen (in den aktuellen Raum)
            elif self.game.location == next_room:
                direction_from = "irgendwoher"
                # Wir suchen den Ausgang im *neuen* Raum, der zum *alten* führt
                if room_data_new:
                    for d, r_id in room_data_new['exits'].items():
                        if r_id == old_loc: direction_from = d; break
                
                # Wenn im aktuellen Raum 'Norden' zum alten Raum führt, kommt der NPC aus Norden.
                trans_from = {
                    "north": "Norden", "south": "Süden", "east": "Osten", "west": "Westen", 
                    "up": "Oben", "down": "Unten", "out": "Draußen", "dock": "dem Dock"
                }
                dir_de = trans_from.get(direction_from, direction_from)
                
                if direction_from != "irgendwoher":
                    msg = f"{npc[ATTR_NAME]} betritt den Raum aus Richtung {dir_de}."
                else:
                    msg = f"{npc[ATTR_NAME]} betritt den Raum."
                
                if self.game.hidden_in: msg = f"(Versteckt) {msg}"
                self.game.log('character', msg)