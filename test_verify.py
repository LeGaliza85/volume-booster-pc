"""Tests for the engine verification (attachment, drift, health levels)."""

from __future__ import annotations

import unittest

import verify

SLOT_5 = "{d04e05a6-594b-4fb6-a80d-01af5eed7d1d},5"
SLOT_7 = "{d04e05a6-594b-4fb6-a80d-01af5eed7d1d},7"
OTHER = "{b725f130-47ef-101a-a5f1-02608c9eebac},10"
TV = "{11111111-1111-1111-1111-111111111111}"
SPEAKERS = "{22222222-2222-2222-2222-222222222222}"
SPEAKERS_DEVICE_ID = f"{{0.0.0.00000000}}.{SPEAKERS}"


class AttachmentTests(unittest.TestCase):
    def test_pre_mix_class_detected(self):
        self.assertTrue(verify.endpoint_has_apo({SLOT_5: verify.PRE_MIX.upper()}))

    def test_post_mix_class_detected(self):
        self.assertTrue(verify.endpoint_has_apo({SLOT_7: "  {EC1CC9CE-FAED-4822-828A-82A81A6F018F} "}))

    def test_stock_apo_is_not_equalizer_apo(self):
        properties = {
            SLOT_5: "{62dc1a93-ae24-464c-a43e-452f824c4250}",
            SLOT_7: "{637c490d-eee3-4c0a-973f-371958802da2}",
        }
        self.assertFalse(verify.endpoint_has_apo(properties))

    def test_other_property_keys_are_ignored(self):
        self.assertFalse(verify.endpoint_has_apo({OTHER: verify.PRE_MIX}))

    def test_empty_endpoint(self):
        self.assertFalse(verify.endpoint_has_apo({}))


class PreampTests(unittest.TestCase):
    def test_reads_value(self):
        self.assertEqual(verify.preamp_db("Preamp: 13.98 dB\n"), 13.98)

    def test_negative(self):
        self.assertEqual(verify.preamp_db("preamp: -6.02 dB"), -6.02)

    def test_missing(self):
        self.assertIsNone(verify.preamp_db("Filter: ON PK Fc 80 Hz"))

    def test_matches_within_tolerance(self):
        self.assertTrue(verify.matches_expected("Preamp: 13.98 dB", 13.98))
        self.assertTrue(verify.matches_expected("Preamp: 14.00 dB", 13.98))
        self.assertFalse(verify.matches_expected("Preamp: 0.00 dB", 13.98))
        self.assertFalse(verify.matches_expected("no block", 13.98))


class HealthTests(unittest.TestCase):
    def _health(self, text, expected, installed=True, endpoints=None, default_id=None):
        return verify.health(
            text,
            expected,
            is_installed=lambda: installed,
            list_endpoints=lambda: endpoints or [],
            default_id=default_id,
        )

    def test_ok_when_attached_and_block_matches(self):
        endpoints = [{"name": "Altavoces", "attached": True}]
        result = self._health("Preamp: 7.96 dB", 7.96, endpoints=endpoints)
        self.assertEqual(result["level"], "ok")
        self.assertEqual(result["devices"], ["Altavoces"])

    def test_drift_when_block_disagrees(self):
        endpoints = [{"name": "Altavoces", "attached": True}]
        result = self._health("Preamp: 0.00 dB", 13.98, endpoints=endpoints)
        self.assertEqual(result["level"], "drift")

    def test_drift_when_block_missing(self):
        endpoints = [{"name": "Altavoces", "attached": True}]
        self.assertEqual(self._health("", 13.98, endpoints=endpoints)["level"], "drift")
        self.assertEqual(self._health(None, 13.98, endpoints=endpoints)["level"], "drift")

    def test_detached_when_installed_but_no_endpoint_uses_it(self):
        endpoints = [{"name": "HDMI", "attached": False}, {"name": "Altavoces", "attached": False}]
        result = self._health("Preamp: 0.00 dB", 0.0, endpoints=endpoints)
        self.assertEqual(result["level"], "detached")
        self.assertEqual(result["endpoints"], 2)

    def test_missing_when_not_installed(self):
        self.assertEqual(self._health("Preamp: 0.00 dB", 0.0, installed=False)["level"], "missing")

    def test_unknown_default_keeps_any_attached_device(self):
        endpoints = [{"name": "HDMI", "attached": False}, {"name": "Auriculares", "attached": True}]
        self.assertEqual(self._health("Preamp: 13.98 dB", 13.98, endpoints=endpoints)["level"], "ok")

    def test_detached_when_the_default_device_lacks_the_apo(self):
        endpoints = [
            {"id": TV, "name": "TV", "attached": True},
            {"id": SPEAKERS, "name": "Altavoces", "attached": False},
        ]
        result = self._health(
            "Preamp: 13.98 dB", 13.98, endpoints=endpoints, default_id=SPEAKERS_DEVICE_ID
        )
        self.assertEqual(result["level"], "detached")
        self.assertEqual(result["default"], "Altavoces")

    def test_ok_when_the_default_device_has_the_apo(self):
        endpoints = [
            {"id": TV, "name": "TV", "attached": False},
            {"id": SPEAKERS, "name": "Altavoces", "attached": True},
        ]
        result = self._health(
            "Preamp: 13.98 dB", 13.98, endpoints=endpoints, default_id=SPEAKERS_DEVICE_ID
        )
        self.assertEqual(result["level"], "ok")

    def test_default_missing_from_the_list_does_not_invent_detached(self):
        endpoints = [{"name": "TV", "attached": True}]
        result = self._health("Preamp: 0.00 dB", 0.0, endpoints=endpoints, default_id=SPEAKERS_DEVICE_ID)
        self.assertEqual(result["level"], "ok")


class EndpointGuidTests(unittest.TestCase):
    def test_tail_guid_is_extracted_and_lowercased(self):
        self.assertEqual(
            verify.endpoint_guid("{0.0.0.00000000}.{2B2E13FA-4964-4D96-A6C6-359B022B53C5}"),
            "{2b2e13fa-4964-4d96-a6c6-359b022b53c5}",
        )

    def test_bare_guid_is_kept(self):
        self.assertEqual(verify.endpoint_guid(SPEAKERS), SPEAKERS)

    def test_empty_value(self):
        self.assertEqual(verify.endpoint_guid(None), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
