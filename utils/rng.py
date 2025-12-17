import random

def pick(collection):
    """Wählt ein zufälliges Element aus einer Liste."""
    if not collection:
        return None
    if isinstance(collection, list):
        return random.choice(collection)
    return None

def chance(percent):
    """Gibt True zurück mit einer Wahrscheinlichkeit von percent%."""
    return random.randint(1, 100) <= percent