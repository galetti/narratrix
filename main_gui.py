# narratrix_engine/main_gui.py
from __future__ import annotations

import copy
import logging
import math
import queue
import sys
import threading
from typing import Any
import warnings

import pygame
import pygame.scrap

warnings.filterwarnings("ignore", category=UserWarning, module="pygame")

from engine.action_dispatcher import ActionDispatcher
from engine.constants import LOC_INVENTORY
from engine.game_state import GameState
from engine.parser.rule_based import RuleBasedParser
from engine.parser.spacy_parser import SpacyParser
from engine.schema import GameSnapshot, ObjectData
from engine.story_loader import StoryLoader
import engine.theme as theme
from engine.ui import (
    AssetLoader,
    RichTextRenderer,
    TextSegment,
    copy_to_clipboard,
    load_system_config,
)

logger = logging.getLogger(__name__)

SYS_CONFIG: dict[str, dict[str, Any]] = load_system_config()
INIT_WIDTH: int = int(SYS_CONFIG["system"].get("resolution_width", 1024))
INIT_HEIGHT: int = int(SYS_CONFIG["system"].get("resolution_height", 768))
PARSER_MODE: str = str(SYS_CONFIG["system"].get("parser_mode", "SPACY")).upper()


class GameGUI:
    def __init__(self) -> None:
        pygame.init()
        display_flags = pygame.RESIZABLE
        if SYS_CONFIG["system"].get("fullscreen", False):
            display_flags |= pygame.FULLSCREEN
        self.screen: pygame.Surface = pygame.display.set_mode(
            (INIT_WIDTH, INIT_HEIGHT), display_flags
        )
        pygame.display.set_caption(f"{SYS_CONFIG['game'].get('title', 'Narratrix')} v6.0")

        try:
            pygame.scrap.init()
        except pygame.error as exc:
            logger.warning("Clipboard konnte nicht initialisiert werden: %s", exc)

        self.clock: pygame.time.Clock = pygame.time.Clock()

        try:
            self.font_log: pygame.font.Font = pygame.font.SysFont(
                "Consolas", theme.FONT_SIZE_LOG
            )
            self.font_header: pygame.font.Font = pygame.font.SysFont(
                "Verdana", theme.FONT_SIZE_HEADER, bold=True
            )
            self.font_big: pygame.font.Font = pygame.font.SysFont(
                "Verdana", theme.FONT_SIZE_GAME_OVER, bold=True
            )
            self.font_med: pygame.font.Font = pygame.font.SysFont("Arial", 24)
            self.font_sensor: pygame.font.Font = pygame.font.SysFont("Consolas", 14)
        except (pygame.error, OSError):
            logger.warning("Systemfonts nicht gefunden, nutze Fallback.")
            self.font_log = pygame.font.SysFont("Arial", theme.FONT_SIZE_LOG)
            self.font_header = pygame.font.SysFont("Arial", theme.FONT_SIZE_HEADER)
            self.font_big = pygame.font.SysFont("Arial", theme.FONT_SIZE_GAME_OVER)
            self.font_med = pygame.font.SysFont("Arial", 24)
            self.font_sensor = pygame.font.SysFont("Arial", 12)

        self.renderer: RichTextRenderer = RichTextRenderer(
            self.font_log, theme.COLOR_TEXT
        )
        self.assets: AssetLoader = AssetLoader()

        self.result_queue: queue.Queue[str] = queue.Queue()

        self.current_chapter: str = str(
            SYS_CONFIG["game"].get("start_chapter", "data.chapters.ep1_deep_zero.config")
        )
        logger.info("Starte mit Kapitel: %s", self.current_chapter)
        self.load_game_chapter(self.current_chapter)

        self.show_all_logs_in_main: bool = False

    def load_game_chapter(
        self, chapter_path: str, transfer_state: dict[str, Any] | None = None
    ) -> None:
        new_config = StoryLoader.load_chapter(chapter_path)

        if not new_config:
            logger.critical("Konnte Kapitel '%s' nicht laden!", chapter_path)
            sys.exit(1)

        new_config["use_llm_dialogue"] = bool(
            SYS_CONFIG["system"].get("llm_enabled", False)
        )
        new_config["llm_url"] = SYS_CONFIG["system"].get("llm_url")
        new_config["llm_model"] = SYS_CONFIG["system"].get("llm_model")
        self.game: GameState = GameState(new_config)
        self.current_chapter = chapter_path

        if transfer_state:
            self.game.knowledge = set(transfer_state.get("knowledge", set()))
            self.game.time = transfer_state.get("time", self.game.time)
            self.game.stability = transfer_state.get("stability", self.game.stability)
            for old_item in transfer_state.get("inventory_objects", []):
                item_id = old_item["id"]
                self.game.objects[item_id] = copy.deepcopy(old_item)

        self.user_text: str = ""
        self.cursor_pos: int = 0
        self.cursor_blink: int = 0
        self.is_processing: bool = False
        self.history: list[str] = []
        self.history_index: int = 0
        self.scroll_offset: float = 0
        self.line_height: int = theme.FONT_SIZE_LOG + 4

        self.parser: RuleBasedParser | SpacyParser
        if PARSER_MODE == "SPACY":
            spacy_parser = SpacyParser(self.game)
            self.parser = (
                spacy_parser if spacy_parser.available else RuleBasedParser(self.game)
            )
        else:
            self.parser = RuleBasedParser(self.game)

        self.submit_command("look", echo=False)

    def restart_game(self) -> None:
        self.current_chapter = str(
            SYS_CONFIG["game"].get("start_chapter", "data.chapters.ep1_deep_zero.config")
        )
        self.load_game_chapter(self.current_chapter)

    def run(self) -> None:
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(30)

    def handle_events(self) -> None:
        try:
            while not self.result_queue.empty():
                msg = self.result_queue.get_nowait()
                if msg == "DONE":
                    self.is_processing = False
        except queue.Empty:
            pass

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode(
                    (event.w, event.h), pygame.RESIZABLE
                )

            if self.game.game_over:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_SPACE, pygame.K_r):
                        self.restart_game()
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    self.scroll_offset += theme.SCROLL_SPEED_MOUSE
                elif event.button == 5:
                    self.scroll_offset = max(
                        0.0, self.scroll_offset - theme.SCROLL_SPEED_MOUSE
                    )

            elif event.type == pygame.KEYDOWN:
                if self.is_processing:
                    continue

                if event.key == pygame.K_PAGEUP:
                    self.scroll_offset += theme.SCROLL_SPEED_KEY
                elif event.key == pygame.K_PAGEDOWN:
                    self.scroll_offset = max(
                        0.0, self.scroll_offset - theme.SCROLL_SPEED_KEY
                    )
                elif event.key == pygame.K_c and (
                    pygame.key.get_mods() & pygame.KMOD_CTRL
                ):
                    snapshot = self.game.get_logs()
                    text_dump = "\n".join(
                        f"{entry['type']}: {entry['text']}" for entry in snapshot
                    )
                    copy_to_clipboard(text_dump)
                    continue
                elif event.key == pygame.K_F1:
                    self.show_all_logs_in_main = not self.show_all_logs_in_main
                    logger.debug("Show all logs = %s", self.show_all_logs_in_main)
                elif event.key == pygame.K_LEFT:
                    self.cursor_pos = max(0, self.cursor_pos - 1)
                    self.cursor_blink = 0
                elif event.key == pygame.K_RIGHT:
                    self.cursor_pos = min(len(self.user_text), self.cursor_pos + 1)
                    self.cursor_blink = 0
                elif event.key == pygame.K_HOME:
                    self.cursor_pos = 0
                elif event.key == pygame.K_END:
                    self.cursor_pos = len(self.user_text)
                elif event.key == pygame.K_RETURN:
                    if self.user_text.strip():
                        cmd = self.user_text
                        self.history.append(cmd)
                        self.history_index = len(self.history)
                        self.user_text = ""
                        self.cursor_pos = 0
                        self.scroll_offset = 0
                        self.submit_command(cmd)
                elif event.key == pygame.K_UP:
                    if self.history:
                        self.history_index = max(0, self.history_index - 1)
                        self.user_text = self.history[self.history_index]
                        self.cursor_pos = len(self.user_text)
                elif event.key == pygame.K_DOWN:
                    if self.history:
                        self.history_index = min(
                            len(self.history), self.history_index + 1
                        )
                        self.user_text = (
                            self.history[self.history_index]
                            if self.history_index < len(self.history)
                            else ""
                        )
                        self.cursor_pos = len(self.user_text)
                elif event.key == pygame.K_BACKSPACE:
                    if self.cursor_pos > 0:
                        self.user_text = (
                            self.user_text[: self.cursor_pos - 1]
                            + self.user_text[self.cursor_pos :]
                        )
                        self.cursor_pos -= 1
                elif event.key == pygame.K_DELETE:
                    if self.cursor_pos < len(self.user_text):
                        self.user_text = (
                            self.user_text[: self.cursor_pos]
                            + self.user_text[self.cursor_pos + 1 :]
                        )
                elif (
                    len(self.user_text) < 120
                    and event.unicode
                    and event.key != pygame.K_TAB
                ):
                    self.user_text = (
                        self.user_text[: self.cursor_pos]
                        + event.unicode
                        + self.user_text[self.cursor_pos :]
                    )
                    self.cursor_pos += 1

    def submit_command(self, text: str, echo: bool = True) -> None:
        self.is_processing = True
        if echo:
            self.game.log("user", f"> {text}")

        def worker() -> None:
            try:
                if self.game.dialogue_active:
                    ActionDispatcher.dialogue_step(self.game, text)
                elif self.game.disambiguation:
                    ActionDispatcher.dispatch(self.game, "disambiguate", [text])
                else:
                    self.parser.parse(text)
            except (KeyError, ValueError, TypeError, RuntimeError) as exc:
                logger.exception("Worker Thread Exception: %s", exc)
                self.game.log("error", f"Systemfehler: {exc}")
            finally:
                self.result_queue.put("DONE")

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def update(self) -> None:
        self.cursor_blink += 1

        if self.game.pending_chapter_load and not self.is_processing:
            target_chapter = self.game.pending_chapter_load
            logger.info("Wechsle zu Kapitel: %s", target_chapter)

            transfer_state = {
                "knowledge": set(self.game.knowledge),
                "time": self.game.time,
                "stability": self.game.stability,
                "inventory_objects": self._collect_inventory_objects(),
            }
            self.load_game_chapter(target_chapter, transfer_state)

    def _collect_inventory_objects(self) -> list[ObjectData]:
        held: list[ObjectData] = []
        for obj in self.game.objects.values():
            location = obj.get("location")
            visited: set[str] = set()
            while location in self.game.objects and location not in visited:
                visited.add(location)
                location = self.game.objects[location].get("location")
            if location == LOC_INVENTORY:
                held.append(copy.deepcopy(obj))
        return held

    def draw(self) -> None:
        snapshot = self.game.get_snapshot()
        self.screen.fill(theme.COLOR_BG)
        w, h = self.screen.get_size()

        if snapshot["game_over"]:
            self.draw_game_over(w, h, snapshot)
            pygame.display.flip()
            return

        scene_height = int(h * theme.SCENE_HEIGHT_RATIO)
        input_height = theme.INPUT_HEIGHT
        log_height = h - scene_height - input_height
        rect_scene = pygame.Rect(0, 0, w, scene_height)
        rect_log = pygame.Rect(0, scene_height, w, log_height)
        rect_input = pygame.Rect(0, h - input_height, w, input_height)

        self.draw_scene_area(rect_scene, snapshot)
        self.draw_log_area(rect_log, snapshot)
        self.draw_input_area(rect_input, snapshot)

        border_col = (
            theme.COLOR_DIALOGUE_BORDER
            if snapshot["dialogue_active"]
            else theme.COLOR_UI_BORDER
        )
        pygame.draw.line(self.screen, border_col, (0, scene_height), (w, scene_height), 2)
        pygame.draw.line(
            self.screen, border_col, (0, h - input_height), (w, h - input_height), 2
        )

        if self.is_processing:
            self.draw_loading_spinner(w, h, snapshot)
        pygame.display.flip()

    def draw_game_over(self, w: int, h: int, snap: GameSnapshot) -> None:
        pulse = abs(math.sin(self.cursor_blink * 0.05)) * 50
        base_r, base_g, base_b = theme.COLOR_GAME_OVER_BG
        bg_col = (min(255, base_r + int(pulse)), base_g, base_b)
        self.screen.fill(bg_col)

        text_go = self.font_big.render("GAME OVER", True, theme.COLOR_GAME_OVER_TEXT)
        go_rect = text_go.get_rect(center=(w // 2, h // 3))
        self.screen.blit(text_go, go_rect)

        last_logs = [entry["text"] for entry in snap["logs"] if entry["type"] == "alarm"]
        death_msg = last_logs[-1] if last_logs else "Signal verloren."

        text_death = self.font_med.render(death_msg, True, (255, 200, 200))
        death_rect = text_death.get_rect(center=(w // 2, h // 2))
        self.screen.blit(text_death, death_rect)

        if (self.cursor_blink // 20) % 2 == 0:
            text_restart = self.font_med.render(
                "Drücke [LEERTASTE] für Neustart", True, theme.COLOR_GAME_OVER_TEXT
            )
            res_rect = text_restart.get_rect(center=(w // 2, h // 2 + 100))
            self.screen.blit(text_restart, res_rect)

    def draw_scene_area(self, rect: pygame.Rect, snap: GameSnapshot) -> None:
        bg_color = (20, 20, 30)
        if snap["stability"] < 50 and (self.cursor_blink // 15) % 2 == 0:
            bg_color = (40, 20, 20)
        pygame.draw.rect(self.screen, bg_color, rect)

        header_text = (
            snap["dialogue_header"]
            if snap["dialogue_active"]
            else snap["room_name"].upper()
        )
        header_col = (
            theme.COLOR_DIALOGUE_BORDER
            if snap["dialogue_active"]
            else theme.COLOR_ACCENT
        )

        text_room = self.font_header.render(header_text, True, header_col)
        self.screen.blit(text_room, (20, 20))

        surf_time = self.font_log.render(
            f"ZEIT: T+{snap['time']}m", True, theme.COLOR_TEXT
        )
        self.screen.blit(surf_time, (20, 70))

        max_h = rect.height - 40
        max_w = int(rect.width * 0.4)
        area_x = rect.width - max_w - 20

        placeholder_w = min(max_w, int(max_h * 1.33))
        placeholder_h = int(placeholder_w / 1.33)
        default_rect = pygame.Rect(
            rect.width - placeholder_w - 20, 20, placeholder_w, placeholder_h
        )

        room_img = self.assets.get_image(snap["room_img"])
        dialogue_img = (
            self.assets.get_image(snap["dialogue_img"])
            if snap["dialogue_active"]
            else None
        )

        final_visual_rect = default_rect

        def get_scaled_rect_and_surf(
            img: pygame.Surface, limit_w: int, limit_h: int
        ) -> tuple[pygame.Rect, pygame.Surface]:
            o_w, o_h = img.get_size()
            aspect = o_w / o_h
            t_h = limit_h
            t_w = int(t_h * aspect)
            if t_w > limit_w:
                t_w = limit_w
                t_h = int(t_w / aspect)
            return pygame.Rect(0, 0, t_w, t_h), pygame.transform.smoothscale(
                img, (t_w, t_h)
            )

        if room_img:
            r_rect, r_surf = get_scaled_rect_and_surf(room_img, max_w, max_h)
            draw_x = area_x + (max_w - r_rect.width) // 2
            draw_y = 20 + (max_h - r_rect.height) // 2
            bg_pos = (draw_x, draw_y)
            final_visual_rect = pygame.Rect(draw_x, draw_y, r_rect.width, r_rect.height)

            if snap["dialogue_active"]:
                pixel_scale = 8
                px_w = max(1, r_surf.get_width() // pixel_scale)
                px_h = max(1, r_surf.get_height() // pixel_scale)
                small = pygame.transform.scale(r_surf, (px_w, px_h))
                pixelated = pygame.transform.scale(small, r_surf.get_size())
                dark_overlay = pygame.Surface(pixelated.get_size()).convert_alpha()
                dark_overlay.fill((0, 0, 0, 160))
                pixelated.blit(dark_overlay, (0, 0))
                bg_surf_to_draw = pixelated
            else:
                bg_surf_to_draw = r_surf
            self.screen.blit(bg_surf_to_draw, bg_pos)
        else:
            pygame.draw.rect(self.screen, (20, 20, 20), default_rect)
            if not snap["dialogue_active"]:
                label_text = f"IMG: {snap['room_img']}"
                label_surf = self.font_log.render(label_text, True, (80, 80, 80))
                label_rect = label_surf.get_rect(center=final_visual_rect.center)
                self.screen.blit(label_surf, label_rect)

        if snap["dialogue_active"] and dialogue_img:
            c_rect, c_surf = get_scaled_rect_and_surf(dialogue_img, max_w, max_h)
            p_draw_x = final_visual_rect.x + (final_visual_rect.width - c_rect.width) // 2
            p_draw_y = (
                final_visual_rect.y + (final_visual_rect.height - c_rect.height) // 2
            )
            self.screen.blit(c_surf, (p_draw_x, p_draw_y))

        border_col = (
            theme.COLOR_DIALOGUE_BORDER
            if snap["dialogue_active"]
            else theme.COLOR_UI_BORDER
        )
        pygame.draw.rect(self.screen, border_col, final_visual_rect, 2)

        # --- SENSOR HUD (Oben Links) ---
        sensor_x = 20
        sensor_y = 110

        hud_logs = []
        for entry in reversed(snap["logs"]):
            if entry["type"] in ("event", "character"):
                if "---" in entry["text"] or entry["text"].startswith("Personen:"):
                    continue
                hud_logs.append(entry)
            if len(hud_logs) >= 5:
                break

        present_npcs = snap.get("present_npcs", [])
        if present_npcs:
            lbl = self.font_sensor.render("SCAN: LEBENSFORMEN", True, (100, 255, 100))
            self.screen.blit(lbl, (sensor_x, sensor_y))
            sensor_y += 20

            for person in present_npcs:
                surf = self.font_sensor.render(f" [!] {person}", True, (150, 255, 150))
                self.screen.blit(surf, (sensor_x, sensor_y))
                sensor_y += 18
            sensor_y += 10

        pygame.draw.line(
            self.screen, (50, 50, 60), (sensor_x, sensor_y), (sensor_x + 200, sensor_y), 1
        )
        sensor_y += 10

        lbl = self.font_sensor.render("SENSOR LOG:", True, (100, 150, 200))
        self.screen.blit(lbl, (sensor_x, sensor_y))
        sensor_y += 20

        for i, log in enumerate(hud_logs):
            if i == 0:
                brightness = 255
            elif i == 1:
                brightness = 200
            elif i == 2:
                brightness = 150
            else:
                brightness = 100

            base_col = (brightness, brightness, brightness)
            if log["type"] == "event":
                base_col = (brightness, int(brightness * 0.8), 50)
            elif log["type"] == "character":
                base_col = (int(brightness * 0.4), int(brightness * 0.8), brightness)

            txt = log["text"]
            if len(txt) > 55:
                txt = txt[:52] + "..."

            surf = self.font_sensor.render(f"> {txt}", True, base_col)
            self.screen.blit(surf, (sensor_x, sensor_y))
            sensor_y += 18

    def draw_log_area(self, rect: pygame.Rect, snap: GameSnapshot) -> None:
        padding_x = theme.PADDING
        padding_y = theme.PADDING
        max_text_width = rect.width - (padding_x * 2)

        render_rows: list[list[TextSegment]] = []

        log_colors: dict[str, theme.ColorTuple] = {
            "user": theme.COLOR_USER_ECHO,
            "error": (255, 80, 80),
            "success": theme.COLOR_ACCENT,
            "event": (255, 200, 50),
            "alarm": theme.COLOR_ALERT,
            "location": theme.COLOR_ACCENT,
            "character": (100, 200, 255),
            "story": (220, 220, 220),
            "info": theme.COLOR_INFO,
        }

        for log in snap["logs"]:
            base_color = log_colors.get(log["type"], theme.COLOR_TEXT)
            wrapped_lines = self.renderer.parse_and_wrap(
                str(log["text"]), max_text_width, base_color
            )
            render_rows.extend(wrapped_lines)

        total_content_height = len(render_rows) * self.line_height
        visible_height = rect.height - (2 * padding_y)
        max_scroll = max(0, total_content_height - visible_height)

        self.scroll_offset = min(max(0.0, self.scroll_offset), float(max_scroll))

        bottom_draw_y = (
            rect.bottom - padding_y - self.line_height + self.scroll_offset
        )
        current_y = bottom_draw_y

        for row in reversed(render_rows):
            if current_y + self.line_height > rect.top and current_y < rect.bottom:
                current_x = rect.x + padding_x
                for segment in row:
                    text_surf = self.font_log.render(
                        segment["text"], True, segment["color"]
                    )
                    self.screen.blit(text_surf, (current_x, current_y))
                    current_x += segment["width"]

            current_y -= self.line_height
            if current_y < rect.top - 50:
                break

        if max_scroll > 0:
            scroll_ratio = self.scroll_offset / max_scroll
            bar_height = max(
                20.0, (visible_height / total_content_height) * visible_height
            )
            bar_y = (
                rect.bottom
                - padding_y
                - bar_height
                - (scroll_ratio * (visible_height - bar_height))
            )

            pygame.draw.rect(
                self.screen,
                (60, 60, 80),
                (rect.right - 10, rect.top + padding_y, 4, visible_height),
            )
            pygame.draw.rect(
                self.screen,
                theme.COLOR_ACCENT,
                (rect.right - 10, bar_y, 4, bar_height),
            )

    def draw_input_area(self, rect: pygame.Rect, snap: GameSnapshot) -> None:
        pygame.draw.rect(self.screen, (0, 0, 0), rect)
        padding = theme.PADDING
        prompt = "> "

        col_prompt = (
            theme.COLOR_DIALOGUE_BORDER
            if snap["dialogue_active"]
            else theme.COLOR_ACCENT
        )
        surf_prompt = self.font_log.render(prompt, True, col_prompt)
        self.screen.blit(surf_prompt, (rect.x + padding, rect.y + padding))
        prompt_w = surf_prompt.get_width()

        surf_text = self.font_log.render(self.user_text, True, theme.COLOR_INPUT)
        self.screen.blit(surf_text, (rect.x + padding + prompt_w, rect.y + padding))

        cursor_str = self.user_text[: self.cursor_pos]
        cursor_offset_x = self.font_log.size(cursor_str)[0]

        if (self.cursor_blink // theme.CURSOR_BLINK_SPEED) % 2 == 0:
            cursor_x = rect.x + padding + prompt_w + cursor_offset_x
            cursor_y = rect.y + padding
            cursor_h = surf_text.get_height()
            pygame.draw.line(
                self.screen,
                theme.COLOR_INPUT,
                (cursor_x, cursor_y),
                (cursor_x, cursor_y + cursor_h),
                2,
            )

    def draw_loading_spinner(self, w: int, h: int, snap: GameSnapshot) -> None:
        center_x, center_y = w - 30, h - 25
        angle = (self.cursor_blink * theme.CURSOR_BLINK_SPEED) % 360
        radius = 10
        end_x = center_x + radius * math.cos(math.radians(angle))
        end_y = center_y + radius * math.sin(math.radians(angle))
        col = (
            theme.COLOR_DIALOGUE_BORDER
            if snap["dialogue_active"]
            else theme.COLOR_LOADING
        )
        pygame.draw.circle(self.screen, col, (center_x, center_y), radius, 1)
        pygame.draw.line(self.screen, col, (center_x, center_y), (end_x, end_y), 2)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="[%(levelname)s] %(name)s: %(message)s"
    )
    gui = GameGUI()
    gui.run()


if __name__ == "__main__":
    main()
