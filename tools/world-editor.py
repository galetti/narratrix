# narratrix_engine/tools/world-editor.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import math

# Konstanten für die Visualisierung
NODE_RADIUS = 30
GRID_SIZE = 20
DEFAULT_Z = 0 # Standard-Ebene

class WorldEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Narratrix World Editor - Multi-Deck Edition")
        self.geometry("1400x900")
        
        self.rooms = {} # id -> {data, x, y, z}
        self.links = [] # (start_id, end_id, direction)
        
        self.current_file = None
        self.selected_node = None
        self.drag_data = {"x": 0, "y": 0, "item": None}
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        # NEU: Aktuelle Ebene (Z-Level)
        self.current_z_level = DEFAULT_Z
        
        self._init_ui()
        self._create_menu()

    def _init_ui(self):
        # Layout: Left Sidebar (Tools), Center (Canvas), Right Sidebar (Properties)
        
        # --- LEFT SIDEBAR (Layers & Tools) ---
        left_panel = ttk.Frame(self, width=200, padding=10)
        left_panel.pack(side=tk.LEFT, fill=tk.Y)
        
        ttk.Label(left_panel, text="Ebenen (Decks)", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Layer Control
        self.layer_var = tk.StringVar(value=str(DEFAULT_Z))
        self.layer_spin = ttk.Spinbox(left_panel, from_=-10, to=10, textvariable=self.layer_var, width=5, command=self._on_layer_change)
        self.layer_spin.pack(pady=5)
        self.layer_spin.bind("<Return>", lambda e: self._on_layer_change())
        
        ttk.Label(left_panel, text="(Pfeiltasten Rauf/Runter)", font=("Arial", 8)).pack()
        
        ttk.Separator(left_panel, orient='horizontal').pack(fill='x', pady=20)
        
        ttk.Button(left_panel, text="Neuer Raum", command=self._add_room).pack(fill='x', pady=5)
        ttk.Button(left_panel, text="Verbindung löschen", command=self._delete_link).pack(fill='x', pady=5)
        ttk.Button(left_panel, text="Raum löschen", command=self._delete_room).pack(fill='x', pady=5)

        # --- CENTER (Canvas) ---
        self.canvas = tk.Canvas(self, bg="#202030", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Canvas Bindings
        self.canvas.bind("<ButtonPress-1>", self._on_canvas_click)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_drop)
        self.canvas.bind("<ButtonPress-3>", self._on_canvas_right_click) # Panning
        self.canvas.bind("<B3-Motion>", self._on_canvas_pan)
        self.canvas.bind("<MouseWheel>", self._on_zoom) # Windows Zoom
        self.canvas.bind("<Button-4>", self._on_zoom)   # Linux Zoom In
        self.canvas.bind("<Button-5>", self._on_zoom)   # Linux Zoom Out

        # --- RIGHT SIDEBAR (Properties) ---
        self.prop_panel = ttk.LabelFrame(self, text="Eigenschaften", padding=10, width=300)
        self.prop_panel.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Properties UI Elements (ID, Name, Desc, Z-Level)
        ttk.Label(self.prop_panel, text="ID:").grid(row=0, column=0, sticky='w')
        self.prop_id = ttk.Entry(self.prop_panel)
        self.prop_id.grid(row=0, column=1, sticky='ew')
        
        ttk.Label(self.prop_panel, text="Name:").grid(row=1, column=0, sticky='w')
        self.prop_name = ttk.Entry(self.prop_panel)
        self.prop_name.grid(row=1, column=1, sticky='ew')
        
        ttk.Label(self.prop_panel, text="Z-Level:").grid(row=2, column=0, sticky='w')
        self.prop_z = ttk.Entry(self.prop_panel) # Manuelles Ändern der Ebene eines Raums
        self.prop_z.grid(row=2, column=1, sticky='ew')

        ttk.Label(self.prop_panel, text="Beschreibung:").grid(row=3, column=0, sticky='w')
        self.prop_desc = tk.Text(self.prop_panel, height=10, width=30)
        self.prop_desc.grid(row=4, column=0, columnspan=2, pady=5)
        
        # Exits List
        ttk.Label(self.prop_panel, text="Ausgänge (Auto-generiert):").grid(row=5, column=0, columnspan=2, sticky='w', pady=(10,0))
        self.exits_list = tk.Listbox(self.prop_panel, height=6)
        self.exits_list.grid(row=6, column=0, columnspan=2, sticky='ew')

        ttk.Button(self.prop_panel, text="Änderungen Übernehmen", command=self._save_node_props).grid(row=7, column=0, columnspan=2, pady=10)

        # Tastatur Shortcuts für Layer
        self.bind("<Up>", lambda e: self._change_layer_rel(1))
        self.bind("<Down>", lambda e: self._change_layer_rel(-1))

    def _create_menu(self):
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Öffnen (JSON/PY)", command=self._load_file)
        file_menu.add_command(label="Speichern (JSON)", command=self._save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="Datei", menu=file_menu)
        
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Alles zeigen (Flatten)", command=self._toggle_flatten) # TODO
        menubar.add_cascade(label="Ansicht", menu=view_menu)
        
        self.config(menu=menubar)

    # --- LOGIC: Layer Management ---

    def _on_layer_change(self):
        try:
            val = int(self.layer_var.get())
            self.current_z_level = val
            self._redraw()
        except ValueError:
            pass
            
    def _change_layer_rel(self, delta):
        self.current_z_level += delta
        self.layer_var.set(str(self.current_z_level))
        self._redraw()

    # --- LOGIC: Data Handling ---

    def _load_file(self):
        path = filedialog.askopenfilename(filetypes=[("Narratrix Config", "*.json *.py")])
        if not path: return
        
        try:
            # Wir unterstützen primär JSON für den Editor.
            # Falls .py gewählt wird, müsste man es parsen (komplex), 
            # hier simulieren wir es oder erwarten JSON Struktur.
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.rooms = {}
            raw_rooms = data.get('rooms', {})
            
            # Auto-Layout wenn keine Koordinaten da sind (einfaches Grid)
            idx = 0
            for rid, rdata in raw_rooms.items():
                meta = rdata.get('_editor', {})
                x = meta.get('x', (idx % 5) * 150 + 100)
                y = meta.get('y', (idx // 5) * 150 + 100)
                z = meta.get('z', DEFAULT_Z) # Lade Z-Koordinate
                
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
        
        # Export Data Construction
        export_rooms = {}
        for rid, node in self.rooms.items():
            rdata = node['data'].copy()
            # Inject Editor Metadata
            rdata['_editor'] = {"x": node['x'], "y": node['y'], "z": node['z']}
            export_rooms[rid] = rdata
            
        final_data = {"rooms": export_rooms, "meta": {"generator": "Narratrix World Editor 2.0"}}
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Erfolg", "Welt gespeichert.")
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte nicht speichern: {e}")

    def _rebuild_links(self):
        self.links = []
        for rid, node in self.rooms.items():
            exits = node['data'].get('exits', {})
            for direction, target_id in exits.items():
                if target_id in self.rooms:
                    # Vermeide Duplikate (bidirektionale Links nur einmal zeichnen?)
                    # Wir speichern sie als gerichtete Kante
                    self.links.append((rid, target_id, direction))

    # --- LOGIC: Canvas Interaction ---

    def _add_room(self):
        # Generiere ID
        base_id = "room_"
        idx = 1
        while f"{base_id}{idx}" in self.rooms: idx += 1
        new_id = f"{base_id}{idx}"
        
        # Position zentriert im Viewport
        cx = (-self.offset_x + self.canvas.winfo_width() / 2) / self.scale
        cy = (-self.offset_y + self.canvas.winfo_height() / 2) / self.scale
        
        self.rooms[new_id] = {
            "data": {"name": "Neuer Raum", "desc": "Leer.", "exits": {}},
            "x": cx, "y": cy, "z": self.current_z_level # Neuer Raum auf aktueller Ebene
        }
        self._redraw()
        self._select_node(new_id)

    def _delete_room(self):
        if not self.selected_node: return
        del self.rooms[self.selected_node]
        # Links bereinigen
        self.selected_node = None
        self._rebuild_links()
        self._redraw()

    def _delete_link(self):
        pass # TODO: Implement Link selection logic first

    def _on_canvas_click(self, event):
        # Transform coords
        wx = (event.x - self.offset_x) / self.scale
        wy = (event.y - self.offset_y) / self.scale
        
        clicked_node = None
        for rid, node in self.rooms.items():
            # Nur klickbar, wenn auf aktueller Ebene (oder wir machen 'Ghost' Clicks möglich?)
            # Fokus auf aktuelle Ebene für Bearbeitung
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
        # Update offsets is tricky with scan_dragto internal logic, 
        # so we might implement manual pan if needed. Simple scan works for visuals.

    def _on_zoom(self, event):
        scale_factor = 1.1
        if event.num == 5 or event.delta < 0: scale_factor = 0.9
        
        self.scale *= scale_factor
        self._redraw()

    # --- LOGIC: Properties ---

    def _select_node(self, rid):
        self.selected_node = rid
        self._update_prop_panel()
        self._redraw()

    def _update_prop_panel(self):
        # Clear
        self.prop_id.delete(0, tk.END)
        self.prop_name.delete(0, tk.END)
        self.prop_z.delete(0, tk.END)
        self.prop_desc.delete("1.0", tk.END)
        self.exits_list.delete(0, tk.END)
        
        if not self.selected_node: return
        
        node = self.rooms[self.selected_node]
        rdata = node['data']
        
        self.prop_id.insert(0, self.selected_node)
        self.prop_name.insert(0, rdata.get('name', ''))
        self.prop_z.insert(0, str(node['z']))
        self.prop_desc.insert("1.0", rdata.get('desc', ''))
        
        for d, t in rdata.get('exits', {}).items():
            self.exits_list.insert(tk.END, f"{d} -> {t}")

    def _save_node_props(self):
        if not self.selected_node: return
        
        new_id = self.prop_id.get().strip()
        new_z = int(self.prop_z.get().strip())
        
        # ID Change handling
        if new_id != self.selected_node:
            if new_id in self.rooms:
                messagebox.showerror("Fehler", "ID existiert bereits!")
                return
            self.rooms[new_id] = self.rooms.pop(self.selected_node)
            self.selected_node = new_id
            
        node = self.rooms[self.selected_node]
        node['z'] = new_z
        node['data']['name'] = self.prop_name.get()
        node['data']['desc'] = self.prop_desc.get("1.0", tk.END).strip()
        
        self._redraw()

    # --- DRAWING ---

    def _redraw(self):
        self.canvas.delete("all")
        
        # Draw Grid
        w, h = 2000, 2000 # Virtual size
        # ... (Grid drawing skipped for brevity)

        # Draw Links first (so they are behind nodes)
        for start, end, direction in self.links:
            if start not in self.rooms or end not in self.rooms: continue
            
            n1 = self.rooms[start]
            n2 = self.rooms[end]
            
            # Layer Visibility Logic
            # Zeige Link nur, wenn BEIDE Nodes auf der aktuellen Ebene sind
            # ODER wenn einer auf der aktuellen Ebene ist und der andere auf einer benachbarten (Ghost Link)
            
            visible = False
            is_vertical = False
            
            if n1['z'] == self.current_z_level and n2['z'] == self.current_z_level:
                visible = True
            elif n1['z'] == self.current_z_level and n2['z'] != self.current_z_level:
                visible = True # Outgoing vertical
                is_vertical = True
            elif n2['z'] == self.current_z_level and n1['z'] != self.current_z_level:
                visible = True # Incoming vertical (optional to draw)
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
                col = "#AA55AA" # Lila für vertikale Verbindungen
                dash = (4, 2)
                # Wenn Ziel nicht auf Ebene ist, zeichnen wir nur einen "Stummel" oder zum echten Punkt (Ghost)?
                # Wir zeichnen zum echten Punkt, aber der Ziel-Node wird evtl. ausgegraut gezeichnet.
            
            self.canvas.create_line(x1, y1, x2, y2, fill=col, width=width, arrow=tk.LAST, dash=dash)
            
            # Label für Richtung
            mx, my = (x1+x2)/2, (y1+y2)/2
            self.canvas.create_text(mx, my, text=direction, fill="#AAAAAA", font=("Arial", 8))

        # Draw Nodes
        for rid, node in self.rooms.items():
            # Visibility:
            # - Full opacity: Current Z
            # - Ghost opacity: Z+1 or Z-1 (reference)
            # - Hidden: Others
            
            z_diff = node['z'] - self.current_z_level
            
            if z_diff == 0:
                fill_col = "#4444AA"
                outline_col = "#FFFFFF"
                alpha = 1.0
            elif abs(z_diff) == 1:
                fill_col = "#222222" # Darker background
                outline_col = "#555555" # Dim outline
                alpha = 0.3 # Simulated via color choice mostly in Tkinter
            else:
                continue # Hide others
                
            if rid == self.selected_node:
                fill_col = "#AA4444"
            
            cx = node['x'] * self.scale + self.offset_x
            cy = node['y'] * self.scale + self.offset_y
            r = NODE_RADIUS * self.scale
            
            # Node Circle
            self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill=fill_col, outline=outline_col, width=2)
            
            # Text
            text_col = "#FFFFFF" if z_diff == 0 else "#666666"
            self.canvas.create_text(cx, cy, text=node['data'].get('name', '???'), fill=text_col, font=("Arial", int(10*self.scale), "bold"))
            self.canvas.create_text(cx, cy+r+10, text=rid, fill="#888888", font=("Arial", int(8*self.scale)))
            
            # Z-Indicator if ghost
            if z_diff != 0:
                 indicator = "▲" if z_diff > 0 else "▼"
                 self.canvas.create_text(cx, cy-r-10, text=indicator, fill="#AA55AA", font=("Arial", int(12*self.scale)))


if __name__ == "__main__":
    app = WorldEditor()
    app.mainloop()