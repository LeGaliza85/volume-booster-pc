"""The window procedure must never run an action: it only records it.

Windows dispatches this window's messages inside Tcl's message loop with the GIL
released. Calling Tkinter from there aborts the process with
``PyEval_RestoreThread ... the current Python thread state is NULL``: the tray
icon disappears and the window never opens. ``pump()`` runs the recorded actions
from a Tk ``after`` callback instead.
"""

from __future__ import annotations

import sys
import unittest

if sys.platform.startswith("win"):
    import tray
else:  # pragma: no cover - the tray is Windows-only
    tray = None


@unittest.skipUnless(sys.platform.startswith("win"), "the tray is Windows-only")
class TrayCallbackDeferralTests(unittest.TestCase):
    def make_tray(self, calls: list[str]) -> tray.Tray:
        return tray.Tray(
            title="test",
            icon_path="unused.ico",
            menu=lambda: [],
            on_open=lambda: calls.append("open"),
        )

    def test_left_click_is_recorded_not_run_from_the_wndproc(self):
        calls: list[str] = []
        icon = self.make_tray(calls)

        icon._wnd_proc(None, tray._CALLBACK, 0, tray.WM_LBUTTONUP)

        self.assertEqual(calls, [])
        self.assertTrue(icon._pending_open)
        icon._dispatch_pending()
        self.assertEqual(calls, ["open"])
        self.assertFalse(icon._pending_open)

    def test_every_left_click_variant_opens_once(self):
        for event in (tray.WM_LBUTTONUP, tray.WM_LBUTTONDBLCLK, tray.NIN_SELECT, tray.NIN_KEYSELECT):
            with self.subTest(event=event):
                calls: list[str] = []
                icon = self.make_tray(calls)
                icon._wnd_proc(None, tray._CALLBACK, 0, event)
                icon._dispatch_pending()
                self.assertEqual(calls, ["open"])

    def test_hotkey_is_recorded_not_run_from_the_wndproc(self):
        calls: list[str] = []
        icon = self.make_tray(calls)
        icon._hotkeys[7] = lambda: calls.append("hot")

        icon._wnd_proc(None, tray.WM_HOTKEY, 7, 0)

        self.assertEqual(calls, [])
        self.assertEqual(icon._pending_hotkeys, [7])
        icon._dispatch_pending()
        self.assertEqual(calls, ["hot"])
        self.assertEqual(icon._pending_hotkeys, [])

    def test_burst_of_hotkeys_is_not_lost(self):
        calls: list[str] = []
        icon = self.make_tray(calls)
        icon._hotkeys[7] = lambda: calls.append("up")
        icon._hotkeys[8] = lambda: calls.append("down")

        icon._wnd_proc(None, tray.WM_HOTKEY, 7, 0)
        icon._wnd_proc(None, tray.WM_HOTKEY, 8, 0)
        icon._wnd_proc(None, tray.WM_HOTKEY, 99, 0)  # unknown id, dropped quietly
        icon._dispatch_pending()

        self.assertEqual(calls, ["up", "down"])

    def test_right_click_only_records_the_menu(self):
        calls: list[str] = []
        icon = self.make_tray(calls)

        icon._wnd_proc(None, tray._CALLBACK, 0, tray.WM_RBUTTONUP)

        self.assertTrue(icon._pending_menu)
        self.assertFalse(icon._pending_open)
        icon._dispatch_pending()  # inactive tray: no Win32 calls, no crash
        self.assertFalse(icon._pending_menu)


if __name__ == "__main__":
    unittest.main(verbosity=2)
