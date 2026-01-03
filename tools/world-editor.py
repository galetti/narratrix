import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import json
import os
import random
import ast
import pprint
import math

# --- KONFIGURATION ---
NODE_WIDTH = 120
NODE_HEIGHT = 80
BG_COLOR = "#2b2b2b"
GRID_COLOR = "#333333"
NODE_COLOR = "#444444"
NODE_SELECTED_COLOR = "#665522"
TEXT_COLOR = "#ffffff"
LINE_COLOR = "#888888"
NPC_COLOR = "#3388bb"
ITEM_COLOR = "#33bb88"

class DataHandler:
    """Kapselt das Laden und Speichern der Daten (Modular vs Monolithisch)"""
    def __init__(self, root_path):
        self.root_path = root_path
        self.active_context_path = None
        self.mode = "unknown" # 'monolith' (config.py) oder 'modular' (rooms.py, npcs.py...)
        self.common_data = {"npcs": [], "rooms": {}, "objects": {}}

    def load_common(self):
        """Lädt Daten aus data/common (falls vorhanden), um globale NPCs/Items verfügbar zu machen."""
        common_path = os.path.join(self.root_path, "common")
        if os.path.exists(common_path):
            self.common_data["npcs"] = self._load_py_list(os.path.join(common_path, "npcs.py"), "NPCS")
            self.common_data["rooms"] = self._load_py_dict(os.path.join(common_path, "rooms.py"), "ROOMS")
            self.common_data["objects"] = self._load_py_dict(os.path.join(common_path, "items.py"), "ITEMS")

    def load_context(self, subpath):
        """Lädt einen Kontext (z.B. 'chapters/ep0_arrival') relativ zum Data-Root"""
        full_path = os.path.join(self.root_path, subpath)
        self.active_context_path = full_path
        
        # Zuerst Common laden (für Referenzen)
        self.load_common()
        
        data = {"rooms": {}, "objects": {}, "npcs": []}
        
        # Check 1: Modulare Struktur (rooms.py, npcs.py...)
        has_rooms = os.path.exists(os.path.join(full_path, "rooms.py"))
        
        if has_rooms:
            self.mode = "modular"
            data["rooms"] = self._load_py_dict(os.path.join(full_path, "rooms.py"), "ROOMS")
            
            # NPCs: Lokale laden + Common NPCs (markiert als 'common')
            local_npcs = self._load_py_list(os.path.join(full_path, "npcs.py"), "NPCS")
            # Wir markieren Common NPCs, damit wir sie beim Speichern nicht duplizieren/überschreiben
            for n in self.common_data["npcs"]:
                n_copy = n.copy()
                n_copy["_source"] = "common" 
                data["npcs"].append(n_copy)
            
            for n in local_npcs:
                n["_source"] = "local"
                data["npcs"].append(n)
            
            # Items
            if os.path.exists(os.path.join(full_path, "items.py")):
                data["objects"] = self._load_py_dict(os.path.join(full_path, "items.py"), "ITEMS")
            elif os.path.exists(os.path.join(full_path, "objects.py")):
                data["objects"] = self._load_py_dict(os.path.join(full_path, "objects.py"), "OBJECTS")
        else:
            # Check 2: Monolithische Config (config.py)
            config_path = os.path.join(full_path, "config.py")
            if os.path.exists(config_path):
                self.mode = "monolith"
                raw = self._load_py_dict(config_path, "CHAPTER_CONFIG") 
                if not raw: raw = self._load_py_dict(config_path, "COMMON_CONFIG")
                
                if raw:
                    data["rooms"] = raw.get("rooms", {})
                    data["objects"] = raw.get("objects", {})
                    data["npcs"] = raw.get("npcs", [])
            else:
                self.mode = "new" 

        return data

    def save_context(self, data):
        if not self.active_context_path: return False
        
        # Filtern: Nur lokale NPCs speichern
        local_npcs = [n for n in data["npcs"] if n.get("_source", "local") == "local"]
        
        # Bereinigen von Editor-Metadaten für Speicher-Objekt (optional, aber sauberer)
        clean_npcs = []
        for n in local_npcs:
            n_copy = n.copy()
            if "_source" in n_copy: del n_copy["_source"]
            clean_npcs.append(n_copy)

        try:
            if self.mode == "modular":
                self._save_py_data(os.path.join(self.active_context_path, "rooms.py"), "ROOMS", data["rooms"])
                self._save_py_data(os.path.join(self.active_context_path, "npcs.py"), "NPCS", clean_npcs)
                self._save_py_data(os.path.join(self.active_context_path, "items.py"), "ITEMS", data["objects"])
            
            elif self.mode == "monolith":
                full_config = {
                    "meta": {"generated": True},
                    "rooms": data["rooms"],
                    "objects": data["objects"],
                    "npcs": clean_npcs
                }
                self._save_py_data(os.path.join(self.active_context_path, "config.py"), "CHAPTER_CONFIG", full_config)
            
            return True
        except Exception as e:
            print(f"Save Error: {e}")
            return False

    def _load_py_dict(self, filepath, var_name):
        try:
            with open(filepath, 'r', encoding='utf-8') as f: content = f.read()
            scope = {}
            exec(content, scope)
            if var_name in scope: return scope[var_name]
            if var_name.lower() in scope: return scope[var_name.lower()]
            for k, v in scope.items():
                if isinstance(v, dict) and not k.startswith("__"): return v
            return {}
        except Exception as e: 
            print(f"Load Dict Error ({filepath}): {e}")
            return {}

    def _load_py_list(self, filepath, var_name):
        try:
            with open(filepath, 'r', encoding='utf-8') as f: content = f.read()
            scope = {}
            exec(content, scope)
            if var_name in scope: return scope[var_name]
            if var_name.lower() in scope: return scope[var_name.lower()]
            for k, v in scope.items():
                if isinstance(v, list) and not k.startswith("__"): return v
            return []
        except Exception as e:
            print(f"Load List Error ({filepath}): {e}")
            return []

    def _save_py_data(self, filepath, var_name, data_obj):
        formatted = pprint.pformat(data_obj, indent=4, width=120, sort_dicts=False)
        content = f"# Auto-generated by Narratrix World Builder\n\n{var_name} = {formatted}\n"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)


class WorldEditorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Narratrix World Builder - Project Edition")
        self.geometry("1600x900")
        self.configure(bg=BG_COLOR)

        # --- STATE ---
        self.data_handler = None
        self.data = {"rooms": {}, "objects": {}, "npcs": []}
        
        self.selection = None 
        
        # View State
        self.pan_x = 0
        self.pan_y = 0
        self.scale = 1.0
        self.drag_data = {"x": 0, "y": 0, "mode": None}

        self._setup_ui()

    def _setup_ui(self):
        # MENUBAR
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="'data' Ordner öffnen...", command=self.open_project_folder, accelerator="Ctrl+O")
        file_menu.add_command(label="Speichern", command=self.save_current, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="Datei", menu=file_menu)
        self.config(menu=menubar)
        self.bind("<Control-s>", lambda e: self.save_current())
        self.bind("<Control-o>", lambda e: self.open_project_folder())

        # MAIN LAYOUT
        main_paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg=BG_COLOR, sashwidth=4)
        main_paned.pack(fill=tk.BOTH, expand=True)

        # 1. LEFT: Project Browser
        self.browser_frame = tk.Frame(main_paned, bg="#1e1e1e")
        main_paned.add(self.browser_frame, width=250)
        
        tk.Label(self.browser_frame, text="PROJEKT BROWSER", fg="yellow", bg="#1e1e1e", font=("Arial", 10, "bold")).pack(pady=5)
        self.tree = ttk.Treeview(self.browser_frame, selectmode="browse")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # 2. CENTER: Canvas & Toolbar
        center_frame = tk.Frame(main_paned, bg=BG_COLOR)
        main_paned.add(center_frame, minsize=400)
        
        # Toolbar
        toolbar = tk.Frame(center_frame, bg="#333", height=40)
        toolbar.pack(fill=tk.X, side=tk.TOP)
        
        tk.Button(toolbar, text="+ Raum", bg="#444", fg="white", command=self.add_room).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(toolbar, text="+ NPC", bg="#336699", fg="white", command=self.add_npc).pack(side=tk.LEFT, padx=5, pady=5)
        self.lbl_status = tk.Label(toolbar, text="Bereit", bg="#333", fg="#aaa")
        self.lbl_status.pack(side=tk.RIGHT, padx=10)

        # Canvas
        self.canvas = tk.Canvas(center_frame, bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self._bind_canvas_events()

        # 3. RIGHT: Inspector
        self.inspector_frame = tk.Frame(main_paned, bg="#1e1e1e")
        main_paned.add(self.inspector_frame, width=350)
        
        tk.Label(self.inspector_frame, text="INSPEKTOR", fg="white", bg="#1e1e1e", font=("Arial", 10, "bold")).pack(pady=10)
        
        # Scrollable Inspector Area
        canvas_ins = tk.Canvas(self.inspector_frame, bg="#1e1e1e", highlightthickness=0)
        scrollbar_ins = ttk.Scrollbar(self.inspector_frame, orient="vertical", command=canvas_ins.yview)
        self.prop_inner = tk.Frame(canvas_ins, bg="#1e1e1e")
        
        self.prop_inner.bind("<Configure>", lambda e: canvas_ins.configure(scrollregion=canvas_ins.bbox("all")))
        canvas_ins.create_window((0, 0), window=self.prop_inner, anchor="nw")
        canvas_ins.configure(yscrollcommand=scrollbar_ins.set)
        
        canvas_ins.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_ins.pack(side=tk.RIGHT, fill=tk.Y)

    def _bind_canvas_events(self):
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<ButtonPress-3>", self.start_pan)
        self.canvas.bind("<B3-Motion>", self.do_pan) # Right click pan
        self.canvas.bind("<MouseWheel>", self.on_zoom)

    # --- PROJECT MANAGEMENT ---

    def open_project_folder(self):
        folder = filedialog.askdirectory(title="Wähle den 'data' Ordner")
        if not folder: return
        
        self.data_handler = DataHandler(folder)
        self.tree.delete(*self.tree.get_children())
        
        # Root Node
        root_node = self.tree.insert("", "end", text="Modules", open=True)
        
        # Common
        if os.path.exists(os.path.join(folder, "common")):
            self.tree.insert(root_node, "end", text="common", values=("common",))
            
        # Chapters
        chapters_path = os.path.join(folder, "chapters")
        if os.path.exists(chapters_path):
            chap_node = self.tree.insert(root_node, "end", text="chapters", open=True)
            for item in os.listdir(chapters_path):
                if os.path.isdir(os.path.join(chapters_path, item)) and not item.startswith("__"):
                    self.tree.insert(chap_node, "end", text=item, values=(f"chapters/{item}",))

    def on_tree_select(self, event):
        sel = self.tree.selection()
        if not sel: return
        
        item = self.tree.item(sel[0])
        if item["values"]:
            subpath = item["values"][0]
            self.load_context(subpath)

    def load_context(self, subpath):
        if not self.data_handler: return
        try:
            self.data = self.data_handler.load_context(subpath)
            self._ensure_layout()
            self.selection = None
            self.pan_x = 0 # Reset Pan beim Laden
            self.pan_y = 0
            self._redraw_canvas()
            self._update_inspector()
            
            # Statistik
            r_count = len(self.data.get("rooms", {}))
            n_count = len(self.data.get("npcs", []))
            self.lbl_status.config(text=f"Geladen: {subpath} (Räume: {r_count}, NPCs: {n_count})")
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte Daten nicht laden: {e}")

    def save_current(self):
        if not self.data_handler or not self.data_handler.active_context_path: return
        
        success = self.data_handler.save_context(self.data)
        if success:
            self.lbl_status.config(text="Gespeichert!", fg="#55ff55")
            self.after(2000, lambda: self.lbl_status.config(text="Bereit", fg="#aaa"))
        else:
            messagebox.showerror("Fehler", "Speichern fehlgeschlagen.")

    def _ensure_layout(self):
        """
        Intelligentes Auto-Layout basierend auf Raum-Verbindungen (Topologie).
        Nutzt BFS, um Räume relativ zueinander zu platzieren.
        """
        rooms = self.data.get("rooms", {})
        if not rooms: return

        # Prüfen, ob wir überhaupt Layout brauchen
        needs_layout = [rid for rid, r in rooms.items() if "editor_x" not in r]
        if not needs_layout: return

        start_node = needs_layout[0]
        
        grid_size_x = 250
        grid_size_y = 200
        start_x, start_y = 400, 300
        
        queue = [(start_node, 0, 0)]
        visited = {start_node}
        
        grid_occupancy = {} 
        
        for rid, r in rooms.items():
            if "editor_x" in r:
                gx = int((r["editor_x"] - start_x) / grid_size_x)
                gy = int((r["editor_y"] - start_y) / grid_size_y)
                grid_occupancy[(gx, gy)] = rid
                visited.add(rid)

        while queue:
            curr_id, gx, gy = queue.pop(0)
            
            if "editor_x" not in rooms[curr_id]:
                while (gx, gy) in grid_occupancy and grid_occupancy[(gx, gy)] != curr_id:
                    gx += 1 
                
                rooms[curr_id]["editor_x"] = start_x + gx * grid_size_x
                rooms[curr_id]["editor_y"] = start_y + gy * grid_size_y
                grid_occupancy[(gx, gy)] = curr_id

            exits = rooms[curr_id].get("exits", {})
            for direction, target_id in exits.items():
                if target_id not in rooms: continue
                if target_id in visited: continue
                
                tx, ty = gx, gy
                if direction in ["north", "up"]: ty -= 1
                elif direction in ["south", "down"]: ty += 1
                elif direction in ["east", "out"]: tx += 1
                elif direction in ["west", "in"]: tx -= 1
                else: tx += 1 
                
                visited.add(target_id)
                queue.append((target_id, tx, ty))
                
        remaining = [rid for rid in needs_layout if rid not in visited]
        if remaining:
            idx = 0
            base_y = max((pos[1] for pos in grid_occupancy.keys()), default=0) + 2
            for rid in remaining:
                if "editor_x" not in rooms[rid]:
                    rooms[rid]["editor_x"] = start_x + (idx % 5) * grid_size_x
                    rooms[rid]["editor_y"] = start_y + (base_y + idx // 5) * grid_size_y
                    idx += 1

    # --- EDITING LOGIC ---

    def add_room(self):
        if not self.data_handler or not self.data_handler.active_context_path: 
            messagebox.showwarning("Info", "Bitte zuerst ein Kapitel laden.")
            return
            
        new_id = f"room_{random.randint(1000, 9999)}"
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        cx = (-self.pan_x + w/2) / self.scale
        cy = (-self.pan_y + h/2) / self.scale
        
        self.data["rooms"][new_id] = {
            "name": "Neuer Raum",
            "desc": "Beschreibung...",
            "exits": {},
            "editor_x": cx,
            "editor_y": cy
        }
        self.select_entity('room', new_id)

    def add_npc(self):
        if not self.data_handler or not self.data_handler.active_context_path:
            messagebox.showwarning("Info", "Bitte zuerst ein Kapitel laden.")
            return

        new_id = f"npc_{random.randint(1000, 9999)}"
        loc = list(self.data["rooms"].keys())[0] if self.data["rooms"] else "void"
        
        new_npc = {
            "id": new_id,
            "name": "Neuer NPC",
            "location": loc,
            "role": "civilian",
            "state": "idle",
            "dialogue": {},
            "_source": "local"
        }
        self.data["npcs"].append(new_npc)
        self.select_entity('npc', new_id)

    def delete_selection(self):
        if not self.selection: return
        
        type_, id_ = self.selection['type'], self.selection['id']
        
        if messagebox.askyesno("Löschen", f"{type_} '{id_}' löschen?"):
            if type_ == 'room':
                del self.data["rooms"][id_]
                for r in self.data["rooms"].values():
                    if "exits" in r:
                        to_del = [d for d, t in r["exits"].items() if t == id_]
                        for d in to_del: del r["exits"][d]
                for n in self.data["npcs"]:
                    if n.get("location") == id_: n["location"] = "void"
                    
            elif type_ == 'npc':
                self.data["npcs"] = [n for n in self.data["npcs"] if n.get("id") != id_]

            self.selection = None
            self._redraw_canvas()
            self._update_inspector()

    def select_entity(self, type_, id_):
        self.selection = {'type': type_, 'id': id_}
        self._redraw_canvas()
        self._update_inspector()

    def _create_door_obj(self, room_id, direction, name, locked=False, key_id=None):
        """Erzeugt ein Tür-Objekt für einen Ausgang und registriert es in den Objekten."""
        door_id = f"door_{room_id}_{direction}"
        door_obj = {
            "id": door_id,
            "name": name,
            "type": "container", # In Narratrix sind Türen oft Container mit linked_exit
            "location": room_id,
            "linked_exit": direction,
            "is_open": not locked,
            "is_locked": locked,
            "desc": f"Eine {name}."
        }
        if key_id: door_obj["key_id"] = key_id
        
        self.data["objects"][door_id] = door_obj
        return door_id

    # --- CANVAS DRAWING ---

    def _redraw_canvas(self):
        self.canvas.delete("all")
        
        # Draw Connections (Lines)
        for r_id, room in self.data["rooms"].items():
            x1 = room.get("editor_x", 0) * self.scale + self.pan_x
            y1 = room.get("editor_y", 0) * self.scale + self.pan_y
            
            exits = room.get("exits", {})
            for direction, target_id in exits.items():
                if target_id in self.data["rooms"]:
                    target = self.data["rooms"][target_id]
                    x2 = target.get("editor_x", 0) * self.scale + self.pan_x
                    y2 = target.get("editor_y", 0) * self.scale + self.pan_y
                    
                    # Prüfen auf Tür/Hindernis
                    is_blocked = False
                    # Wir suchen Objekte im Raum, die diesen Ausgang blockieren (linked_exit)
                    for obj in self.data["objects"].values():
                        if obj.get("location") == r_id and obj.get("linked_exit") == direction:
                            if obj.get("is_locked") or not obj.get("is_open"):
                                is_blocked = True
                                break
                    
                    line_col = "#dd4444" if is_blocked else LINE_COLOR
                    width = 3 if is_blocked else 2
                    
                    self.canvas.create_line(x1, y1, x2, y2, fill=line_col, width=width, arrow=tk.LAST)
                    
                    mx = x1 + (x2 - x1) * 0.3
                    my = y1 + (y2 - y1) * 0.3
                    
                    text_id = self.canvas.create_text(mx, my, text=direction, fill="#bbb", font=("Arial", 8))
                    bbox = self.canvas.bbox(text_id)
                    if bbox:
                        self.canvas.create_rectangle(bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2, fill="#222", outline="", tags="label_bg")
                        self.canvas.tag_lower("label_bg", text_id)

        # Draw Rooms
        for r_id, room in self.data["rooms"].items():
            x = room.get("editor_x", 0) * self.scale + self.pan_x
            y = room.get("editor_y", 0) * self.scale + self.pan_y
            
            nw = NODE_WIDTH * self.scale
            nh = NODE_HEIGHT * self.scale
            
            is_sel = (self.selection and self.selection['type'] == 'room' and self.selection['id'] == r_id)
            color = NODE_SELECTED_COLOR if is_sel else NODE_COLOR
            outline = "white" if is_sel else "black"
            width = 3 if is_sel else 1
            
            self.canvas.create_rectangle(x - nw/2, y - nh/2, x + nw/2, y + nh/2, 
                                       fill=color, outline=outline, width=width, tags=("room", r_id))
            
            self.canvas.create_text(x, y-10*self.scale, text=room.get("name", "Unbenannt"), 
                                  fill=TEXT_COLOR, font=("Arial", int(10*self.scale), "bold"), tags=("room", r_id))
            self.canvas.create_text(x, y+10*self.scale, text=r_id, 
                                  fill="#aaaaaa", font=("Arial", int(8*self.scale)), tags=("room", r_id))

            # Draw NPCs
            npcs_here = [n for n in self.data["npcs"] if n.get("location") == r_id]
            for i, npc in enumerate(npcs_here):
                offset_x = (i - (len(npcs_here)-1)/2) * (15 * self.scale)
                nx = x + offset_x
                ny = y + nh/2 - (10 * self.scale)
                nid = npc.get("id", "unk")
                
                npc_sel = (self.selection and self.selection['type'] == 'npc' and self.selection['id'] == nid)
                npc_outline = "yellow" if npc_sel else "black"
                npc_width = 2 if npc_sel else 1
                
                r_size = 5 * self.scale
                # Unterscheidung Common vs Local
                fill_col = NPC_COLOR if npc.get("_source") == "local" else "#555577"
                
                self.canvas.create_oval(nx-r_size, ny-r_size, nx+r_size, ny+r_size, 
                                      fill=fill_col, outline=npc_outline, width=npc_width, tags=("npc", nid))


    # --- INPUT HANDLERS ---

    def on_mouse_down(self, event):
        x, y = event.x, event.y
        items = self.canvas.find_overlapping(x-4, y-4, x+4, y+4)
        
        clicked_type, clicked_id = None, None
        
        for item in reversed(items):
            tags = self.canvas.gettags(item)
            if "npc" in tags:
                clicked_type, clicked_id = "npc", tags[1]
                break
            if "room" in tags:
                clicked_type, clicked_id = "room", tags[1]
        
        if clicked_type:
            self.select_entity(clicked_type, clicked_id)
            if clicked_type == 'room':
                self.drag_data = {"mode": "move_room", "id": clicked_id, "x": x, "y": y}
            else:
                self.drag_data = {"mode": None, "x": x, "y": y} 
        else:
            self.selection = None
            self._update_inspector()
            self._redraw_canvas()
            self.drag_data = {"mode": "pan", "x": x, "y": y}

    def on_mouse_drag(self, event):
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        mode = self.drag_data.get("mode")

        if mode == "move_room":
            rid = self.drag_data["id"]
            if rid in self.data["rooms"]:
                room = self.data["rooms"][rid]
                room["editor_x"] = room.get("editor_x", 0) + dx / self.scale
                room["editor_y"] = room.get("editor_y", 0) + dy / self.scale
                self._redraw_canvas()
            
        elif mode == "pan":
            self.pan_x += dx
            self.pan_y += dy
            self._redraw_canvas()

        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def on_mouse_up(self, event):
        self.drag_data["mode"] = None

    def start_pan(self, event):
        self.drag_data = {"mode": "pan", "x": event.x, "y": event.y}
    
    def do_pan(self, event):
        if self.drag_data.get("mode") == "pan":
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]
            self.pan_x += dx
            self.pan_y += dy
            self._redraw_canvas()
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y

    def stop_pan(self, event):
        self.drag_data["mode"] = None

    def on_zoom(self, event):
        factor = 1.1 if event.delta > 0 else 0.9
        self.scale *= factor
        self.scale = max(0.2, min(3.0, self.scale))
        self._redraw_canvas()

    # --- INSPECTOR UI ---

    def _update_inspector(self):
        for w in self.prop_inner.winfo_children(): w.destroy()
        
        if not self.selection:
            tk.Label(self.prop_inner, text="(Keine Auswahl)", bg="#1e1e1e", fg="#555").pack(pady=20)
            return

        type_ = self.selection['type']
        id_ = self.selection['id']
        
        if type_ == 'room':
            if id_ in self.data["rooms"]:
                self._build_room_inspector(id_)
            else:
                self.selection = None 
        elif type_ == 'npc':
            if any(n.get("id") == id_ for n in self.data["npcs"]):
                self._build_npc_inspector(id_)
            else:
                self.selection = None
            
        tk.Button(self.prop_inner, text="Element Löschen", bg="#882222", fg="white", command=self.delete_selection).pack(fill=tk.X, pady=20)

    def _build_room_inspector(self, rid):
        room = self.data["rooms"][rid]
        
        self._add_entry("ID", rid, readonly=True)
        self._add_entry("Name", room.get("name", ""), lambda v: self._update_data('rooms', rid, 'name', v))
        self._add_text("Beschreibung", room.get("desc", ""), lambda v: self._update_data('rooms', rid, 'desc', v))
        
        tk.Label(self.prop_inner, text="--- AUSGÄNGE ---", bg="#1e1e1e", fg="#888").pack(pady=5)
        for direction, target in room.get("exits", {}).items():
            f = tk.Frame(self.prop_inner, bg="#1e1e1e")
            f.pack(fill=tk.X, pady=2)
            tk.Label(f, text=direction, bg="#1e1e1e", fg="white", width=8).pack(side=tk.LEFT)
            
            target_ids = list(self.data["rooms"].keys())
            cb = ttk.Combobox(f, values=target_ids, width=12)
            cb.set(target)
            cb.bind("<<ComboboxSelected>>", lambda e, d=direction, c=cb: self._update_exit(rid, d, c.get()))
            cb.pack(side=tk.LEFT, fill=tk.X)
            
            # Door Settings Button
            btn_door = tk.Button(f, text="🚪", bg="#444", fg="white", borderwidth=0,
                               command=lambda d=direction: self._configure_door(rid, d))
            btn_door.pack(side=tk.LEFT, padx=2)
            
            tk.Button(f, text="X", bg="#552222", fg="white", borderwidth=0, 
                     command=lambda d=direction: self._remove_exit(rid, d)).pack(side=tk.RIGHT)

        f_new = tk.Frame(self.prop_inner, bg="#1e1e1e")
        f_new.pack(fill=tk.X, pady=10)
        dirs = ["north", "south", "east", "west", "up", "down", "out", "in"]
        cb_dir = ttk.Combobox(f_new, values=dirs, width=8)
        cb_dir.current(0)
        cb_dir.pack(side=tk.LEFT)
        
        default_target = rid
        if len(self.data["rooms"]) > 1:
             for r in self.data["rooms"]:
                 if r != rid: 
                     default_target = r; break

        tk.Button(f_new, text="+", bg="#336633", fg="white", 
                 command=lambda: self._update_exit(rid, cb_dir.get(), default_target)).pack(side=tk.LEFT, padx=5)

    def _configure_door(self, rid, direction):
        """Öffnet Dialog zum Konfigurieren einer Tür."""
        # Check existing door obj
        existing_door = None
        for obj in self.data["objects"].values():
            if obj.get("location") == rid and obj.get("linked_exit") == direction:
                existing_door = obj
                break
        
        dialog = tk.Toplevel(self)
        dialog.title(f"Tür Einstellungen ({direction})")
        dialog.geometry("300x250")
        dialog.configure(bg=BG_COLOR)
        
        tk.Label(dialog, text="Tür Name:", bg=BG_COLOR, fg="white").pack(pady=5)
        name_var = tk.StringVar(value=existing_door["name"] if existing_door else "Stahltür")
        tk.Entry(dialog, textvariable=name_var).pack(fill=tk.X, padx=20)
        
        locked_var = tk.BooleanVar(value=existing_door["is_locked"] if existing_door else False)
        tk.Checkbutton(dialog, text="Verschlossen", variable=locked_var, bg=BG_COLOR, fg="white", selectcolor="#444").pack(pady=5)
        
        tk.Label(dialog, text="Schlüssel ID (opt):", bg=BG_COLOR, fg="white").pack(pady=5)
        key_var = tk.StringVar(value=existing_door.get("key_id", "") if existing_door else "")
        tk.Entry(dialog, textvariable=key_var).pack(fill=tk.X, padx=20)
        
        def save():
            door_id = self._create_door_obj(rid, direction, name_var.get(), locked_var.get(), key_var.get())
            self._redraw_canvas()
            dialog.destroy()
            
        def delete():
            if existing_door:
                del self.data["objects"][existing_door["id"]]
            self._redraw_canvas()
            dialog.destroy()

        tk.Button(dialog, text="Speichern", command=save, bg="#336633", fg="white").pack(side=tk.LEFT, padx=20, pady=20)
        tk.Button(dialog, text="Entfernen", command=delete, bg="#663333", fg="white").pack(side=tk.RIGHT, padx=20, pady=20)


    def _build_npc_inspector(self, nid):
        npc = next((n for n in self.data["npcs"] if n.get("id") == nid), None)
        if not npc: return
        
        def update_npc(key, val):
            npc[key] = val
            self._redraw_canvas()

        self._add_entry("ID", nid, readonly=True)
        self._add_entry("Name", npc.get("name", ""), lambda v: update_npc('name', v))
        self._add_entry("Rolle", npc.get("role", ""), lambda v: update_npc('role', v))
        self._add_entry("Status", npc.get("state", ""), lambda v: update_npc('state', v))
        
        tk.Label(self.prop_inner, text="Standort", bg="#1e1e1e", fg="#aaa", anchor="w").pack(fill=tk.X)
        locs = ["void"] + list(self.data["rooms"].keys())
        cb = ttk.Combobox(self.prop_inner, values=locs)
        cb.set(npc.get("location", "void"))
        cb.bind("<<ComboboxSelected>>", lambda e: update_npc('location', cb.get()))
        cb.pack(fill=tk.X, pady=(0, 10))

        # --- FIX: INTELIGENTES DIALOG/STATE HANDLING ---
        
        key_to_edit = "dialogue" # Default old style
        data_to_edit = npc.get("dialogue", {})
        
        if "states" in npc:
            key_to_edit = "states"
            data_to_edit = npc["states"]
            label_text = "Erweiterte Daten (States/Complex)"
        else:
            label_text = "Dialog (Einfach)"

        tk.Label(self.prop_inner, text=label_text, bg="#1e1e1e", fg="#aaa", anchor="w").pack(fill=tk.X)
        
        txt_frame = tk.Frame(self.prop_inner)
        txt_frame.pack(fill=tk.X, pady=(0, 10))
        
        txt = tk.Text(txt_frame, height=12, bg="#333", fg="white", insertbackground="white", font=("Consolas", 9))
        
        formatted = pprint.pformat(data_to_edit, width=40, sort_dicts=False)
        txt.insert("1.0", formatted)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        def save_dict(event=None):
            raw = txt.get("1.0", "end-1c")
            try:
                val = ast.literal_eval(raw)
                if isinstance(val, dict):
                    update_npc(key_to_edit, val)
                    txt.configure(bg="#223322") 
                else:
                    raise ValueError("Muss ein Dictionary sein")
            except Exception as e:
                txt.configure(bg="#442222") 
                print(f"Dict Error: {e}")

        txt.bind("<Control-s>", save_dict) 
        txt.bind("<FocusOut>", save_dict)

    # --- INSPECTOR HELPERS ---

    def _add_entry(self, label, value, callback=None, readonly=False):
        tk.Label(self.prop_inner, text=label, bg="#1e1e1e", fg="#aaa", anchor="w").pack(fill=tk.X)
        var = tk.StringVar(value=str(value))
        entry = tk.Entry(self.prop_inner, textvariable=var, bg="#333", fg="white", insertbackground="white")
        if readonly: entry.config(state='readonly')
        entry.pack(fill=tk.X, pady=(0, 10))
        if callback:
            var.trace_add("write", lambda *args: callback(var.get()))

    def _add_text(self, label, value, callback):
        tk.Label(self.prop_inner, text=label, bg="#1e1e1e", fg="#aaa", anchor="w").pack(fill=tk.X)
        txt = tk.Text(self.prop_inner, height=4, bg="#333", fg="white", insertbackground="white")
        txt.insert("1.0", value)
        txt.pack(fill=tk.X, pady=(0, 10))
        txt.bind("<FocusOut>", lambda e: callback(txt.get("1.0", "end-1c")))

    def _update_data(self, collection, id_, key, value):
        self.data[collection][id_][key] = value
        self._redraw_canvas()

    def _update_exit(self, rid, direction, target):
        if "exits" not in self.data["rooms"][rid]: self.data["rooms"][rid]["exits"] = {}
        self.data["rooms"][rid]["exits"][direction] = target
        self._redraw_canvas()
        self._update_inspector() 

    def _remove_exit(self, rid, direction):
        if direction in self.data["rooms"][rid].get("exits", {}):
            del self.data["rooms"][rid]["exits"][direction]
            self._redraw_canvas()
            self._update_inspector()


if __name__ == "__main__":
    app = WorldEditorApp()
    app.mainloop()