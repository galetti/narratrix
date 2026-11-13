from __future__ import annotations

import logging
from pathlib import Path

try:
    import pygame
except ImportError:  # Allow headless imports without pygame installed.
    pygame = None  # type: ignore[assignment]

from engine.ui.config import PROJECT_ROOT

logger = logging.getLogger(__name__)


def _resolve_asset_dir(base_dir: Path | str | None) -> Path:
    if base_dir is None:
        return PROJECT_ROOT / "data" / "assets" / "images"
    candidate = Path(base_dir)
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate


class AssetLoader:
    def __init__(
        self,
        base_dir: Path | str | None = None,
        fallback_dir: Path | str | None = None,
    ) -> None:
        self.cache: dict[str, pygame.Surface | None] = {}
        self.base_path: Path = _resolve_asset_dir(base_dir)
        self.fallback_path: Path | None = (
            _resolve_asset_dir(fallback_dir) if fallback_dir is not None else None
        )
        if base_dir is not None:
            self.base_path.mkdir(parents=True, exist_ok=True)

    def set_base_dir(self, base_dir: Path | str | None) -> None:
        """Switch the active module/chapter image directory and clear the image cache."""

        resolved = _resolve_asset_dir(base_dir)
        if resolved != self.base_path:
            self.base_path = resolved
            self.cache.clear()
        if base_dir is not None:
            self.base_path.mkdir(parents=True, exist_ok=True)

    def _find_image_path(self, img_id: str) -> Path | None:
        search_dirs = [self.base_path]
        if self.fallback_path is not None and self.fallback_path != self.base_path:
            search_dirs.append(self.fallback_path)

        for directory in search_dirs:
            if not directory.exists():
                continue
            for ext in (".png", ".jpg", ".jpeg"):
                candidate = directory / f"{img_id}{ext}"
                if candidate.exists():
                    return candidate
        return None

    def get_image(self, img_id: str | None) -> pygame.Surface | None:
        if not img_id or pygame is None:
            return None
        if img_id in self.cache:
            return self.cache[img_id]

        found_path = self._find_image_path(img_id)
        if found_path:
            try:
                img = pygame.image.load(str(found_path)).convert_alpha()
                self.cache[img_id] = img
                return img
            except (pygame.error, OSError) as exc:
                logger.error("Fehler beim Laden von '%s': %s", img_id, exc)

        self.cache[img_id] = None
        return None
