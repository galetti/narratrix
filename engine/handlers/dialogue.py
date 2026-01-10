# narratrix_engine/engine/handlers/dialogue.py
from engine.resolver import Resolver
from engine.constants import *

class DialogueHandler:
    @staticmethod
    def talk(game, args_words):
        clean_args = [w for w in args_words if w.lower() not in ["mit", "zu", "an"]]
        target_npc = Resolver.find_mentioned_npc(game, clean_args)
        
        if not target_npc:
            local = [n for n in game.npcs if n['location'] == game.location]
            if len(local) == 1: 
                target_npc = local[0]
            else: 
                return game.log('error', "Mit wem willst du sprechen?")

        # Delegiere Start an System
        game.dialogue_system.start_dialogue(target_npc)

    @staticmethod
    def step(game, user_input):
        text = user_input.strip().lower()
        npc = game.dialogue_partner
        
        if not npc: 
            game.dialogue_active = False
            return

        exit_words = ["bye", "ende", "tschüss", "weg", "stop", "exit", "leave", "q"]
        if any(w == text for w in exit_words):
            game.dialogue_system.end_dialogue()
            return

        # "Gib Item" Sonderfall im Dialog
        args = text.split()
        if args and args[0] in ["gib", "give", "geb", "geben", "reich"]:
            # Dieser Import ist okay, da InventoryHandler keine Abhängigkeit mehr zu DialogueHandler hat.
            from engine.handlers.inventory import InventoryHandler
            if "an" not in args and "to" not in args:
                new_args = args[1:] + ["an", npc[ATTR_NAME]]
                InventoryHandler.give(game, new_args)
            else:
                InventoryHandler.give(game, args[1:])
            
            # Refresh Topics nach Item-Übergabe
            game.dialogue_system.refresh_topics()
            return

        # Auswahl-Logik
        visible_topics, _ = game.dialogue_system.get_visible_topics(npc)
        
        chosen_entry = None
        chosen_topic_key = None

        if text.isdigit():
            idx = int(text) - 1
            if 0 <= idx < len(visible_topics):
                chosen_topic_key, chosen_entry = visible_topics[idx]
        else:
            # Textsuche
            # Wir holen die DB erneut (könnte ineffizient sein, aber sicher)
            _, dialogue_db = game.dialogue_system.get_visible_topics(npc)
            
            for topic, entry in dialogue_db.items():
                if topic in ['greeting', 'default']: continue
                # Conditions wurden schon bei get_visible_topics grob geprüft, aber hier für Hidden Topics wichtig
                if topic in text:
                    chosen_entry = entry
                    chosen_topic_key = topic
                    break

        if chosen_entry:
            game.dialogue_system.handle_selection(chosen_entry, chosen_topic_key)
        else:
            game.dialogue_system.handle_fallback(text)