# Objekt-Zustände
STATE_NORMAL = "normal"
STATE_SABOTAGED = "sabotaged"
STATE_BROKEN = "broken"

# Objekt-Typen
TYPE_CONTAINER = "container"
TYPE_SURFACE = "surface"
TYPE_ITEM = "item"
TYPE_SCENERY = "scenery"

# Aggregatzustände (NEU)
MATTER_SOLID = "solid"
MATTER_LIQUID = "liquid"
MATTER_GAS = "gas"

# Orte
LOC_INVENTORY = "inventory"
LOC_VOID = "void" # Aus dem Spiel entfernt

# Attribute
ATTR_AFFINITY = "affinity"
ATTR_MOVABLE = "movable"
ATTR_ALIASES = "aliases"
ATTR_DESC = "desc"
ATTR_ID = "id"
ATTR_NAME = "name"
ATTR_TEMP = "temp" # Temperatur in Grad Celsius (NEU)
ATTR_MATTER = "matter" # Fest/Flüssig (NEU)

# Dialog & AI
AI_CHANCE_MOVE = 20
AI_CHANCE_STAY = 80

# Filter für Resolver
FILTER_ROOM = "room"
FILTER_INVENTORY = "inventory"
FILTER_RECURSIVE = "recursive_room"