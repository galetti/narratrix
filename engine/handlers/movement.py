# narratrix_engine/engine/handlers/movement.py
from engine.constants import *
from engine.resolver import Resolver, ResolutionError

class MovementHandler:
    @staticmethod
    def handle(game, args):
        if game.hidden_in:
            if any(w in args for w in ["raus", "out", "verlasse", "exit"]):
                # Aus Versteck kommen
                game.hidden_in = None
                game.log('success', "Du kommst aus deinem Versteck hervor.")
                # Zeige Raumbeschreibung
                game.log('location', game.rooms[game.location][ATTR_NAME])
                desc = game.render_room_desc(game.location)
                game.log('story', desc)
                return
            else:
                return game.log('error', "Du bist versteckt. Komm erst raus (gehe raus).")

        direction = args[0].lower()
        
        # Mapping für Synonyme (falls Resolver nicht genutzt wird)
        vocab_dirs = game.config.get('vocabulary', {}).get('directions', {})
        target_dir = None
        
        for canonical, synonyms in vocab_dirs.items():
            if direction == canonical or direction in synonyms:
                target_dir = canonical
                break
        
        if not target_dir: target_dir = direction # Fallback falls direkt eingegeben
        
        room = game.rooms[game.location]
        exits = room.get('exits', {})
        
        if target_dir in exits:
            target_id = exits[target_dir]
            
            # Check Türstatus (Locks)
            # Wir suchen Objekte im Raum, die diesen Exit blockieren könnten (linked_exit)
            blocked = False
            blocker_name = ""
            
            room_objs = [o for o in game.objects.values() if o['location'] == game.location]
            for obj in room_objs:
                if obj.get('linked_exit') == target_dir:
                    if not obj.get('is_open', True): # Default True wenn Property fehlt
                        blocked = True
                        blocker_name = obj[ATTR_NAME]
                        break
            
            if blocked:
                game.log('error', f"Der Weg ist versperrt durch: {blocker_name}")
            else:
                # Move
                game.location = target_id
                game.log('location', game.rooms[target_id][ATTR_NAME])
                desc = game.render_room_desc(target_id)
                game.log('story', desc)
                
                # Zeige Exits
                visible_exits = [k for k in game.rooms[target_id].get('exits', {}).keys()]
                dir_trans = {
                    "north": "Norden", "south": "Süden", "east": "Osten", "west": "Westen", 
                    "up": "Oben", "down": "Unten", "out": "Draußen",
                    "northeast": "Nordost", "northwest": "Nordwest", 
                    "southeast": "Südost", "southwest": "Südwest"
                }
                exit_names = [dir_trans.get(d, d) for d in visible_exits]
                if exit_names: game.log('info', f"Ausgänge: {', '.join(exit_names)}")
                
                game.tick(1) # Bewegung kostet Zeit
                
                # Check Auto-Events im neuen Raum? Passiert im nächsten Tick via EventManager.
                
        else:
            game.log('error', f"Nach '{target_dir}' führt kein Weg.")

    @staticmethod
    def climb(game, args):
        """
        Erlaubt das Klettern auf Objekte.
        Ermöglicht das Erreichen von versteckten Ausgängen, wenn im Raum definiert.
        """
        if game.hidden_in: return game.log('error', "Nicht während du versteckt bist.")
        
        if not args:
            return game.log('error', "Worauf willst du klettern?")

        # Sonderfall: "klettere hoch" / "climb up" ohne Objekt -> Versuche normalen 'up' Move
        if args[0].lower() in ["up", "hoch", "rauf", "oben"]:
            MovementHandler.handle(game, ["up"])
            return
        if args[0].lower() in ["down", "runter", "ab", "unten"]:
            MovementHandler.handle(game, ["down"])
            return

        try:
            # 1. Objekt finden
            target = Resolver.resolve_target(game, args, location_filter=FILTER_ROOM, verb='climb')
            
            # 2. Ist es bekletterbar?
            if not target.get(ATTR_CLIMBABLE, False):
                game.log('info', f"Du kannst nicht auf {target[ATTR_NAME]} klettern.")
                return

            # 3. Hat das Objekt selbst ein Ziel? (z.B. fest installierte Leiter)
            if 'destination' in target:
                dest = target['destination']
                game.location = dest
                game.log('success', f"Du kletterst auf {target[ATTR_NAME]}...")
                game.tick(1)
                
                # Room Refresh
                game.log('location', game.rooms[dest][ATTR_NAME])
                game.log('story', game.render_room_desc(dest))
                return

            # 4. Hat der RAUM ein Ziel für dieses Objekt? (Puzzle-Logik: Kiste stapeln um an Lüftung zu kommen)
            current_room = game.rooms[game.location]
            climb_targets = current_room.get('climb_targets', {}) # Dict: {obj_id: target_room_id}
            
            target_id = target[ATTR_ID]
            
            if target_id in climb_targets:
                dest_room_id = climb_targets[target_id]
                game.log('success', f"Du kletterst auf {target[ATTR_NAME]} und erreichst den Durchgang...")
                
                game.location = dest_room_id
                game.tick(1)
                
                # Room Refresh
                game.log('location', game.rooms[dest_room_id][ATTR_NAME])
                game.log('story', game.render_room_desc(dest_room_id))
            else:
                # Nur Flavor: Man steht drauf
                game.log('success', f"Du kletterst auf {target[ATTR_NAME]}. Du bist jetzt etwas größer, aber es bringt dich hier nicht weiter.")
                # Optional: Flag setzen "standing_on" = target_id für detailliertere Checks
        
        except ResolutionError as e:
            game.log('error', str(e))