# engine/systems/ai.py
from engine.constants import *
from utils import rng

class AISystem:
    def __init__(self, game):
        self.game = game

    def process_all_npcs(self):
        """Haupt-Loop für alle NPCs."""
        for npc in self.game.npcs:
            # Wenn NPC gerade spricht, pausiert seine KI (damit er nicht wegrennt)
            if not self.game.silent and npc == self.game.dialogue_partner and self.game.dialogue_active:
                continue
            self._process_single_npc(npc)

    def _process_single_npc(self, npc):
        # 1. Wahrscheinlichkeit ermitteln (Bewegt er sich überhaupt?)
        chance_to_move = AI_CHANCE_MOVE_DEFAULT
        
        # Override NPC Level
        if 'movement_chance' in npc:
            chance_to_move = npc['movement_chance']
            
        # Override State Level
        current_state = npc.get('state', 'default')
        dialogue_conf = npc.get('dialogue', {})
        state_conf = dialogue_conf.get(current_state, {})
        
        if 'movement_chance' in state_conf:
            chance_to_move = state_conf['movement_chance']
            
        # Wenn er sich gar nicht bewegen soll (0%), brechen wir sofort ab.
        # Auch bestehende Pfade werden pausiert.
        if chance_to_move <= 0:
            return

        # 2. Bestehendes Ziel prüfen (Intent Persistence)
        destination = npc.get('destination')
        
        # Wenn wir ein Ziel haben, prüfen wir, ob wir schon da sind
        if destination:
            if npc['location'] == destination:
                # Angekommen! Ziel löschen.
                npc['destination'] = None
                destination = None
                # Chance zu bleiben, wenn man gerade angekommen ist?
                if rng.chance(AI_CHANCE_STAY): return
            else:
                # Noch nicht da. Wir müssen weiterlaufen.
                # Wir würfeln trotzdem, ob er trödelt, es sei denn er ist in Panik (Chance > 50)
                if chance_to_move < 50 and not rng.chance(chance_to_move):
                    return

                # Pfad zum Ziel berechnen (Schritt für Schritt)
                path = self.game.pathfinder.find_path(npc['location'], destination)
                
                if path:
                    # Nächster Schritt
                    self.move_npc(npc, path[0])
                    return
                else:
                    # Weg blockiert oder nicht gefunden? Ziel verwerfen.
                    npc['destination'] = None
                    destination = None

        # 3. Neues Ziel wählen (nur wenn wir kein aktives Ziel haben)
        # Wir würfeln jetzt erst für den Start einer *neuen* Reise
        if not rng.chance(chance_to_move): 
            return 

        # NEU: ROUTEN LOGIK (Prio 2)
        route = None
        behavior = "loop"
        
        if 'route' in state_conf:
            route = state_conf['route']
            behavior = state_conf.get('route_behavior', 'loop')
        elif 'route' in npc:
            route = npc['route']
            behavior = npc.get('route_behavior', 'loop')
            
        if route and len(route) > 0:
            # Aktuellen Index holen oder initialisieren
            idx = npc.get('route_index', 0)
            
            # Nächstes Ziel bestimmen
            if idx < len(route):
                next_target = route[idx]
                
                # Wenn wir schon dort sind, Index inkrementieren
                if npc['location'] == next_target:
                    idx += 1
                    
                    # Verhalten am Ende der Route
                    if idx >= len(route):
                        if behavior == 'loop':
                            idx = 0
                        elif behavior == 'pingpong':
                            # Einfaches Pingpong: Route umkehren
                            # Wir müssen die Route im NPC-State umdrehen oder Logik anpassen
                            # Einfacher: Reverse Liste im Speicher des NPCs
                            # Hier simulieren wir Pingpong durch statische Umkehr wenn am Ende
                            pass # TODO: Pingpong Logik verfeinern
                            idx = 0 # Fallback Loop
                        elif behavior == 'once':
                            # Route fertig -> Fallback auf Affinity
                            route = None 
                            
                    npc['route_index'] = idx
                    if route: next_target = route[idx]
                
                if route and next_target != npc['location']:
                    # Pfad checken
                    path = self.game.pathfinder.find_path(npc['location'], next_target)
                    if path:
                        npc['destination'] = next_target
                        self.move_npc(npc, path[0])
                        return

        # Prio 3: Affinity / Random Walk
        affinity_rooms = npc.get(ATTR_AFFINITY, [])
        current_loc = npc['location']
        
        if not affinity_rooms: return 
        
        # Zielwahl
        target = rng.pick(affinity_rooms)
        
        # Wenn das Ziel der aktuelle Raum ist und es Alternativen gibt, wähle Alternative
        if target == current_loc and len(affinity_rooms) > 1:
            target = rng.pick([r for r in affinity_rooms if r != current_loc])
            
        # Wenn wir ein valides neues Ziel haben (das nicht der aktuelle Ort ist)
        if target and target != current_loc:
            # Pfad checken
            path = self.game.pathfinder.find_path(current_loc, target)
            if path:
                # Ziel ins Gedächtnis schreiben
                npc['destination'] = target
                # Ersten Schritt machen
                self.move_npc(npc, path[0])

    def move_npc(self, npc, next_room):
        player_sees_movement = (self.game.location == npc['location']) or (self.game.location == next_room)
        old_loc = npc['location']
        npc['location'] = next_room
        
        if player_sees_movement and not self.game.silent:
            room_data_old = self.game.rooms.get(old_loc)
            room_data_new = self.game.rooms.get(next_room)
            
            # Fall 1: Spieler sieht NPC gehen
            if self.game.location == old_loc:
                direction = "davon"
                if room_data_old:
                    for d, r_id in room_data_old['exits'].items():
                        if r_id == next_room: 
                            direction = d
                            break
                trans = {"north": "Norden", "south": "Süden", "east": "Osten", "west": "Westen", "up": "Oben", "down": "Unten", "out": "Raus", "dock": "zum Dock"}
                dir_de = trans.get(direction, direction)
                self.game.log('character', f"{npc[ATTR_NAME]} verlässt den Raum nach {dir_de}.")
            
            # Fall 2: Spieler sieht NPC kommen (Realistischere Beschreibung)
            elif self.game.location == next_room:
                direction_from = "irgendwoher"
                # Wir suchen den Ausgang im *neuen* Raum, der zurück zum *alten* führt, um die Herkunft zu bestimmen
                if room_data_new:
                    for d, r_id in room_data_new['exits'].items():
                        if r_id == old_loc:
                            direction_from = d
                            break
                
                trans_from = {
                    "north": "Süden", # Wenn Ausgang Norden ist, kommt er von Norden (im neuen Raum ist Norden der Weg zurück? Nein, Moment.)
                    # Logik: Wenn im aktuellen Raum (B) der Ausgang nach (A) "Norden" ist, dann liegt A im Norden von B.
                    # Also kommt der NPC aus dem Norden.
                    "north": "Norden", 
                    "south": "Süden", 
                    "east": "Osten", 
                    "west": "Westen", 
                    "up": "Oben", 
                    "down": "Unten",
                    "out": "Draußen",
                    "dock": "dem Dock"
                }
                
                # Wenn im aktuellen Raum 'north' zum alten Raum führt, kommt der NPC aus Norden.
                dir_de = trans_from.get(direction_from, direction_from)
                
                if direction_from != "irgendwoher":
                    self.game.log('character', f"{npc[ATTR_NAME]} betritt den Raum aus Richtung {dir_de}.")
                else:
                    self.game.log('character', f"{npc[ATTR_NAME]} betritt den Raum.")
