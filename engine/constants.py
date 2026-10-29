# narratrix_engine/engine/constants.py
from __future__ import annotations

# Objekt-Zustände
STATE_NORMAL: str = "normal"
STATE_SABOTAGED: str = "sabotaged"
STATE_BROKEN: str = "broken"

# Objekt-Typen
TYPE_CONTAINER: str = "container"
TYPE_SURFACE: str = "surface"
TYPE_ITEM: str = "item"
TYPE_SCENERY: str = "scenery"
TYPE_FIXTURE: str = "fixture" # Fest installierte, interaktive Objekte (Maschinen etc.)

# Aggregatzustände
MATTER_SOLID: str = "solid"
MATTER_LIQUID: str = "liquid"
MATTER_GAS: str = "gas"

# Orte
LOC_INVENTORY: str = "inventory"
LOC_VOID: str = "void" # Aus dem Spiel entfernt

# Attribute
ATTR_WEIGHT: str = "weight"
ATTR_ALIASES: str = "aliases"
ATTR_DESC: str = "desc"
ATTR_ID: str = "id"
ATTR_NAME: str = "name"
ATTR_TEMP: str = "temp"
ATTR_MATTER: str = "matter"
ATTR_CLIMBABLE: str = "climbable" # NEU: Ist das Objekt bekletterbar?

# Filter für Resolver
FILTER_ROOM: str = "room"
FILTER_INVENTORY: str = "inventory"
FILTER_RECURSIVE: str = "recursive_room"

# Akustik (Durchlässigkeit 0.0 bis 1.0)
ACOUSTIC_OPEN_AIR: float = 0.9      # Durchlässigkeit offener Durchgang (Luft dämpft etwas)
ACOUSTIC_OPEN_DOOR: float = 0.9     # Offene Tür
ACOUSTIC_CLOSED_DOOR: float = 0.2   # Geschlossene Standard-Tür
ACOUSTIC_THIN_WALL: float = 0.1     # Dünne Wand
ACOUSTIC_SOLID_WALL: float = 0.0    # Massive Wand
ACOUSTIC_SOUNDPROOF: float = 0.0    # Schallschutz
