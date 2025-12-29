from engine.resolver import Resolver
from engine.constants import *

class MovementHandler:
    @staticmethod
    def handle(game, args):
        if not args: return 

        raw_direction = args[0] if isinstance(args, list) else args
        if isinstance(raw_direction, list):
            if not raw_direction: return
            raw_direction = raw_direction[0]
            
        raw_direction = str(raw_direction).lower()
        
        direction = raw_direction
        vocab_dirs = game.config.get('vocabulary', {}).get('directions', {})
        
        for canonical, synonyms in vocab_dirs.items():
            if raw_direction == canonical or raw_direction in synonyms:
                direction = canonical
                break
        
        room = game.get_room(game.location)
        dest = room['exits'].get(direction)
        
        if dest:
            # NEU: Tür-Check
            # Wir suchen im aktuellen Raum nach einem Objekt, das diesen Ausgang blockiert
            local_objs = [o for o in game.objects.values() if o['location'] == game.location]
            
            for obj in local_objs:
                linked = obj.get('linked_exit')
                if linked == direction:
                    # Tür gefunden! Ist sie offen?
                    # Wir prüfen "is_open" (Container Logik)
                    # Wenn sie zu ist -> Blockiert.
                    if not obj.get('is_open', False):
                        game.log('error', f"Der Weg ist versperrt durch: {obj[ATTR_NAME]}.")
                        return

            game.tick(5)
            game.location = dest
            
            from engine.handlers.interaction import InteractionHandler
            InteractionHandler.look(game, [])
        else:
            game.log('error', f"Nach '{raw_direction}' führt kein Weg.")