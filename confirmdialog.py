"""Modal confirmation with a "do not ask again" option.

Tk's messagebox cannot offer a checkbox, and this particular warning is the one
people most want to silence, so it gets a small themed window of its own.
"""

from __future__ import annotations

import tkinter as tk

import theme as T
import widgets as W


class LoudConfirm:
    """``confirm(message)`` blocks and returns ``(accepted, dont_ask_again)``."""

    def __init__(self, app) -> None:
        self.app = app
        self.accepted = False
        self.dont_ask = False
        self._flag: tk.BooleanVar | None = None
        self._switch: W.ToggleSwitch | None = None

    def confirm(self, message: str) -> tuple[bool, bool]:
        self.accepted = False
        self.dont_ask = False
        self._flag = tk.BooleanVar(value=False)

        top = tk.Toplevel(self.app.root)
        top.title(self.app.t("confirm_title"))
        top.configure(bg=T.BG)
        top.resizable(False, False)
        top.transient(self.app.root)
        top.protocol("WM_DELETE_WINDOW", lambda: self._close(top, False))

        tk.Label(
            top,
            text="\u26a0",
            bg=T.BG,
            fg=T.WARN,
            font=(self.app.family, T.px(18)),
        ).pack(side="left", padx=(18, 0), pady=18, anchor="n")

        body = tk.Frame(top, bg=T.BG)
        body.pack(side="left", fill="both", expand=True, padx=(10, 18), pady=18)

        tk.Label(
            body,
            text=message,
            bg=T.BG,
            fg=T.TEXT,
            font=(self.app.family, T.px(10)),
            wraplength=320,
            justify="left",
            anchor="w",
        ).pack(fill="x")

        row = tk.Frame(body, bg=T.BG)
        row.pack(fill="x", pady=(12, 0))
        self._switch = W.ToggleSwitch(row, False, self._set_flag)
        self._switch.pack(side="left")
        label = tk.Label(
            row,
            text=self.app.t("dont_ask_again"),
            bg=T.BG,
            fg=T.MUTED,
            font=(self.app.family, T.px(9)),
            cursor="hand2",
        )
        label.pack(side="left", padx=(8, 0))
        label.bind("<Button-1>", lambda _event: self._toggle_flag())

        buttons = tk.Frame(body, bg=T.BG)
        buttons.pack(fill="x", pady=(14, 0))
        W.PillButton(
            buttons,
            self.app.t("apply"),
            lambda: self._close(top, True),
            family=self.app.family,
            size=10,
        ).pack(side="right")
        W.PillButton(
            buttons,
            self.app.t("cancel"),
            lambda: self._close(top, False),
            family=self.app.family,
            size=10,
            weight="normal",
            fill=T.SURFACE,
            hover=T.SURFACE_HOVER,
            pressed=T.SURFACE_HOVER,
            fg=T.TEXT,
        ).pack(side="right", padx=(0, 8))

        top.update_idletasks()
        x = self.app.root.winfo_rootx() + (self.app.root.winfo_width() - top.winfo_reqwidth()) // 2
        y = self.app.root.winfo_rooty() + 60
        top.geometry(f"+{max(0, x)}+{max(0, y)}")
        top.grab_set()
        top.focus_force()
        self.app.root.wait_window(top)
        return self.accepted, self.dont_ask

    def _set_flag(self, value: bool) -> None:
        if self._flag is not None:
            self._flag.set(bool(value))

    def _toggle_flag(self) -> None:
        if self._flag is None:
            return
        value = not self._flag.get()
        self._flag.set(value)
        if self._switch is not None:
            self._switch.set_state(value)

    def _close(self, top: tk.Toplevel, accepted: bool) -> None:
        self.accepted = accepted
        self.dont_ask = accepted and bool(self._flag.get()) if self._flag is not None else False
        top.destroy()
