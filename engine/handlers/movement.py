from engine.resolver import Resolver
from engine.constants import *
from engine.handlers.exploration import ExplorationHandler

class MovementHandler:
    @staticmethod
    def handle(game, args):
        if not args: return 

        # Input normalisieren (kann Liste oder String sein)
        raw_direction = args[0] if isinstance(args, list) else args
        if isinstance(raw_direction, list):
            if not raw_direction: return
            raw_direction = raw_direction[0]
            
        raw_direction = str(raw_direction).lower()
        
        # Richtung auflösen (Synonyme)
        direction = raw_direction
        vocab_dirs = game.config.get('vocabulary', {}).get('directions', {})
        
        for canonical, synonyms in vocab_dirs.items():
            if raw_direction == canonical or raw_direction in synonyms:
                direction = canonical
                break
        
        # Raum und Ziel ermitteln
        room = game.get_room(game.location)
        if not room:
            game.log('error', "Systemfehler: Aktueller Raum unbekannt.")
            return

        dest = room.get('exits', {}).get(direction)
        
        if dest:
            # Hindernis-Check (Türen)
            local_objs = [o for o in game.objects.values() if o['location'] == game.location]
            for obj in local_objs:
                linked = obj.get('linked_exit')
                if linked == direction:
                    # Tür gefunden! Ist sie offen?
                    if not obj.get('is_open', False):
                        game.log('error', f"Der Weg ist versperrt durch: {obj[ATTR_NAME]}.")
                        return

            # WICHTIG: Erst bewegen, dann Events/Tick triggern
            old_loc = game.location
            game.location = dest
            
            # Zeit vergehen lassen (triggert Events im neuen Raum)
            game.tick(5)
            
            # Automatisch umschauen
            ExplorationHandler.look(game, [])
        else:
            game.log('error', f"Nach '{raw_direction}' führt kein Weg.")