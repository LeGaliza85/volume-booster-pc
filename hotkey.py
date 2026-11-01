"""Global hotkey model: parse, normalise and format ``Ctrl+Alt+Up`` style strings.

Pure data and string work, no Windows calls, so it can be tested anywhere. The
virtual-key numbers are the Win32 ones; they are just integers here.
"""

from __future__ import annotations

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008

MODIFIERS: dict[str, int] = {
    "ctrl": MOD_CONTROL,
    "alt": MOD_ALT,
    "shift": MOD_SHIFT,
    "win": MOD_WIN,
}
MODIFIER_ORDER = ("ctrl", "alt", "shift", "win")
MODIFIER_LABELS = {"ctrl": "Ctrl", "alt": "Alt", "shift": "Shift", "win": "Win"}

# Only keys that make sense as a shortcut, plus the letters, digits and F-keys.
NAMED_KEYS: dict[str, int] = {
    "up": 0x26,
    "down": 0x28,
    "left": 0x25,
    "right": 0x27,
    "space": 0x20,
    "home": 0x24,
    "end": 0x23,
    "pageup": 0x21,
    "pagedown": 0x22,
    "insert": 0x2D,
    "delete": 0x2E,
    "tab": 0x09,
    "enter": 0x0D,
    "backspace": 0x08,
    "pause": 0x13,
    "printscreen": 0x2C,
    "comma": 0xBC,
    "period": 0xBE,
    "minus": 0xBD,
    "plus": 0xBB,
}

KEY_LABELS = {
    "up": "Up",
    "down": "Down",
    "left": "Left",
    "right": "Right",
    "space": "Space",
    "home": "Home",
    "end": "End",
    "pageup": "PageUp",
    "pagedown": "PageDown",
    "insert": "Insert",
    "delete": "Delete",
    "tab": "Tab",
    "enter": "Enter",
    "backspace": "Backspace",
    "pause": "Pause",
    "printscreen": "PrintScreen",
    "comma": "Comma",
    "period": "Period",
    "minus": "Minus",
    "plus": "Plus",
}

_VK_BY_NUMBER = {value: name for name, value in NAMED_KEYS.items()}


def _key_code(token: str) -> int | None:
    """Virtual-key code for a single key token, or None when it is not a key."""
    token = token.strip().lower()
    if not token:
        return None
    if token in NAMED_KEYS:
        return NAMED_KEYS[token]
    if len(token) == 1 and token.isalnum():
        if token.isdigit():
            return ord(token)
        return ord(token.upper())
    if token.startswith("f") and token[1:].isdigit():
        number = int(token[1:])
        if 1 <= number <= 24:
            return 0x6F + number  # VK_F1 = 0x70
    return None


def _key_label(code: int) -> str:
    if code in _VK_BY_NUMBER:
        return KEY_LABELS[_VK_BY_NUMBER[code]]
    if 0x41 <= code <= 0x5A:
        return chr(code)
    if 0x30 <= code <= 0x39:
        return chr(code)
    if 0x70 <= code <= 0x87:
        return f"F{code - 0x6F}"
    return ""


def parse(text: str | None) -> tuple[int, int] | None:
    """``"ctrl+alt+up"`` -> (modifiers, virtual key), or None when unusable.

    A global hotkey without a modifier is rejected on purpose: it would swallow
    the key for every other program on the machine.
    """
    if not text or not isinstance(text, str):
        return None
    parts = [part for part in text.replace(" ", "").split("+") if part]
    if len(parts) < 2:
        return None
    modifiers = 0
    key: int | None = None
    for part in parts:
        lower = part.lower()
        if lower in MODIFIERS:
            modifiers |= MODIFIERS[lower]
            continue
        code = _key_code(part)
        if code is None or key is not None:
            return None
        key = code
    if key is None or modifiers == 0:
        return None
    return modifiers, key


def normalise(text: str | None) -> str:
    """Canonical form, or an empty string when the text is not a valid hotkey."""
    parsed = parse(text)
    if parsed is None:
        return ""
    return format_hotkey(*parsed)


def format_hotkey(modifiers: int, key: int) -> str:
    labels = [MODIFIER_LABELS[name] for name in MODIFIER_ORDER if modifiers & MODIFIERS[name]]
    label = _key_label(key)
    if not labels or not label:
        return ""
    return "+".join([*labels, label])


def is_valid(text: str | None) -> bool:
    return parse(text) is not None


_KEYSYM_ALIASES = {
    "prior": "pageup",
    "next": "pagedown",
    "return": "enter",
    "print": "printscreen",
}

_MODIFIER_KEYSYMS = frozenset(
    {
        "control_l",
        "control_r",
        "alt_l",
        "alt_r",
        "shift_l",
        "shift_r",
        "super_l",
        "super_r",
        "meta_l",
        "meta_r",
        "caps_lock",
        "num_lock",
    }
)


def _from_keysym(keysym: str) -> int | None:
    name = (keysym or "").strip()
    lower = name.lower()
    if lower in _KEYSYM_ALIASES:
        lower = _KEYSYM_ALIASES[lower]
    if lower in NAMED_KEYS:
        return NAMED_KEYS[lower]
    if len(lower) == 1 and lower.isalnum():
        return _key_code(lower)
    if lower.startswith("f") and lower[1:].isdigit():
        return _key_code(lower)
    return None


def is_modifier_keysym(keysym: str) -> bool:
    return (keysym or "").lower() in _MODIFIER_KEYSYMS


def from_event(keysym: str, modifiers: int) -> str:
    """Tk keysym plus the modifiers held right now -> canonical hotkey string."""
    code = _from_keysym(keysym)
    if code is None or modifiers == 0:
        return ""
    return format_hotkey(modifiers, code)


def pressed_modifiers() -> int:
    """Modifiers physically down at this instant (Windows only, 0 elsewhere).

    ``event.state`` cannot be trusted for this: Tk on Windows reports Control
    and Alt in bits that do not match the X11 masks, and it never reports Win.
    Asking the keyboard directly gives exactly what RegisterHotKey expects.
    """
    import ctypes
    import sys

    if not sys.platform.startswith("win"):
        return 0
    try:
        user32 = ctypes.windll.user32
    except (AttributeError, OSError):
        return 0
    held = 0
    if user32.GetAsyncKeyState(0x11) & 0x8000:
        held |= MOD_CONTROL
    if user32.GetAsyncKeyState(0x12) & 0x8000:
        held |= MOD_ALT
    if user32.GetAsyncKeyState(0x10) & 0x8000:
        held |= MOD_SHIFT
    if (user32.GetAsyncKeyState(0x5B) | user32.GetAsyncKeyState(0x5C)) & 0x8000:
        held |= MOD_WIN
    return held
