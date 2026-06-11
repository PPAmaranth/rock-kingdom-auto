"""测试 Interception 驱动是否可用。"""
import ctypes
import time
from ctypes import wintypes

# Interception constants
INTERCEPTION_MAX_DEVICE = 20
INTERCEPTION_KEY_DOWN = 0x00
INTERCEPTION_KEY_UP = 0x01

INTERCEPTION_MOUSE_MOVE_RELATIVE = 0x000
INTERCEPTION_MOUSE_MOVE_ABSOLUTE = 0x001
INTERCEPTION_MOUSE_LEFT_BUTTON_DOWN = 0x001
INTERCEPTION_MOUSE_LEFT_BUTTON_UP = 0x002

class KeyStroke(ctypes.Structure):
    _fields_ = [
        ("code", ctypes.c_ushort),
        ("state", ctypes.c_ushort),
        ("information", ctypes.c_uint),
    ]

class MouseStroke(ctypes.Structure):
    _fields_ = [
        ("state", ctypes.c_ushort),
        ("flags", ctypes.c_ushort),
        ("rolling", ctypes.c_short),
        ("x", ctypes.c_int),
        ("y", ctypes.c_int),
        ("information", ctypes.c_uint),
    ]

# Load DLL
import os
dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "interception.dll")
try:
    dll = ctypes.CDLL(dll_path)
    print(f"[OK] interception.dll loaded from {dll_path}")
except Exception as e:
    print(f"[FAIL] Cannot load interception.dll: {e}")
    exit(1)

# Setup API
dll.interception_create_context.restype = ctypes.c_void_p
dll.interception_create_context.argtypes = []

dll.interception_destroy_context.restype = None
dll.interception_destroy_context.argtypes = [ctypes.c_void_p]

dll.interception_is_keyboard.restype = ctypes.c_int
dll.interception_is_keyboard.argtypes = [ctypes.c_int]

dll.interception_is_mouse.restype = ctypes.c_int
dll.interception_is_mouse.argtypes = [ctypes.c_int]

dll.interception_set_filter.restype = None
dll.interception_set_filter.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ushort]

dll.interception_send.restype = ctypes.c_int
dll.interception_send.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint]

# Try creating context
print("Creating Interception context...")
ctx = dll.interception_create_context()
if not ctx:
    print("[FAIL] Context creation failed — driver not installed or not running")
    print("需要安装 Interception 内核驱动: https://github.com/oblitum/Interception")
    exit(1)

print(f"[OK] Context created: 0x{ctx:X}")

# Find keyboard device
kb_cb = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int)(dll.interception_is_keyboard)
mouse_cb = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int)(dll.interception_is_mouse)

kbd = None
mouse = None
for i in range(1, INTERCEPTION_MAX_DEVICE + 1):
    if dll.interception_is_keyboard(i):
        kbd = i
        print(f"[OK] Keyboard device: {i}")
    if dll.interception_is_mouse(i):
        mouse_dev = i
        print(f"[OK] Mouse device: {i}")

if kbd is None:
    print("[WARN] No keyboard found via enumeration")
if mouse is None:
    print("[WARN] No mouse found via enumeration")

# Try mouse test
if mouse_dev:
    print(f"\n[TEST] Click at screen center via Interception...")
    user32 = ctypes.windll.user32
    sw = user32.GetSystemMetrics(0)
    sh = user32.GetSystemMetrics(1)

    # Get game window center
    hwnd = 395978
    r = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    cr = wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(cr))
    cx = r.left + cr.right // 2
    cy = r.top + cr.bottom // 2
    print(f"Target: ({cx}, {cy}), Screen: {sw}x{sh}")

    # Convert to Interception coordinates (0-65535)
    ix = int(cx * 65535 / sw)
    iy = int(cy * 65535 / sh)
    print(f"Interception coords: ({ix}, {iy})")

    print("3 秒后执行点击...")
    time.sleep(3)

    # Send mouse down
    stroke_down = MouseStroke()
    stroke_down.state = INTERCEPTION_MOUSE_LEFT_BUTTON_DOWN
    stroke_down.flags = INTERCEPTION_MOUSE_MOVE_ABSOLUTE
    stroke_down.x = ix
    stroke_down.y = iy
    stroke_down.information = 0

    ptr = ctypes.cast(ctypes.pointer(stroke_down), ctypes.c_void_p)
    r = dll.interception_send(ctx, mouse_dev, ptr, 1)
    print(f"Mouse DOWN: {'OK' if r > 0 else 'FAIL'} ({r})")

    time.sleep(0.3)  # Hold

    # Send mouse up
    stroke_up = MouseStroke()
    stroke_up.state = INTERCEPTION_MOUSE_LEFT_BUTTON_UP
    stroke_up.flags = INTERCEPTION_MOUSE_MOVE_ABSOLUTE
    stroke_up.x = ix
    stroke_up.y = iy
    stroke_up.information = 0

    ptr = ctypes.cast(ctypes.pointer(stroke_up), ctypes.c_void_p)
    r = dll.interception_send(ctx, mouse_dev, ptr, 1)
    print(f"Mouse UP: {'OK' if r > 0 else 'FAIL'} ({r})")

    print("\n游戏里看到丢球动作了吗？")

# Cleanup
dll.interception_destroy_context(ctx)
