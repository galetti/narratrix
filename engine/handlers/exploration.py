from engine.resolver import Resolver, ResolutionError
from engine.constants import *
from engine.strings import Texts
from engine.handlers.common import CommonHandler

class ExplorationHandler:
    
    @staticmethod
    def hide(game, args):
        if game.hidden_in:
            return game.log('info', Texts.HIDE_ALREADY)
            
        clean_args = Resolver.clean_args(args)
        try:
            target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_ROOM, verb='hide')
            
            if target:
                if target.get('type') != TYPE_CONTAINER:
                    return game.log('error', Texts.HIDE_ERROR_TYPE)
                
                # Check Size via Weight heuristic (Objekte unter 100kg sind meist zu klein zum Verstecken)
                if target.get(ATTR_WEIGHT, 0) < 100 and target.get(ATTR_WEIGHT, 0) != float('inf'):
                     return game.log('error', Texts.HIDE_ERROR_SIZE)
                
                if not target.get('is_open', True):
                    return game.log('error', Texts.HIDE_ERROR_CLOSED)

                game.hidden_in = target[ATTR_ID]
                game.log('success', Texts.HIDE_SUCCESS.format(target=target[ATTR_NAME]))
                
        except ResolutionError as e: game.log('error', str(e))

    @staticmethod
    def look(game, args):
        # Wenn versteckt, sieht man nur eingeschränkt
        if game.hidden_in:
            container = game.objects.get(game.hidden_in)
            if container:
                game.log('info', f"Du versteckst dich in {container[ATTR_NAME]}.")
            
            # Eingeschränkter Blick in den Raum
            visible_npcs = [n[ATTR_NAME] for n in game.npcs if n['location'] == game.location]
            if visible_npcs: 
                game.log('character', Texts.HIDE_SEE_NPCS.format(', '.join(visible_npcs)))
            else: 
                game.log('info', Texts.LOOK_EMPTY)
            return

        room = game.get_room(game.location)
        if not room:
            game.log('error', "Fehler: Aktueller Raum nicht gefunden.")
            return

        if not args:
            # Raum-Name und Beschreibung
            game.log('location', room.get(ATTR_NAME, "Unbekannt"))
            game.log('story', game.render_room_desc(game.location))
            
            # Ausgänge anzeigen
            exits = room.get('exits', {})
            if exits:
                trans = {"north": "Norden", "south": "Süden", "east": "Osten", "west": "Westen", "up": "Oben", "down": "Unten", "out": "Ausgang"}
                exit_names = [trans.get(d, d.capitalize()) for d in exits.keys()]
                game.log('info', Texts.LOOK_EXITS.format(', '.join(exit_names)))
            else: 
                game.log('info', Texts.LOOK_NO_EXITS)

            # Objekte im Raum anzeigen
            visible_objs = []
            local_objects = [o for o in game.objects.values() if o['location'] == game.location]
            
            for obj in local_objects:
                if CommonHandler.is_open_container(obj):
                    content_str = CommonHandler.format_contents_recursive(game, obj[ATTR_ID])
                    prep = "Auf dem" if obj.get('type') == TYPE_SURFACE else "Im offenen"
                    if content_str: 
                        game.log('info', f"{prep} {obj[ATTR_NAME]}: {content_str}")
                    else:
                        game.log('info', f"{prep} {obj[ATTR_NAME]} ist nichts.")
                
                # Türen/Schotts extra anzeigen (Status)
                elif obj.get('linked_exit'):
                    state = Texts.LOOK_OPEN if obj.get('is_open') else Texts.LOOK_CLOSED
                    game.log('info', f"{obj[ATTR_NAME]} ({state})")
                    
                # Normale Items
                elif obj.get('type') == TYPE_ITEM or (not obj.get('type') and obj.get(ATTR_WEIGHT, float('inf')) < float('inf')):
                     visible_objs.append(obj[ATTR_NAME])
            
            if visible_objs: 
                game.log('info', Texts.LOOK_GROUND.format(', '.join(visible_objs)))
            
            # NPCs anzeigen
            visible_npcs = [n[ATTR_NAME] for n in game.npcs if n['location'] == game.location]
            if visible_npcs: 
                game.log('character', Texts.LOOK_PERSONS.format(', '.join(visible_npcs)))
            return

        # Gezieltes Anschauen ("schaue kiste")
        clean_args = Resolver.clean_args(args)
        try:
            target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_RECURSIVE, verb='look')
            if target:
                desc = target.get(ATTR_DESC, Texts.LOOK_DEFAULT)
                status = []
                
                # Temperatur Info
                temp = target.get(ATTR_TEMP, 20)
                if temp > 50: status.append(Texts.LOOK_HOT)
                elif temp > 30: status.append(Texts.LOOK_WARM)
                elif temp < 5: status.append(Texts.LOOK_COLD)
                
                # Aggregatszustand
                if target.get(ATTR_MATTER) == MATTER_LIQUID: status.append(Texts.LOOK_LIQUID)

                # Waagen-Display
                if target.get('is_scale'):
                    contents = [o for o in game.objects.values() if o['location'] == target[ATTR_ID]]
                    total_weight = sum(o.get('weight', 0) for o in contents)
                    status.append(f"Display: {total_weight:.2f} kg")

                # Container Status
                if target.get('type') in [TYPE_CONTAINER, TYPE_SURFACE]:
                    if target.get('type') == TYPE_CONTAINER and target.get('is_locked'): 
                        status.append(Texts.LOOK_LOCKED)
                    elif CommonHandler.is_open_container(target):
                        content_str = CommonHandler.format_contents_recursive(game, target[ATTR_ID])
                        if content_str: status.append(Texts.LOOK_CONTENT.format(content_str))
                        else: status.append(Texts.LOOK_EMPTY_CONTAINER)
                    elif target.get('type') == TYPE_CONTAINER:
                        if target.get('linked_exit'):
                            status.append(Texts.LOOK_OPEN if target.get('is_open') else Texts.LOOK_CLOSED)
                        else:
                            status.append(Texts.LOOK_CLOSED)
                
                # Defekte / Sabotage
                if target.get('state') == STATE_SABOTAGED: status.append(Texts.LOOK_SABOTAGED)
                if target.get('state') == STATE_BROKEN: status.append(Texts.LOOK_BROKEN)
                
                if status: desc += " " + " ".join(status)
                game.log('story', desc)
        except ResolutionError as e:
            game.log('error', str(e))