import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json
import math

# Constants
NODE_RADIUS = 30
DEFAULT_Z = 0

# Types for Radio Buttons
TYPE_OPTIONS = [
    ("Item (Tragbar)", "item"),
    ("Fixture (Fest)", "fixture"),
    ("Container", "container"),
    ("Surface (Ablage)", "surface"),
    ("Scenery (Deko)", "scenery")
]

class WorldEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Narratrix World Editor v3.0")
        self.geometry("1500x950")
        
        self.rooms = {} # id -> {data, x, y, z}
        self.links = [] 
        self.items = {} # id -> item_data
        self.npcs = []  # list of npc_data
        self.meta = {}
        self.extra_data = {
            "combinations": [],
            "narrative_matrix": [],
            "events": [],
            "quests": {},
        }
        
        self.current_file = None
        self.selected_node = None
        self.drag_data = {"x": 0, "y": 0, "item": None}
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        self.current_z_level = DEFAULT_Z
        
        self._init_ui()
        self._create_menu()

    def _init_ui(self):
        # LEFT SIDEBAR
        left_panel = ttk.Frame(self, width=200, padding=10)
        left_panel.pack(side=tk.LEFT, fill=tk.Y)
        
        ttk.Label(left_panel, text="Ebenen (Decks)", font=("Arial", 12, "bold")).pack(pady=10)
        
        self.layer_var = tk.StringVar(value=str(DEFAULT_Z))
        self.layer_spin = ttk.Spinbox(left_panel, from_=-10, to=10, textvariable=self.layer_var, width=5, command=self._on_layer_change)
        self.layer_spin.pack(pady=5)
        self.layer_spin.bind("<Return>", lambda e: self._on_layer_change())
        
        ttk.Separator(left_panel, orient='horizontal').pack(fill='x', pady=20)
        
        ttk.Button(left_panel, text="Neuer Raum", command=self._add_room).pack(fill='x', pady=5)
        ttk.Button(left_panel, text="Verbindung (+)", command=self._add_link_dialog).pack(fill='x', pady=5)
        ttk.Button(left_panel, text="Löschen (Del)", command=self._delete_room).pack(fill='x', pady=5)

        # CENTER CANVAS
        self.canvas = tk.Canvas(self, bg="#202030", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas.bind("<ButtonPress-1>", self._on_canvas_click)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_drop)
        self.canvas.bind("<ButtonPress-3>", self._on_canvas_right_click)
        self.canvas.bind("<B3-Motion>", self._on_canvas_pan)
        self.canvas.bind("<MouseWheel>", self._on_zoom) 
        self.canvas.bind("<Button-4>", self._on_zoom)
        self.canvas.bind("<Button-5>", self._on_zoom)

        # RIGHT SIDEBAR (Scrollable Properties)
        right_container = ttk.Frame(self, width=350)
        right_container.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Canvas for scrolling the sidebar if it gets too long
        self.prop_canvas = tk.Canvas(right_container, width=350)
        scrollbar = ttk.Scrollbar(right_container, orient="vertical", command=self.prop_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.prop_canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.prop_canvas.configure(scrollregion=self.prop_canvas.bbox("all"))
        )

        self.prop_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.prop_canvas.configure(yscrollcommand=scrollbar.set)

        self.prop_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.prop_panel = ttk.LabelFrame(self.scrollable_frame, text="Raum Eigenschaften", padding=10)
        self.prop_panel.pack(fill="x", expand=True)
        
        # Room Basic Props
        ttk.Label(self.prop_panel, text="ID:").grid(row=0, column=0, sticky='w')
        self.prop_id = ttk.Entry(self.prop_panel)
        self.prop_id.grid(row=0, column=1, sticky='ew')
        
        ttk.Label(self.prop_panel, text="Name:").grid(row=1, column=0, sticky='w')
        self.prop_name = ttk.Entry(self.prop_panel)
        self.prop_name.grid(row=1, column=1, sticky='ew')
        
        ttk.Label(self.prop_panel, text="Z-Level:").grid(row=2, column=0, sticky='w')
        self.prop_z = ttk.Entry(self.prop_panel)
        self.prop_z.grid(row=2, column=1, sticky='ew')

        ttk.Label(self.prop_panel, text="Beschreibung:").grid(row=3, column=0, sticky='w')
        self.prop_desc = tk.Text(self.prop_panel, height=5, width=30)
        self.prop_desc.grid(row=4, column=0, columnspan=2, pady=5)
        
        # Exits
        ttk.Label(self.prop_panel, text="Ausgänge:").grid(row=5, column=0, sticky='w', pady=(10,0))
        self.exits_list = tk.Listbox(self.prop_panel, height=4)
        self.exits_list.grid(row=6, column=0, columnspan=2, sticky='ew')

        # --- CONTENT SECTION ---
        self.content_frame = ttk.LabelFrame(self.scrollable_frame, text="Inhalt (Items & NPCs)", padding=10)
        self.content_frame.pack(fill="x", expand=True, pady=10)

        self.content_list = tk.Listbox(self.content_frame, height=6)
        self.content_list.pack(fill='x', pady=5)
        self.content_list.bind('<Double-Button-1>', self._edit_content_item)

        btn_frame = ttk.Frame(self.content_frame)
        btn_frame.pack(fill='x')
        ttk.Button(btn_frame, text="+ Item", command=self._add_item).pack(side=tk.LEFT, fill='x', expand=True)
        ttk.Button(btn_frame, text="+ NPC", command=self._add_npc).pack(side=tk.LEFT, fill='x', expand=True)
        ttk.Button(btn_frame, text="Edit", command=self._edit_content_item).pack(side=tk.LEFT, fill='x', expand=True)
        ttk.Button(btn_frame, text="- Löschen", command=self._delete_content_item).pack(side=tk.LEFT, fill='x', expand=True)

        # Save Button at bottom
        ttk.Button(self.scrollable_frame, text="Raum-Daten Speichern", command=self._save_node_props).pack(pady=20, fill='x')

        self.bind("<Up>", lambda e: self._change_layer_rel(1))
        self.bind("<Down>", lambda e: self._change_layer_rel(-1))
        self.bind("<Delete>", lambda e: self._delete_room())

    def _create_menu(self):
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Öffnen (JSON)", command=self._load_file)
        file_menu.add_command(label="Speichern (JSON)", command=self._save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="Datei", menu=file_menu)
        self.config(menu=menubar)

    # --- DATA & LOADING ---

    def _load_file(self):
        path = filedialog.askopenfilename(filetypes=[("Narratrix Config", "*.json")])
        if not path: return
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.rooms = {}
            raw_rooms = data.get('rooms', {})
            self.meta = data.get('meta', {})
            for key in self.extra_data:
                self.extra_data[key] = data.get(key, self.extra_data[key])
            
            # Load Items & NPCs
            self.items = data.get('objects', {})
            self.npcs = data.get('npcs', [])
            
            idx = 0
            for rid, rdata in raw_rooms.items():
                rdata['id'] = rid
                meta = rdata.get('_editor', {})
                x = meta.get('x', (idx % 5) * 150 + 100)
                y = meta.get('y', (idx // 5) * 150 + 100)
                z = meta.get('z', DEFAULT_Z)
                
                self.rooms[rid] = {
                    "data": rdata,
                    "x": x, "y": y, "z": z
                }
                idx += 1
                
            self._rebuild_links()
            self._redraw()
            self.current_file = path
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte Datei nicht laden: {e}")

    def _save_file(self):
        if not self.rooms: return
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not path: return
        
        export_rooms = {}
        for rid, node in self.rooms.items():
            rdata = node['data'].copy()
            rdata['_editor'] = {"x": node['x'], "y": node['y'], "z": node['z']}
            export_rooms[rid] = rdata
            
        final_data = {
            "meta": {
                **self.meta,
                "generator": "Narratrix World Editor 3.0",
                "start_room": self.meta.get("start_room", next(iter(export_rooms))),
            },
            "rooms": export_rooms,
            "objects": self.items,
            "npcs": self.npcs,
            **self.extra_data,
        }
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Erfolg", "Welt gespeichert.")
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte nicht speichern: {e}")

    # --- ITEM & NPC MANAGEMENT ---

    def _get_room_contents(self, room_id):
        items = [i_id for i_id, i in self.items.items() if i.get('location') == room_id]
        npcs = [n.get('id') for n in self.npcs if n.get('location') == room_id]
        return items, npcs

    def _update_content_list(self):
        self.content_list.delete(0, tk.END)
        if not self.selected_node: return
        
        items, npcs = self._get_room_contents(self.selected_node)
        for i_id in items:
            name = self.items[i_id].get('name', '???')
            self.content_list.insert(tk.END, f"[ITEM] {name} ({i_id})")
        for n_id in npcs:
            # Find name
            npc_data = next((n for n in self.npcs if n['id'] == n_id), {})
            name = npc_data.get('name', '???')
            self.content_list.insert(tk.END, f"[NPC] {name} ({n_id})")

    def _add_item(self):
        if not self.selected_node: return
        new_id = simpledialog.askstring("Neues Item", "Item ID:")
        if not new_id: return
        if new_id in self.items:
            messagebox.showerror("Fehler", "ID existiert bereits!")
            return
            
        # Default Data
        self.items[new_id] = {
            "id": new_id,
            "name": "Neues Item",
            "desc": "Beschreibung hier.",
            "location": self.selected_node,
            "type": "item",
            "climbable": False
        }
        self._edit_object_dialog(new_id)
        self._update_content_list()

    def _add_npc(self):
        if not self.selected_node: return
        new_id = simpledialog.askstring("Neuer NPC", "NPC ID:")
        if not new_id: return
        if any(n['id'] == new_id for n in self.npcs):
            messagebox.showerror("Fehler", "ID existiert bereits!")
            return
            
        new_npc = {
            "id": new_id,
            "name": "Neuer NPC",
            "desc": "Beschreibung.",
            "location": self.selected_node,
            "state": "idle",
            "behavior_id": "idle"
        }
        self.npcs.append(new_npc)
        self._edit_npc_dialog(new_npc)
        self._update_content_list()

    def _delete_content_item(self):
        sel = self.content_list.curselection()
        if not sel: return
        text = self.content_list.get(sel[0])
        
        if "[ITEM]" in text:
            obj_id = text.split("(")[-1].strip(")")
            del self.items[obj_id]
        elif "[NPC]" in text:
            npc_id = text.split("(")[-1].strip(")")
            self.npcs = [n for n in self.npcs if n['id'] != npc_id]
            
        self._update_content_list()

    def _edit_content_item(self, event=None):
        sel = self.content_list.curselection()
        if not sel: return
        text = self.content_list.get(sel[0])
        
        if "[ITEM]" in text:
            obj_id = text.split("(")[-1].strip(")")
            self._edit_object_dialog(obj_id)
        elif "[NPC]" in text:
            npc_id = text.split("(")[-1].strip(")")
            npc_data = next((n for n in self.npcs if n['id'] == npc_id), None)
            if npc_data: self._edit_npc_dialog(npc_data)

    # --- DIALOGS (Radio Buttons!) ---

    def _edit_object_dialog(self, item_id):
        item = self.items[item_id]
        
        dlg = tk.Toplevel(self)
        dlg.title(f"Edit Item: {item_id}")
        dlg.geometry("400x600")
        
        ttk.Label(dlg, text="Name:").pack(anchor='w', padx=5)
        ent_name = ttk.Entry(dlg)
        ent_name.insert(0, item.get('name', ''))
        ent_name.pack(fill='x', padx=5)
        
        ttk.Label(dlg, text="Beschreibung:").pack(anchor='w', padx=5, pady=(10,0))
        txt_desc = tk.Text(dlg, height=5)
        txt_desc.insert("1.0", item.get('desc', ''))
        txt_desc.pack(fill='x', padx=5)
        
        # TYPE RADIO BUTTONS
        ttk.Label(dlg, text="Typ:").pack(anchor='w', padx=5, pady=(10,0))
        type_var = tk.StringVar(value=item.get('type', 'item'))
        
        # Gewicht (Referenz für Aktivierung)
        ttk.Label(dlg, text="Gewicht (0 = fixiert):").pack(anchor='w', padx=5, pady=(10,0))
        ent_weight = ttk.Entry(dlg)
        ent_weight.insert(0, str(item.get('weight', 0)))
        ent_weight.pack(fill='x', padx=5)

        def update_weight_state():
            t = type_var.get()
            if t in ["fixture", "surface", "scenery"]:
                ent_weight.delete(0, tk.END)
                ent_weight.insert(0, "0")
                ent_weight.config(state='disabled')
            else:
                ent_weight.config(state='normal')

        # Initial Update
        update_weight_state()

        for label, val in TYPE_OPTIONS:
            rb = ttk.Radiobutton(dlg, text=label, variable=type_var, value=val, command=update_weight_state)
            rb.pack(anchor='w', padx=20)
            
        # CLIMBABLE RADIO
        ttk.Label(dlg, text="Bekletterbar?").pack(anchor='w', padx=5, pady=(10,0))
        climb_var = tk.BooleanVar(value=item.get('climbable', False))
        ttk.Radiobutton(dlg, text="Nein", variable=climb_var, value=False).pack(anchor='w', padx=20)
        ttk.Radiobutton(dlg, text="Ja (Ermöglicht Klettern)", variable=climb_var, value=True).pack(anchor='w', padx=20)

        def save():
            item['name'] = ent_name.get()
            item['desc'] = txt_desc.get("1.0", tk.END).strip()
            item['type'] = type_var.get()
            item['climbable'] = climb_var.get()
            
            # Gewicht nur speichern wenn aktiv, sonst 0
            if type_var.get() in ["fixture", "surface", "scenery"]:
                item['weight'] = 0
            else:
                try:
                    item['weight'] = float(ent_weight.get())
                except: item['weight'] = 0
                
            self._update_content_list()
            dlg.destroy()
            
        ttk.Button(dlg, text="Speichern", command=save).pack(pady=20)

    def _edit_npc_dialog(self, npc):
        dlg = tk.Toplevel(self)
        dlg.title(f"Edit NPC: {npc['id']}")
        dlg.geometry("400x500")
        
        ttk.Label(dlg, text="Name:").pack(anchor='w', padx=5)
        ent_name = ttk.Entry(dlg)
        ent_name.insert(0, npc.get('name', ''))
        ent_name.pack(fill='x', padx=5)
        
        ttk.Label(dlg, text="Beschreibung:").pack(anchor='w', padx=5, pady=(10,0))
        txt_desc = tk.Text(dlg, height=5)
        txt_desc.insert("1.0", npc.get('desc', ''))
        txt_desc.pack(fill='x', padx=5)
        
        # BEHAVIOR RADIO (Example)
        ttk.Label(dlg, text="Verhalten (KI):").pack(anchor='w', padx=5, pady=(10,0))
        beh_var = tk.StringVar(value=npc.get('behavior_id', 'idle'))
        ttk.Radiobutton(dlg, text="Stationär", variable=beh_var, value="idle").pack(anchor='w', padx=20)
        ttk.Radiobutton(dlg, text="Wache (Patrouille)", variable=beh_var, value="guard").pack(anchor='w', padx=20)
        ttk.Radiobutton(dlg, text="Ängstlich (Flucht)", variable=beh_var, value="fearful").pack(anchor='w', padx=20)
        
        # Speed
        ttk.Label(dlg, text="Geschwindigkeit:").pack(anchor='w', padx=5, pady=(10,0))
        ent_speed = ttk.Entry(dlg)
        ent_speed.insert(0, str(npc.get('speed', 1.0)))
        ent_speed.pack(fill='x', padx=5)

        def save():
            npc['name'] = ent_name.get()
            npc['desc'] = txt_desc.get("1.0", tk.END).strip()
            npc['behavior_id'] = beh_var.get()
            try: npc['speed'] = float(ent_speed.get())
            except: npc['speed'] = 1.0
            self._update_content_list()
            dlg.destroy()
            
        ttk.Button(dlg, text="Speichern", command=save).pack(pady=20)

    # --- STANDARD ROOM LOGIC ---

    def _on_layer_change(self):
        try:
            val = int(self.layer_var.get())
            self.current_z_level = val
            self._redraw()
        except ValueError: pass
            
    def _change_layer_rel(self, delta):
        self.current_z_level += delta
        self.layer_var.set(str(self.current_z_level))
        self._redraw()

    def _rebuild_links(self):
        self.links = []
        for rid, node in self.rooms.items():
            exits = node['data'].get('exits', {})
            for direction, target_id in exits.items():
                if target_id in self.rooms:
                    self.links.append((rid, target_id, direction))

    def _add_room(self):
        base_id = "room_"
        idx = 1
        while f"{base_id}{idx}" in self.rooms: idx += 1
        new_id = f"{base_id}{idx}"
        
        cx = (-self.offset_x + self.canvas.winfo_width() / 2) / self.scale
        cy = (-self.offset_y + self.canvas.winfo_height() / 2) / self.scale
        
        self.rooms[new_id] = {
            "data": {"id": new_id, "name": "Neuer Raum", "desc": "Leer.", "exits": {}},
            "x": cx, "y": cy, "z": self.current_z_level
        }
        self._redraw()
        self._select_node(new_id)

    def _add_link_dialog(self):
        if len(self.rooms) < 2: return
        dialog = tk.Toplevel(self)
        dialog.title("Verbindung")
        
        ttk.Label(dialog, text="Von:").grid(row=0, column=0)
        from_var = tk.StringVar()
        from_cb = ttk.Combobox(dialog, textvariable=from_var, values=list(self.rooms.keys()))
        if self.selected_node: from_cb.set(self.selected_node)
        from_cb.grid(row=0, column=1)
        
        ttk.Label(dialog, text="Nach:").grid(row=1, column=0)
        to_var = tk.StringVar()
        to_cb = ttk.Combobox(dialog, textvariable=to_var, values=list(self.rooms.keys()))
        to_cb.grid(row=1, column=1)
        
        ttk.Label(dialog, text="Richtung:").grid(row=2, column=0)
        dir_var = tk.StringVar(value="north")
        dirs = ["north", "south", "east", "west", "up", "down", "northeast", "northwest", "southeast", "southwest"]
        dir_cb = ttk.Combobox(dialog, textvariable=dir_var, values=dirs)
        dir_cb.grid(row=2, column=1)
        
        def create():
            f, t, d = from_var.get(), to_var.get(), dir_var.get()
            if f and t and d and f in self.rooms and t in self.rooms:
                if 'exits' not in self.rooms[f]['data']: self.rooms[f]['data']['exits'] = {}
                self.rooms[f]['data']['exits'][d] = t
                self._rebuild_links()
                self._redraw()
                dialog.destroy()
        
        ttk.Button(dialog, text="Erstellen", command=create).grid(row=3, column=0, columnspan=2)

    def _delete_room(self):
        if not self.selected_node: return
        if len(self.rooms) == 1:
            messagebox.showerror("Fehler", "Die Welt benötigt mindestens einen Raum.")
            return
        deleted_id = self.selected_node
        replacement_room = next(room_id for room_id in self.rooms if room_id != deleted_id)
        for node in self.rooms.values():
            node['data']['exits'] = {
                direction: target
                for direction, target in node['data'].get('exits', {}).items()
                if target != deleted_id
            }
        for item in self.items.values():
            if item.get('location') == deleted_id:
                item['location'] = 'void'
        for npc in self.npcs:
            if npc.get('location') == deleted_id:
                npc['location'] = replacement_room
        if self.meta.get('start_room') == deleted_id:
            self.meta['start_room'] = replacement_room
        del self.rooms[self.selected_node]
        self.selected_node = None
        self._rebuild_links()
        self._redraw()

    def _on_canvas_click(self, event):
        wx = (event.x - self.offset_x) / self.scale
        wy = (event.y - self.offset_y) / self.scale
        
        clicked_node = None
        for rid, node in self.rooms.items():
            if node['z'] != self.current_z_level: continue
            dist = math.hypot(node['x'] - wx, node['y'] - wy)
            if dist <= NODE_RADIUS:
                clicked_node = rid
                break
        
        if clicked_node:
            self._select_node(clicked_node)
            self.drag_data["item"] = clicked_node
            self.drag_data["x"] = wx
            self.drag_data["y"] = wy
        else:
            self.selected_node = None
            self._update_prop_panel()
            self._redraw()

    def _on_canvas_drag(self, event):
        if self.drag_data["item"]:
            wx = (event.x - self.offset_x) / self.scale
            wy = (event.y - self.offset_y) / self.scale
            node = self.rooms[self.drag_data["item"]]
            node['x'] = wx
            node['y'] = wy
            self._redraw()

    def _on_canvas_drop(self, event):
        self.drag_data["item"] = None

    def _on_canvas_right_click(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def _on_canvas_pan(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def _on_zoom(self, event):
        scale_factor = 1.1
        if event.num == 5 or event.delta < 0: scale_factor = 0.9
        self.scale *= scale_factor
        self._redraw()

    def _select_node(self, rid):
        self.selected_node = rid
        self._update_prop_panel()
        self._update_content_list() # Load items for room
        self._redraw()

    def _update_prop_panel(self):
        self.prop_id.delete(0, tk.END)
        self.prop_name.delete(0, tk.END)
        self.prop_z.delete(0, tk.END)
        self.prop_desc.delete("1.0", tk.END)
        self.exits_list.delete(0, tk.END)
        self.content_list.delete(0, tk.END) # Clear content list too
        
        if not self.selected_node: return
        
        node = self.rooms[self.selected_node]
        rdata = node['data']
        
        self.prop_id.insert(0, self.selected_node)
        self.prop_name.insert(0, rdata.get('name', ''))
        self.prop_z.insert(0, str(node['z']))
        self.prop_desc.insert("1.0", rdata.get('desc', ''))
        
        for d, t in rdata.get('exits', {}).items():
            self.exits_list.insert(tk.END, f"{d} -> {t}")
            
        self._update_content_list()

    def _save_node_props(self):
        if not self.selected_node: return
        new_id = self.prop_id.get().strip()
        try: new_z = int(self.prop_z.get().strip())
        except: new_z = 0
        
        if new_id != self.selected_node:
            if new_id in self.rooms:
                messagebox.showerror("Fehler", "ID existiert bereits!")
                return
            self.rooms[new_id] = self.rooms.pop(self.selected_node)
            self.rooms[new_id]['data']['id'] = new_id
            for node in self.rooms.values():
                exits = node['data'].get('exits', {})
                for direction, target in list(exits.items()):
                    if target == self.selected_node:
                        exits[direction] = new_id
            # Update location of items/npcs
            for i in self.items.values():
                if i['location'] == self.selected_node: i['location'] = new_id
            for n in self.npcs:
                if n['location'] == self.selected_node: n['location'] = new_id
            if self.meta.get('start_room') == self.selected_node:
                self.meta['start_room'] = new_id
            
            self.selected_node = new_id
            
        node = self.rooms[self.selected_node]
        node['z'] = new_z
        node['data']['name'] = self.prop_name.get()
        node['data']['desc'] = self.prop_desc.get("1.0", tk.END).strip()
        self._redraw()

    def _redraw(self):
        self.canvas.delete("all")
        
        for start, end, direction in self.links:
            if start not in self.rooms or end not in self.rooms: continue
            
            n1 = self.rooms[start]
            n2 = self.rooms[end]
            
            visible = False
            is_vertical = False
            
            if n1['z'] == self.current_z_level and n2['z'] == self.current_z_level:
                visible = True
            elif n1['z'] == self.current_z_level and n2['z'] != self.current_z_level:
                visible = True
                is_vertical = True
            elif n2['z'] == self.current_z_level and n1['z'] != self.current_z_level:
                visible = True
                is_vertical = True
            
            if not visible: continue
            
            x1 = n1['x'] * self.scale + self.offset_x
            y1 = n1['y'] * self.scale + self.offset_y
            x2 = n2['x'] * self.scale + self.offset_x
            y2 = n2['y'] * self.scale + self.offset_y
            
            col = "#555555"
            width = 2
            dash = None
            if is_vertical:
                col = "#AA55AA"
                dash = (4, 2)
            
            self.canvas.create_line(x1, y1, x2, y2, fill=col, width=width, arrow=tk.LAST, dash=dash)
            mx, my = (x1+x2)/2, (y1+y2)/2
            self.canvas.create_text(mx, my, text=direction, fill="#AAAAAA", font=("Arial", 8))

        for rid, node in self.rooms.items():
            z_diff = node['z'] - self.current_z_level
            if z_diff == 0:
                fill_col = "#4444AA"
                outline_col = "#FFFFFF"
            elif abs(z_diff) == 1:
                fill_col = "#222222"
                outline_col = "#555555"
            else:
                continue 
                
            if rid == self.selected_node:
                fill_col = "#AA4444"
            
            cx = node['x'] * self.scale + self.offset_x
            cy = node['y'] * self.scale + self.offset_y
            r = NODE_RADIUS * self.scale
            
            self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill=fill_col, outline=outline_col, width=2)
            
            text_col = "#FFFFFF" if z_diff == 0 else "#666666"
            self.canvas.create_text(cx, cy, text=node['data'].get('name', '???'), fill=text_col, font=("Arial", int(10*self.scale), "bold"))
            self.canvas.create_text(cx, cy+r+10, text=rid, fill="#888888", font=("Arial", int(8*self.scale)))
            
            if z_diff != 0:
                 indicator = "▲" if z_diff > 0 else "▼"
                 self.canvas.create_text(cx, cy-r-10, text=indicator, fill="#AA55AA", font=("Arial", int(12*self.scale)))

if __name__ == "__main__":
    app = WorldEditor()
    app.mainloop()
