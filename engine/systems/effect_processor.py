# narratrix_engine/engine/systems/effect_processor.py
from engine.constants import *

class EffectProcessor:
    """
    Zentrales System zur Verarbeitung von Spieleffekten.
    Löst den Konflikt zwischen EventManager-Logik und DialogueHandler-Logik,
    indem es eine vereinheitlichte Schnittstelle bietet.
    """
    def __init__(self, game):
        self.game = game

    def process(self, effects_data, context_npc=None):
        """
        Verarbeitet einen einzelnen Effekt oder eine Liste von Effekten.
        context_npc: Der NPC, der den Effekt auslöst (wichtig für 'self'-Referenzen im Dialog).
        """
        if not effects_data: return
        
        # Normalisierung: Immer eine Liste verarbeiten
        effect_list = effects_data if isinstance(effects_data, list) else [effects_data]
            
        for eff in effect_list:
            self._execute_single_effect(eff, context_npc)

    def _execute_single_effect(self, eff, context_npc):
        e_type = eff.get('type')
        
        # --- ZUSTANDSÄNDERUNGEN ---
        if e_type == 'set_state' or e_type == 'set_npc_state':
            # 'set_state' bezog sich im Dialog oft auf den sprechenden NPC selbst
            target = None
            npc_id = eff.get('npc')
            
            if npc_id:
                target = self._find_npc(npc_id)
            elif context_npc:
                target = context_npc
            
            if target:
                new_state = eff.get('value')
                target['state'] = new_state
                self.game.log('info', f"({target['name']} wirkt verändert.)")
                # Trigger für State-Change Hooks (z.B. Visuals updaten) könnten hier hin
            else:
                print(f"[WARN] EffectProcessor: Kein Ziel für set_state gefunden.")

        # --- WISSEN ---
        elif e_type == 'learn':
            fact = eff.get('fact')
            self.game.add_knowledge(fact)
            # Optional: Feedback nur wenn es neu ist? Das macht add_knowledge schon intern (Set).
            self.game.log('success', f"(Wissen erhalten: {fact})")

        # --- BEWEGUNG ---
        elif e_type == 'move_npc':
            npc_id = eff.get('npc')
            # Fallback: Wenn kein NPC angegeben, aber context da ist (z.B. "Ich gehe jetzt")
            if not npc_id and context_npc:
                npc_id = context_npc['id']
                
            room_id = eff.get('room') or eff.get('target') # Kompatibilität für beide Key-Namen
            
            if hasattr(self.game.ai, 'move_npc'):
                self.game.ai.move_npc(npc_id, room_id)
                
                # Wenn der Dialog-Partner geht, Gespräch beenden
                if context_npc and context_npc['id'] == npc_id and room_id != self.game.location:
                    if self.game.dialogue_active:
                        self.game.dialogue_active = False
                        self.game.dialogue_partner = None
                        self.game.log('event', "--- GESPRÄCH BEENDET (Partner gegangen) ---")
            else:
                print("[WARN] EffectProcessor: AI System fehlt oder hat keine move_npc Methode.")

        # --- ITEMS & OBJEKTE ---
        elif e_type == 'spawn_item' or e_type == 'receive_item':
            item_id = eff.get('item') or eff.get('item_id')
            location = eff.get('location', LOC_INVENTORY) # Default ins Inventar
            
            obj = self.game.objects.get(item_id)
            if obj:
                obj['location'] = location
                if location == LOC_INVENTORY:
                    self.game.log('success', f"Erhalten: {obj['name']}")
            else:
                print(f"[WARN] EffectProcessor: Item '{item_id}' nicht gefunden.")

        elif e_type == 'update_object':
            target_id = eff.get('target')
            updates = eff.get('updates', {})
            
            # Suche in Objekten
            target = self.game.objects.get(target_id)
            # Suche in NPCs (Fallback)
            if not target:
                target = self._find_npc(target_id)
                
            if target:
                target.update(updates)
            else:
                print(f"[WARN] EffectProcessor: Objekt '{target_id}' für Update nicht gefunden.")

        # --- SYSTEM ---
        elif e_type == 'damage_stability':
            amount = eff.get('value', 0)
            self.game.stability -= amount
            if amount > 0:
                self.game.log('alarm', f"WARNUNG: Hüllenintegrität gefallen (-{amount}%)")
                
        elif e_type == 'game_over':
            reason = eff.get('reason', "Game Over")
            self.game.log('alarm', reason)
            self.game.game_over = True

        elif e_type == 'trigger_event':
            # Event Chain: Ein Event löst ein anderes aus
            next_event_id = eff.get('id')
            # Zugriff auf Events via GameState, um Zirkelbezug zu vermeiden
            if hasattr(self.game, 'events'):
                next_event = next((e for e in self.game.events.events if e.get('id') == next_event_id), None)
                if next_event:
                    # Wir nutzen hier die interne Methode des Managers, 
                    # idealerweise würde man eine public method 'trigger' nutzen.
                    self.game.events.trigger_event_by_id(next_event_id)
                else:
                    print(f"[WARN] EffectProcessor: Folge-Event '{next_event_id}' nicht gefunden.")

    def _find_npc(self, identifier):
        """Hilfsfunktion: Findet NPC nach ID oder Name."""
        return next((n for n in self.game.npcs if n.get('id') == identifier or n.get('name') == identifier), None)