from __future__ import annotations

from typing import Any

MODULE_CONFIG: dict[str, Any] = {
    "id": "deep_zero",
    "title": "Deep Zero (Sci-Fi Adventure)",
    "description": "Dreiteilige Sci-Fi-Kampagne auf der Forschungsstation Deep Zero.",
    "start_chapter": "data.modules.deep_zero.chapters.ep1_deep_zero.config",
    "chapters": [
        "data.modules.deep_zero.chapters.ep1_deep_zero.config",
        "data.modules.deep_zero.chapters.ep2_habitat_sector.config",
        "data.modules.deep_zero.chapters.ep3_reactor_core.config",
    ],
    "theme": "deep_zero",
    "common_module": "data.modules.deep_zero.common.config",
    "asset_dir": "data/modules/deep_zero/assets/images",
}
