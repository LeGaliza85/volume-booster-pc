"""The settings window: Windows requirements, global hotkeys and startup options.

A real Toplevel instead of a message box, because the Windows checks are
actionable: each failing row can open the exact place in Windows where the fix
lives.
"""

from __future__ import annotations

import functools
import tkinter as tk

import hotkey
import theme as T
import widgets as W
import winenv

_STATE_COLOURS = {winenv.OK: T.OK, winenv.FAIL: T.ERROR, winenv.INFO: T.MUTED}


class SettingsWindow:
    """One instance at a time; ``open`` re-focuses the existing window."""

    def __init__(self, app) -> None:
        self.app = app
        self.top = tk.Toplevel(app.root)
        self.top.title(app.t("setup"))
        self.top.configure(bg=T.BG)
        self.top.resizable(False, False)
        self.top.transient(app.root)
        self.top.protocol("WM_DELETE_WINDOW", self.close)
        self._capturing: str | None = None
        self._requirements = tk.Frame(self.top, bg=T.BG)
        self._build()
        self.refresh()
        self._centre()

    # ------------------------------------------------------------- layout
    def _section(self, text: str, *, first: bool = False) -> None:
        tk.Label(
            self.top,
            text=text,
            bg=T.BG,
            fg=T.MUTED,
            font=(self.app.family, T.px(9), "bold"),
            anchor="w",
        ).pack(fill="x", padx=22, pady=((10, 4) if first else (14, 4)))

    def _build(self) -> None:
        self._section(self.app.t("windows_section"), first=True)
        self._requirements.pack(fill="x")

        self._section(self.app.t("hotkeys_section"))
        self._hotkey_row("hotkey_up", self.app.t("hotkey_up"))
        self._hotkey_row("hotkey_down", self.app.t("hotkey_down"))
        self._hotkey_hint = tk.Label(
            self.top,
            text="",
            bg=T.BG,
            fg=T.MUTED,
            font=(self.app.family, T.px(8)),
            anchor="w",
            wraplength=440,
            justify="left",
        )
        self._hotkey_hint.pack(fill="x", padx=22, pady=(4, 0))

        self._section(self.app.t("start_section"))
        self._toggle_row("start_hidden", self.app.t("start_hidden"))
        self._toggle_row("close_to_tray", self.app.t("close_to_tray"))

        footer = tk.Frame(self.top, bg=T.BG)
        footer.pack(fill="x", padx=22, pady=(14, 14))
        W.PillButton(
            footer, self.app.t("close"), self.close, family=self.app.family, size=10
        ).pack(side="right")

    def _hotkey_row(self, key: str, label: str) -> None:
        row = tk.Frame(self.top, bg=T.BG)
        row.pack(fill="x", padx=22, pady=3)
        tk.Label(
            row, text=label, bg=T.BG, fg=T.TEXT, font=(self.app.family, T.px(10)), width=9, anchor="w"
        ).pack(side="left")
        field = tk.Label(
            row,
            text=self._hotkey_text(key),
            bg=T.SURFACE,
            fg=T.TEXT,
            font=(self.app.family, T.px(9)),
            padx=12,
            pady=5,
            cursor="hand2",
        )
        field.pack(side="left")
        field.bind("<Button-1>", functools.partial(self._on_field_click, key))
        clear = tk.Label(
            row,
            text="\u00d7",
            bg=T.BG,
            fg=T.MUTED,
            font=(self.app.family, T.px(11)),
            padx=6,
            cursor="hand2",
        )
        clear.pack(side="left")
        clear.bind("<Button-1>", functools.partial(self._on_clear_click, key))
        if not hasattr(self, "_fields"):
            self._fields = {}
        self._fields[key] = field

    def _toggle_row(self, key: str, label: str) -> None:
        row = tk.Frame(self.top, bg=T.BG)
        row.pack(fill="x", padx=22, pady=3)
        switch = W.ToggleSwitch(
            row,
            bool(self.app.settings.get(key)),
            functools.partial(self._set_bool, key),
        )
        switch.pack(side="left")
        tk.Label(
            row, text=label, bg=T.BG, fg=T.TEXT, font=(self.app.family, T.px(10)), cursor="hand2"
        ).pack(side="left", padx=(10, 0))

    def _on_field_click(self, key: str, _event) -> None:
        self._start_capture(key)

    def _on_clear_click(self, key: str, _event) -> None:
        self._clear_hotkey(key)

    def _hotkey_text(self, key: str) -> str:
        value = self.app.settings.get(key) or ""
        return value or self.app.t("hotkey_none")

    # ---------------------------------------------------------- requirements
    def refresh(self) -> None:
        for child in self._requirements.winfo_children():
            child.destroy()
        installed = winenv.apo_installed()
        health = self.app.health()
        for requirement in winenv.inspect(installed=installed, level=health.get("level", "missing")):
            self._requirement_row(requirement)

    def _requirement_row(self, requirement: dict) -> None:
        row = tk.Frame(self._requirements, bg=T.BG)
        row.pack(fill="x", padx=22, pady=3)
        tk.Label(
            row,
            text="\u25cf",
            bg=T.BG,
            fg=_STATE_COLOURS.get(requirement["state"], T.MUTED),
            font=(self.app.family, T.px(9)),
        ).pack(side="left", anchor="n", pady=(2, 0))
        body = tk.Frame(row, bg=T.BG)
        body.pack(side="left", fill="x", expand=True, padx=(8, 8))
        tk.Label(
            body,
            text=self.app.t(requirement["key"]),
            bg=T.BG,
            fg=T.TEXT,
            font=(self.app.family, T.px(10)),
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            body,
            text=self.app.t(requirement["key"] + "_body"),
            bg=T.BG,
            fg=T.MUTED,
            font=(self.app.family, T.px(8)),
            anchor="w",
            justify="left",
            wraplength=400,
        ).pack(fill="x")
        action = requirement["action"]
        if action != winenv.NONE:
            W.PillButton(
                row,
                self.app.t("open"),
                lambda name=action: winenv.open_action(name),
                family=self.app.family,
                size=8,
                weight="normal",
                fill=T.SURFACE,
                hover=T.SURFACE_HOVER,
                pressed=T.SURFACE_HOVER,
                fg=T.TEXT,
                padx=12,
                height=26,
            ).pack(side="right", anchor="n")

    # --------------------------------------------------------------- hotkeys
    def _start_capture(self, key: str) -> None:
        self._capturing = key
        self._fields[key].configure(text=self.app.t("hotkey_press"), fg=T.ACCENT)
        self._hotkey_hint.configure(text="")
        self.app.suspend_hotkeys()
        self.top.focus_force()
        self.top.bind("<KeyPress>", self._on_capture_key)

    def _stop_capture(self) -> None:
        if self._capturing is None:
            return
        key = self._capturing
        self._capturing = None
        self.top.unbind("<KeyPress>")
        self._fields[key].configure(text=self._hotkey_text(key), fg=T.TEXT)
        self.app.resume_hotkeys()

    def _on_capture_key(self, event) -> str:
        if event.keysym == "Escape":
            self._stop_capture()
            return "break"
        if event.keysym in {"Control_L", "Control_R", "Alt_L", "Alt_R", "Shift_L", "Shift_R", "Super_L", "Super_R"}:
            return "break"
        combination = hotkey.from_event(event.keysym, hotkey.pressed_modifiers())
        if not combination:
            self._hotkey_hint.configure(text=self.app.t("hotkey_invalid"), fg=T.WARN)
            return "break"
        key = self._capturing
        self._stop_capture()
        if key is None:
            return "break"
        self._set_hotkey(key, combination)
        return "break"

    def _set_hotkey(self, key: str, combination: str) -> None:
        accepted = self.app.set_hotkey(key, combination)
        self._fields[key].configure(text=self._hotkey_text(key))
        if accepted:
            self._hotkey_hint.configure(text=self.app.t("hotkey_saved"), fg=T.OK)
        else:
            self._hotkey_hint.configure(
                text=self.app.t("hotkey_taken", combo=combination), fg=T.ERROR
            )

    def _clear_hotkey(self, key: str) -> None:
        self.app.set_hotkey(key, "")
        self._fields[key].configure(text=self._hotkey_text(key))
        self._hotkey_hint.configure(text=self.app.t("hotkey_saved"), fg=T.OK)

    # -------------------------------------------------------------- toggles
    def _set_bool(self, key: str, value: bool) -> None:
        self.app.settings[key] = bool(value)
        self.app.save_settings()

    # ------------------------------------------------------------------ misc
    def _centre(self) -> None:
        self.top.update_idletasks()
        width = max(self.top.winfo_reqwidth(), 480)
        height = self.top.winfo_reqheight()
        root = self.app.root
        x = root.winfo_rootx() + (root.winfo_width() - width) // 2
        y = root.winfo_rooty() + 40
        limit = self.top.winfo_screenheight() - height - 20
        y = min(y, max(0, limit))
        self.top.geometry(f"{width}x{height}+{max(0, x)}+{max(0, y)}")

    def focus(self) -> None:
        self.top.deiconify()
        self.top.lift()
        self.top.focus_force()
        self.refresh()

    def close(self) -> None:
        self._stop_capture()
        self.app.settings_window = None
        self.top.destroy()
