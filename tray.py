"""Windows notification-area icon and global hotkeys, with no dependencies.

Pure ``ctypes``: no pystray, no Pillow. A hidden window receives the tray
callback and ``WM_HOTKEY``; its message queue is pumped from a Tk ``after`` loop
and filtered to that window, so Tk's own messages are never touched.

The window procedure never touches Tk. Windows dispatches this window's messages
inside Tcl's own message loop, with the GIL released, so calling Tkinter from the
callback aborts the whole process (``PyEval_RestoreThread ... the current Python
thread state is NULL``). The procedure only records what happened; ``pump()``,
which runs from a Tk callback, is the one that acts on it.

Everything here is best effort. ``start()`` returns False when Windows refuses
(no Explorer, no icon, a broken class registration) and the caller falls back to
an ordinary window — an app that vanishes because the tray failed would be worse
than no tray at all.
"""

from __future__ import annotations

import ctypes
import sys
from collections.abc import Callable
from ctypes import wintypes

LRESULT = ctypes.c_ssize_t

WM_APP = 0x8000
WM_HOTKEY = 0x0312
WM_NULL = 0x0000
WM_LBUTTONUP = 0x0202
WM_LBUTTONDBLCLK = 0x0203
WM_RBUTTONUP = 0x0205
NIN_SELECT = 0x0400
NIN_KEYSELECT = 0x0401

NIM_ADD = 0x00000000
NIM_MODIFY = 0x00000001
NIM_DELETE = 0x00000002
NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_TIP = 0x00000004
NIF_INFO = 0x00000010
NIIF_NOSOUND = 0x00000010
TOAST_MS = 4000

IMAGE_ICON = 1
LR_LOADFROMFILE = 0x00000010
LR_DEFAULTSIZE = 0x00000040

MF_STRING = 0x00000000
TPM_RIGHTBUTTON = 0x0002
TPM_NONOTIFY = 0x0080
TPM_RETURNCMD = 0x0100

PM_REMOVE = 0x0001
GWLP_USERDATA = -21

_CALLBACK = WM_APP + 1
_TIP_LIMIT = 127


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_byte * 8),
    ]


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uID", wintypes.UINT),
        ("uFlags", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("hIcon", wintypes.HICON),
        ("szTip", wintypes.WCHAR * 128),
        ("dwState", wintypes.DWORD),
        ("dwStateMask", wintypes.DWORD),
        ("szInfo", wintypes.WCHAR * 256),
        ("uVersion", wintypes.UINT),
        ("szInfoTitle", wintypes.WCHAR * 64),
        ("dwInfoFlags", wintypes.DWORD),
        ("guidItem", GUID),
        ("hBalloonIcon", wintypes.HICON),
    ]


WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]


Instances: dict[int, Tray] = {}
_libraries_ready = False


def _libraries():
    """Load the DLLs once and pin the signatures that matter on 64-bit."""
    global _libraries_ready
    user32 = ctypes.windll.user32
    shell32 = ctypes.windll.shell32
    kernel32 = ctypes.windll.kernel32
    if not _libraries_ready:
        user32.CreateWindowExW.restype = wintypes.HWND
        user32.CreateWindowExW.argtypes = (
            wintypes.DWORD,
            wintypes.LPCWSTR,
            wintypes.LPCWSTR,
            wintypes.DWORD,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.HWND,
            wintypes.HMENU,
            wintypes.HINSTANCE,
            wintypes.LPVOID,
        )
        user32.DefWindowProcW.restype = LRESULT
        user32.DefWindowProcW.argtypes = (wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
        user32.LoadImageW.restype = wintypes.HANDLE
        user32.LoadImageW.argtypes = (
            wintypes.HINSTANCE,
            wintypes.LPCWSTR,
            wintypes.UINT,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.UINT,
        )
        user32.TrackPopupMenu.restype = ctypes.c_int
        user32.DestroyMenu.argtypes = (wintypes.HMENU,)
        user32.AppendMenuW.argtypes = (wintypes.HMENU, wintypes.UINT, ctypes.c_size_t, wintypes.LPCWSTR)
        user32.PeekMessageW.argtypes = (
            ctypes.POINTER(wintypes.MSG),
            wintypes.HWND,
            wintypes.UINT,
            wintypes.UINT,
            wintypes.UINT,
        )
        user32.DispatchMessageW.argtypes = (ctypes.POINTER(wintypes.MSG),)
        user32.RegisterHotKey.argtypes = (wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT)
        user32.UnregisterHotKey.argtypes = (wintypes.HWND, ctypes.c_int)
        shell32.Shell_NotifyIconW.argtypes = (wintypes.DWORD, ctypes.POINTER(NOTIFYICONDATAW))
        kernel32.GetModuleHandleW.restype = wintypes.HMODULE
        user32.RegisterWindowMessageW.restype = wintypes.UINT
        user32.RegisterWindowMessageW.argtypes = (wintypes.LPCWSTR,)
        _libraries_ready = True
    return user32, shell32, kernel32


class Tray:
    """One notification-area icon with a right-click menu and optional hotkeys."""

    def __init__(
        self,
        *,
        title: str,
        icon_path: str,
        menu: Callable[[], list[tuple[str, Callable[[], None]]]],
        on_open: Callable[[], None],
    ) -> None:
        self.title = title
        self.icon_path = icon_path
        self._menu = menu
        self._on_open = on_open
        self._hwnd: int | None = None
        self._icon = None
        self._nid: NOTIFYICONDATAW | None = None
        self._proc: object | None = None
        self._class_name = ""
        self._pending_menu = False
        self._pending_open = False
        self._pending_hotkeys: list[int] = []
        self._taskbar_created = 0
        self._hotkeys: dict[int, Callable[[], None]] = {}
        self._active = False

    # ---------------------------------------------------------------- life
    def start(self) -> bool:
        if self._active:
            return True
        if not sys.platform.startswith("win"):
            return False
        try:
            user32, _shell32, kernel32 = _libraries()
            self._class_name = f"VolumeBoosterTray{id(self)}"
            self._proc = WNDPROC(self._wnd_proc)
            window_class = WNDCLASSW()
            window_class.lpfnWndProc = self._proc
            window_class.hInstance = kernel32.GetModuleHandleW(None)
            window_class.lpszClassName = self._class_name
            if not user32.RegisterClassW(ctypes.byref(window_class)):
                return False
            hwnd = user32.CreateWindowExW(
                0, self._class_name, self._class_name, 0, 0, 0, 0, 0, None, None, window_class.hInstance, None
            )
            if not hwnd:
                return False
            self._hwnd = hwnd
            Instances[int(hwnd)] = self

            self._icon = user32.LoadImageW(
                None, self.icon_path, IMAGE_ICON, 0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE
            )
            if not self._add_icon():
                self._teardown()
                return False
            self._taskbar_created = user32.RegisterWindowMessageW("TaskbarCreated")
            self._active = True
            return True
        except (AttributeError, OSError, ValueError):
            self._teardown()
            return False

    def _add_icon(self) -> bool:
        """Add the icon (again after an Explorer restart). False when refused."""
        if self._hwnd is None:
            return False
        try:
            _user32, shell32, _kernel32 = _libraries()
            notice = NOTIFYICONDATAW()
            notice.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
            notice.hWnd = self._hwnd
            notice.uID = 1
            notice.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
            notice.uCallbackMessage = _CALLBACK
            notice.hIcon = self._icon
            notice.szTip = self.title[:_TIP_LIMIT]
            if not shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(notice)):
                return False
            self._nid = notice
            return True
        except (AttributeError, OSError):
            return False

    def stop(self) -> None:
        if not self._active:
            return
        try:
            _user32, shell32, _kernel32 = _libraries()
            if self._nid is not None:
                shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(self._nid))
        except (AttributeError, OSError):
            pass
        self._active = False
        self._teardown()

    def _teardown(self) -> None:
        try:
            user32, _shell32, _kernel32 = _libraries()
            if self._hwnd:
                Instances.pop(int(self._hwnd), None)
                user32.DestroyWindow(self._hwnd)
            if self._class_name:
                user32.UnregisterClassW(self._class_name, None)
        except (AttributeError, OSError):
            pass
        self._hwnd = None
        self._nid = None
        self._active = False

    @property
    def active(self) -> bool:
        return self._active

    # -------------------------------------------------------------- hotkeys
    def set_tooltip(self, text: str) -> None:
        """Hover text, so the current level is visible without opening anything."""
        if not self._active or self._nid is None:
            return
        try:
            _user32, shell32, _kernel32 = _libraries()
            notice = self._nid
            notice.uFlags = NIF_TIP
            notice.szTip = text[:_TIP_LIMIT]
            shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(notice))
            notice.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
        except (AttributeError, OSError):
            return

    def notify(self, title: str, text: str) -> bool:
        """Balloon/toast from the icon; the only feedback when the window is hidden."""
        if not self._active or self._nid is None:
            return False
        try:
            _user32, shell32, _kernel32 = _libraries()
            notice = self._nid
            notice.uFlags = NIF_INFO
            notice.szInfoTitle = title[:63]
            notice.szInfo = text[:255]
            notice.dwInfoFlags = NIIF_NOSOUND
            notice.uVersion = TOAST_MS
            shown = bool(shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(notice)))
            notice.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
            notice.uVersion = 0
            return shown
        except (AttributeError, OSError):
            return False

    def register_hotkey(self, ident: int, modifiers: int, key: int, callback: Callable[[], None]) -> bool:
        """False when Windows refuses, typically because another app owns it."""
        if not self._active or self._hwnd is None:
            return False
        try:
            user32, _shell32, _kernel32 = _libraries()
            self.unregister_hotkey(ident)
            if not user32.RegisterHotKey(self._hwnd, ident, modifiers, key):
                return False
        except (AttributeError, OSError):
            return False
        self._hotkeys[ident] = callback
        return True

    def unregister_hotkey(self, ident: int) -> None:
        self._hotkeys.pop(ident, None)
        if not self._active or self._hwnd is None:
            return
        try:
            user32, _shell32, _kernel32 = _libraries()
            user32.UnregisterHotKey(self._hwnd, ident)
        except (AttributeError, OSError):
            pass

    # ----------------------------------------------------------------- pump
    def pump(self) -> None:
        """Drain this window's messages, then act on what the procedure recorded."""
        if not self._active or self._hwnd is None:
            return
        try:
            user32, _shell32, _kernel32 = _libraries()
            message = wintypes.MSG()
            while user32.PeekMessageW(ctypes.byref(message), self._hwnd, 0, 0, PM_REMOVE):
                user32.TranslateMessage(ctypes.byref(message))
                user32.DispatchMessageW(ctypes.byref(message))
        except (AttributeError, OSError):
            return
        self._dispatch_pending()

    def _dispatch_pending(self) -> None:
        """Run the recorded actions from a Tk callback, never from the WNDPROC."""
        if self._pending_open:
            self._pending_open = False
            self._on_open()
        pending = self._pending_hotkeys
        self._pending_hotkeys = []
        for ident in pending:
            callback = self._hotkeys.get(ident)
            if callback is not None:
                callback()
        if self._pending_menu:
            self._pending_menu = False
            self._show_menu()

    # ---------------------------------------------------------------- menu
    def _show_menu(self) -> None:
        if not self._active or self._hwnd is None:
            return
        try:
            user32, _shell32, _kernel32 = _libraries()
            items = self._menu()
            if not items:
                return
            menu = user32.CreatePopupMenu()
            for index, (label, _callback) in enumerate(items, start=1):
                user32.AppendMenuW(menu, MF_STRING, index, label)
            point = wintypes.POINT()
            user32.GetCursorPos(ctypes.byref(point))
            user32.SetForegroundWindow(self._hwnd)
            choice = user32.TrackPopupMenu(
                menu,
                TPM_RIGHTBUTTON | TPM_RETURNCMD | TPM_NONOTIFY,
                point.x,
                point.y,
                0,
                self._hwnd,
                None,
            )
            user32.DestroyMenu(menu)
            user32.PostMessageW(self._hwnd, WM_NULL, 0, 0)
        except (AttributeError, OSError):
            return
        if 0 < choice <= len(items):
            items[choice - 1][1]()

    # ----------------------------------------------------------------- wndproc
    def _wnd_proc(self, hwnd, message, wparam, lparam):
        if self._taskbar_created and message == self._taskbar_created:
            # Explorer restarted: every icon was lost with it.
            self._add_icon()
            return 0
        if message == _CALLBACK:
            event = int(lparam) & 0xFFFF
            if event in (WM_LBUTTONUP, WM_LBUTTONDBLCLK, NIN_SELECT, NIN_KEYSELECT):
                self._pending_open = True
            elif event == WM_RBUTTONUP:
                self._pending_menu = True
            return 0
        if message == WM_HOTKEY:
            self._pending_hotkeys.append(int(wparam))
            return 0
        user32, _shell32, _kernel32 = _libraries()
        return user32.DefWindowProcW(hwnd, message, wparam, lparam)
