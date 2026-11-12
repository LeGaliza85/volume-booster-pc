"""Canvas-drawn controls: pill button, toggle switch and the volume slider.

Tk's native widgets cannot be recoloured on Windows, so the controls are drawn
on a Canvas. Tk's canvas primitives have no anti-aliasing, which leaves visible
stair-stepping on every rounded edge, so the round parts are rendered here as
small RGBA images: each pixel is the coverage of a 4x4 supersample grid, and Tk
composites the alpha over the canvas. The images are cached per interpreter, so
a redraw only recreates canvas items, never pixels.

Each control is self-contained: it draws from its own state, exposes a small API
and calls back on user interaction.
"""

from __future__ import annotations

import struct
import tkinter as tk
import zlib
from tkinter import font as tkfont
from typing import Literal

import theme as T

_SUPERSAMPLE = 4
_CACHE: dict[tuple[str, int, str], tk.PhotoImage] = {}


def _hex(colour: str) -> tuple[int, int, int]:
    value = colour.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def _png(width: int, height: int, rgba: bytearray) -> bytes:
    """Minimal PNG writer: truecolour+alpha, no filters."""

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    raw = bytearray()
    stride = width * 4
    for y in range(height):
        raw.append(0)
        raw += rgba[y * stride : (y + 1) * stride]
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )


def _disc(master, diameter: float, colour: str) -> tk.PhotoImage | None:
    """Anti-aliased filled circle, or None when Tk cannot build the image."""
    size = max(2, round(diameter))
    key = (str(master.tk), size, colour)
    image = _CACHE.get(key)
    if image is not None:
        return image

    red, green, blue = _hex(colour)
    radius = size / 2
    step = 1.0 / _SUPERSAMPLE
    total = _SUPERSAMPLE * _SUPERSAMPLE
    data = bytearray(size * size * 4)
    try:
        for y in range(size):
            for x in range(size):
                hits = 0
                for sy in range(_SUPERSAMPLE):
                    dy = y + (sy + 0.5) * step - radius
                    for sx in range(_SUPERSAMPLE):
                        dx = x + (sx + 0.5) * step - radius
                        if dx * dx + dy * dy <= radius * radius:
                            hits += 1
                if hits:
                    offset = (y * size + x) * 4
                    data[offset] = red
                    data[offset + 1] = green
                    data[offset + 2] = blue
                    data[offset + 3] = hits * 255 // total
        image = tk.PhotoImage(master=master, data=_png(size, size, data), format="png")
    except tk.TclError:
        return None
    _CACHE[key] = image
    return image


def _pill(canvas: tk.Canvas, x1: float, y1: float, x2: float, y2: float, colour: str) -> None:
    """Rounded ends drawn as two discs, so the curve is anti-aliased."""
    left, top = round(x1), round(y1)
    right, bottom = round(x2), round(y2)
    height = bottom - top
    if height % 2:
        bottom -= 1
        height -= 1
    if height < 2:
        canvas.create_rectangle(left, top, right, bottom, fill=colour, outline="")
        return
    radius = height // 2
    centre = top + radius
    canvas.create_rectangle(left + radius, top, right - radius, bottom, fill=colour, outline="")
    disc = _disc(canvas, height, colour)
    if disc is None:
        canvas.create_oval(left, top, left + height, bottom, fill=colour, outline="")
        canvas.create_oval(right - height, top, right, bottom, fill=colour, outline="")
        return
    canvas.create_image(left + radius, centre, image=disc, anchor="center")
    canvas.create_image(right - radius, centre, image=disc, anchor="center")


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
        self._font = tkfont.Font(family=family, size=T.px(size), weight=weight)
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
        self.bind("<Button-1>", lambda _event: self._toggle())
        self.bind("<Return>", lambda _event: self._toggle())
        self.bind("<space>", lambda _event: self._toggle())
        self._draw()

    def _toggle(self) -> None:
        """Flip first, then report: the widget owns its look, the caller the effect.

        Callers that refuse the change call ``set_state`` with the old value, so
        the switch always matches what actually happened.
        """
        value = not self._value
        self.set_state(value)
        self._command(value)

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
        knob = int(radius) - 3
        disc = _disc(self, 2 * knob, "#FFFFFF")
        if disc is None:
            self.create_oval(
                centre - knob,
                radius - knob,
                centre + knob,
                radius + knob,
                fill="#FFFFFF",
                outline="",
            )
            return
        self.create_image(round(centre), round(radius), image=disc, anchor="center")


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
        position_of=None,
        value_at=None,
    ) -> None:
        super().__init__(master, bg=bg, highlightthickness=0, bd=0, height=self.HEIGHT)
        self.minimum, self.maximum = minimum, maximum
        self._value = int(value)
        self._on_change = on_change
        self._on_release = on_release
        # Position and value are separate scales: the app maps travel to dB and
        # the default stays linear for any other caller.
        self._position_of = position_of or self._linear_position
        self._value_at = value_at or self._linear_value

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

    def _linear_position(self, value: int) -> float:
        span = self.maximum - self.minimum
        return (value - self.minimum) / span if span else 0.0

    def _linear_value(self, ratio: float) -> int:
        return round(self.minimum + ratio * (self.maximum - self.minimum))

    def _thumb_x(self) -> float:
        ratio = max(0.0, min(1.0, self._position_of(self._value)))
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
        self.set_value(int(self._value_at(ratio)), notify=True)

    def _bar(self, left: float, right: float, centre: float, colour: str) -> None:
        half = self.TRACK_WIDTH // 2
        self.create_rectangle(left, centre - half, right, centre + half, fill=colour, outline="")
        disc = _disc(self, self.TRACK_WIDTH, colour)
        if disc is None:
            self.create_oval(left - half, centre - half, left + half, centre + half, fill=colour, outline="")
            self.create_oval(right - half, centre - half, right + half, centre + half, fill=colour, outline="")
            return
        self.create_image(left, centre, image=disc, anchor="center")
        self.create_image(right, centre, image=disc, anchor="center")

    def _draw(self) -> None:
        self.delete("all")
        width = self.winfo_width()
        if width <= 2:
            return
        centre = self.HEIGHT / 2
        left = self.PADDING
        right = width - self.PADDING
        self._bar(left, right, centre, T.TRACK)
        thumb_x = self._thumb_x()
        self._bar(left, max(left, thumb_x), centre, T.ACCENT)
        disc = _disc(self, 2 * self.THUMB, "#FFFFFF")
        if disc is None:
            self.create_oval(
                thumb_x - self.THUMB,
                centre - self.THUMB,
                thumb_x + self.THUMB,
                centre + self.THUMB,
                fill="#FFFFFF",
                outline="",
            )
            return
        self.create_image(thumb_x, centre, image=disc, anchor="center")
