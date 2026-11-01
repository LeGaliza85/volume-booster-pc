"""A short test tone, generated in memory and played through the default device.

Pure standard library: ``wave`` + ``struct`` build the WAV and ``winsound`` plays
it. Because it goes out through the default endpoint, Equalizer APO applies the
same boost to the tone as to your music — which is the whole point of a level
preview.

The tone is generated with a fade at both ends so it never clicks, and its
amplitude is clamped: a volume booster is exactly the wrong place for a sound
that can clip.
"""

from __future__ import annotations

import io
import math
import struct
import sys
import wave

SAMPLE_RATE = 44100
FREQUENCY = 520.0
BASE_AMPLITUDE = 0.12  # about -18 dBFS at the reference level
MAX_AMPLITUDE = 0.85
SHORT_MS = 180
LONG_MS = 600


def tone(amplitude: float, milliseconds: int, frequency: float = FREQUENCY) -> bytes:
    """Mono 16-bit WAV of a faded sine, as bytes."""
    frames = max(1, int(SAMPLE_RATE * max(1, milliseconds) / 1000))
    amplitude = max(0.0, min(MAX_AMPLITUDE, float(amplitude)))
    edge = max(1, int(frames * 0.15))
    samples = bytearray()
    for index in range(frames):
        if index < edge:
            envelope = index / edge
        elif index >= frames - edge:
            envelope = max(0.0, (frames - index) / edge)
        else:
            envelope = 1.0
        value = amplitude * envelope * math.sin(2 * math.pi * frequency * index / SAMPLE_RATE)
        samples += struct.pack("<h", int(value * 32767))
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(bytes(samples))
    return buffer.getvalue()


def amplitude_for(delta_db: float) -> float:
    """Amplitude that makes the tone sound ``delta_db`` louder than now."""
    try:
        factor = 10 ** (float(delta_db) / 20)
    except (OverflowError, ValueError):
        factor = 1.0
    return min(MAX_AMPLITUDE, BASE_AMPLITUDE * factor)


def play(wav: bytes) -> bool:
    """Play asynchronously through the default endpoint. False when unsupported."""
    if not sys.platform.startswith("win"):
        return False
    try:
        import winsound
    except ImportError:
        return False
    try:
        winsound.PlaySound(wav, winsound.SND_MEMORY | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
    except RuntimeError:
        return False
    return True


def play_level(delta_db: float, milliseconds: int = SHORT_MS) -> bool:
    return play(tone(amplitude_for(delta_db), milliseconds))
