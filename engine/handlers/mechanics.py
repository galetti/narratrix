# narratrix_engine/engine/handlers/mechanics.py
from engine.resolver import Resolver, ResolutionError
from engine.constants import *
from engine.strings import Texts

class MechanicsHandler:

    @staticmethod
    def put(game, args):
        if game.hidden_in: return game.log('error', Texts.ERR_HIDDEN)
        
        separators = ["in", "into", "auf", "on", "an"]
        sep_indices = [i for i, w in enumerate(args) if w.lower() in separators]
        
        if not sep_indices:
            return game.log('error', "Wo willst du das hintun? (Benutze 'in' oder 'auf')")
            
        idx = sep_indices[0]
        item_words = args[:idx]
        container_words = args[idx+1:]
        
        try:
            # 1. Was wollen wir reinlegen? (Muss im Inventar oder greifbar sein)
            item = Resolver.resolve_target(game, item_words, location_filter=FILTER_RECURSIVE, verb='put_item')
            
            # 2. Wo soll es rein?
            target = Resolver.resolve_target(game, container_words, location_filter=FILTER_ROOM, verb='put_container')
            
            if item[ATTR_ID] == target[ATTR_ID]:
                return game.log('error', "Das geht physikalisch nicht.")
            
            # Logic: Ist es ein Container/Surface?
            if target.get('type') not in [TYPE_CONTAINER, TYPE_SURFACE, TYPE_FIXTURE]: 
                return game.log('error', f"Du kannst nichts in oder auf {target[ATTR_NAME]} legen.")
                
            if target.get('type') == TYPE_CONTAINER and not target.get('is_open', False):
                return game.log('error', f"{target[ATTR_NAME]} ist geschlossen.")

            # Verschieben
            item['location'] = target[ATTR_ID]
            # NEU: Item übernimmt Level des Containers/Surface
            item['level'] = target.get('level', 0)
            
            game.log('success', f"Du legst {item[ATTR_NAME]} in/auf {target[ATTR_NAME]}.")
            game.tick(1)
            
        except ResolutionError as e:
            game.log('error', str(e))

    @staticmethod
    def use(game, args):
        if game.hidden_in: return game.log('error', Texts.ERR_HIDDEN)
        
        # Check auf "use X with Y"
        separators = ["mit", "with", "an", "on", "in"]
        sep_indices = [i for i, w in enumerate(args) if w.lower() in separators]
        
        if sep_indices:
            # Kombinationsversuch
            idx = sep_indices[-1] 
            obj1_words = args[:idx]
            obj2_words = args[idx+1:]
            
            obj1_name = " ".join(obj1_words)
            obj2_name = " ".join(obj2_words)
            
            # 1. Standard: Versuche Crafting/Interaktion via GameState
            result = game.perform_combine(obj1_name, obj2_name, verb="use")
            
            # Prüfen ob es ein Fehler war (Heuristik basierend auf Standard-Antworten)
            is_failure = "scheint nicht" in result or "weiß nicht" in result or "nicht zu funktionieren" in result
            
            if not is_failure:
                 game.log('success', result)
                 game.tick(2)
                 return

            # 2. Smart Fallback: "Reach" Scenario (Zange mit Karte -> Nimm Karte)
            # Wenn Crafting fehlschlägt, prüfen wir, ob der Spieler eigentlich etwas nehmen wollte.
            try:
                # Import hier um Zirkelbezüge auf Modulebene zu vermeiden
                from engine.handlers.inventory import InventoryHandler
                
                # Wir lösen die Objekte auf, um ihre Eigenschaften zu prüfen
                o1 = Resolver.resolve_target(game, obj1_words, location_filter=FILTER_RECURSIVE)
                o2 = Resolver.resolve_target(game, obj2_words, location_filter=FILTER_RECURSIVE)
                
                tool = None
                target = None
                
                # Hilfsfunktion: Ist es ein Greifwerkzeug?
                def is_reach_tool(o): return o and o.get('is_tool') and o.get('reach', 0) > 0
                
                # Fall A: "Benutze Zange mit Karte" (o1=Tool, o2=Target)
                if is_reach_tool(o1) and o2 and o2['location'] != LOC_INVENTORY:
                    tool = o1; target = o2
                    # Argumente für Take: [target] mit [tool]
                    take_args = obj2_words + ["mit"] + obj1_words
                    
                # Fall B: "Benutze Karte mit Zange" (o1=Target, o2=Tool)
                elif is_reach_tool(o2) and o1 and o1['location'] != LOC_INVENTORY:
                    tool = o2; target = o1
                    take_args = obj1_words + ["mit"] + obj2_words
                
                if tool and target:
                    # Umleitung zum InventoryHandler
                    game.log('info', f"(Versuche, {target[ATTR_NAME]} mit {tool[ATTR_NAME]} zu nehmen...)")
                    InventoryHandler.take(game, take_args)
                    return

            except ResolutionError:
                # Wenn Auflösung fehlschlägt, zeigen wir einfach den originalen Fehler
                pass

            # Wenn kein Fallback griff, zeige den originalen Crafting-Fehler
            game.log('info', result)
        else:
            # Einzelnutzung (Schalter drücken etc.)
            try:
                target = Resolver.resolve_target(game, args, location_filter=FILTER_RECURSIVE, verb='use')
                
                if target.get('type') == TYPE_FIXTURE or target.get('usable', False):
                    if 'state' in target:
                        old_state = target['state']
                        new_state = "on" if old_state == "off" else "off"
                        target['state'] = new_state
                        game.log('success', f"Du benutzt {target[ATTR_NAME]}. (Zustand: {new_state})")
                    else:
                        game.log('info', f"Du benutzt {target[ATTR_NAME]}, aber nichts passiert.")
                    game.tick(1)
                else:
                    game.pending_interaction = {'verb': 'use', 'args': args}
                    game.log('info', f"Was willst du mit {target[ATTR_NAME]} benutzen?")
                    
            except ResolutionError as e:
                game.log('error', str(e))

    @staticmethod
    def open(game, args):
        if game.hidden_in: return game.log('error', Texts.ERR_HIDDEN)
        try:
            target = Resolver.resolve_target(game, args, location_filter=FILTER_RECURSIVE, verb='open')
            
            if target.get('type') == TYPE_CONTAINER:
                if target.get('locked', False):
                    game.log('info', f"{target[ATTR_NAME]} ist verschlossen.")
                elif target.get('is_open', False):
                    game.log('info', f"{target[ATTR_NAME]} ist bereits offen.")
                else:
                    target['is_open'] = True
                    game.log('success', f"Du öffnest {target[ATTR_NAME]}.")
                    # Zeige Inhalt
                    contents = [o[ATTR_NAME] for o in game.objects.values() if o['location'] == target[ATTR_ID]]
                    if contents:
                        game.log('info', f"Darin befindet sich: {', '.join(contents)}")
                    game.tick(1)
            else:
                game.log('error', "Das kann man nicht öffnen.")
        except ResolutionError as e:
            game.log('error', str(e))

    @staticmethod
    def break_(game, args):
        """
        Versucht, ein Objekt zu zerstören.
        Unterstützt: 'break X', 'break X with Y', 'break X in Y'
        """
        if game.hidden_in: return game.log('error', Texts.ERR_HIDDEN)
        
        separators = ["mit", "with", "in", "using", "an", "gegen"]
        sep_indices = [i for i, w in enumerate(args) if w.lower() in separators]
        
        target_words = []
        tool_words = []
        separator_used = ""
        
        if sep_indices:
            idx = sep_indices[0] 
            separator_used = args[idx].lower()
            target_words = args[:idx]
            tool_words = args[idx+1:]
        else:
            target_words = args
            
        try:
            target = Resolver.resolve_target(game, target_words, location_filter=FILTER_RECURSIVE, verb='break_target')
            
            # --- Fall A: Zerstören MIT/IN etwas ---
            if tool_words:
                tool = Resolver.resolve_target(game, tool_words, location_filter=FILTER_RECURSIVE, verb='break_tool')
                
                target_name_str = " ".join(target_words)
                tool_name_str = " ".join(tool_words)
                
                # "Missbrauch" des Crafting Systems für 'break'
                result = game.perform_combine(target_name_str, tool_name_str, verb="break")
                
                found_recipe = False
                for combo in game.combinations:
                    items = combo.get('items', [])
                    if len(items) != 2: continue
                    
                    ids = [target[ATTR_ID], tool[ATTR_ID]]
                    if set(items) == set(ids):
                        if combo.get('verb') == 'break':
                            msg = game.crafting._execute_combination(combo, [target, tool])
                            game.log('success', msg)
                            game.tick(1)
                            return
                
                # --- Fallback: Generische Physik ---
                tool_dmg = tool.get('damage', 1) 
                target_hp = target.get('toughness', 1) 
                
                if separator_used in ["in", "im"]:
                    if tool.get('type') == TYPE_CONTAINER or tool.get('type') == TYPE_FIXTURE:
                        if tool.get('state') == 'on' or tool.get('hot', False):
                            game.log('success', f"Du zerstörst {target[ATTR_NAME]} in {tool[ATTR_NAME]}.")
                            target['location'] = LOC_VOID
                            game.tick(1)
                            return
                        else:
                            game.log('info', f"{tool[ATTR_NAME]} ist nicht aktiv/heiß genug.")
                            return
                
                if tool_dmg >= target_hp:
                    game.log('success', f"Mit {tool[ATTR_NAME]} zerstörst du {target[ATTR_NAME]}!")
                    target['state'] = STATE_BROKEN
                    target['name'] = f"kaputte(s) {target['name']}"
                    target['desc'] = "Völlig zerstört."
                    game.tick(1)
                else:
                    game.log('info', f"{tool[ATTR_NAME]} ist nicht stark genug, um {target[ATTR_NAME]} zu zerstören.")

            # --- Fall B: Zerstören OHNE Werkzeug (Hände) ---
            else:
                if target.get('state') == STATE_BROKEN:
                    return game.log('info', f"{target[ATTR_NAME]} ist bereits kaputt.")
                
                if target.get('fragile', False) or target.get('toughness', 1) == 0:
                    game.log('success', f"Du zerstörst {target[ATTR_NAME]} mit bloßen Händen.")
                    target['state'] = STATE_BROKEN
                    target['name'] = f"kaputte(s) {target['name']}"
                    game.tick(1)
                else:
                    game.log('info', f"Du kannst {target[ATTR_NAME]} nicht einfach so zerstören. Du brauchst wohl ein Werkzeug.")

        except ResolutionError as e:
            game.log('error', str(e))

    @staticmethod
    def fix(game, args):
        if game.hidden_in: return game.log('error', Texts.ERR_HIDDEN)
        
        try:
            target = Resolver.resolve_target(game, args, location_filter=FILTER_RECURSIVE, verb='fix')
            
            if target.get('state') == STATE_BROKEN:
                has_tools = any(o.get('is_tool', False) for o in game.objects.values() if o['location'] == LOC_INVENTORY)
                
                if has_tools:
                    target['state'] = STATE_NORMAL
                    clean_name = target['name'].replace("kaputte(s) ", "").replace("broken ", "")
                    target['name'] = clean_name
                    game.log('success', f"Du hast {target[ATTR_NAME]} repariert.")
                    game.tick(5)
                else:
                    game.log('error', "Du hast kein Werkzeug für eine Reparatur.")
            elif target.get('state') == STATE_SABOTAGED:
                game.log('info', "Das sieht nach Sabotage aus. Das ist komplizierter.")
            else:
                game.log('info', f"{target[ATTR_NAME]} scheint in Ordnung zu sein.")
                
        except ResolutionError as e:
            game.log('error', str(e))

    @staticmethod
    def wait(game, args):
        game.log('info', "Du wartest eine Weile...")
        game.tick(10)