"""Generate assets/volume-amplifier.ico (speaker on a rounded blue tile).

Pure standard library: renders each size with 4x supersampling, writes a classic
32-bit BGRA icon with an AND mask, no external image library needed.
"""

from __future__ import annotations

import math
import struct
from pathlib import Path

SIZES = (16, 24, 32, 48, 64, 128, 256)
SUPERSAMPLE = 4

ACCENT = (37, 99, 235)
GLYPH = (255, 255, 255)

OUTPUT = Path(__file__).resolve().parent.parent / "assets" / "volume-amplifier.ico"


def _in_rounded_rect(u: float, v: float, x0: float, y0: float, x1: float, y1: float, radius: float) -> bool:
    if not (x0 <= u <= x1 and y0 <= v <= y1):
        return False
    cx = min(max(u, x0 + radius), x1 - radius)
    cy = min(max(v, y0 + radius), y1 - radius)
    return (u - cx) ** 2 + (v - cy) ** 2 <= radius ** 2


def _in_polygon(u: float, v: float, points: list[tuple[float, float]]) -> bool:
    inside = False
    j = len(points) - 1
    for i, (xi, yi) in enumerate(points):
        xj, yj = points[j]
        if (yi > v) != (yj > v):
            crossing = (xj - xi) * (v - yi) / (yj - yi) + xi
            if u < crossing:
                inside = not inside
        j = i
    return inside


def _in_arc(u: float, v: float, centre_x: float, radius: float, thickness: float) -> bool:
    if u <= centre_x:
        return False
    distance = math.hypot(u - centre_x, v - 0.5)
    if abs(distance - radius) > thickness / 2:
        return False
    return abs(v - 0.5) <= distance * math.sin(math.radians(60))


def _in_speaker(u: float, v: float) -> bool:
    if 0.235 <= u <= 0.365 and 0.405 <= v <= 0.595:
        return True
    cone = [(0.355, 0.405), (0.530, 0.265), (0.530, 0.735), (0.355, 0.595)]
    if _in_polygon(u, v, cone):
        return True
    return _in_arc(u, v, 0.545, 0.105, 0.042) or _in_arc(u, v, 0.545, 0.175, 0.042)


def _sample(u: float, v: float) -> tuple[int, int, int, int]:
    if not _in_rounded_rect(u, v, 0.02, 0.02, 0.98, 0.98, 0.22):
        return (0, 0, 0, 0)
    if _in_speaker(u, v):
        return (*GLYPH, 255)
    return (*ACCENT, 255)


def _render(size: int) -> bytes:
    scale = SUPERSAMPLE
    pixels: list[tuple[int, int, int, int]] = []
    for y in range(size):
        for x in range(size):
            red = green = blue = alpha = 0
            for sy in range(scale):
                for sx in range(scale):
                    u = (x + (sx + 0.5) / scale) / size
                    v = (y + (sy + 0.5) / scale) / size
                    r, g, b, a = _sample(u, v)
                    red += r * a
                    green += g * a
                    blue += b * a
                    alpha += a
            samples = scale * scale
            if alpha == 0:
                pixels.append((0, 0, 0, 0))
            else:
                pixels.append(
                    (red // alpha, green // alpha, blue // alpha, alpha // samples)
                )

    rows = []
    for y in range(size - 1, -1, -1):  # bottom-up
        row = bytearray()
        for x in range(size):
            r, g, b, a = pixels[y * size + x]
            row += bytes((b, g, r, a))
        rows.append(bytes(row))
    xor = b"".join(rows)

    mask_row = ((size + 31) // 32) * 4
    mask = b"\x00" * (mask_row * size)
    return xor + mask


def _dib(size: int) -> bytes:
    header = struct.pack(
        "<IiiHHIIiiII",
        40,  # header size
        size,  # width
        size * 2,  # height (xor + and mask)
        1,  # planes
        32,  # bit count
        0,  # compression
        0,  # image size
        0,  # x pixels per metre
        0,  # y pixels per metre
        0,  # colours used
        0,  # important colours
    )
    return header + _render(size)


def build() -> Path:
    images = [(size, _dib(size)) for size in SIZES]
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    entries = bytearray()
    payload = bytearray()
    for size, dib in images:
        dimension = 0 if size >= 256 else size
        entries += struct.pack("<BBBBHHII", dimension, dimension, 0, 0, 1, 32, len(dib), offset)
        offset += len(dib)
        payload += dib
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(header + bytes(entries) + bytes(payload))
    return OUTPUT


if __name__ == "__main__":
    path = build()
    print(f"wrote {path} ({path.stat().st_size} bytes)")
