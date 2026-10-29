from __future__ import annotations

import random
from typing import TypeVar

T = TypeVar("T")


def pick(collection: list[T] | None) -> T | None:
    """Wählt ein zufälliges Element aus einer Liste."""
    if not collection:
        return None
    if isinstance(collection, list):
        return random.choice(collection)
    return None


def chance(percent: float) -> bool:
    """Gibt True zurück mit einer Wahrscheinlichkeit von percent%."""
    return random.randint(1, 100) <= percent
