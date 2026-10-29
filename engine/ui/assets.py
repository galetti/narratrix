from __future__ import annotations

import logging
from pathlib import Path

try:
    import pygame
except ImportError:  # Allow headless imports without pygame installed.
    pygame = None  # type: ignore[assignment]

from engine.ui.config import PROJECT_ROOT

logger = logging.getLogger(__name__)


class AssetLoader:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.cache: dict[str, pygame.Surface | None] = {}
        self.base_path: Path = base_dir or (PROJECT_ROOT / "data" / "assets" / "images")
        self.base_path.mkdir(parents=True, exist_ok=True)

    def get_image(self, img_id: str | None) -> pygame.Surface | None:
        if not img_id or pygame is None:
            return None
        if img_id in self.cache:
            return self.cache[img_id]

        found_path: Path | None = None
        for ext in (".png", ".jpg", ".jpeg"):
            candidate = self.base_path / f"{img_id}{ext}"
            if candidate.exists():
                found_path = candidate
                break

        if found_path:
            try:
                img = pygame.image.load(str(found_path)).convert_alpha()
                self.cache[img_id] = img
                return img
            except (pygame.error, OSError) as exc:
                logger.error("Fehler beim Laden von '%s': %s", img_id, exc)

        self.cache[img_id] = None
        return None
