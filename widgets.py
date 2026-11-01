"""Canvas-drawn controls: pill button, toggle switch and the volume slider.

Tk's native widgets cannot be recoloured on Windows, so the controls are drawn
on a Canvas. Each one is self-contained: it draws from its own state, exposes a
small API and calls back on user interaction.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from typing import Literal

import theme as T


def _pill(canvas: tk.Canvas, x1: float, y1: float, x2: float, y2: float, colour: str) -> None:
    radius = (y2 - y1) / 2
    canvas.create_oval(x1, y1, x1 + 2 * radius, y2, fill=colour, outline="")
    canvas.create_oval(x2 - 2 * radius, y1, x2, y2, fill=colour, outline="")
    canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=colour, outline="")


class PillButton(tk.Canvas):
    """Rounded flat button with hover and pressed states."""

    def __init__(
        self,
        master,
        text: str,
        command,
        *,
        family: str,
        size: int = 10,
        weight: Literal["normal", "bold"] = "bold",
        fill: str = T.ACCENT,
        hover: str = T.ACCENT_HOVER,
        pressed: str = T.ACCENT_PRESS,
        fg: str = "#FFFFFF",
        bg: str = T.BG,
        padx: int = 18,
        height: int = 34,
    ) -> None:
        super().__init__(master, bg=bg, highlightthickness=0, bd=0, height=height, width=1)
        self._command = command
        self._fill, self._hover, self._pressed, self._fg = fill, hover, pressed, fg
        self._padx = padx
        self._text = text
        self._font = tkfont.Font(family=family, size=size, weight=weight)
        self._colour = fill

        self.configure(cursor="hand2", takefocus=1)
        self.bind("<Configure>", lambda _event: self._draw())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_down)
        self.bind("<ButtonRelease-1>", self._on_up)
        self.bind("<Return>", lambda _event: self._invoke())
        self.bind("<space>", lambda _event: self._invoke())
        self.set_text(text)

    def set_text(self, text: str) -> None:
        self._text = text
        self.configure(width=self._font.measure(text) + 2 * self._padx)
        self._draw()

    def _invoke(self) -> None:
        if self._command:
            self._command()

    def _on_enter(self, _event) -> None:
        self._colour = self._hover
        self._draw()

    def _on_leave(self, _event) -> None:
        self._colour = self._fill
        self._draw()

    def _on_down(self, _event) -> None:
        self._colour = self._pressed
        self._draw()

    def _on_up(self, _event) -> None:
        self._colour = self._hover
        self._draw()
        self.focus_set()
        self._invoke()

    def _draw(self) -> None:
        self.delete("all")
        width = max(self.winfo_width(), int(self["width"]))
        height = max(self.winfo_height(), int(self["height"]))
        if width <= 2 or height <= 2:
            return
        _pill(self, 1, 1, width - 1, height - 1, self._colour)
        self.create_text(
            width / 2,
            height / 2,
            text=self._text,
            fill=self._fg,
            font=self._font,
            anchor="center",
        )


class ToggleSwitch(tk.Canvas):
    """Small iOS-style switch. The caller owns the value and its side effects."""

    WIDTH = 46
    HEIGHT = 26

    def __init__(self, master, value: bool, command, *, bg: str = T.BG) -> None:
        super().__init__(master, bg=bg, highlightthickness=0, bd=0, width=self.WIDTH, height=self.HEIGHT)
        self._value = bool(value)
        self._command = command
        self.configure(cursor="hand2", takefocus=1)
        self.bind("<Button-1>", lambda _event: self._command(not self._value))
        self.bind("<Return>", lambda _event: self._command(not self._value))
        self.bind("<space>", lambda _event: self._command(not self._value))
        self._draw()

    def get(self) -> bool:
        return self._value

    def set_state(self, value: bool) -> None:
        self._value = bool(value)
        self._draw()

    def _draw(self) -> None:
        self.delete("all")
        width, height = self.WIDTH, self.HEIGHT
        radius = height / 2
        _pill(self, 0, 0, width, height, T.ACCENT if self._value else T.TRACK)
        centre = width - radius if self._value else radius
        knob = radius - 3
        self.create_oval(
            centre - knob,
            radius - knob,
            centre + knob,
            radius + knob,
            fill="#FFFFFF",
            outline="",
        )


class ModernSlider(tk.Canvas):
    """Continuous slider with a filled track and a round thumb."""

    HEIGHT = 44
    PADDING = 13
    TRACK_WIDTH = 8
    THUMB = 10

    def __init__(
        self,
        master,
        *,
        minimum: int,
        maximum: int,
        value: int,
        on_change,
        on_release,
        bg: str = T.BG,
    ) -> None:
        super().__init__(master, bg=bg, highlightthickness=0, bd=0, height=self.HEIGHT)
        self.minimum, self.maximum = minimum, maximum
        self._value = int(value)
        self._on_change = on_change
        self._on_release = on_release

        self.configure(cursor="hand2", takefocus=1)
        self.bind("<Configure>", lambda _event: self._draw())
        self.bind("<Button-1>", self._on_click)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_up)
        self.bind("<Left>", lambda _event: self._nudge(-1))
        self.bind("<Right>", lambda _event: self._nudge(1))
        self.bind("<Down>", lambda _event: self._nudge(-1))
        self.bind("<Up>", lambda _event: self._nudge(1))
        self.bind("<Prior>", lambda _event: self._nudge(25))
        self.bind("<Next>", lambda _event: self._nudge(-25))
        self.bind("<Home>", lambda _event: self._set(self.minimum))
        self.bind("<End>", lambda _event: self._set(self.maximum))

    def get(self) -> int:
        return self._value

    def set_value(self, value: int, *, notify: bool = False) -> None:
        value = int(max(self.minimum, min(self.maximum, value)))
        if value == self._value:
            self._draw()
            return
        self._value = value
        self._draw()
        if notify:
            self._on_change(value)

    def _nudge(self, delta: int) -> None:
        self.set_value(self._value + delta, notify=True)
        self._on_release(self._value)

    def _set(self, value: int) -> None:
        self.set_value(value, notify=True)
        self._on_release(self._value)

    def _track_width(self) -> float:
        return max(1.0, self.winfo_width() - 2 * self.PADDING)

    def _thumb_x(self) -> float:
        ratio = (self._value - self.minimum) / (self.maximum - self.minimum)
        return self.PADDING + ratio * self._track_width()

    def _on_click(self, event) -> None:
        self.focus_set()
        self._set_from_x(event.x)

    def _on_drag(self, event) -> None:
        self._set_from_x(event.x)

    def _on_up(self, _event) -> None:
        self._on_release(self._value)

    def _set_from_x(self, x: float) -> None:
        ratio = (x - self.PADDING) / self._track_width()
        ratio = max(0.0, min(1.0, ratio))
        self.set_value(round(self.minimum + ratio * (self.maximum - self.minimum)), notify=True)

    def _draw(self) -> None:
        self.delete("all")
        width = self.winfo_width()
        if width <= 2:
            return
        centre = self.HEIGHT / 2
        left = self.PADDING
        right = width - self.PADDING
        self.create_line(
            left,
            centre,
            right,
            centre,
            width=self.TRACK_WIDTH,
            capstyle="round",
            fill=T.TRACK,
        )
        thumb_x = self._thumb_x()
        self.create_line(
            left,
            centre,
            max(left, thumb_x),
            centre,
            width=self.TRACK_WIDTH,
            capstyle="round",
            fill=T.ACCENT,
        )
        self.create_oval(
            thumb_x - self.THUMB,
            centre - self.THUMB,
            thumb_x + self.THUMB,
            centre + self.THUMB,
            fill="#FFFFFF",
            outline="",
        )
