# narratrix_engine/engine/systems/effect_processor.py
from engine.constants import *

class EffectProcessor:
    """
    Zentrales System zur Verarbeitung von Spieleffekten.
    """
    def __init__(self, game):
        self.game = game

    def process(self, effects_data, context_npc=None):
        if not effects_data: return
        
        effect_list = effects_data if isinstance(effects_data, list) else [effects_data]
            
        for eff in effect_list:
            self._execute_single_effect(eff, context_npc)

    def _execute_single_effect(self, eff, context_npc):
        e_type = eff.get('type')
        
        # --- BEWEGUNG (Realistisch) ---
        if e_type == 'move_npc':
            npc_id = eff.get('npc')
            if not npc_id and context_npc:
                npc_id = context_npc['id']
                
            room_id = eff.get('room') or eff.get('target') 
            
            if hasattr(self.game.ai, 'move_npc'):
                self.game.ai.move_npc(npc_id, room_id, instant=False)
                
                if context_npc and context_npc['id'] == npc_id and room_id != self.game.location:
                    if self.game.dialogue_active:
                        self.game.dialogue_active = False
                        self.game.dialogue_partner = None
                        self.game.log('event', "--- GESPRÄCH BEENDET (Partner geht) ---")
            else:
                print("[WARN] EffectProcessor: AI System fehlt oder hat keine move_npc Methode.")

        # --- TELEPORT (Instant) ---
        elif e_type == 'teleport_npc':
            npc_id = eff.get('npc')
            if not npc_id and context_npc: npc_id = context_npc['id']
            room_id = eff.get('target')
            
            if hasattr(self.game.ai, 'move_npc'):
                self.game.ai.move_npc(npc_id, room_id, instant=True)
            else:
                target = self._find_npc(npc_id)
                if target: target['location'] = room_id

        # --- ZUSTANDSÄNDERUNGEN ---
        elif e_type == 'set_state' or e_type == 'set_npc_state':
            target = None
            npc_id = eff.get('npc')
            
            if npc_id:
                target = self._find_npc(npc_id)
            elif context_npc:
                target = context_npc
            
            if target:
                new_state = eff.get('value')
                target['state'] = new_state
                
                # Fix: Nur loggen, wenn Spieler den NPC sehen kann
                if target.get('location') == self.game.location:
                    self.game.log('info', f"({target['name']} wirkt verändert.)")
                # Optional: Wenn nicht sichtbar, könnten wir das im Debug-Log vermerken, aber nicht für den Spieler
            else:
                print(f"[WARN] EffectProcessor: Kein Ziel für set_state gefunden.")

        # --- WISSEN ---
        elif e_type == 'learn':
            fact = eff.get('fact')
            self.game.add_knowledge(fact)
            # Log nur für Spieler relevante Infos, "technische" Flags müssen nicht geloggt werden
            if not fact.startswith("task_"): 
                self.game.log('success', f"(Wissen erhalten: {fact})")

        # --- ITEMS & OBJEKTE ---
        elif e_type == 'spawn_item' or e_type == 'receive_item':
            item_id = eff.get('item') or eff.get('item_id')
            location = eff.get('location', LOC_INVENTORY) 
            
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
            
            target = self.game.objects.get(target_id)
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
            next_event_id = eff.get('id')
            if hasattr(self.game, 'events'):
                self.game.events.trigger_event_by_id(next_event_id)

    def _find_npc(self, identifier):
        return next((n for n in self.game.npcs if n.get('id') == identifier or n.get('name') == identifier), None)