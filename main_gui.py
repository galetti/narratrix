# narratrix_engine/main_gui.py
from __future__ import annotations

import argparse
from datetime import datetime
import json
import logging
import math
from pathlib import Path
import queue
import sys
import threading
from typing import Any
import warnings

import pygame
import pygame.scrap

warnings.filterwarnings("ignore", category=UserWarning, module="pygame")

from engine.action_dispatcher import ActionDispatcher
from engine.game_state import GameState
from engine.handlers.system import SystemHandler
from engine.llm_bridge import LLMBridge
from engine.parser.rule_based import RuleBasedParser
from engine.parser.spacy_parser import SpacyParser
from engine.schema import GameSnapshot
from engine.story_loader import StoryLoader
from engine.strings import Texts
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
    def __init__(
        self,
        module_id: str | None = None,
        start_chapter: str | None = None,
        *,
        show_start_menu: bool = True,
    ) -> None:
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

        # Fonts & Renderer werden dynamisch durch das Theme geladen
        self.font_log: pygame.font.Font
        self.font_header: pygame.font.Font
        self.font_big: pygame.font.Font
        self.font_med: pygame.font.Font
        self.font_sensor: pygame.font.Font
        self.font_badge: pygame.font.Font
        self.renderer: RichTextRenderer
        self.line_height: int = 22
        self._reload_theme_fonts_and_renderer()

        self.assets: AssetLoader = AssetLoader()
        self.result_queue: queue.Queue[str] = queue.Queue()

        # Zwischenablage & Auswahl
        self.selection_start_idx: int | None = None
        self.selection_end_idx: int | None = None
        self.is_selecting: bool = False
        self.copy_btn_rect: pygame.Rect = pygame.Rect(0, 0, 0, 0)
        self.rendered_line_rects: list[tuple[int, pygame.Rect, str]] = []
        self.all_render_rows: list[list[TextSegment]] = []
        self.toast_msg: str | None = None
        self.toast_timer: int = 0

        # Startmenü & Modus-Auswahl
        self.menu_state: str | None = "main" if show_start_menu else None
        self.menu_selected_idx: int = 0
        self.menu_item_rects: list[tuple[str, pygame.Rect]] = []
        self.menu_error: str | None = None
        self.llm_enabled_override: bool | None = None
        self.llm_model_override: str | None = None
        self.ollama_check_queue: queue.Queue[tuple[bool, list[str]]] = queue.Queue()
        self.ollama_active: bool = False
        self.ollama_models: list[str] = []
        self.selected_model_idx: int = 0
        self.save_list: list[dict[str, Any]] = []
        self.selected_save_idx: int = 0
        self.cursor_blink: int = 0

        configured_target = (
            start_chapter
            or module_id
            or SYS_CONFIG["game"].get("start_chapter")
            or SYS_CONFIG["game"].get("default_module", "deep_zero")
        )
        self.initial_chapter: str = StoryLoader.resolve_start_chapter(str(configured_target))
        self.current_chapter: str = self.initial_chapter
        self.show_all_logs_in_main: bool = False

        if show_start_menu:
            mod_cfg = StoryLoader.get_module(str(configured_target))
            if mod_cfg and mod_cfg.get("theme"):
                theme.set_active_theme(mod_cfg["theme"])
                self._reload_theme_fonts_and_renderer()
        else:
            logger.info("Starte mit Kapitel: %s", self.current_chapter)
            self.load_game_chapter(self.current_chapter)

    def _reload_theme_fonts_and_renderer(self) -> None:
        try:
            self.font_log = pygame.font.SysFont("Consolas", theme.FONT_SIZE_LOG)
            self.font_header = pygame.font.SysFont("Verdana", theme.FONT_SIZE_HEADER, bold=True)
            self.font_big = pygame.font.SysFont("Verdana", theme.FONT_SIZE_GAME_OVER, bold=True)
            self.font_med = pygame.font.SysFont("Arial", 22)
            self.font_sensor = pygame.font.SysFont("Consolas", 14)
            self.font_badge = pygame.font.SysFont("Arial", 12, bold=True)
        except (pygame.error, OSError):
            self.font_log = pygame.font.SysFont("Arial", theme.FONT_SIZE_LOG)
            self.font_header = pygame.font.SysFont("Arial", theme.FONT_SIZE_HEADER)
            self.font_big = pygame.font.SysFont("Arial", theme.FONT_SIZE_GAME_OVER)
            self.font_med = pygame.font.SysFont("Arial", 22)
            self.font_sensor = pygame.font.SysFont("Arial", 12)
            self.font_badge = pygame.font.SysFont("Arial", 12)

        self.renderer = RichTextRenderer(self.font_log, theme.COLOR_TEXT)
        self.line_height = theme.FONT_SIZE_LOG + 4

    def load_game_chapter(
        self,
        chapter_path: str,
        transfer_state: dict[str, Any] | None = None,
        *,
        run_initial_look: bool = True,
    ) -> None:
        new_config = StoryLoader.load_chapter(chapter_path)

        if not new_config:
            logger.critical("Konnte Kapitel '%s' nicht laden!", chapter_path)
            sys.exit(1)

        # 1. Theme- und Asset-Verzeichnis deklarativ aus Kapitel-/Modul-Config übernehmen
        theme_spec = new_config.get("theme") or "default"
        theme.set_active_theme(theme_spec)
        self._reload_theme_fonts_and_renderer()
        self.assets.set_base_dir(new_config.get("asset_dir"))

        use_llm = (
            self.llm_enabled_override
            if self.llm_enabled_override is not None
            else bool(SYS_CONFIG["system"].get("llm_enabled", False))
        )
        new_config["use_llm_dialogue"] = use_llm
        new_config["language"] = str(SYS_CONFIG["game"].get("language", "de"))
        new_config["llm_url"] = SYS_CONFIG["system"].get("llm_url")
        new_config["llm_model"] = (
            self.llm_model_override
            if self.llm_model_override
            else SYS_CONFIG["system"].get("llm_model")
        )
        new_config["llm_api_key"] = SYS_CONFIG["system"].get("llm_api_key")
        new_config["llm_fallback_url"] = SYS_CONFIG["system"].get("llm_fallback_url")
        new_config["llm_fallback_model"] = SYS_CONFIG["system"].get("llm_fallback_model")
        new_config["llm_fallback_api_key"] = SYS_CONFIG["system"].get("llm_fallback_api_key")
        new_config["llm_providers"] = SYS_CONFIG["system"].get("llm_providers")
        self.game: GameState = GameState(new_config, transfer_state=transfer_state)
        self.current_chapter = chapter_path

        self.user_text: str = ""
        self.cursor_pos: int = 0
        self.cursor_blink: int = 0
        self.is_processing: bool = False
        self.history: list[str] = []
        self.history_index: int = 0
        self.scroll_offset: float = 0
        self.selection_start_idx = None
        self.selection_end_idx = None
        self.is_selecting = False

        self.parser: RuleBasedParser | SpacyParser
        if PARSER_MODE == "SPACY":
            spacy_parser = SpacyParser(self.game)
            self.parser = (
                spacy_parser if spacy_parser.available else RuleBasedParser(self.game)
            )
        else:
            self.parser = RuleBasedParser(self.game)

        if run_initial_look:
            self.submit_command("look", echo=False)

    def restart_game(self) -> None:
        self.current_chapter = self.initial_chapter
        self.load_game_chapter(self.current_chapter)

    def run(self) -> None:
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(30)

    def copy_selection_or_log(self) -> None:
        """Kopiert die aktuelle Textauswahl oder den gesamten lesbaren Story-Verlauf in die Zwischenablage."""
        text_to_copy = ""
        if (
            self.selection_start_idx is not None
            and self.selection_end_idx is not None
            and self.all_render_rows
        ):
            min_idx = max(0, min(self.selection_start_idx, self.selection_end_idx))
            max_idx = min(len(self.all_render_rows) - 1, max(self.selection_start_idx, self.selection_end_idx))
            lines: list[str] = []
            for row in self.all_render_rows[min_idx : max_idx + 1]:
                raw_line = "".join(seg.get("raw", seg.get("text", "")) for seg in row).strip()
                if raw_line:
                    lines.append(raw_line)
            text_to_copy = "\n".join(lines)

        if not text_to_copy:
            clean_lines: list[str] = []
            for entry in self.game.get_logs():
                entry_type = entry.get("type", "")
                text = entry.get("text", "")
                if entry_type == "user":
                    clean_lines.append(f"> {text}")
                elif entry_type in ("story", "info", "location", "success", "event", "alarm", "character"):
                    clean_lines.append(text)
            text_to_copy = "\n".join(clean_lines)

        if text_to_copy:
            success = copy_to_clipboard(text_to_copy)
            if success:
                self.toast_msg = "✓ In Zwischenablage kopiert"
            else:
                self.toast_msg = "X Kopieren fehlgeschlagen"
            self.toast_timer = 75

    def _get_row_index_at_y(self, my: int) -> int | None:
        for row_idx, r_rect, _ in self.rendered_line_rects:
            if r_rect.collidepoint(r_rect.centerx, my):
                return row_idx
        if self.rendered_line_rects:
            if my < self.rendered_line_rects[0][1].top:
                return self.rendered_line_rects[0][0]
            if my > self.rendered_line_rects[-1][1].bottom:
                return self.rendered_line_rects[-1][0]
        return None

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

            if self.menu_state is not None:
                self.handle_menu_event(event)
                continue

            if self.game.game_over:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_SPACE, pygame.K_r):
                        self.restart_game()
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # Klick auf Kopieren-Button
                    if self.copy_btn_rect.collidepoint(event.pos):
                        self.copy_selection_or_log()
                        continue

                    # Klick in den Log-Bereich zur Textauswahl
                    clicked_idx = self._get_row_index_at_y(event.pos[1])
                    if clicked_idx is not None:
                        self.selection_start_idx = clicked_idx
                        self.selection_end_idx = clicked_idx
                        self.is_selecting = True
                    else:
                        self.selection_start_idx = None
                        self.selection_end_idx = None

                elif event.button == 4:
                    self.scroll_offset += theme.SCROLL_SPEED_MOUSE
                elif event.button == 5:
                    self.scroll_offset = max(
                        0.0, self.scroll_offset - theme.SCROLL_SPEED_MOUSE
                    )

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.is_selecting = False

            elif event.type == pygame.MOUSEMOTION:
                if self.is_selecting:
                    hover_idx = self._get_row_index_at_y(event.pos[1])
                    if hover_idx is not None:
                        self.selection_end_idx = hover_idx

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
                    self.copy_selection_or_log()
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
                        self.selection_start_idx = None
                        self.selection_end_idx = None
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
                with self.game.lock:
                    in_dialogue = self.game.dialogue_active
                    in_disambiguation = bool(self.game.disambiguation)
                if in_dialogue:
                    ActionDispatcher.dialogue_step(self.game, text)
                elif in_disambiguation:
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
        if self.toast_timer > 0:
            self.toast_timer -= 1
            if self.toast_timer <= 0:
                self.toast_msg = None

        if self.menu_state is not None:
            try:
                while not self.ollama_check_queue.empty():
                    active, models = self.ollama_check_queue.get_nowait()
                    self._apply_ollama_check_result(active, models)
            except queue.Empty:
                pass
            return

        with self.game.lock:
            pending_chapter = self.game.pending_chapter_load if not self.is_processing else None
        if pending_chapter:
            target_chapter = pending_chapter
            logger.info("Wechsle zu Kapitel: %s", target_chapter)
            transfer_state = self.game.export_transfer_state()
            self.load_game_chapter(target_chapter, transfer_state)

    def draw(self) -> None:
        self.screen.fill(theme.COLOR_BG)
        w, h = self.screen.get_size()

        if self.menu_state is not None:
            self.draw_start_menu(w, h)
            pygame.display.flip()
            return

        snapshot = self.game.get_snapshot()

        if snapshot["game_over"]:
            self.draw_game_over(w, h, snapshot)
            pygame.display.flip()
            return

        # Adaptives Layout: Wenn ein Bild vorhanden ist, etwas mehr Raum, sonst schlanker Header
        has_room_img = bool(
            snapshot.get("room_img")
            and snapshot["room_img"] != "???"
            and self.assets.get_image(snapshot["room_img"])
        )
        has_dialogue_img = bool(
            snapshot.get("dialogue_active")
            and snapshot.get("dialogue_img")
            and self.assets.get_image(snapshot["dialogue_img"])
        )
        has_image = has_room_img or has_dialogue_img

        if has_image:
            scene_height = max(170, int(h * theme.SCENE_HEIGHT_RATIO))
        else:
            # Schlanker, moderner Status- & Stimmungs-Header ohne verschwendeten Leerraum
            scene_height = max(108, int(h * 0.15))

        input_height = theme.INPUT_HEIGHT
        log_height = h - scene_height - input_height
        rect_scene = pygame.Rect(0, 0, w, scene_height)
        rect_log = pygame.Rect(0, scene_height, w, log_height)
        rect_input = pygame.Rect(0, h - input_height, w, input_height)

        self.draw_scene_area(rect_scene, snapshot, has_image)
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

        # Toast-Overlay (Kopier-Bestätigung)
        if self.toast_msg and self.toast_timer > 0:
            self.draw_toast(w, h)

        pygame.display.flip()

    def draw_toast(self, w: int, h: int) -> None:
        if not self.toast_msg:
            return
        toast_surf = self.font_med.render(self.toast_msg, True, (255, 255, 255))
        tw, th = toast_surf.get_size()
        pad = 12
        toast_rect = pygame.Rect(w - tw - pad * 2 - 20, h - theme.INPUT_HEIGHT - th - pad * 2 - 15, tw + pad * 2, th + pad * 2)
        bg_surf = pygame.Surface((toast_rect.width, toast_rect.height), pygame.SRCALPHA)
        bg_surf.fill((20, 30, 45, 230))
        self.screen.blit(bg_surf, toast_rect.topleft)
        pygame.draw.rect(self.screen, theme.COLOR_ACCENT, toast_rect, 2, border_radius=6)
        self.screen.blit(toast_surf, (toast_rect.x + pad, toast_rect.y + pad))

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

    def draw_scene_area(self, rect: pygame.Rect, snap: GameSnapshot, has_image: bool) -> None:
        # 1. Panel-Hintergrund
        bg_color = theme.COLOR_PANEL_BG
        if snap["stability"] < 50 and (self.cursor_blink // 15) % 2 == 0:
            bg_color = (40, 20, 20)
        pygame.draw.rect(self.screen, bg_color, rect)

        # 2. Rechter Bereich: Bild/Portrait (NUR wenn vorhanden, kein schwarzer Leerkasten!)
        available_text_width = rect.width - 40
        if has_image:
            max_img_h = rect.height - 24
            max_img_w = min(int(rect.width * 0.35), int(max_img_h * 1.5))
            area_x = rect.width - max_img_w - 20
            available_text_width = area_x - 30

            room_img = self.assets.get_image(snap.get("room_img"))
            dialogue_img = (
                self.assets.get_image(snap.get("dialogue_img"))
                if snap.get("dialogue_active")
                else None
            )
            active_surf = dialogue_img or room_img
            if active_surf:
                o_w, o_h = active_surf.get_size()
                aspect = o_w / max(1, o_h)
                t_h = max_img_h
                t_w = int(t_h * aspect)
                if t_w > max_img_w:
                    t_w = max_img_w
                    t_h = max(1, int(t_w / aspect))
                scaled = pygame.transform.smoothscale(active_surf, (t_w, t_h))
                draw_x = area_x + (max_img_w - t_w) // 2
                draw_y = rect.y + 12 + (max_img_h - t_h) // 2
                img_rect = pygame.Rect(draw_x, draw_y, t_w, t_h)
                self.screen.blit(scaled, img_rect.topleft)

                border_col = (
                    theme.COLOR_DIALOGUE_BORDER
                    if snap.get("dialogue_active")
                    else theme.COLOR_UI_BORDER
                )
                pygame.draw.rect(self.screen, border_col, img_rect, 2, border_radius=4)

        # 3. Linker/Zentraler Bereich: Atmosphäre, Raumstatus, Umgebungsgeräusche & Stimmungen
        cur_x = rect.x + 20
        cur_y = rect.y + 14

        # --- ZEILE 1: Raumtitel & Status-Badges ---
        header_text = (
            snap.get("dialogue_header")
            if snap.get("dialogue_active")
            else snap.get("room_name", "Unbekannt").upper()
        )
        header_col = (
            theme.COLOR_DIALOGUE_BORDER
            if snap.get("dialogue_active")
            else theme.COLOR_ACCENT
        )
        text_room = self.font_header.render(header_text, True, header_col)
        self.screen.blit(text_room, (cur_x, cur_y))

        # Status-Pills rechts neben dem Raumnamen
        badge_x = cur_x + text_room.get_width() + 15
        badge_y = cur_y + 4

        # Höhen-Ebene Badge
        elevation = snap.get("elevation", 0)
        if elevation > 0:
            ele_surf = self.font_badge.render(f"▲ EBENE {elevation}", True, (255, 230, 100))
            ele_rect = pygame.Rect(badge_x, badge_y, ele_surf.get_width() + 10, 22)
            pygame.draw.rect(self.screen, (50, 45, 20), ele_rect, border_radius=4)
            pygame.draw.rect(self.screen, (160, 140, 50), ele_rect, 1, border_radius=4)
            self.screen.blit(ele_surf, (badge_x + 5, badge_y + 4))
            badge_x += ele_rect.width + 8

        # Zeit & Stabilität Badge
        stab_val = int(snap.get("stability", 100))
        stab_col = (255, 100, 100) if stab_val < 50 else (100, 220, 150)
        time_text = f"T+{snap.get('time', 0)}m | 🛡 {stab_val}%"
        time_surf = self.font_badge.render(time_text, True, stab_col)
        time_rect = pygame.Rect(badge_x, badge_y, time_surf.get_width() + 10, 22)
        pygame.draw.rect(self.screen, (25, 30, 40), time_rect, border_radius=4)
        pygame.draw.rect(self.screen, theme.COLOR_UI_BORDER, time_rect, 1, border_radius=4)
        self.screen.blit(time_surf, (badge_x + 5, badge_y + 4))

        cur_y += text_room.get_height() + 8

        # --- ZEILE 2: Ausgänge & Orientierung ---
        exits = snap.get("exits", [])
        if exits:
            dir_short = {"north": "N", "east": "O", "south": "S", "west": "W", "up": "OBEN", "down": "UNTEN"}
            exit_lbl = self.font_sensor.render("WEGE: ", True, theme.COLOR_TEXT_DIM)
            self.screen.blit(exit_lbl, (cur_x, cur_y))
            e_x = cur_x + exit_lbl.get_width()
            for d in exits:
                label = dir_short.get(d, d.upper())
                p_surf = self.font_badge.render(f"[{label}]", True, theme.COLOR_ACCENT)
                self.screen.blit(p_surf, (e_x, cur_y))
                e_x += p_surf.get_width() + 6
            cur_y += 22

        # --- ZEILE 3: Akustik- & Umgebungssensor (Stimmungen / Geräusche) ---
        sound_event: str | None = None
        for entry in reversed(snap.get("logs", [])):
            if entry.get("type") == "event":
                t = entry.get("text", "")
                if any(k in t.lower() for k in ("hörst", "geräusch", "wummern", "pulsieren", "schall", "lärm", "stimmen")):
                    sound_event = t
                    break

        if sound_event:
            # Akustik-Signal erkannt
            if len(sound_event) > 75:
                sound_event = sound_event[:72] + "..."
            sound_icon = self.font_sensor.render("🔊 AKUSTIK: ", True, (255, 205, 75))
            sound_txt = self.font_sensor.render(sound_event, True, (240, 230, 180))
            self.screen.blit(sound_icon, (cur_x, cur_y))
            self.screen.blit(sound_txt, (cur_x + sound_icon.get_width(), cur_y))
        else:
            ambient_icon = self.font_sensor.render("🤫 UMGEBUNG: ", True, theme.COLOR_TEXT_DIM)
            ambient_txt = self.font_sensor.render("Ruhig (keine auffälligen Schallemissionen)", True, (130, 140, 150))
            self.screen.blit(ambient_icon, (cur_x, cur_y))
            self.screen.blit(ambient_txt, (cur_x + ambient_icon.get_width(), cur_y))

        cur_y += 22

        # --- ZEILE 4: Anwesende Personen oder Aktive Aufgabe ---
        present_npcs = snap.get("present_npcs", [])
        if present_npcs:
            char_lbl = self.font_sensor.render("👤 ANWESEND: ", True, (120, 200, 255))
            char_names = self.font_sensor.render(", ".join(present_npcs), True, (180, 225, 255))
            self.screen.blit(char_lbl, (cur_x, cur_y))
            self.screen.blit(char_names, (cur_x + char_lbl.get_width(), cur_y))
        elif snap.get("active_quest_info"):
            q_info = snap["active_quest_info"]
            if len(q_info) > 80:
                q_info = q_info[:77] + "..."
            quest_lbl = self.font_sensor.render("🎯 ZIEL: ", True, (255, 180, 100))
            quest_txt = self.font_sensor.render(q_info, True, (240, 210, 170))
            self.screen.blit(quest_lbl, (cur_x, cur_y))
            self.screen.blit(quest_txt, (cur_x + quest_lbl.get_width(), cur_y))

        # 4. Kopieren-Button (Oben Rechts im Header)
        btn_w, btn_h = 135, 26
        btn_x = rect.right - btn_w - 20
        btn_y = rect.y + 12
        if has_image:
            btn_x = rect.x + cur_x + max(250, available_text_width - btn_w - 10)

        self.copy_btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        mouse_pos = pygame.mouse.get_pos()
        is_hover = self.copy_btn_rect.collidepoint(mouse_pos)

        btn_bg = (35, 45, 60) if is_hover else (22, 28, 38)
        btn_border = theme.COLOR_ACCENT if is_hover else theme.COLOR_UI_BORDER
        pygame.draw.rect(self.screen, btn_bg, self.copy_btn_rect, border_radius=4)
        pygame.draw.rect(self.screen, btn_border, self.copy_btn_rect, 1, border_radius=4)

        btn_text = "📋 Kopieren [Ctrl+C]"
        btn_surf = self.font_badge.render(btn_text, True, theme.COLOR_TEXT if not is_hover else (255, 255, 255))
        self.screen.blit(btn_surf, (self.copy_btn_rect.x + 8, self.copy_btn_rect.y + 6))

    def draw_log_area(self, rect: pygame.Rect, snap: GameSnapshot) -> None:
        padding_x = theme.PADDING
        padding_y = theme.PADDING
        max_text_width = rect.width - (padding_x * 2) - 15  # Platz für Scrollbar

        render_rows: list[list[TextSegment]] = []

        log_colors: dict[str, theme.ColorTuple] = {
            "user": theme.COLOR_USER_ECHO,
            "error": theme.COLOR_ALERT,
            "success": theme.COLOR_ACCENT,
            "event": (255, 205, 75),
            "alarm": theme.COLOR_ALERT,
            "location": theme.COLOR_ACCENT,
            "character": (110, 200, 255),
            "story": theme.COLOR_TEXT,
            "info": theme.COLOR_INFO,
        }

        for log in snap.get("logs", []):
            base_color = log_colors.get(log.get("type", ""), theme.COLOR_TEXT)
            wrapped_lines = self.renderer.parse_and_wrap(
                str(log.get("text", "")), max_text_width, base_color
            )
            render_rows.extend(wrapped_lines)

        self.all_render_rows = render_rows
        total_content_height = len(render_rows) * self.line_height
        visible_height = rect.height - (2 * padding_y)
        max_scroll = max(0, total_content_height - visible_height)

        self.scroll_offset = min(max(0.0, self.scroll_offset), float(max_scroll))
        bottom_draw_y = rect.bottom - padding_y - self.line_height + int(self.scroll_offset)

        self.rendered_line_rects.clear()

        # Ermittle Auswahl-Bereich
        has_selection = (self.selection_start_idx is not None and self.selection_end_idx is not None)
        min_sel = min(self.selection_start_idx or 0, self.selection_end_idx or 0) if has_selection else -1
        max_sel = max(self.selection_start_idx or 0, self.selection_end_idx or 0) if has_selection else -1

        # Zeilen berechnen & zeichnen
        total_rows = len(render_rows)
        for row_idx, row in enumerate(render_rows):
            # Zeile row_idx: Position von oben nach unten relativ zur Unterkante
            row_y = bottom_draw_y - (total_rows - 1 - row_idx) * self.line_height

            if row_y + self.line_height >= rect.top and row_y <= rect.bottom:
                line_rect = pygame.Rect(rect.x + padding_x, row_y, max_text_width, self.line_height)
                row_raw = "".join(seg.get("raw", seg.get("text", "")) for seg in row)
                self.rendered_line_rects.append((row_idx, line_rect, row_raw))

                # 1. Auswahl-Hervorhebung zeichnen
                if has_selection and min_sel <= row_idx <= max_sel:
                    sel_bg = pygame.Rect(rect.x + padding_x - 4, row_y, max_text_width + 8, self.line_height)
                    pygame.draw.rect(self.screen, theme.COLOR_SELECTION, sel_bg, border_radius=2)

                # 2. Textsegmente zeichnen
                cur_x = rect.x + padding_x
                for segment in row:
                    seg_text = segment.get("text", "")
                    if seg_text:
                        seg_color = (255, 255, 255) if (has_selection and min_sel <= row_idx <= max_sel) else segment.get("color", theme.COLOR_TEXT)
                        text_surf = self.font_log.render(seg_text, True, seg_color)
                        self.screen.blit(text_surf, (cur_x, row_y))
                        cur_x += segment.get("width", 0)

        # Scrollbar zeichnen
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
                (40, 45, 60),
                (rect.right - 10, rect.top + padding_y, 4, visible_height),
                border_radius=2,
            )
            pygame.draw.rect(
                self.screen,
                theme.COLOR_ACCENT_DIM,
                (rect.right - 10, bar_y, 4, bar_height),
                border_radius=2,
            )

    def draw_input_area(self, rect: pygame.Rect, snap: GameSnapshot) -> None:
        pygame.draw.rect(self.screen, (10, 12, 16), rect)
        padding = theme.PADDING
        prompt = "> "

        col_prompt = (
            theme.COLOR_DIALOGUE_BORDER
            if snap.get("dialogue_active")
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
            if snap.get("dialogue_active")
            else theme.COLOR_LOADING
        )
        pygame.draw.circle(self.screen, col, (center_x, center_y), radius, 1)
        pygame.draw.line(self.screen, col, (center_x, center_y), (end_x, end_y), 2)

    def start_normal_mode(self) -> None:
        self.llm_enabled_override = False
        self.llm_model_override = None
        self.menu_error = None
        self.menu_state = None
        logger.info("Starte im normalen Modus (Kapitel: %s)", self.initial_chapter)
        self.load_game_chapter(self.initial_chapter)

    def start_ai_mode(self, model: str | None = None) -> None:
        chosen_model = model or (
            self.ollama_models[self.selected_model_idx]
            if self.ollama_models and 0 <= self.selected_model_idx < len(self.ollama_models)
            else str(SYS_CONFIG["system"].get("llm_model") or LLMBridge.DEFAULT_MODEL)
        )
        self.llm_enabled_override = True
        self.llm_model_override = chosen_model
        self.menu_error = None
        self.menu_state = None
        logger.info(
            "Starte im KI-Modus mit Modell '%s' (Kapitel: %s)",
            chosen_model,
            self.initial_chapter,
        )
        self.load_game_chapter(self.initial_chapter)

    def start_ollama_check(self) -> None:
        self.menu_error = None
        self.menu_state = "ai_checking"
        self.ollama_active = False
        self.ollama_models = []
        self.selected_model_idx = 0

        api_url = SYS_CONFIG["system"].get("llm_url")
        api_key = SYS_CONFIG["system"].get("llm_api_key")

        def worker() -> None:
            active, models = LLMBridge.list_available_models(
                api_url=api_url,
                api_key=api_key,
                timeout=2.0,
            )
            self.ollama_check_queue.put((active, models))

        threading.Thread(target=worker, daemon=True).start()

    def _apply_ollama_check_result(self, active: bool, models: list[str]) -> None:
        self.ollama_active = active
        self.ollama_models = list(models)
        configured_model = str(SYS_CONFIG["system"].get("llm_model") or "")
        if configured_model and configured_model in self.ollama_models:
            self.selected_model_idx = self.ollama_models.index(configured_model)
        else:
            self.selected_model_idx = 0
        self.menu_state = "ai_setup"

    def open_load_menu(self) -> None:
        self.menu_error = None
        self.save_list = SystemHandler.list_saves()
        self.selected_save_idx = 0
        self.menu_state = "load_game"

    def load_selected_save(self, save_info: dict[str, Any]) -> None:
        filepath = str(save_info.get("filepath", ""))
        if not filepath or not Path(filepath).is_file():
            self.menu_error = Texts.LOAD_NOT_FOUND.format(
                filename=save_info.get("filename", "savegame.json")
            )
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            self.menu_error = Texts.LOAD_CRITICAL_ERROR.format(error=exc)
            return

        saved_chapter = (
            data.get("meta", {}).get("chapter")
            if isinstance(data.get("meta"), dict)
            else None
        )
        target_chapter = (
            StoryLoader.resolve_start_chapter(str(saved_chapter))
            if saved_chapter
            else self.initial_chapter
        )
        if not StoryLoader.load_chapter(target_chapter):
            target_chapter = self.initial_chapter

        self.llm_enabled_override = False
        self.llm_model_override = None
        self.load_game_chapter(target_chapter, run_initial_look=False)

        if self.game.deserialize_state(data):
            self.menu_error = None
            self.menu_state = None
            self.game.log("success", Texts.LOAD_SUCCESS)
            self.submit_command("look", echo=False)
        else:
            self.menu_error = Texts.LOAD_PROCESS_ERROR

    def _trigger_menu_action(self, action_id: str) -> None:
        if action_id == "mode_normal":
            self.start_normal_mode()
        elif action_id == "mode_ai":
            self.start_ollama_check()
        elif action_id == "mode_load":
            self.open_load_menu()
        elif action_id == "ai_retry":
            self.start_ollama_check()
        elif action_id == "ai_start":
            if self.ollama_active and self.ollama_models:
                self.start_ai_mode(self.ollama_models[self.selected_model_idx])
        elif action_id.startswith("model:"):
            idx = int(action_id.split(":", 1)[1])
            if 0 <= idx < len(self.ollama_models):
                self.selected_model_idx = idx
        elif action_id.startswith("save:"):
            idx = int(action_id.split(":", 1)[1])
            if 0 <= idx < len(self.save_list):
                self.selected_save_idx = idx
        elif action_id == "load_selected":
            if self.save_list and 0 <= self.selected_save_idx < len(self.save_list):
                self.load_selected_save(self.save_list[self.selected_save_idx])
        elif action_id == "back":
            self.menu_error = None
            self.menu_state = "main"

    def handle_menu_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for action_id, rect in self.menu_item_rects:
                if rect.collidepoint(event.pos):
                    self._trigger_menu_action(action_id)
                    return
            return

        if event.type != pygame.KEYDOWN:
            return

        if self.menu_state == "main":
            if event.key == pygame.K_UP:
                self.menu_selected_idx = (self.menu_selected_idx - 1) % 3
            elif event.key == pygame.K_DOWN:
                self.menu_selected_idx = (self.menu_selected_idx + 1) % 3
            elif event.key in (pygame.K_1, pygame.K_KP1):
                self._trigger_menu_action("mode_normal")
            elif event.key in (pygame.K_2, pygame.K_KP2):
                self._trigger_menu_action("mode_ai")
            elif event.key in (pygame.K_3, pygame.K_KP3):
                self._trigger_menu_action("mode_load")
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                actions = ("mode_normal", "mode_ai", "mode_load")
                self._trigger_menu_action(actions[self.menu_selected_idx])

        elif self.menu_state == "ai_checking":
            if event.key == pygame.K_ESCAPE:
                self._trigger_menu_action("back")

        elif self.menu_state == "ai_setup":
            if event.key == pygame.K_ESCAPE:
                self._trigger_menu_action("back")
            elif self.ollama_active and self.ollama_models:
                if event.key == pygame.K_UP:
                    self.selected_model_idx = (self.selected_model_idx - 1) % len(
                        self.ollama_models
                    )
                elif event.key == pygame.K_DOWN:
                    self.selected_model_idx = (self.selected_model_idx + 1) % len(
                        self.ollama_models
                    )
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._trigger_menu_action("ai_start")
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_r):
                self._trigger_menu_action("ai_retry")

        elif self.menu_state == "load_game":
            if event.key == pygame.K_ESCAPE:
                self._trigger_menu_action("back")
            elif self.save_list:
                if event.key == pygame.K_UP:
                    self.selected_save_idx = (self.selected_save_idx - 1) % len(
                        self.save_list
                    )
                elif event.key == pygame.K_DOWN:
                    self.selected_save_idx = (self.selected_save_idx + 1) % len(
                        self.save_list
                    )
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._trigger_menu_action("load_selected")

    def _draw_menu_button(
        self,
        rect: pygame.Rect,
        title: str,
        subtitle: str | None,
        selected: bool,
        hovered: bool,
        accent: tuple[int, int, int] | None = None,
    ) -> None:
        accent_col = accent or theme.COLOR_ACCENT
        bg_col = (
            (
                min(255, theme.COLOR_PANEL_BG[0] + 18),
                min(255, theme.COLOR_PANEL_BG[1] + 22),
                min(255, theme.COLOR_PANEL_BG[2] + 30),
            )
            if (selected or hovered)
            else theme.COLOR_PANEL_BG
        )
        border_col = accent_col if selected else (theme.COLOR_ACCENT_DIM if hovered else theme.COLOR_UI_BORDER)
        pygame.draw.rect(self.screen, bg_col, rect, border_radius=6)
        pygame.draw.rect(self.screen, border_col, rect, 2 if selected else 1, border_radius=6)

        prefix = "> " if selected else "  "
        title_col = accent_col if selected else theme.COLOR_TEXT
        surf_title = self.font_med.render(f"{prefix}{title}", True, title_col)
        if subtitle:
            self.screen.blit(surf_title, (rect.x + 16, rect.y + 10))
            surf_sub = self.font_sensor.render(subtitle, True, theme.COLOR_TEXT_DIM)
            self.screen.blit(surf_sub, (rect.x + 34, rect.y + 40))
        else:
            title_y = rect.y + (rect.height - surf_title.get_height()) // 2
            self.screen.blit(surf_title, (rect.x + 16, title_y))

    def draw_start_menu(self, w: int, h: int) -> None:
        self.menu_item_rects = []
        mouse_pos = pygame.mouse.get_pos()

        panel_w = min(680, max(420, w - 80))
        panel_h = min(560, max(400, h - 80))
        panel_x = (w - panel_w) // 2
        panel_y = (h - panel_h) // 2
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

        pygame.draw.rect(self.screen, theme.COLOR_PANEL_BG, panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, theme.COLOR_UI_BORDER, panel_rect, 2, border_radius=10)

        title_text = f"{SYS_CONFIG['game'].get('title', 'Narratrix').upper()}  v6.0"
        surf_title = self.font_header.render(title_text, True, theme.COLOR_ACCENT)
        self.screen.blit(
            surf_title,
            (panel_x + (panel_w - surf_title.get_width()) // 2, panel_y + 24),
        )

        surf_sub = self.font_sensor.render(
            "Modulare Textadventure-Engine", True, theme.COLOR_TEXT_DIM
        )
        self.screen.blit(
            surf_sub,
            (panel_x + (panel_w - surf_sub.get_width()) // 2, panel_y + 64),
        )

        pygame.draw.line(
            self.screen,
            theme.COLOR_UI_BORDER,
            (panel_x + 28, panel_y + 94),
            (panel_x + panel_w - 28, panel_y + 94),
            1,
        )

        inner_x = panel_x + 36
        inner_w = panel_w - 72
        cur_y = panel_y + 114

        if self.menu_state == "main":
            prompt = self.font_log.render("Wähle deinen Spielmodus:", True, theme.COLOR_TEXT)
            self.screen.blit(prompt, (inner_x, cur_y))
            cur_y += 38

            options = [
                (
                    "mode_normal",
                    "[1] Normaler Modus",
                    "Klassisches Textadventure mit deterministischen Dialogen",
                ),
                (
                    "mode_ai",
                    "[2] KI Modus (Ollama)",
                    "Dynamische NPC-Dialoge über lokalen Ollama-Server",
                ),
                (
                    "mode_load",
                    "[3] Spiel laden",
                    "Gespeicherten Spielstand aus saves/ fortsetzen",
                ),
            ]
            for idx, (action_id, label, desc) in enumerate(options):
                btn_rect = pygame.Rect(inner_x, cur_y, inner_w, 72)
                hovered = btn_rect.collidepoint(mouse_pos)
                self._draw_menu_button(
                    btn_rect,
                    label,
                    desc,
                    selected=(idx == self.menu_selected_idx),
                    hovered=hovered,
                )
                self.menu_item_rects.append((action_id, btn_rect))
                cur_y += 88

            hint = self.font_sensor.render(
                "Pfeiltasten / [1-3] / Maus zum Auswählen  •  Enter zum Starten",
                True,
                theme.COLOR_TEXT_DIM,
            )
            self.screen.blit(
                hint,
                (panel_x + (panel_w - hint.get_width()) // 2, panel_rect.bottom - 34),
            )

        elif self.menu_state == "ai_checking":
            url = LLMBridge.get_api_url(SYS_CONFIG["system"].get("llm_url"))
            status = self.font_med.render(
                "Prüfe Ollama-Server und verfügbare Modelle...",
                True,
                theme.COLOR_LOADING,
            )
            self.screen.blit(status, (inner_x, cur_y + 20))
            url_surf = self.font_sensor.render(f"Ziel: {url}", True, theme.COLOR_TEXT_DIM)
            self.screen.blit(url_surf, (inner_x, cur_y + 56))

            center_x = panel_x + panel_w // 2
            center_y = cur_y + 130
            angle = (self.cursor_blink * theme.CURSOR_BLINK_SPEED) % 360
            end_x = center_x + 18 * math.cos(math.radians(angle))
            end_y = center_y + 18 * math.sin(math.radians(angle))
            pygame.draw.circle(self.screen, theme.COLOR_LOADING, (center_x, center_y), 18, 2)
            pygame.draw.line(
                self.screen, theme.COLOR_LOADING, (center_x, center_y), (end_x, end_y), 2
            )

            back_rect = pygame.Rect(inner_x, panel_rect.bottom - 68, 160, 42)
            self._draw_menu_button(
                back_rect,
                "Abbrechen",
                None,
                selected=False,
                hovered=back_rect.collidepoint(mouse_pos),
            )
            self.menu_item_rects.append(("back", back_rect))

        elif self.menu_state == "ai_setup":
            url = LLMBridge.get_api_url(SYS_CONFIG["system"].get("llm_url"))
            status_col = theme.COLOR_ACCENT if self.ollama_active else theme.COLOR_ALERT
            status_label = (
                "● Ollama-Server aktiv"
                if self.ollama_active
                else "● Ollama-Server nicht erreichbar"
            )
            surf_status = self.font_med.render(status_label, True, status_col)
            self.screen.blit(surf_status, (inner_x, cur_y))
            cur_y += 30

            surf_url = self.font_sensor.render(f"Server: {url}", True, theme.COLOR_TEXT_DIM)
            self.screen.blit(surf_url, (inner_x, cur_y))
            cur_y += 28

            if self.ollama_active and self.ollama_models:
                configured = str(SYS_CONFIG["system"].get("llm_model") or "")
                lbl = self.font_log.render(
                    f"Verfügbare Modelle ({len(self.ollama_models)}):",
                    True,
                    theme.COLOR_TEXT,
                )
                self.screen.blit(lbl, (inner_x, cur_y))
                cur_y += 30

                max_visible = 5
                start_idx = max(
                    0,
                    min(
                        self.selected_model_idx - max_visible // 2,
                        len(self.ollama_models) - max_visible,
                    ),
                )
                visible_models = self.ollama_models[start_idx : start_idx + max_visible]
                for offset, model_name in enumerate(visible_models):
                    m_idx = start_idx + offset
                    suffix = "  (Standard)" if model_name == configured else ""
                    row_rect = pygame.Rect(inner_x, cur_y, inner_w, 42)
                    self._draw_menu_button(
                        row_rect,
                        f"{model_name}{suffix}",
                        None,
                        selected=(m_idx == self.selected_model_idx),
                        hovered=row_rect.collidepoint(mouse_pos),
                    )
                    self.menu_item_rects.append((f"model:{m_idx}", row_rect))
                    cur_y += 48

                btn_y = panel_rect.bottom - 68
                start_rect = pygame.Rect(inner_x, btn_y, 240, 44)
                retry_rect = pygame.Rect(inner_x + 256, btn_y, 170, 44)
                back_rect = pygame.Rect(inner_x + 442, btn_y, inner_w - 442, 44)
                self._draw_menu_button(
                    start_rect,
                    "KI-Modus starten",
                    None,
                    selected=True,
                    hovered=start_rect.collidepoint(mouse_pos),
                )
                self._draw_menu_button(
                    retry_rect,
                    "Erneut prüfen",
                    None,
                    selected=False,
                    hovered=retry_rect.collidepoint(mouse_pos),
                )
                self._draw_menu_button(
                    back_rect,
                    "Zurück",
                    None,
                    selected=False,
                    hovered=back_rect.collidepoint(mouse_pos),
                )
                self.menu_item_rects.append(("ai_start", start_rect))
                self.menu_item_rects.append(("ai_retry", retry_rect))
                self.menu_item_rects.append(("back", back_rect))
            else:
                hint_msg = (
                    "Server aktiv, aber keine Modelle installiert (z. B. 'ollama pull gemma4:12b')."
                    if self.ollama_active
                    else "Bitte Ollama starten (z. B. 'ollama serve') oder im normalen Modus spielen."
                )
                surf_hint = self.font_log.render(hint_msg[:62], True, theme.COLOR_TEXT)
                self.screen.blit(surf_hint, (inner_x, cur_y + 12))
                if len(hint_msg) > 62:
                    surf_hint2 = self.font_log.render(hint_msg[62:], True, theme.COLOR_TEXT)
                    self.screen.blit(surf_hint2, (inner_x, cur_y + 36))

                btn_y = panel_rect.bottom - 68
                retry_rect = pygame.Rect(inner_x, btn_y, 190, 44)
                normal_rect = pygame.Rect(inner_x + 206, btn_y, 230, 44)
                back_rect = pygame.Rect(inner_x + 452, btn_y, inner_w - 452, 44)
                self._draw_menu_button(
                    retry_rect,
                    "Erneut prüfen",
                    None,
                    selected=True,
                    hovered=retry_rect.collidepoint(mouse_pos),
                    accent=theme.COLOR_LOADING,
                )
                self._draw_menu_button(
                    normal_rect,
                    "Normaler Modus",
                    None,
                    selected=False,
                    hovered=normal_rect.collidepoint(mouse_pos),
                )
                self._draw_menu_button(
                    back_rect,
                    "Zurück",
                    None,
                    selected=False,
                    hovered=back_rect.collidepoint(mouse_pos),
                )
                self.menu_item_rects.append(("ai_retry", retry_rect))
                self.menu_item_rects.append(("mode_normal", normal_rect))
                self.menu_item_rects.append(("back", back_rect))

        elif self.menu_state == "load_game":
            lbl = self.font_log.render("Gespeicherte Spielstände:", True, theme.COLOR_TEXT)
            self.screen.blit(lbl, (inner_x, cur_y))
            cur_y += 34

            if self.save_list:
                max_visible = 4
                start_idx = max(
                    0,
                    min(
                        self.selected_save_idx - max_visible // 2,
                        len(self.save_list) - max_visible,
                    ),
                )
                visible_saves = self.save_list[start_idx : start_idx + max_visible]
                for offset, save_info in enumerate(visible_saves):
                    s_idx = start_idx + offset
                    ts = datetime.fromtimestamp(float(save_info.get("mtime", 0))).strftime(
                        "%Y-%m-%d %H:%M"
                    )
                    chap = save_info.get("chapter") or "?"
                    loc = save_info.get("location") or "?"
                    sub = f"Kapitel: {chap}  •  Ort: {loc}  •  {ts}"
                    row_rect = pygame.Rect(inner_x, cur_y, inner_w, 64)
                    self._draw_menu_button(
                        row_rect,
                        str(save_info.get("filename", "savegame.json")),
                        sub,
                        selected=(s_idx == self.selected_save_idx),
                        hovered=row_rect.collidepoint(mouse_pos),
                    )
                    self.menu_item_rects.append((f"save:{s_idx}", row_rect))
                    cur_y += 72

                if self.menu_error:
                    err_surf = self.font_sensor.render(
                        self.menu_error[:80], True, theme.COLOR_ALERT
                    )
                    self.screen.blit(err_surf, (inner_x, panel_rect.bottom - 94))

                btn_y = panel_rect.bottom - 68
                load_rect = pygame.Rect(inner_x, btn_y, 240, 44)
                back_rect = pygame.Rect(inner_x + 256, btn_y, 180, 44)
                self._draw_menu_button(
                    load_rect,
                    "Spielstand laden",
                    None,
                    selected=True,
                    hovered=load_rect.collidepoint(mouse_pos),
                )
                self._draw_menu_button(
                    back_rect,
                    "Zurück",
                    None,
                    selected=False,
                    hovered=back_rect.collidepoint(mouse_pos),
                )
                self.menu_item_rects.append(("load_selected", load_rect))
                self.menu_item_rects.append(("back", back_rect))
            else:
                empty_surf = self.font_log.render(
                    "Keine Spielstände im Ordner 'saves/' gefunden.",
                    True,
                    theme.COLOR_TEXT_DIM,
                )
                self.screen.blit(empty_surf, (inner_x, cur_y + 16))
                back_rect = pygame.Rect(inner_x, panel_rect.bottom - 68, 180, 44)
                self._draw_menu_button(
                    back_rect,
                    "Zurück",
                    None,
                    selected=True,
                    hovered=back_rect.collidepoint(mouse_pos),
                )
                self.menu_item_rects.append(("back", back_rect))


def parse_cli_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Narratrix Engine 6.0")
    parser.add_argument(
        "--module",
        help="Spielmodul-ID aus data/modules/<id>/module.py (z. B. deep_zero oder test_lab)",
    )
    parser.add_argument(
        "--chapter",
        help="Direkter Kapitel-Importpfad oder JSON-Datei",
    )
    parser.add_argument(
        "--list-modules",
        action="store_true",
        help="Alle verfügbaren Spielmodule auflisten und beenden",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(
        level=logging.INFO, format="[%(levelname)s] %(name)s: %(message)s"
    )
    args = parse_cli_args(argv)
    if args.list_modules:
        modules = StoryLoader.discover_modules()
        for mod_id, cfg in modules.items():
            logger.info("%s: %s (%s)", mod_id, cfg.get("title", mod_id), cfg.get("start_chapter"))
        return

    gui = GameGUI(module_id=args.module, start_chapter=args.chapter)
    gui.run()


if __name__ == "__main__":
    main()
