"""测试 Interception 驱动是否可用。"""
import ctypes
import time
import os
from ctypes import wintypes

# Interception constants
INTERCEPTION_MAX_DEVICE = 20
INTERCEPTION_MOUSE_MOVE_ABSOLUTE = 0x001
INTERCEPTION_MOUSE_LEFT_BUTTON_DOWN = 0x001
INTERCEPTION_MOUSE_LEFT_BUTTON_UP = 0x002


class MouseStroke(ctypes.Structure):
    _fields_ = [
        ("state", ctypes.c_ushort),
        ("flags", ctypes.c_ushort),
        ("rolling", ctypes.c_short),
        ("x", ctypes.c_int),
        ("y", ctypes.c_int),
        ("information", ctypes.c_uint),
    ]


def find_game_window():
    """自动查找 NRC 游戏窗口（Unreal Engine）。"""
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    # 已知的游戏进程名
    targets = ["NRC-Win64-Shipping", "nrc_launcher", "RockKingdom"]

    # 枚举所有顶层窗口
    hwnds = []

    def enum_callback(hwnd, lparam):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

        # 获取窗口标题
        title = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, title, 256)

        if title.value:
            hwnds.append((hwnd, title.value, pid.value))
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(WNDENUMPROC(enum_callback), 0)

    # 查找匹配的窗口
    for hwnd, title, pid in hwnds:
        try:
            process_name = None
            # 获取进程名
            h_process = kernel32.OpenProcess(0x0400 | 0x0010, False, pid)
            if h_process:
                exe_name = ctypes.create_unicode_buffer(260)
                size = ctypes.c_uint(260)
                kernel32.QueryFullProcessImageNameW(h_process, 0, exe_name, ctypes.byref(size))
                process_name = os.path.basename(exe_name.value)
                kernel32.CloseHandle(h_process)

            if process_name and process_name.lower() in [t.lower() for t in targets]:
                return hwnd, process_name, pid
        except Exception:
            continue

    # 备选：通过窗口标题包含 "洛克" 查找
    for hwnd, title, pid in hwnds:
        if "洛克" in title:
            return hwnd, "unknown", pid

    return None, None, None


def get_click_coords(hwnd):
    """获取游戏窗口客户区中心屏幕坐标（适用于 Interception）。"""
    user32 = ctypes.windll.user32

    cr = wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(cr))

    pt = wintypes.POINT()
    pt.x = cr.right // 2
    pt.y = cr.bottom // 2
    user32.ClientToScreen(hwnd, ctypes.byref(pt))

    sw = user32.GetSystemMetrics(0)
    sh = user32.GetSystemMetrics(1)

    ix = int(pt.x * 65535 / sw)
    iy = int(pt.y * 65535 / sh)

    return pt.x, pt.y, ix, iy, sw, sh


def main():
    print("=" * 60)
    print("Interception 驱动测试")
    print("=" * 60)

    # -------- 1. 加载 DLL --------
    dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "interception.dll")
    try:
        dll = ctypes.CDLL(dll_path)
        print(f"[OK] interception.dll loaded from {dll_path}")
    except Exception as e:
        print(f"[FAIL] Cannot load interception.dll: {e}")
        return 1

    # -------- 2. 设置 API --------
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

    # -------- 3. 创建上下文 --------
    print("Creating Interception context...")
    ctx = dll.interception_create_context()
    if not ctx:
        print("[FAIL] Context creation failed — driver not installed or not running")
        print("需要安装 Interception 内核驱动: https://github.com/oblitum/Interception")
        return 1
    print(f"[OK] Context created: 0x{ctx:X}")

    # -------- 4. 枚举设备 --------
    keyboards = []
    mice = []
    for i in range(1, INTERCEPTION_MAX_DEVICE + 1):
        if dll.interception_is_keyboard(i):
            keyboards.append(i)
        if dll.interception_is_mouse(i):
            mice.append(i)

    print(f"[OK] Found {len(keyboards)} keyboards: {keyboards}")
    print(f"[OK] Found {len(mice)} mice: {mice}")

    if not mice:
        print("[FAIL] No mouse devices found")
        dll.interception_destroy_context(ctx)
        return 1

    # 使用第一个鼠标设备（通常是物理鼠标）
    mouse_dev = mice[0]
    print(f"Using mouse device: {mouse_dev}")

    # -------- 5. 查找游戏窗口 --------
    hwnd, proc_name, pid = find_game_window()
    if not hwnd:
        print("[WARN] Game window not found. Trying fallback: click at screen center.")
        user32 = ctypes.windll.user32
        sw = user32.GetSystemMetrics(0)
        sh = user32.GetSystemMetrics(1)
        sx, sy = sw // 2, sh // 2
        ix, iy = int(sx * 65535 / sw), int(sy * 65535 / sh)
        print(f"Screen center: ({sx}, {sy}) -> Interception ({ix}, {iy})")
    else:
        sx, sy, ix, iy, sw, sh = get_click_coords(hwnd)
        print(f"Game window: HWND=0x{hwnd:X} Process={proc_name} PID={pid}")
        print(f"Screen center: ({sx}, {sy})")
        print(f"Interception coords: ({ix}, {iy})")
        print(f"Screen size: {sw}x{sh}")

    # -------- 6. 执行鼠标点击 --------
    print(f"\n[TEST] 3 秒后向游戏窗口中心发送鼠标点击...")
    print("      请确保游戏窗口在前台！")
    for i in range(3, 0, -1):
        print(f"      {i}...")
        time.sleep(1)

    # Mouse DOWN
    stroke_down = MouseStroke()
    stroke_down.state = INTERCEPTION_MOUSE_LEFT_BUTTON_DOWN
    stroke_down.flags = INTERCEPTION_MOUSE_MOVE_ABSOLUTE
    stroke_down.x = ix
    stroke_down.y = iy
    stroke_down.information = 0

    ptr = ctypes.cast(ctypes.pointer(stroke_down), ctypes.c_void_p)
    ret = dll.interception_send(ctx, mouse_dev, ptr, 1)
    print(f"Mouse DOWN: {'OK' if ret > 0 else 'FAIL'} (ret={ret})")

    time.sleep(0.35)

    # Mouse UP
    stroke_up = MouseStroke()
    stroke_up.state = INTERCEPTION_MOUSE_LEFT_BUTTON_UP
    stroke_up.flags = INTERCEPTION_MOUSE_MOVE_ABSOLUTE
    stroke_up.x = ix
    stroke_up.y = iy
    stroke_up.information = 0

    ptr = ctypes.cast(ctypes.pointer(stroke_up), ctypes.c_void_p)
    ret = dll.interception_send(ctx, mouse_dev, ptr, 1)
    print(f"Mouse UP: {'OK' if ret > 0 else 'FAIL'} (ret={ret})")

    # -------- 7. 清理 --------
    dll.interception_destroy_context(ctx)
    print("\n[DONE] 测试完成。请观察游戏是否响应了点击。")
    return 0


if __name__ == "__main__":
    exit(main())
