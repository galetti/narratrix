from engine.resolver import Resolver

class MovementHandler:
    @staticmethod
    def handle(game, args):
        # Fix: Robustere Prüfung der Argumente
        if not args:
            return 

        raw_direction = args[0] if isinstance(args, list) else args
        
        # Falls raw_direction immer noch eine Liste ist (nested), auspacken
        if isinstance(raw_direction, list):
            if not raw_direction: return
            raw_direction = raw_direction[0]
            
        raw_direction = str(raw_direction).lower()
        
        direction = raw_direction
        vocab_dirs = game.config.get('vocabulary', {}).get('directions', {})
        
        # Synonym check
        for canonical, synonyms in vocab_dirs.items():
            if raw_direction == canonical or raw_direction in synonyms:
                direction = canonical
                break
        
        room = game.get_room(game.location)
        dest = room['exits'].get(direction)
        
        if dest:
            game.tick(5)
            game.location = dest
            # Nach Bewegung umschauen
            from engine.handlers.interaction import InteractionHandler
            InteractionHandler.look(game, [])
        else:
            game.log('error', f"Nach '{raw_direction}' führt kein Weg.")