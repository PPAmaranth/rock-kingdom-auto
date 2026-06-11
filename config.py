import os
import re

# WA: set empty PATH to resolve qfluentwidgets/PySide6 access os.environ['PATH'] issue
if 'PATH' not in os.environ:
    os.environ['PATH'] = ""
from qfluentwidgets import FluentIcon

from ok import Box, ConfigOption

version = "0.1.0"

# ============================================================
# 游戏热键配置（暂用默认值，后续根据游戏设置同步修改）
# ============================================================
key_config_option = ConfigOption('Game Hotkey', {
    'Jump Key': 'space',
    'Dodge Key': 'lshift',
    'Tool Key': 't',
}, description='In Game Hotkey for Skills', show_at_tab=True, icon=FluentIcon.GAME)

# ============================================================
# TODO: 后续补充 — 游戏窗口类名确认
# Unity 游戏常见的窗口类名可能是 'UnityWndClass'，
# 实际值需要用 Spy++ 工具查看游戏窗口的"类名"属性确认
# ============================================================

config = {
    'debug': False,
    'use_gui': True,
    'config_folder': 'configs',
    'gui_icon': None,  # 暂不设置图标
    'global_configs': [key_config_option],
    'gui_title': 'Rock Kingdom Auto',  # 窗口标题
    'my_app': ['src.globals', 'Globals'],
    'start_timeout': 60,
    'wait_until_settle_time': 0,

    # ---------- 窗口配置 ----------
    'windows': {
        # 顶层窗口类名列表 — 用于过滤搜索（参考 ok-ww）
        'top_hwnd_class': [
            re.compile('CAgreementDlg'), re.compile('CLoginDlg_P_'),
            'CefBrowserWindow', 'Chrome_RenderWidgetHostHWND', '#32770',
            re.compile('CNativeLoginDlg'), 'Static', 'ComboBox', 'ComboLBox', 'Button'
        ],
        # TODO: 游戏 exe 文件名，后续补充
        'exe': 'Game.exe',
        # Unity 游戏的窗口类名（待确认，先用常见值）
        # 常见 Unity 类名: 'UnityWndClass', 'UnityGuiWndClass'
        'hwnd_class': 'UnityWndClass',
        # 后台输入模式
        'interaction': 'PostMessage',
        # 画面捕获方式：WGC 优先（支持后台/最小化），BitBlt 回退
        'capture_method': ['WGC', 'BitBlt_RenderFull'],
        'check_hdr': False,
        'force_no_hdr': False,
        'check_night_light': False,
        'force_no_night_light': False,
    },

    # ---------- GUI 窗口大小 ----------
    'window_size': {
        'width': 1000,
        'height': 700,
        'min_width': 800,
        'min_height': 600,
    },

    # ---------- 游戏分辨率 ----------
    'supported_resolution': {
        'ratio': '16:9',
        'resize_to': [(2560, 1440)],
        'min_size': (1280, 720)
    },

    # ---------- 任务注册 ----------
    # trigger_tasks: 触发式任务，勾选即运行，取消即停止
    'trigger_tasks': [
        ["src.task.AutoThrowTask", "AutoThrowTask"],
    ],

    # ---------- 场景 ----------
    'scene': ["src.scene.RKScene", "RKScene"],

    # ---------- 日志 ----------
    'log_file': 'logs/rock-kingdom.log',
    'error_log_file': 'logs/rock-kingdom_error.log',
    'screenshots_folder': 'screenshots',

    # ---------- 版本 ----------
    'version': version,

    # ---------- 链接（暂无）----------
    'links': {
        'default': {
            'github': 'https://github.com/ok-oldking/ok-wuthering-waves',
        },
    },

    # ---------- 关于信息 ----------
    'about': """
    <p><strong>Rock Kingdom Auto</strong></p>
    <p>基于 ok-script 框架的洛克王国：世界自动化工具。</p>
    <p>仅供个人学习 Python 编程、计算机视觉、UI 自动化使用。</p>
    """,
}
