"""Interception 内核驱动控制器。

通过 Interception 驱动在内核 HID 层注入鼠标/键盘事件，
绕过 ACE (AntiCheatExpert) 在 Win32 API 层的 hook。
"""

import ctypes
import os
import threading
import time
from ctypes import wintypes


# ============================================================
# Constants
# ============================================================
INTERCEPTION_MAX_DEVICE = 20

# Mouse states
INTERCEPTION_MOUSE_LEFT_BUTTON_DOWN = 0x001
INTERCEPTION_MOUSE_LEFT_BUTTON_UP = 0x002
INTERCEPTION_MOUSE_RIGHT_BUTTON_DOWN = 0x004
INTERCEPTION_MOUSE_RIGHT_BUTTON_UP = 0x008

# Mouse flags
INTERCEPTION_MOUSE_MOVE_RELATIVE = 0x000
INTERCEPTION_MOUSE_MOVE_ABSOLUTE = 0x001

# Keyboard states
INTERCEPTION_KEY_DOWN = 0x00
INTERCEPTION_KEY_UP = 0x01

# Windows scan codes (Set 1, used by HID)
SCAN_CODES = {
    'ESC': 0x01,
    '1': 0x02, '2': 0x03, '3': 0x04, '4': 0x05, '5': 0x06,
    '6': 0x07, '7': 0x08, '8': 0x09, '9': 0x0A, '0': 0x0B,
    'Q': 0x10, 'W': 0x11, 'E': 0x12, 'R': 0x13, 'T': 0x14,
    'Y': 0x15, 'U': 0x16, 'I': 0x17, 'O': 0x18, 'P': 0x19,
    'A': 0x1E, 'S': 0x1F, 'D': 0x20, 'F': 0x21, 'G': 0x22,
    'H': 0x23, 'J': 0x24, 'K': 0x25, 'L': 0x26,
    'Z': 0x2C, 'X': 0x2D, 'C': 0x2E, 'V': 0x2F, 'B': 0x30,
    'N': 0x31, 'M': 0x32,
    'F1': 0x3B, 'F2': 0x3C, 'F3': 0x3D, 'F4': 0x3E,
    'F5': 0x3F, 'F6': 0x40, 'F7': 0x41, 'F8': 0x42,
    'F9': 0x43, 'F10': 0x44, 'F11': 0x57, 'F12': 0x58,
    'TAB': 0x0F, 'SPACE': 0x39, 'ENTER': 0x1C,
    'CTRL': 0x1D, 'ALT': 0x38, 'SHIFT': 0x2A,
}


# ============================================================
# C Structures
# ============================================================
class MouseStroke(ctypes.Structure):
    _fields_ = [
        ("state", ctypes.c_ushort),
        ("flags", ctypes.c_ushort),
        ("rolling", ctypes.c_short),
        ("x", ctypes.c_int),
        ("y", ctypes.c_int),
        ("information", ctypes.c_uint),
    ]


class KeyStroke(ctypes.Structure):
    _fields_ = [
        ("code", ctypes.c_ushort),
        ("state", ctypes.c_ushort),
        ("information", ctypes.c_uint),
    ]


class InterceptionController:
    """Interception 驱动封装。

    用法:
        controller = InterceptionController()
        controller.initialize()

        # 找到游戏窗口
        hwnd = controller.find_game_window()

        # 点击游戏窗口中心
        controller.click_at_window_center(hwnd, hold_time=0.35)

        controller.destroy()
    """

    def __init__(self):
        self._dll = None
        self._ctx = None
        self._mouse_dev = None
        self._keyboard_dev = None
        self._keyboards = []
        self._mice = []

    # ============================================================
    # 初始化 / 销毁
    # ============================================================

    def initialize(self) -> bool:
        """加载 DLL、创建上下文、枚举设备。返回是否成功。"""
        # 加载 DLL
        # DLL 在项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dll_path = os.path.join(project_root, "interception.dll")
        try:
            self._dll = ctypes.CDLL(dll_path)
        except Exception as e:
            print(f"[Interception] Cannot load DLL: {e}")
            return False

        self._setup_api()

        # 创建上下文
        self._ctx = self._dll.interception_create_context()
        if not self._ctx:
            print("[Interception] Context creation failed — driver not installed?")
            return False

        # 枚举设备
        self._enumerate_devices()

        if not self._mice:
            print("[Interception] No mouse devices found")
            return False

        self._mouse_dev = self._mice[0]
        if self._keyboards:
            self._keyboard_dev = self._keyboards[0]
        return True

    def destroy(self):
        """销毁上下文，释放资源。"""
        if self._dll and self._ctx:
            self._dll.interception_destroy_context(self._ctx)
            self._ctx = None

    def _setup_api(self):
        """设置 DLL API 签名。"""
        dll = self._dll
        dll.interception_create_context.restype = ctypes.c_void_p
        dll.interception_create_context.argtypes = []
        dll.interception_destroy_context.restype = None
        dll.interception_destroy_context.argtypes = [ctypes.c_void_p]
        dll.interception_is_keyboard.restype = ctypes.c_int
        dll.interception_is_keyboard.argtypes = [ctypes.c_int]
        dll.interception_is_mouse.restype = ctypes.c_int
        dll.interception_is_mouse.argtypes = [ctypes.c_int]
        dll.interception_set_filter.restype = None
        dll.interception_set_filter.argtypes = [
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ushort,
        ]
        dll.interception_send.restype = ctypes.c_int
        dll.interception_send.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint,
        ]
        dll.interception_receive.restype = ctypes.c_int
        dll.interception_receive.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint,
        ]
        dll.interception_wait.restype = ctypes.c_int
        dll.interception_wait.argtypes = [ctypes.c_void_p]
        dll.interception_wait_with_timeout.restype = ctypes.c_int
        dll.interception_wait_with_timeout.argtypes = [ctypes.c_void_p, ctypes.c_ulong]

    def _enumerate_devices(self):
        """枚举所有键盘和鼠标设备。"""
        self._keyboards = []
        self._mice = []
        for i in range(1, INTERCEPTION_MAX_DEVICE + 1):
            if self._dll.interception_is_keyboard(i):
                self._keyboards.append(i)
            if self._dll.interception_is_mouse(i):
                self._mice.append(i)

    # ============================================================
    # 窗口查找
    # ============================================================

    @staticmethod
    def find_game_window():
        """自动查找 NRC 游戏窗口。返回 (hwnd, process_name, pid) 或 (None, None, None)。"""
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        targets = ["NRC-Win64-Shipping", "nrc_launcher", "RockKingdom"]

        hwnds = []

        def enum_callback(hwnd, lparam):
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            title = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, title, 256)
            if title.value:
                hwnds.append((hwnd, title.value, pid.value))
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(WNDENUMPROC(enum_callback), 0)

        for hwnd, title, pid in hwnds:
            try:
                h_process = kernel32.OpenProcess(0x0400 | 0x0010, False, pid)
                if h_process:
                    exe_name = ctypes.create_unicode_buffer(260)
                    size = ctypes.c_uint(260)
                    kernel32.QueryFullProcessImageNameW(
                        h_process, 0, exe_name, ctypes.byref(size)
                    )
                    process_name = os.path.basename(exe_name.value)
                    kernel32.CloseHandle(h_process)
                    if process_name.lower() in [t.lower() for t in targets]:
                        return hwnd, process_name, pid
            except Exception:
                continue

        # 备选：窗口标题含"洛克"
        for hwnd, title, pid in hwnds:
            if "洛克" in title:
                return hwnd, "unknown", pid

        return None, None, None

    # ============================================================
    # 坐标计算
    # ============================================================

    @staticmethod
    def client_center_to_interception(hwnd):
        """将窗口客户区中心转换为 Interception 绝对坐标 (0-65535)。

        返回 (screen_x, screen_y, interception_x, interception_y, screen_w, screen_h)
        """
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

    # ============================================================
    # 鼠标操作
    # ============================================================

    def _send_mouse(self, state: int, x: int, y: int,
                    flags: int = INTERCEPTION_MOUSE_MOVE_ABSOLUTE) -> bool:
        """发送单次鼠标事件。"""
        stroke = MouseStroke()
        stroke.state = state
        stroke.flags = flags
        stroke.x = x
        stroke.y = y
        stroke.information = 0

        ptr = ctypes.cast(ctypes.pointer(stroke), ctypes.c_void_p)
        ret = self._dll.interception_send(self._ctx, self._mouse_dev, ptr, 1)
        return ret > 0

    def click(self, x: int, y: int, hold_time: float = 0.05):
        """在指定 Interception 绝对坐标执行鼠标点击（按下→按住→松开）。"""
        if not self._mouse_dev:
            return False

        # DOWN
        if not self._send_mouse(INTERCEPTION_MOUSE_LEFT_BUTTON_DOWN, x, y):
            return False

        if hold_time > 0:
            time.sleep(hold_time)

        # UP
        return self._send_mouse(INTERCEPTION_MOUSE_LEFT_BUTTON_UP, x, y)

    def click_at_screen(self, screen_x: int, screen_y: int, hold_time: float = 0.05):
        """在屏幕坐标执行鼠标点击。"""
        user32 = ctypes.windll.user32
        sw = user32.GetSystemMetrics(0)
        sh = user32.GetSystemMetrics(1)
        ix = int(screen_x * 65535 / sw)
        iy = int(screen_y * 65535 / sh)
        return self.click(ix, iy, hold_time)

    def click_at_window_center(self, hwnd, hold_time: float = 0.05):
        """在窗口客户区中心执行鼠标点击。"""
        _, _, ix, iy, _, _ = self.client_center_to_interception(hwnd)
        return self.click(ix, iy, hold_time)

    # ============================================================
    # 键盘操作
    # ============================================================

    def _send_key(self, code: int, state: int) -> bool:
        """发送单次键盘事件。"""
        if not self._keyboard_dev:
            return False
        stroke = KeyStroke()
        stroke.code = code
        stroke.state = state
        stroke.information = 0
        ptr = ctypes.cast(ctypes.pointer(stroke), ctypes.c_void_p)
        ret = self._dll.interception_send(self._ctx, self._keyboard_dev, ptr, 1)
        return ret > 0

    def press_key(self, key: str, hold_time: float = 0.05):
        """按下并松开一个键（通过扫描码）。

        支持键名参考 SCAN_CODES 字典，如 'E', '1', 'F8', 'ESC' 等。
        """
        code = self._key_code(key)
        if code is None:
            return False
        if not self._send_key(code, INTERCEPTION_KEY_DOWN):
            return False
        if hold_time > 0:
            time.sleep(hold_time)
        return self._send_key(code, INTERCEPTION_KEY_UP)

    def _key_code(self, key: str):
        """获取扫描码。支持单字符或键名。"""
        upper = key.upper()
        if upper in SCAN_CODES:
            return SCAN_CODES[upper]
        # 尝试作为单字符
        if len(key) == 1:
            return SCAN_CODES.get(upper)
        return None

    # ============================================================
    # 键盘监听（用于全局热键，绕过 ACE 的键盘过滤）
    # ============================================================

    def create_keyboard_listener(self, callback, stop_flag):
        """创建后台线程，通过 Interception 监听键盘事件。

        Interception 在 HID 层（ACE 下面），能收到 ACE 过滤前的原始按键。
        监听线程会拦截所有键盘事件、检查、再透传，对 F9 调用 callback。

        返回线程对象。
        """
        dll = self._dll  # 复用已加载的 DLL

        # 键盘判定回调
        IS_KB_FUNC = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int)
        is_kb = IS_KB_FUNC(dll.interception_is_keyboard)

        def listener():
            ctx = None
            try:
                ctx = dll.interception_create_context()
                if not ctx:
                    return
                dll.interception_set_filter(ctx, is_kb, 0xFFFF)  # INTERCEPTION_FILTER_KEY_ALL
                while not stop_flag():
                    ret = dll.interception_wait_with_timeout(ctx, 100)  # 100ms timeout
                    if ret <= 0:
                        continue
                    # 找到键盘设备
                    kbd = None
                    for i in range(1, INTERCEPTION_MAX_DEVICE + 1):
                        if dll.interception_is_keyboard(i):
                            kbd = i
                            break
                    if kbd is None:
                        continue
                    stroke = KeyStroke()
                    ptr = ctypes.cast(ctypes.pointer(stroke), ctypes.c_void_p)
                    r = dll.interception_receive(ctx, kbd, ptr, 1)
                    if r <= 0:
                        continue
                    # 检测 F9 (scan code 0x42) key down
                    if stroke.code == 0x42 and stroke.state == INTERCEPTION_KEY_DOWN:
                        callback()
                    # 透传事件（让游戏/系统正常接收）
                    dll.interception_send(ctx, kbd, ptr, 1)
            finally:
                if ctx:
                    dll.interception_destroy_context(ctx)

        t = threading.Thread(target=listener, daemon=True, name="Interception-KB-Listener")
        t.start()
        return t

    @property
    def is_initialized(self) -> bool:
        return self._ctx is not None and self._mouse_dev is not None

    @property
    def mouse_count(self) -> int:
        return len(self._mice)

    @property
    def keyboard_count(self) -> int:
        return len(self._keyboards)
