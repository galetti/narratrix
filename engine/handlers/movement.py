from engine.constants import *
from engine.resolver import Resolver, ResolutionError

class MovementHandler:
    @staticmethod
    def _list_room_items(game, room_id):
        visible_items = []
        for obj in game.objects.values():
            if obj['location'] == room_id:
                if obj.get('type') == TYPE_SCENERY: continue
                
                obj_level = obj.get('level', 0)
                level_info = ""
                
                if obj_level != game.elevation:
                    if obj_level > game.elevation: level_info = f" (oben auf Ebene {obj_level})"
                    else: level_info = f" (unten auf Ebene {obj_level})"

                name = obj[ATTR_NAME]
                
                if obj.get('type') == TYPE_CONTAINER:
                    if obj.get('is_open'): name += " (offen)"
                    else: name += " (geschlossen)"
                
                if obj.get('is_resource') and obj.get('count', 1) > 1:
                    name = f"{obj['count']}x {name}"

                visible_items.append(f"{name}{level_info}")
        
        if visible_items:
            game.log('info', f"Hier siehst du: {', '.join(visible_items)}")

    @staticmethod
    def handle(game, args):
        if game.hidden_in:
            if any(w in args for w in ["raus", "out", "verlasse", "exit"]):
                game.hidden_in = None
                game.log('success', "Du kommst aus deinem Versteck hervor.")
                game.log('location', game.rooms[game.location][ATTR_NAME])
                desc = game.render_room_desc(game.location)
                game.log('story', desc)
                MovementHandler._list_room_items(game, game.location)
                return
            else:
                return game.log('error', "Du bist versteckt. Komm erst raus (gehe raus).")

        if not args:
            return game.log('error', "Wohin willst du gehen?")

        direction = args[0].lower()
        vocab_dirs = game.config.get('vocabulary', {}).get('directions', {})
        target_dir = None
        
        for canonical, synonyms in vocab_dirs.items():
            if direction == canonical or direction in synonyms:
                target_dir = canonical
                break
        
        if not target_dir: target_dir = direction 
        
        room = game.rooms[game.location]
        exits = room.get('exits', {})
        
        if target_dir in exits:
            target_id = exits[target_dir]
            
            blocked = False
            blocker_name = ""
            room_objs = [o for o in game.objects.values() if o['location'] == game.location]
            for obj in room_objs:
                if obj.get('linked_exit') == target_dir:
                    if not obj.get('is_open', True): 
                        blocked = True
                        blocker_name = obj[ATTR_NAME]
                        break
            
            if blocked:
                game.log('error', f"Der Weg ist versperrt durch: {blocker_name}")
            else:
                game.location = target_id
                game.elevation = 0 
                game.visit_room(target_id)
                
                game.log('location', game.rooms[target_id][ATTR_NAME])
                desc = game.render_room_desc(target_id)
                game.log('story', desc)
                
                visible_exits = [k for k in game.rooms[target_id].get('exits', {}).keys()]
                dir_trans = {
                    "north": "Norden", "south": "Süden", "east": "Osten", "west": "Westen", 
                    "up": "Oben", "down": "Unten", "out": "Draußen",
                    "northeast": "Nordost", "northwest": "Nordwest", 
                    "southeast": "Südost", "southwest": "Südwest"
                }
                exit_names = [dir_trans.get(d, d) for d in visible_exits]
                if exit_names: game.log('info', f"Ausgänge: {', '.join(exit_names)}")
                
                MovementHandler._list_room_items(game, target_id)
                game.tick(1) 
        else:
            game.log('error', f"Nach '{target_dir}' führt kein Weg.")

    @staticmethod
    def climb(game, args):
        if game.hidden_in: return game.log('error', "Nicht während du versteckt bist.")
        
        if not args:
            return game.log('error', "Worauf willst du klettern?")

        # Filter "auf", "on" aus den Argumenten für sauberes Resolver-Matching
        clean_args = [w for w in args if w.lower() not in ["auf", "on", "up", "hoch"]]
        
        # Fallback: Wenn nur "klettere auf" eingegeben wurde, ist clean_args leer
        if not clean_args:
             if args[0].lower() not in ["up", "hoch", "rauf", "oben"]:
                 return game.log('error', "Worauf willst du klettern?")

        # "Climb down" logic
        if args[0].lower() in ["down", "runter", "ab", "unten", "boden"]:
            if game.elevation > 0:
                game.elevation = 0
                game.log('success', "Du kletterst zurück auf den Boden.")
                MovementHandler._list_room_items(game, game.location)
                game.tick(1)
                return
            else:
                MovementHandler.handle(game, ["down"])
                return

        # "Climb up" logic (ohne Zielobjekt)
        if args[0].lower() in ["up", "hoch", "rauf", "oben"]:
            if game.elevation == 0:
                if 'up' in game.rooms[game.location].get('exits', {}):
                    MovementHandler.handle(game, ["up"])
                else:
                    game.log('error', "Du kannst hier nicht einfach hochklettern. Benutze ein Objekt.")
                return
            else:
                game.log('error', "Du bist schon oben.")
                return

        try:
            # WICHTIG: Nutze die bereinigten Argumente
            target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_ROOM, verb='climb')
            
            if not target.get(ATTR_CLIMBABLE, False):
                game.log('info', f"Du kannst nicht auf {target[ATTR_NAME]} klettern.")
                return

            if 'target_elevation' in target:
                new_level = target['target_elevation']
                if new_level == game.elevation:
                    game.log('info', f"Du bist bereits auf dieser Höhe.")
                else:
                    game.elevation = new_level
                    game.log('success', f"Du kletterst auf {target[ATTR_NAME]}. (Ebene {new_level})")
                    MovementHandler._list_room_items(game, game.location)
                    game.tick(1)
                return

            if 'destination' in target:
                dest = target['destination']
                game.location = dest
                game.elevation = 0
                game.visit_room(dest)
                game.log('success', f"Du kletterst auf {target[ATTR_NAME]}...")
                game.tick(1)
                
                game.log('location', game.rooms[dest][ATTR_NAME])
                game.log('story', game.render_room_desc(dest))
                MovementHandler._list_room_items(game, dest)
                return

            current_room = game.rooms[game.location]
            climb_targets = current_room.get('climb_targets', {})
            target_id = target[ATTR_ID]
            
            if target_id in climb_targets:
                dest_room_id = climb_targets[target_id]
                game.log('success', f"Du kletterst auf {target[ATTR_NAME]} und erreichst den Durchgang...")
                game.location = dest_room_id
                game.elevation = 0
                game.visit_room(dest_room_id)
                game.tick(1)
                
                game.log('location', game.rooms[dest_room_id][ATTR_NAME])
                game.log('story', game.render_room_desc(dest_room_id))
                MovementHandler._list_room_items(game, dest_room_id)
            else:
                game.log('success', f"Du kletterst auf {target[ATTR_NAME]}, aber es bringt dich nicht höher.")
        
        except ResolutionError as e:
            game.log('error', str(e))
