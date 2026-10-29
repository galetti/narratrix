from __future__ import annotations

import re
from typing import TYPE_CHECKING, TypedDict

import engine.theme as theme
from engine.theme import ColorTuple

if TYPE_CHECKING:
    import pygame


class TextSegment(TypedDict):
    text: str
    color: ColorTuple
    width: int
    raw: str


class RichTextRenderer:
    def __init__(self, font: pygame.font.Font, default_color: ColorTuple) -> None:
        self.font: pygame.font.Font = font
        self.default_color: ColorTuple = default_color
        self.color_map: dict[str, ColorTuple] = {
            "alert": theme.COLOR_ALERT,
            "alarm": theme.COLOR_ALERT,
            "success": theme.COLOR_ACCENT,
            "accent": theme.COLOR_ACCENT,
            "info": theme.COLOR_INFO,
            "cmd": (255, 255, 255),
            "user": theme.COLOR_USER_ECHO,
            "char": (100, 200, 255),
            "story": (220, 220, 220),
            "yellow": (255, 200, 50),
            "red": (255, 80, 80),
            "blue": (100, 200, 255),
            "header": (255, 255, 100),
        }
        self.tag_pattern: re.Pattern[str] = re.compile(r"(<[/a-zA-Z0-9]+>)")

    def parse_and_wrap(
        self, text: str, max_width: int, base_color: ColorTuple | None = None
    ) -> list[list[TextSegment]]:
        if base_color is None:
            base_color = self.default_color

        raw_lines = text.split("\n")
        all_wrapped_lines: list[list[TextSegment]] = []

        for raw_line in raw_lines:
            if not raw_line:
                all_wrapped_lines.append(
                    [{"text": " ", "color": base_color, "width": 0, "raw": ""}]
                )
                continue

            parts = self.tag_pattern.split(raw_line)
            segments: list[TextSegment] = []
            color_stack: list[ColorTuple] = [base_color]

            for part in parts:
                if not part:
                    continue

                if part.startswith("<") and part.endswith(">"):
                    tag_content = part[1:-1]
                    if tag_content.startswith("/"):
                        if len(color_stack) > 1:
                            color_stack.pop()
                    elif tag_content in self.color_map:
                        color_stack.append(self.color_map[tag_content])
                    continue

                words = part.split(" ")
                current_col = color_stack[-1]

                for i, w in enumerate(words):
                    if w:
                        w_width = self.font.size(w)[0]
                        segments.append(
                            {"text": w, "color": current_col, "width": w_width, "raw": w}
                        )
                    elif i < len(words) - 1:
                        sp_w = self.font.size(" ")[0]
                        segments.append(
                            {"text": " ", "color": current_col, "width": sp_w, "raw": ""}
                        )

            current_line: list[tuple[TextSegment, int]] = []
            current_width = 0
            space_width = self.font.size(" ")[0]

            for seg in segments:
                seg_w = seg["width"]
                needs_space = False
                add_width = seg_w

                if current_line and seg["text"] != " " and current_line[-1][0]["text"] != " ":
                    needs_space = True
                    add_width += space_width

                if current_width + add_width <= max_width:
                    if needs_space:
                        space_dict: TextSegment = {
                            "text": " ",
                            "color": seg["color"],
                            "width": space_width,
                            "raw": " ",
                        }
                        current_line.append((space_dict, space_width))
                        current_width += space_width

                    current_line.append((seg, seg_w))
                    current_width += seg_w
                else:
                    all_wrapped_lines.append([s[0] for s in current_line])
                    current_line = [(seg, seg_w)]
                    current_width = seg_w

            if current_line:
                all_wrapped_lines.append([s[0] for s in current_line])

        return all_wrapped_lines
