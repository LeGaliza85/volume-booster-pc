"""Volume Booster PC - system-wide volume boost from 0 to 500 %."""

from __future__ import annotations

import contextlib
import ctypes
import functools
import json
import logging
import os
import queue
import sys
import tempfile
import threading
import time
import tkinter as tk
import webbrowser
from collections.abc import Callable
from ctypes import wintypes
from pathlib import Path
from tkinter import font as tkfont
from tkinter import messagebox

import autostart
import backend as backends
import configfile
import confirmdialog
import diagnostics
import gainmath
import hotkey
import i18n
import preview
import report
import settings
import settingswindow
import theme as T
import tray
import update
import updater
import version
import widgets as W

LOG = logging.getLogger("app")

WINDOW_TITLE = version.APP_NAME
CLIP_THRESHOLD = 200

_MUTEX_NAME = rf"Local\{version.APP_ID}SingleInstance"
_ERROR_ALREADY_EXISTS = 183
_MUTEX_HANDLES: list[int] = []

HOTKEY_UP = 1
HOTKEY_DOWN = 2
BOOST_STEP = 10
TRAY_PUMP_MS = 60
TOAST_DELAY_MS = 700
PREVIEW_INTERVAL = 0.25


def resource_path(relative: str) -> Path:
    bundled = getattr(sys, "_MEIPASS", None)
    if bundled:
        return Path(bundled) / relative
    return Path(__file__).resolve().parent / relative


def default_state_path() -> Path:
    roaming = os.environ.get("APPDATA")
    if roaming:
        return Path(roaming) / version.APP_ID / "state.json"
    return Path.home() / ".config" / "volume-booster-pc" / "state.json"


STATE_PATH = default_state_path()
SETTINGS_PATH = STATE_PATH.parent / "settings.json"


def load_state() -> tuple[int, str | None]:
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, AttributeError):
        return gainmath.DEFAULT_PERCENT, None
    percent = gainmath.clamp_percent(data.get("percent", gainmath.DEFAULT_PERCENT))
    language = data.get("language")
    if language not in i18n.LANGUAGES:
        language = None
    return percent, language


def save_state(percent: int, language: str) -> None:
    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(
            json.dumps({"percent": percent, "language": language}), encoding="utf-8"
        )
    except OSError:
        pass


def _claim_single_instance() -> bool:
    """False when another instance already owns the mutex (Windows only)."""
    if not sys.platform.startswith("win"):
        return True
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.restype = wintypes.HANDLE
    kernel32.CreateMutexW.argtypes = (wintypes.LPCVOID, wintypes.BOOL, wintypes.LPCWSTR)
    handle = kernel32.CreateMutexW(None, False, _MUTEX_NAME)
    if not handle:
        return True
    if ctypes.get_last_error() == _ERROR_ALREADY_EXISTS:
        kernel32.CloseHandle(handle)
        return False
    _MUTEX_HANDLES.append(handle)
    return True


def _focus_existing_window() -> None:
    if not sys.platform.startswith("win"):
        return
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.FindWindowW.restype = wintypes.HWND
    hwnd = user32.FindWindowW(None, WINDOW_TITLE)
    if not hwnd:
        return
    user32.ShowWindow(hwnd, 9)  # SW_RESTORE, also reveals a hidden window
    user32.SetForegroundWindow(hwnd)


def apply_dark_titlebar(root: tk.Tk) -> None:
    """Ask DWM for the dark frame and force it to repaint (Win10 2004+)."""
    if not sys.platform.startswith("win"):
        return
    try:
        root.update()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        enabled = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 20, ctypes.byref(enabled), ctypes.sizeof(enabled)
        )
        ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0027)
    except (AttributeError, OSError):
        pass


class AmplifierApp:
    def __init__(self, root: tk.Tk, engine, *, minimized: bool = False, use_tray: bool = True) -> None:
        self.root = root
        self.engine = engine
        self.percent, saved_language = load_state()
        self.language = saved_language or i18n.system_language()
        self.first_run = not SETTINGS_PATH.exists()
        self.settings = settings.load(SETTINGS_PATH)
        self._applied = self.percent
        self.autostart_enabled = autostart.is_enabled()
        self.family = T.pick_font(root)
        self._dot_colour = T.MUTED
        self.use_tray = use_tray
        self._toast_job: str | None = None
        self._last_preview = 0.0
        self._checking_update = False
        self._update_results: queue.Queue = queue.Queue()
        self._download_results: queue.Queue = queue.Queue()
        self._updating = False
        self.settings_window: settingswindow.SettingsWindow | None = None
        self.tray: tray.Tray | None = None

        self.gain_var = tk.StringVar()
        self.entry_var = tk.StringVar()
        self.warning_var = tk.StringVar()
        self.status_var = tk.StringVar()

        self._build()
        self._refresh(self.percent)
        self._apply(silent=True)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._start_tray()
        if minimized or (
            self.settings["start_hidden"] and not self.first_run and self.tray is not None
        ):
            self.root.withdraw()
        if self.settings.get("check_updates") or self.settings.get("auto_update"):
            self.root.after(3000, lambda: self._check_updates(manual=False))

    # ------------------------------------------------------------ i18n
    def t(self, key: str, **values: object) -> str:
        return i18n.translate(self.language, key, **values)

    # ------------------------------------------------------------ layout
    def _build(self) -> None:
        root = self.root
        root.title(WINDOW_TITLE)
        root.resizable(False, False)
        root.configure(bg=T.BG)
        with contextlib.suppress(tk.TclError, OSError):
            root.iconbitmap(default=str(resource_path("assets/volume-amplifier.ico")))

        old_menu = getattr(self, "lang_menu", None)
        if old_menu is not None:
            old_menu.destroy()
        self.lang_menu = tk.Menu(
            root,
            tearoff=0,
            bg=T.SURFACE,
            fg=T.TEXT,
            activebackground=T.ACCENT,
            activeforeground="#FFFFFF",
            bd=0,
            activeborderwidth=0,
        )
        for code, name in i18n.LANGUAGES.items():
            self.lang_menu.add_command(
                label=name, command=functools.partial(self._set_language, code)
            )

        frame = tk.Frame(root, bg=T.BG, padx=26, pady=22)
        frame.pack(fill="both", expand=True)

        header = tk.Frame(frame, bg=T.BG)
        header.pack(fill="x")
        tk.Label(
            header, text=self.t("subtitle"), bg=T.BG, fg=T.MUTED, font=(self.family, T.px(9))
        ).pack(side="left")
        self.lang_button = W.PillButton(
            header,
            i18n.LANGUAGES[self.language],
            self._open_languages,
            family=self.family,
            size=9,
            weight="normal",
            fill=T.SURFACE,
            hover=T.SURFACE_HOVER,
            pressed=T.SURFACE_HOVER,
            fg=T.TEXT,
            padx=12,
            height=28,
        )
        self.lang_button.pack(side="right")

        number_row = tk.Frame(frame, bg=T.BG)
        number_row.pack(fill="x", pady=(12, 0))
        self.number_font = tkfont.Font(family=self.family, size=T.px(46), weight="bold")
        self.percent_font = tkfont.Font(family=self.family, size=T.px(15))
        self.number_canvas = tk.Canvas(
            number_row, bg=T.BG, highlightthickness=0, bd=0, height=76, width=250
        )
        self.number_canvas.pack(anchor="w")
        self._number_item = self.number_canvas.create_text(
            0, 70, text="100", anchor="sw", fill=T.TEXT, font=self.number_font
        )
        self._percent_item = self.number_canvas.create_text(
            0, 70, text="%", anchor="sw", fill=T.MUTED, font=self.percent_font
        )

        tk.Label(
            frame,
            textvariable=self.gain_var,
            bg=T.BG,
            fg=T.ACCENT,
            font=(self.family, T.px(11), "bold"),
        ).pack(anchor="w", pady=(0, 10))

        self.slider = W.ModernSlider(
            frame,
            minimum=gainmath.MIN_PERCENT,
            maximum=self.settings["max_percent"],
            value=self.percent,
            on_change=self._on_slide,
            on_release=self._on_slide_release,
        )
        self.slider.pack(fill="x")

        hints = tk.Frame(frame, bg=T.BG)
        hints.pack(fill="x")
        tk.Label(hints, text="0", bg=T.BG, fg=T.MUTED, font=(self.family, T.px(8))).pack(side="left")
        tk.Label(
            hints,
            text=str(self.settings["max_percent"]),
            bg=T.BG,
            fg=T.MUTED,
            font=(self.family, T.px(8)),
        ).pack(side="right")

        exact = tk.Frame(frame, bg=T.BG)
        exact.pack(fill="x", pady=(16, 0))
        tk.Label(
            exact, text=self.t("exact"), bg=T.BG, fg=T.MUTED, font=(self.family, T.px(9))
        ).pack(side="left")
        self.entry = tk.Entry(
            exact,
            textvariable=self.entry_var,
            width=5,
            justify="center",
            bg=T.SURFACE,
            fg=T.TEXT,
            insertbackground=T.TEXT,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=T.BORDER,
            highlightcolor=T.ACCENT,
            font=(self.family, T.px(11)),
        )
        self.entry.pack(side="left", padx=(10, 5), ipady=5)
        tk.Label(exact, text="%", bg=T.BG, fg=T.MUTED, font=(self.family, T.px(10))).pack(side="left")
        self.apply_button = W.PillButton(
            exact, self.t("apply"), self._apply, family=self.family, size=10
        )
        self.apply_button.pack(side="right")
        self.test_button = W.PillButton(
            exact,
            self.t("test"),
            self._test_tone,
            family=self.family,
            size=10,
            weight="normal",
            fill=T.SURFACE,
            hover=T.SURFACE_HOVER,
            pressed=T.SURFACE_HOVER,
            fg=T.TEXT,
            padx=14,
        )
        self.test_button.pack(side="right", padx=(0, 8))
        self.entry.bind("<Return>", lambda _event: self._apply())
        self.entry.bind("<FocusOut>", lambda _event: self._apply())

        auto = tk.Frame(frame, bg=T.BG)
        auto.pack(fill="x", pady=(16, 0))
        self.toggle = W.ToggleSwitch(
            auto, self.autostart_enabled, self._toggle_autostart
        )
        self.toggle.pack(side="left")
        self.autostart_label = tk.Label(
            auto,
            text=self.t("autostart"),
            bg=T.BG,
            fg=T.TEXT,
            font=(self.family, T.px(10)),
            cursor="hand2",
        )
        self.autostart_label.pack(side="left", padx=(10, 0))
        self.autostart_label.bind(
            "<Button-1>", lambda _event: self._toggle_autostart(not self.autostart_enabled)
        )

        self.warning_label = tk.Label(
            frame,
            textvariable=self.warning_var,
            bg=T.BG,
            fg=T.WARN,
            font=(self.family, T.px(9)),
            wraplength=430,
            justify="left",
        )
        self.warning_label.pack(anchor="w", pady=(12, 0))

        tk.Frame(frame, bg=T.BORDER, height=1).pack(fill="x", pady=14)

        footer = tk.Frame(frame, bg=T.BG)
        footer.pack(fill="x")
        self.dot = tk.Canvas(footer, width=10, height=10, bg=T.BG, highlightthickness=0, bd=0)
        self.dot.pack(side="left")
        self.status_label = tk.Label(
            footer,
            textvariable=self.status_var,
            bg=T.BG,
            fg=T.MUTED,
            font=(self.family, T.px(9)),
            wraplength=320,
            justify="left",
        )
        self.status_label.pack(side="left", padx=(8, 0))
        self.setup_button = W.PillButton(
            footer,
            self.t("setup"),
            self._show_setup,
            family=self.family,
            size=9,
            weight="normal",
            fill=T.SURFACE,
            hover=T.SURFACE_HOVER,
            pressed=T.SURFACE_HOVER,
            fg=T.TEXT,
            padx=14,
            height=30,
        )
        self.setup_button.pack(side="right")

        links = tk.Frame(frame, bg=T.BG)
        links.pack(anchor="w", pady=(10, 0))
        self.report_label = tk.Label(
            links,
            text=self.t("report"),
            bg=T.BG,
            fg=T.MUTED,
            font=(self.family, T.px(8), "underline"),
            cursor="hand2",
        )
        self.report_label.pack(side="left")
        self.report_label.bind("<Button-1>", lambda _event: self._report_bug())
        tk.Label(
            links, text="\u00b7", bg=T.BG, fg=T.MUTED, font=(self.family, T.px(8))
        ).pack(side="left", padx=6)
        self.update_label = tk.Label(
            links,
            text=self.t("check_update"),
            bg=T.BG,
            fg=T.MUTED,
            font=(self.family, T.px(8), "underline"),
            cursor="hand2",
        )
        self.update_label.pack(side="left")
        self.update_label.bind("<Button-1>", lambda _event: self._check_updates())

        self.root.update_idletasks()
        width = max(self.root.winfo_reqwidth(), 480)
        height = self.root.winfo_reqheight()
        x = (self.root.winfo_screenwidth() - width) // 2
        y = (self.root.winfo_screenheight() - height) // 3
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self._draw_dot()

    # ------------------------------------------------------------ events
    def _open_languages(self) -> None:
        self.lang_button.update_idletasks()
        x = self.lang_button.winfo_rootx()
        y = self.lang_button.winfo_rooty() + self.lang_button.winfo_height() + 4
        try:
            self.lang_menu.tk_popup(x, y)
        finally:
            self.lang_menu.grab_release()

    def _set_language(self, code: str) -> None:
        if code == self.language:
            return
        LOG.info("language changed to %s", code)
        self.language = code
        save_state(self.percent, self.language)
        self._rebuild()

    def _report_bug(self) -> None:
        url = report.build_issue_url(
            app_version=version.VERSION, os_name=report.os_option()
        )
        LOG.info("opening the bug report form")
        webbrowser.open(url)

    # ------------------------------------------------------------- updates
    def _check_updates(self, *, manual: bool = True) -> None:
        if self._checking_update:
            return
        self._checking_update = True
        if manual:
            self._set_status(self.t("checking_update"), "idle")
        threading.Thread(target=self._update_worker, args=(manual,), daemon=True).start()
        self.root.after(200, self._poll_update_result)

    def _update_worker(self, manual: bool) -> None:
        """Runs off the UI thread: urllib can block for seconds."""
        self._update_results.put((manual, update.check()))

    def _poll_update_result(self) -> None:
        try:
            manual, result = self._update_results.get_nowait()
        except queue.Empty:
            self.root.after(200, self._poll_update_result)
            return
        self._checking_update = False
        self._handle_update_result(result, manual)

    def _handle_update_result(self, result: dict, manual: bool) -> None:
        status = result.get("status")
        latest = result.get("latest") or ""
        if status == update.STATUS_UNKNOWN:
            LOG.info("update check failed")
            self._set_status(self.t("update_failed"), "warn")
            return
        if status == update.STATUS_CURRENT:
            LOG.info("update check: up to date")
            self._set_status(self.t("update_current", version=version.VERSION), "ok")
            return
        LOG.info("update check: %s available", latest)
        self._set_status(self.t("update_available", version=latest), "warn")
        if self._can_auto_install(latest):
            self._auto_install(latest)
            return
        if not manual:
            if self.tray is not None:
                self.tray.notify(version.APP_NAME, self.t("update_available", version=latest))
            return
        if messagebox.askyesno(
            self.t("update_title"), self.t("update_available", version=latest)
        ):
            webbrowser.open(result.get("url") or update.RELEASES_URL)

    def _can_auto_install(self, latest: str) -> bool:
        """Automatic installation needs the switch, an installed build, and no loop."""
        if not self.settings.get("auto_update") or self._updating:
            return False
        if latest and latest == self.settings.get("update_attempted"):
            LOG.info("auto update: %s already attempted, not retrying", latest)
            return False
        if not updater.installed_build():
            LOG.info("auto update: portable build, only notifying")
            return False
        return True

    def _auto_install(self, latest: str) -> None:
        self._updating = True
        self.settings["update_attempted"] = latest
        self.save_settings()
        LOG.info("auto update: downloading %s", latest)
        self._set_status(self.t("updating", version=latest), "warn")
        if self.tray is not None:
            self.tray.notify(version.APP_NAME, self.t("updating", version=latest))
        threading.Thread(target=self._download_worker, daemon=True).start()
        self.root.after(300, self._poll_download)

    def _download_worker(self) -> None:
        target = Path(tempfile.gettempdir()) / update.SETUP_NAME
        self._download_results.put(update.download_installer(target))

    def _poll_download(self) -> None:
        try:
            path = self._download_results.get_nowait()
        except queue.Empty:
            self.root.after(300, self._poll_download)
            return
        self._updating = False
        if path is None:
            LOG.warning("auto update: download or checksum failed")
            self._set_status(self.t("update_install_failed"), "error")
            if self.tray is not None:
                self.tray.notify(version.APP_NAME, self.t("update_install_failed"))
            with contextlib.suppress(OSError):
                (Path(tempfile.gettempdir()) / update.SETUP_NAME).unlink()
            return
        LOG.info("auto update: verified, handing over to the installer")
        if updater.launch(path):
            self.quit()
            return
        LOG.warning("auto update: could not start the installer")
        self._set_status(self.t("update_install_failed"), "error")

    # ------------------------------------------------------------ tray / hotkeys
    def _start_tray(self) -> None:
        if not self.use_tray:
            return
        self.tray = tray.Tray(
            title=version.APP_NAME,
            icon_path=str(resource_path("assets/volume-amplifier.ico")),
            menu=self._tray_menu,
            on_open=lambda: self._later(self.show_window),
        )
        if not self.tray.start():
            self.tray = None
            LOG.info("tray unavailable, falling back to the taskbar")
            return
        LOG.info("tray icon active")
        self.tray.set_tooltip(f"{version.APP_NAME} - {self.percent} %")
        self.root.after(TRAY_PUMP_MS, self._pump_tray)
        self._sync_hotkeys()

    def _pump_tray(self) -> None:
        try:
            if self.tray is not None:
                self.tray.pump()
        except Exception:
            LOG.exception("tray pump failed")
        finally:
            self.root.after(TRAY_PUMP_MS, self._pump_tray)

    def _later(self, action: Callable[[], None]) -> None:
        self.root.after(0, action)

    def _tray_menu(self) -> list[tuple[str, Callable[[], None]]]:
        return [
            (self.t("tray_open"), lambda: self._later(self.show_window)),
            (self.t("setup"), lambda: self._later(self.show_settings)),
            (self.t("report"), lambda: self._later(self._report_bug)),
            (self.t("tray_exit"), self.quit),
        ]

    def show_window(self) -> None:
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def show_settings(self) -> None:
        if self.settings_window is not None:
            self.settings_window.focus()
            return
        self.settings_window = settingswindow.SettingsWindow(self)

    def _sync_hotkeys(self) -> bool:
        """(Re)register both hotkeys. False means Windows refused one of them."""
        if self.tray is None:
            return True
        self.tray.unregister_hotkey(HOTKEY_UP)
        self.tray.unregister_hotkey(HOTKEY_DOWN)
        accepted = True
        for ident, name, action in (
            (HOTKEY_UP, "hotkey_up", self._boost_up),
            (HOTKEY_DOWN, "hotkey_down", self._boost_down),
        ):
            parsed = hotkey.parse(self.settings.get(name, ""))
            if parsed is None:
                continue
            if not self.tray.register_hotkey(ident, parsed[0], parsed[1], action):
                accepted = False
                LOG.warning("hotkey refused by Windows: %s", self.settings.get(name))
            else:
                LOG.info("hotkey registered: %s", self.settings.get(name))
        return accepted

    def set_hotkey(self, name: str, combination: str) -> bool:
        if combination and not hotkey.is_valid(combination):
            return False
        previous = self.settings.get(name, "")
        self.settings[name] = combination
        self.save_settings()
        if self._sync_hotkeys():
            LOG.info("hotkey %s = %s", name, combination or "(none)")
            return True
        self.settings[name] = previous
        self.save_settings()
        self._sync_hotkeys()
        return False

    def suspend_hotkeys(self) -> None:
        if self.tray is not None:
            self.tray.unregister_hotkey(HOTKEY_UP)
            self.tray.unregister_hotkey(HOTKEY_DOWN)

    def resume_hotkeys(self) -> None:
        self._sync_hotkeys()

    def _boost_up(self) -> None:
        self._nudge_boost(BOOST_STEP)

    def _boost_down(self) -> None:
        self._nudge_boost(-BOOST_STEP)

    def _nudge_boost(self, delta: int) -> None:
        low = gainmath.MIN_PERCENT
        high = int(self.settings["max_percent"])
        self.entry_var.set(str(max(low, min(high, self.percent + delta))))
        self._apply()
        self._announce_level()

    def _level_text(self) -> str:
        gain = (
            self.t("muted")
            if self.percent == 0
            else gainmath.format_db(gainmath.percent_to_db(self.percent))
        )
        return f"{self.percent} % \u00b7 {gain}"

    def _announce_level(self) -> None:
        """One toast for a burst of hotkey presses, and only while hidden."""
        if self.tray is None or self.root.state() != "withdrawn":
            return
        if self._toast_job is not None:
            self.root.after_cancel(self._toast_job)
        self._toast_job = self.root.after(TOAST_DELAY_MS, self._show_level_toast)

    def _show_level_toast(self) -> None:
        self._toast_job = None
        if self.tray is None:
            return
        try:
            if not self.tray.notify(version.APP_NAME, self._level_text()):
                LOG.info("level toast not shown")
        except Exception:
            LOG.exception("level toast failed")

    def save_settings(self) -> None:
        settings.save(SETTINGS_PATH, self.settings)
        self.settings = settings.load(SETTINGS_PATH)

    def _rebuild(self) -> None:
        for child in self.root.winfo_children():
            child.destroy()
        self._build()
        self._refresh(self.percent)
        self._apply(silent=True)

    def _on_slide(self, value: int) -> None:
        self.percent = value
        self._refresh(value)
        self._preview_level(value)

    def _preview_level(self, value: int) -> None:
        """A short tone that sounds like the level the slider points to.

        The gain has not been written yet while dragging, so the tone carries the
        difference between the target and what is applied: played through the APO,
        the result matches the slider position instead of doubling the boost.
        """
        if not self.settings.get("preview_sound", True):
            return
        now = time.monotonic()
        if now - self._last_preview < PREVIEW_INTERVAL:
            return
        self._last_preview = now
        delta = gainmath.percent_to_db(value) - gainmath.percent_to_db(self._applied)
        preview.play_level(max(-24.0, min(24.0, delta)))

    def _test_tone(self) -> None:
        preview.play_level(0.0, preview.LONG_MS)

    def _on_slide_release(self, value: int) -> None:
        self.percent = value
        self._apply()

    def _toggle_autostart(self, wanted: bool) -> None:
        if wanted:
            if not messagebox.askyesno(self.t("autostart"), self.t("autostart_question")):
                self.toggle.set_state(False)
                return
            try:
                autostart.enable()
            except OSError as exc:
                self.toggle.set_state(False)
                self._set_status(self.t("autostart_failed", error=str(exc)), "error")
                return
            self.autostart_enabled = True
            self.toggle.set_state(True)
            return
        try:
            autostart.disable()
        except OSError as exc:
            self._set_status(self.t("autostart_failed", error=str(exc)), "error")
            return
        self.autostart_enabled = False
        self.toggle.set_state(False)

    def _refresh(self, percent: int) -> None:
        text = str(percent)
        self.number_canvas.itemconfigure(self._number_item, text=text)
        self.number_canvas.coords(self._percent_item, self.number_font.measure(text) + 7, 70)
        db = gainmath.percent_to_db(percent)
        self.gain_var.set(self.t("muted") if percent == 0 else gainmath.format_db(db))
        self.entry_var.set(text)
        if self.slider.get() != percent:
            self.slider.set_value(percent)
        self.warning_var.set(
            self.t("warning", gain=gainmath.format_db(db)) if percent > CLIP_THRESHOLD else ""
        )

    def _apply(self, silent: bool = False) -> None:
        raw = self.entry_var.get().strip()
        try:
            number = round(float(raw))
        except (TypeError, ValueError, OverflowError):
            self._refresh(self.percent)
            self._set_status(self.t("bad_number"), "warn")
            return

        value = max(0, min(self.settings["max_percent"], gainmath.clamp_percent(number)))
        if settings.should_confirm(value, self.settings) and value > self._applied:
            gain_text = gainmath.format_db(gainmath.percent_to_db(value))
            accepted, dont_ask = confirmdialog.LoudConfirm(self).confirm(
                self.t("confirm_loud", gain=gain_text)
            )
            if dont_ask:
                self.settings["confirm_above"] = 0
                self.save_settings()
                LOG.info("loud confirmation disabled by the user")
            if not accepted:
                self.percent = self._applied
                self._refresh(self.percent)
                return
        self.percent = value
        self._refresh(value)
        save_state(value, self.language)

        if not self.engine.available():
            self._set_status(self.t("not_available"), "error")
            return

        try:
            self.engine.apply(value)
        except (backends.BackendError, OSError) as exc:
            LOG.warning("apply failed percent=%s error=%s", value, exc)
            self._set_status(self.t("write_failed", error=str(exc)), "error")
            return

        self._applied = value
        LOG.info("applied percent=%s engine=%s", value, self.engine.key)
        if self.tray is not None:
            self.tray.set_tooltip(f"{version.APP_NAME} - {value} %")
        gain = self.t("muted") if value == 0 else gainmath.format_db(
            gainmath.percent_to_db(value)
        )
        state = self.health()
        if state["level"] == "detached":
            self._set_status(self.t("detached"), "error")
        elif state["level"] == "drift":
            self._set_status(self.t("drift"), "warn")
        else:
            self._set_status(self.t("applied", gain=gain, engine=self.engine.engine), "ok")

    def health(self) -> dict:
        return engine_health(self.engine, self.percent)

    def _set_status(self, text: str, kind: str) -> None:
        self._dot_colour = {"ok": T.OK, "warn": T.WARN, "error": T.ERROR}.get(kind, T.MUTED)
        self.status_var.set(text)
        self.status_label.configure(fg=T.MUTED if kind == "idle" else self._dot_colour)
        self._draw_dot()

    def _draw_dot(self) -> None:
        self.dot.delete("all")
        self.dot.create_oval(1, 1, 9, 9, fill=self._dot_colour, outline="")

    def _show_setup(self) -> None:
        self.show_settings()

    def _on_close(self) -> None:
        if self.tray is not None and self.settings.get("close_to_tray"):
            self.root.withdraw()
            LOG.info("hidden to the notification area")
            return
        self.quit()

    def quit(self) -> None:
        save_state(self.percent, self.language)
        if self.settings.get("restore_on_exit") and self._applied != gainmath.DEFAULT_PERCENT:
            try:
                self.engine.apply(gainmath.DEFAULT_PERCENT)
                LOG.info("restored 100%% on exit")
            except (backends.BackendError, OSError) as exc:
                LOG.warning("restore on exit failed: %s", exc)
        if self.tray is not None:
            self.tray.stop()
            self.tray = None
        self.root.destroy()


def _smoke_engine() -> int:
    import tempfile

    if not sys.platform.startswith("win"):
        print("smoke skipped: Windows-only engine")
        return 0

    import apo

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.txt"
        path.write_bytes(
            b"\xef\xbb\xbfDevice: Headphones\r\n"
            b"Filter: ON PK Fc 80 Hz Gain 3 dB Q 1.0\r\n"
        )
        apo.apply_percent(path, 500)
        text, encoding, has_bom = apo.read_config(path)
        assert configfile.include_present(text), text
        assert "Filter: ON PK Fc 80 Hz Gain 3 dB Q 1.0" in text, text
        assert has_bom and encoding == "utf-8", (has_bom, encoding)
        assert "13.98 dB" in apo.gain_text(path), apo.gain_text(path)
        assert path.with_name(path.name + ".amplificador-voz.bak").exists()

        apo.apply_percent(path, 120)
        text, _, _ = apo.read_config(path)
        assert "Preamp: 1.58 dB" in apo.gain_text(path), apo.gain_text(path)
        assert text.count("Filter: ON PK Fc 80 Hz Gain 3 dB Q 1.0") == 1, text
    print("smoke ok")
    return 0


def _smoke_ui() -> int:
    import tempfile

    if not sys.platform.startswith("win"):
        print("smoke-ui skipped: Windows-only engine")
        return 0

    import apo

    global STATE_PATH, SETTINGS_PATH
    original_state = STATE_PATH
    original_settings = SETTINGS_PATH
    with tempfile.TemporaryDirectory() as tmp:
        STATE_PATH = Path(tmp) / "state.json"
        SETTINGS_PATH = Path(tmp) / "settings.json"
        SETTINGS_PATH.write_text('{"confirm_above": 0}', encoding="utf-8")
        STATE_PATH.write_text('{"percent": 100, "language": "en"}', encoding="utf-8")
        path = Path(tmp) / "config.txt"
        path.write_text("Device: Speakers\n", encoding="utf-8")
        os.environ[apo.ENV_OVERRIDE] = str(path)
        root = tk.Tk()
        root.withdraw()
        try:
            window = AmplifierApp(root, backends.detect(), use_tray=False)
            root.update()

            window.slider.set_value(500, notify=True)
            window._on_slide_release(500)
            root.update()
            text = path.read_text(encoding="utf-8")
            assert configfile.include_present(text), text
            assert "13.98 dB" in apo.gain_text(path), apo.gain_text(path)
            assert "Device: Speakers" in text, text

            window.slider.set_value(250, notify=True)
            window._on_slide_release(250)
            root.update()
            window.entry_var.set("abc")
            window._apply()
            root.update()
            assert window.percent == 250, window.percent
            assert "Enter a number" in window.status_var.get(), window.status_var.get()
            assert "7.96 dB" in apo.gain_text(path), apo.gain_text(path)

            window._set_language("fr")
            root.update()
            assert window.language == "fr"
            assert window.t("apply") == "Appliquer", window.t("apply")
            assert int(window.lang_button["width"]) > 1

            window._set_language("en")
            root.update()
            window.slider.set_value(0, notify=True)
            window._on_slide_release(0)
            root.update()
            assert "-100.00 dB" in apo.gain_text(path), apo.gain_text(path)
        finally:
            STATE_PATH = original_state
            SETTINGS_PATH = original_settings
            os.environ.pop(apo.ENV_OVERRIDE, None)
            root.destroy()
    print("smoke-ui ok")
    return 0


def engine_health(engine, percent: int) -> dict:
    """Whether the OS is really running the APO. Read-only: never writes."""
    if engine.key != "windows":
        return {"level": "unsupported"}
    try:
        import apo
        import verify
    except ImportError:
        return {"level": "unknown"}
    try:
        path = getattr(engine, "path", None)
        if path is None or not path.exists():
            return {"level": "missing"}
        text = apo.gain_text(path)
        return verify.health(text, gainmath.percent_to_db(percent))
    except (OSError, apo.ConfigError):
        return {"level": "unknown"}

def _engine_report(engine) -> dict:
    """Facts about the gain engine, without any user content."""
    report = {
        "backend": engine.key,
        "engine": engine.engine,
        "available": engine.available(),
        "location": engine.location(),
        "config": {"exists": False},
    }
    if engine.key == "windows":
        import apo

        path = getattr(engine, "path", None)
        if path is not None and path.exists():
            try:
                text, encoding, has_bom = apo.read_config(path)
            except apo.ConfigError as exc:
                report["config"] = {"exists": True, "error": str(exc)}
                return report
            report["config"] = {
                "exists": True,
                "bytes": path.stat().st_size,
                "encoding": encoding,
                "bom": has_bom,
                "include_present": configfile.include_present(text),
                "preamp": diagnostics.text_block(apo.gain_text(path)),
            }
    return report


def _diagnostics() -> int:
    """Write the support bundle and print its path."""
    percent, language = load_state()
    engine = backends.detect()
    report = diagnostics.export(
        {
            "state": {"percent": percent, "language": language},
            "autostart": autostart.is_enabled(),
            "system_language": i18n.system_language(),
            "engine": _engine_report(engine),
            "verification": engine_health(engine, percent),
        }
    )
    print(report)
    return 0


def main() -> int:
    arguments = set(sys.argv[1:])
    if "--version" in arguments:
        print(f"{version.APP_NAME} {version.VERSION}")
        print(f"by {version.AUTHOR} - {version.REPOSITORY}")
        return 0
    if "--settings" in arguments:
        print(json.dumps({"path": str(SETTINGS_PATH), "effective": settings.load(SETTINGS_PATH)}, ensure_ascii=False))
        return 0
    if "--health" in arguments:
        print(json.dumps(engine_health(backends.detect(), load_state()[0]), ensure_ascii=False))
        return 0
    if "--diagnostics" in arguments:
        return _diagnostics()
    if "--report" in arguments:
        print(report.build_issue_url(app_version=version.VERSION, os_name=report.os_option()))
        return 0
    if "--smoke" in arguments:
        return _smoke_engine()
    if "--smoke-ui" in arguments:
        return _smoke_ui()

    if not _claim_single_instance():
        _focus_existing_window()
        return 0

    root = tk.Tk()
    diagnostics.configure(root)
    logging.getLogger("app").info(
        "start version=%s frozen=%s args=%s", version.VERSION, bool(getattr(sys, "frozen", False)), sys.argv[1:]
    )
    AmplifierApp(root, backends.detect(), minimized="--minimized" in arguments)
    apply_dark_titlebar(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
