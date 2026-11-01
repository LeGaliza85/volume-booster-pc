"""Tests for the preview tone: it must be a valid WAV and never clip."""

from __future__ import annotations

import io
import struct
import sys
import unittest
import wave

import preview


def read_wav(data: bytes) -> tuple[int, int, int, list[int]]:
    with wave.open(io.BytesIO(data)) as handle:
        channels = handle.getnchannels()
        width = handle.getsampwidth()
        rate = handle.getframerate()
        frames = handle.readframes(handle.getnframes())
    samples = list(struct.unpack(f"<{len(frames) // 2}h", frames))
    return channels, width, rate, samples


class ToneTests(unittest.TestCase):
    def test_is_a_mono_16_bit_wav(self):
        channels, width, rate, _samples = read_wav(preview.tone(0.2, 100))
        self.assertEqual(channels, 1)
        self.assertEqual(width, 2)
        self.assertEqual(rate, preview.SAMPLE_RATE)

    def test_length_matches_the_request(self):
        _c, _w, rate, samples = read_wav(preview.tone(0.2, 200))
        self.assertAlmostEqual(len(samples) / rate, 0.2, places=2)

    def test_never_clips(self):
        for amplitude in (0.5, 1.0, 5.0, -3.0):
            _c, _w, _r, samples = read_wav(preview.tone(amplitude, 60))
            self.assertLessEqual(max(abs(value) for value in samples), int(preview.MAX_AMPLITUDE * 32767) + 1)

    def test_starts_and_ends_quietly(self):
        _c, _w, _r, samples = read_wav(preview.tone(0.5, 120))
        self.assertLess(abs(samples[0]), 600)
        self.assertLess(abs(samples[-1]), 600)

    def test_silence_stays_silent(self):
        _c, _w, _r, samples = read_wav(preview.tone(0.0, 60))
        self.assertEqual(max(abs(value) for value in samples), 0)

    def test_zero_milliseconds_still_produces_a_frame(self):
        _c, _w, _r, samples = read_wav(preview.tone(0.2, 0))
        self.assertGreaterEqual(len(samples), 1)


class AmplitudeTests(unittest.TestCase):
    def test_zero_db_is_the_reference(self):
        self.assertAlmostEqual(preview.amplitude_for(0), preview.BASE_AMPLITUDE)

    def test_six_db_is_double(self):
        self.assertAlmostEqual(preview.amplitude_for(6.0206), preview.BASE_AMPLITUDE * 2, places=5)

    def test_negative_db_is_quieter(self):
        self.assertLess(preview.amplitude_for(-6), preview.amplitude_for(0))

    def test_clamped_at_the_top(self):
        self.assertEqual(preview.amplitude_for(60), preview.MAX_AMPLITUDE)

    def test_extremes_do_not_explode(self):
        self.assertGreaterEqual(preview.amplitude_for(-4000), 0.0)
        self.assertEqual(preview.amplitude_for(4000), preview.MAX_AMPLITUDE)


class PlayTests(unittest.TestCase):
    def test_a_silent_tone_plays_or_declines_cleanly(self):
        # winsound refuses SND_MEMORY together with SND_ASYNC, so play() must go
        # through a file; this fails loudly if somebody switches it back.
        result = preview.play(preview.tone(0.0, 20))
        if sys.platform.startswith("win"):
            self.assertTrue(result)
        else:
            self.assertFalse(result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
