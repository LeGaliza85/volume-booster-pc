"""Design tokens: one dark palette shared by every widget."""

from __future__ import annotations

from tkinter import font as tkfont

BG = "#0B1220"
SURFACE = "#16223A"
SURFACE_HOVER = "#1D2B45"
BORDER = "#24324E"
TEXT = "#F2F6FC"
MUTED = "#8DA0BC"
ACCENT = "#4F8CFF"
ACCENT_HOVER = "#6EA0FF"
ACCENT_PRESS = "#3D78E8"
TRACK = "#22304A"
OK = "#34D399"
WARN = "#FBBF24"
ERROR = "#F87171"

_FONT_STACK = (
    "Segoe UI Variable Text",
    "Segoe UI",
    "Cantarell",
    "Inter",
    "DejaVu Sans",
    "Helvetica",
)


def pick_font(root) -> str:
    """First font in the stack the system actually has."""
    available = set(tkfont.families(root))
    for name in _FONT_STACK:
        if name in available:
            return name
    return "TkDefaultFont"
