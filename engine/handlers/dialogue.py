from engine.resolver import Resolver
from engine.llm_bridge import LLMBridge
from engine.constants import *

class DialogueHandler:
    @staticmethod
    def talk(game, args_words):
        # Nutzt allgemeine Präpositionen zum Filtern
        ignore_words = game.config.get('vocabulary', {}).get('prepositions', {}).get('general', ["mit", "zu", "an"])
        clean_args = [w for w in args_words if w.lower() not in ignore_words]
        
        target_npc = Resolver.find_mentioned_npc(game, clean_args)
        
        if not target_npc:
            local = [n for n in game.npcs if n['location'] == game.location]
            if len(local) == 1: 
                target_npc = local[0]
            else: 
                return game.log('error', "Mit wem willst du sprechen?")

        game.dialogue_active = True
        game.dialogue_partner = target_npc
        
        current_state = target_npc.get('state', 'default')
        
        game.log('event', f"--- GESPRÄCH MIT {target_npc[ATTR_NAME].upper()} ---")
        game.log('info', "(Tippe Themen oder 'gib [Item]')")
        
        dialogue_db = target_npc.get('dialogue', {})
        state_db = dialogue_db.get(current_state, {})
        
        greeting = state_db.get('greeting', "...")
        if not greeting and current_state != 'default':
             greeting = dialogue_db.get('default', {}).get('greeting', "...")

        DialogueHandler._print_dialogue(game, target_npc, greeting)

    @staticmethod
    def step(game, user_input):
        text = user_input.strip().lower()
        npc = game.dialogue_partner
        
        if not npc: 
            game.dialogue_active = False
            return

        # NEU: Exit-Wörter aus Config
        exit_words = game.config.get('vocabulary', {}).get('dialogue_exits', ["bye", "ende"])
        
        if any(w in text for w in exit_words):
            game.log('event', "--- GESPRÄCH BEENDET ---")
            game.dialogue_active = False
            game.dialogue_partner = None
            return

        # Check auf 'give' Befehle im Dialog
        args = text.split()
        if args and args[0] in ["gib", "give", "geb", "geben", "reich"]:
            from engine.handlers.interaction import InteractionHandler
            # Prüfen ob 'an' im Satz ist, wenn nicht, fügen wir den NPC hinzu
            give_preps = game.config.get('vocabulary', {}).get('prepositions', {}).get('give', ["an"])
            
            if not any(p in args for p in give_preps):
                # Füge "an [NPC]" hinzu, damit der InteractionHandler weiß, an wen es geht
                new_args = args[1:] + ["an", npc[ATTR_NAME]]
                InteractionHandler.give(game, new_args)
            else:
                InteractionHandler.give(game, args[1:])
            return

        current_state = npc.get('state', 'default')
        dialogue_root = npc.get('dialogue', {})
        
        state_db = dialogue_root.get(current_state, {})
        global_db = dialogue_root.get('global', {})

        found_topic = None
        source_db = None
        entry = None

        for topic in state_db.keys():
            if topic in ['greeting', 'desc', 'img', 'personality']: continue
            if topic in text:
                candidate = state_db[topic]
                if DialogueHandler._check_condition_wrapper(game, candidate):
                    found_topic = topic; source_db = state_db; entry = candidate; break
        
        if not found_topic:
            for topic in global_db.keys():
                if topic in text:
                    candidate = global_db[topic]
                    if DialogueHandler._check_condition_wrapper(game, candidate):
                        found_topic = topic; source_db = global_db; entry = candidate; break
        
        if found_topic and entry:
            DialogueHandler._print_dialogue(game, npc, entry)
            DialogueHandler.process_effects(game, entry, npc)
        else:
            use_llm = game.config.get('use_llm_dialogue', False)
            if use_llm: DialogueHandler._print_dialogue(game, npc, "LLM_AUTO_REPLY", prompt_context=text)
            else: game.log('character', f"{npc[ATTR_NAME]} schaut dich fragend an.")

    @staticmethod
    def _check_condition_wrapper(game, entry):
        if isinstance(entry, dict) and 'condition' in entry: return DialogueHandler._check_condition(game, entry['condition'])
        return True

    @staticmethod
    def _check_condition(game, condition):
        if not condition: return True
        if isinstance(condition, str): return condition in game.knowledge
        if isinstance(condition, dict):
            c_type = condition.get('type')
            if c_type == 'knowledge': return condition.get('value') in game.knowledge
            elif c_type == 'location': return game.location == condition.get('value')
            elif c_type == 'npc_state':
                target_name = condition.get('npc'); required_state = condition.get('state')
                target = next((n for n in game.npcs if n[ATTR_NAME] == target_name or target_name in n.get(ATTR_ALIASES, [])), None)
                if target: return target.get('state', 'default') == required_state
                return False
            elif c_type == 'not_npc_state':
                target_name = condition.get('npc'); forbidden_state = condition.get('state')
                target = next((n for n in game.npcs if n[ATTR_NAME] == target_name or target_name in n.get(ATTR_ALIASES, [])), None)
                if target: return target.get('state', 'default') != forbidden_state
                return True 
        return True

    @staticmethod
    def process_effects(game, entry, npc):
        """Verarbeitet einen oder mehrere Effekte aus einem Dialog-Eintrag."""
        if 'effect' not in entry: return
        
        effects_data = entry['effect']
        
        # Normalisiere zu Liste
        effect_list = []
        if isinstance(effects_data, list):
            effect_list = effects_data
        elif isinstance(effects_data, dict):
            effect_list = [effects_data]
            
        for eff in effect_list:
            DialogueHandler._execute_effect(game, eff, npc)

    @staticmethod
    def _execute_effect(game, effect, npc):
        e_type = effect.get('type')
        
        if e_type == 'move_npc':
            target_room = effect.get('target')
            if target_room in game.rooms:
                game.log('event', f"[{npc[ATTR_NAME]} macht sich auf den Weg.]")
                npc[ATTR_AFFINITY] = [target_room]
                npc['location'] = target_room
                if target_room != game.location:
                    game.dialogue_active = False; game.dialogue_partner = None
                    game.log('event', "--- GESPRÄCH BEENDET (Partner gegangen) ---")
            else: game.log('error', f"Effect Error: Room {target_room} not found.")
            
        elif e_type == 'learn':
            fact = effect.get('fact'); game.add_knowledge(fact); game.log('success', f"(Wissen erhalten: {fact})")
            
        elif e_type == 'game_over':
            reason = effect.get('reason', "Game Over"); game.log('alarm', reason); game.game_over = True
            
        elif e_type == 'set_state':
            new_state = effect.get('value'); npc['state'] = new_state
            dialogue_root = npc.get('dialogue', {}); state_config = dialogue_root.get(new_state, {})
            if 'desc' in state_config: npc[ATTR_DESC] = state_config['desc']; game.log('info', f"(Die Ausstrahlung von {npc[ATTR_NAME]} hat sich verändert.)")
            if 'img' in state_config: npc['img'] = state_config['img']
            if 'personality' in state_config: npc['personality'] = state_config['personality']

        elif e_type == 'receive_item':
            item_id = effect.get('item_id')
            if item_id in game.objects:
                item = game.objects[item_id]
                item['location'] = LOC_INVENTORY
                game.log('success', f"Erhalten: {item[ATTR_NAME]}")
            else:
                game.log('error', f"Effect Error: Item {item_id} existiert nicht.")

        elif e_type == 'set_npc_state':
            target_name = effect.get('npc')
            new_state = effect.get('value')
            target = next((n for n in game.npcs if n[ATTR_NAME] == target_name or target_name in n.get(ATTR_ALIASES, [])), None)
            
            if target:
                target['state'] = new_state
                dialogue_root = target.get('dialogue', {})
                state_config = dialogue_root.get(new_state, {})
                if 'desc' in state_config: target[ATTR_DESC] = state_config['desc']
                if 'img' in state_config: target['img'] = state_config['img']
                game.log('success', f"(Status von {target[ATTR_NAME]} aktualisiert)")
            else:
                game.log('error', f"Effect Error: NPC '{target_name}' nicht gefunden.")

    @staticmethod
    def _print_dialogue(game, npc, response_entry, prompt_context=None):
        core_text = response_entry
        if isinstance(response_entry, dict): core_text = response_entry.get('text', "")
        final_text = core_text
        use_llm = game.config.get('use_llm_dialogue', False)
        if use_llm:
            personality = npc.get('personality', 'Neutral'); state = npc.get('state', 'default'); stress = "HOCH" if game.stability < 50 else "NIEDRIG"
            if response_entry == "LLM_AUTO_REPLY":
                sys_prompt = f"Du bist {npc[ATTR_NAME]} ({personality}). Stimmung: {state}. Stress: {stress}. Antworte auf: '{prompt_context}'."
                user_msg = "Antworte kurz und passend zur Rolle."
            else:
                sys_prompt = f"Du bist {npc[ATTR_NAME]} ({personality}). Stimmung: {state}. Stress: {stress}. Formuliere um:"
                user_msg = f"Kern-Aussage: {core_text}"
            game.log('info', f"({npc[ATTR_NAME]} denkt nach...)"); enhanced = LLMBridge.call(sys_prompt, user_msg)
            if enhanced: final_text = enhanced
        game.log('character', f"{npc[ATTR_NAME]}: \"{final_text}\"")
