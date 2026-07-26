# narratrix_engine/engine/constants.py

# Objekt-Zustände
STATE_NORMAL = "normal"
STATE_SABOTAGED = "sabotaged"
STATE_BROKEN = "broken"

# Objekt-Typen
TYPE_CONTAINER = "container"
TYPE_SURFACE = "surface"
TYPE_ITEM = "item"
TYPE_SCENERY = "scenery"
TYPE_FIXTURE = "fixture" # Fest installierte, interaktive Objekte (Maschinen etc.)

# Aggregatzustände
MATTER_SOLID = "solid"
MATTER_LIQUID = "liquid"
MATTER_GAS = "gas"

# Orte
LOC_INVENTORY = "inventory"
LOC_VOID = "void" # Aus dem Spiel entfernt

# Attribute
ATTR_WEIGHT = "weight"
ATTR_ALIASES = "aliases"
ATTR_DESC = "desc"
ATTR_ID = "id"
ATTR_NAME = "name"
ATTR_TEMP = "temp"
ATTR_MATTER = "matter"
ATTR_CLIMBABLE = "climbable" # NEU: Ist das Objekt bekletterbar?

# Filter für Resolver
FILTER_ROOM = "room"
FILTER_INVENTORY = "inventory"
FILTER_RECURSIVE = "recursive_room"

# Akustik (Durchlässigkeit 0.0 bis 1.0)
ACOUSTIC_OPEN_AIR = 0.9      # Durchlässigkeit offener Durchgang (Luft dämpft etwas)
ACOUSTIC_OPEN_DOOR = 0.9     # Offene Tür
ACOUSTIC_CLOSED_DOOR = 0.2   # Geschlossene Standard-Tür
ACOUSTIC_THIN_WALL = 0.1     # Dünne Wand
ACOUSTIC_SOLID_WALL = 0.0    # Massive Wand
ACOUSTIC_SOUNDPROOF = 0.0    # Schallschutz
