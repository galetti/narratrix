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
            if target.get('type') not in [TYPE_CONTAINER, TYPE_SURFACE, TYPE_FIXTURE]: # Fixture als Ablage ok?
                return game.log('error', f"Du kannst nichts in oder auf {target[ATTR_NAME]} legen.")
                
            if target.get('type') == TYPE_CONTAINER and not target.get('is_open', False):
                return game.log('error', f"{target[ATTR_NAME]} ist geschlossen.")

            # Verschieben
            item['location'] = target[ATTR_ID]
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
            idx = sep_indices[-1] # Nimm das letzte "mit", falls Namen auch "mit" enthalten (selten)
            obj1_words = args[:idx]
            obj2_words = args[idx+1:]
            
            obj1_name = " ".join(obj1_words)
            obj2_name = " ".join(obj2_words)
            
            # Wir nutzen direkt perform_combine des GameState, das Resolver nutzt
            result = game.perform_combine(obj1_name, obj2_name, verb="use")
            
            # Feedback-Interpretation (perform_combine gibt String zurück)
            if "nichts" in result.lower() or "nicht" in result.lower() and "funktionier" in result.lower():
                 game.log('info', result)
            else:
                 game.log('success', result)
                 game.tick(2)
        else:
            # Einzelnutzung (Schalter drücken etc.)
            try:
                target = Resolver.resolve_target(game, args, location_filter=FILTER_RECURSIVE, verb='use')
                
                # Checke, ob das Item eine 'use' Funktion in den Daten hat (Events)
                # Oder generische Schalter-Logik
                if target.get('type') == TYPE_FIXTURE or target.get('usable', False):
                    # Einfaches Toggle Beispiel
                    if 'state' in target:
                        old_state = target['state']
                        new_state = "on" if old_state == "off" else "off"
                        target['state'] = new_state
                        game.log('success', f"Du benutzt {target[ATTR_NAME]}. (Zustand: {new_state})")
                        
                        # Trigger Events basierend auf State Change? -> Passiert via EventManager check
                    else:
                        game.log('info', f"Du benutzt {target[ATTR_NAME]}, aber nichts passiert.")
                    game.tick(1)
                else:
                    # Wenn nicht direkt benutzbar, merken wir es uns für den nächsten Klick als "Pending Combine"
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
        
        # 1. Argumente trennen (Ziel vs. Werkzeug)
        separators = ["mit", "with", "in", "using", "an", "gegen"]
        sep_indices = [i for i, w in enumerate(args) if w.lower() in separators]
        
        target_words = []
        tool_words = []
        separator_used = ""
        
        if sep_indices:
            idx = sep_indices[0] # Erstes Vorkommen trennt
            separator_used = args[idx].lower()
            target_words = args[:idx]
            tool_words = args[idx+1:]
        else:
            target_words = args
            
        try:
            target = Resolver.resolve_target(game, target_words, location_filter=FILTER_RECURSIVE, verb='break_target')
            
            # --- Fall A: Zerstören MIT/IN etwas ---
            if tool_words:
                # Wir lösen das Werkzeug auf
                tool = Resolver.resolve_target(game, tool_words, location_filter=FILTER_RECURSIVE, verb='break_tool')
                
                # Check 1: Gibt es ein explizites Crafting-Rezept für "break"?
                # Wir bauen die Namen zusammen für perform_combine
                # Achtung: perform_combine erwartet Strings, keine Objekte
                
                # Wir nutzen die Resolver-Logik in perform_combine nicht direkt, sondern rufen das System manuell auf,
                # da wir die Objekte schon haben. Aber perform_combine ist auf Namen ausgelegt.
                # Wir rufen es einfach auf, da es robust ist.
                
                target_name_str = " ".join(target_words)
                tool_name_str = " ".join(tool_words)
                
                # Wir "missbrauchen" das Crafting System mit dem Verb "break"
                result = game.perform_combine(target_name_str, tool_name_str, verb="break")
                
                # Wenn perform_combine kein Rezept findet, gibt es oft einen Standard-Fehler zurück.
                # Wir wollen aber unsere eigene Fallback-Logik, falls es kein Rezept gibt.
                # Da perform_combine Strings zurückgibt, ist das Parsen schwer.
                # Besser: Wir schauen direkt in die Kombinationen des GameState.
                
                found_recipe = False
                for combo in game.combinations:
                    items = combo.get('items', [])
                    if len(items) != 2: continue
                    
                    # Check, ob IDs passen (Reihenfolge egal)
                    ids = [target[ATTR_ID], tool[ATTR_ID]]
                    if set(items) == set(ids):
                        # Check Verb
                        if combo.get('verb') == 'break':
                            # Treffer! Führe aus via GameState
                            msg = game.crafting._execute_combination(combo, [target, tool])
                            game.log('success', msg)
                            game.tick(1)
                            return
                
                # --- Fallback: Generische Physik ---
                # Wenn kein spezielles Rezept da ist ("Hammer auf Glas"), prüfen wir Attribute
                
                # Beispiel: Tool hat 'damage' Wert, Target hat 'toughness'
                tool_dmg = tool.get('damage', 1) # Standard 1
                target_hp = target.get('toughness', 1) # Standard 1
                
                if separator_used in ["in", "im"]:
                    # Kontext "in": Z.B. "Wirf Papier in Ofen"
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
                
                # Check Fragilität
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
        
        # Ähnlich wie break, könnte man "fix X with Y" erlauben
        # Hier vereinfacht:
        try:
            target = Resolver.resolve_target(game, args, location_filter=FILTER_RECURSIVE, verb='fix')
            
            if target.get('state') == STATE_BROKEN:
                # Check inventory for repair kit?
                # Vereinfacht: Braucht "tool_kit" oder ähnliches
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