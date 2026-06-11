import ctypes
import random
import time

from qfluentwidgets import FluentIcon

from ok import Logger, TriggerTask
from src.task.BaseRKTask import BaseRKTask
from src.interception import InterceptionController

logger = Logger.get_logger(__name__)


class AutoThrowTask(BaseRKTask, TriggerTask):
    """自动丢球捕捉任务。

    使用 Interception 内核驱动绕过 ACE 反作弊。
    每次 run() 执行一个动作后返回，由 ok-script 框架控制循环。

    功能：
    - 启动后 5 秒倒计时，期间不检测前台
    - 倒计时结束后，游戏不在前台则自动停止
    - 以随机间隔向屏幕中央丢球
    - 连续工作后休息（模拟人类行为）
    - 每 N 次丢球按 E 确保球模式
    """

    _STATE_STARTUP = 'startup'
    _STATE_THROW = 'throw'
    _STATE_REST = 'rest'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "Auto Throw"
        self.group_name = "Capture"
        self.group_icon = FluentIcon.GAME
        self.description = "自动丢球捕捉（启动5秒倒计时，丢失焦点自动停止）"
        self.icon = FluentIcon.CALORIES
        self.trigger_interval = 0.1

        # ========== 可配置参数 ==========
        self.default_config = {
            '_enabled': True,
            'Throw Interval Min (s)': 0.3,
            'Throw Interval Max (s)': 1.0,
            'Hold Time Min (s)': 0.20,
            'Hold Time Max (s)': 0.40,
            'Work Duration Min (min)': 2.0,
            'Work Duration Max (min)': 3.0,
            'Rest Duration Min (s)': 8.0,
            'Rest Duration Max (s)': 15.0,
        }
        self.config_description = {
            'Throw Interval Min (s)': '两次丢球之间的最短间隔',
            'Throw Interval Max (s)': '两次丢球之间的最长间隔',
            'Hold Time Min (s)': '长按鼠标左键的最短时间（出准星）',
            'Hold Time Max (s)': '长按鼠标左键的最长时间',
            'Work Duration Min (min)': '连续工作的最短时间',
            'Work Duration Max (min)': '连续工作的最长时间',
            'Rest Duration Min (s)': '休息的最短时间',
            'Rest Duration Max (s)': '休息的最长时间',
        }

        # ========== Interception 驱动 ==========
        self._interception = None
        self._game_hwnd = None
        self._interception_ix = 0
        self._interception_iy = 0

        # ========== 模式控制 ==========
        self._ball_mode_every_n = 3

        # ========== 运行时状态 ==========
        self._initialized = False
        self._state = self._STATE_STARTUP
        self._startup_deadline = 0       # 倒计时结束时间
        self._next_throw_time = 0
        self._rest_end_time = 0
        self._work_start_time = 0
        self._work_duration = 0
        self.throw_count = 0
        self.total_throws = 0
        self.session_start = 0

    # ================================================================
    # run() — 每次返回一个动作
    # ================================================================

    def run(self):
        if not self._initialized:
            self._on_first_run()

        if not self.enabled:
            self.log_info('[停止] 任务已禁用')
            self.update_info()
            return None

        if self._state == self._STATE_STARTUP:
            return self._tick_startup()
        elif self._state == self._STATE_REST:
            return self._tick_rest()
        else:
            return self._tick_throw()

    # ================================================================
    # 各状态
    # ================================================================

    def _on_first_run(self):
        self._initialized = True
        self._init_interception()
        self.throw_count = 0
        self.session_start = time.time()
        self._work_duration = self._random_work_duration()
        self._next_throw_time = 0

        # 5 秒启动倒计时
        self._state = self._STATE_STARTUP
        self._startup_deadline = time.time() + 5

        self.log_info('[启动] 5 秒倒计时开始，请切换到游戏窗口...')

    def _tick_startup(self):
        """启动倒计时：不检测前台，5 秒后切换到丢球状态。"""
        remaining = self._startup_deadline - time.time()
        if remaining > 0:
            if remaining < 2:
                self.log_info(f'[启动] {remaining:.0f} 秒后开始丢球...')
            return None  # 继续等待

        # 倒计时结束
        self._state = self._STATE_THROW
        self._work_start_time = time.time()
        self._next_throw_time = 0
        self.log_info(
            f'[开始] 自动丢球启动 | 本轮工作 {self._work_duration / 60:.1f} 分钟 | '
            f'丢失焦点自动停止'
        )
        self._ensure_ball_mode()
        return True

    def _tick_throw(self):
        now = time.time()

        # ---- 后台检测：不在前台就自动停止 ----
        if not self._is_game_foreground():
            self.log_info('[停止] 游戏窗口丢失焦点，自动停止')
            self.disable()
            self.update_info()
            return None

        # ---- 检查休息 ----
        if now - self._work_start_time >= self._work_duration:
            self._enter_rest()
            return True

        # ---- 还没到丢球时间 ----
        if now < self._next_throw_time:
            return None

        # ---- 丢球 ----
        self._do_throw_once()
        self._next_throw_time = now + self._random_throw_interval()
        return True

    def _tick_rest(self):
        if time.time() < self._rest_end_time:
            return None

        # 休息结束
        self._state = self._STATE_THROW
        self._work_duration = self._random_work_duration()
        self._work_start_time = time.time()
        self.throw_count = 0
        self._next_throw_time = 0
        self.log_info(f'[继续] 新一轮工作 {self._work_duration / 60:.1f} 分钟')
        self._ensure_ball_mode()
        return True

    def _enter_rest(self):
        rest = self._random_rest_duration()
        elapsed = time.time() - self._work_start_time
        self.log_info(f'[休息] 已连续工作 {elapsed / 60:.1f} 分钟，休息 {rest:.1f} 秒')
        self.update_info()
        self._state = self._STATE_REST
        self._rest_end_time = time.time() + rest

    # ================================================================
    # 单次丢球
    # ================================================================

    def _do_throw_once(self):
        hold_time = self._random_hold_time()

        if not self._interception:
            x = self.width_of_screen(0.5)
            y = self.height_of_screen(0.5)
            self.click(x=x, y=y, down_time=hold_time)
            self.throw_count += 1
            self.total_throws += 1
            return

        # E 键球模式
        if self.throw_count % self._ball_mode_every_n == 0 and self.throw_count > 0:
            self._ensure_ball_mode()

        # 刷新坐标
        if self.throw_count % 100 == 0:
            self._refresh_interception_coords()

        # 点击前最后确认
        if not self._is_game_foreground():
            return

        success = self._interception.click(
            self._interception_ix, self._interception_iy,
            hold_time=hold_time,
        )
        if not success:
            self.log_error('[Interception] 点击失败，重新初始化')
            self._interception.destroy()
            self._interception = None
            self._init_interception()
            return

        self.throw_count += 1
        self.total_throws += 1

        if self.throw_count % 50 == 0:
            self.log_info(
                f'[丢球] 本轮 {self.throw_count} 次 | '
                f'总计 {self.total_throws} 次 | '
                f'按住 {hold_time:.2f}s'
            )

    # ================================================================
    # Interception
    # ================================================================

    def _init_interception(self):
        if self._interception is not None:
            return
        self._interception = InterceptionController()
        if not self._interception.initialize():
            self.log_error('[Interception] 驱动初始化失败')
            self._interception = None
            return
        self.log_info(
            f'[Interception] 已加载 '
            f'(mice={self._interception.mouse_count}, '
            f'kb={self._interception.keyboard_count})'
        )
        hwnd, proc, pid = self._interception.find_game_window()
        if hwnd:
            self._game_hwnd = hwnd
            sx, sy, ix, iy, sw, sh = \
                self._interception.client_center_to_interception(hwnd)
            self._interception_ix = ix
            self._interception_iy = iy
            self.log_info(
                f'[Interception] 游戏: HWND=0x{hwnd:X} '
                f'PID={pid} 中心=({sx},{sy})'
            )
        else:
            self.log_error('[Interception] 未找到游戏窗口')

    def _refresh_interception_coords(self):
        if not self._interception or not self._game_hwnd:
            return
        try:
            _, _, ix, iy, _, _ = \
                self._interception.client_center_to_interception(self._game_hwnd)
            self._interception_ix = ix
            self._interception_iy = iy
        except Exception:
            pass

    # ================================================================
    # 工具
    # ================================================================

    def _is_game_foreground(self):
        if not self._game_hwnd:
            return False
        try:
            return ctypes.windll.user32.GetForegroundWindow() == self._game_hwnd
        except Exception:
            return False

    def _ensure_ball_mode(self):
        if not self._interception or not self._is_game_foreground():
            return
        self.log_info('[模式] 按下 E 切换到球模式')
        self._interception.press_key('E', hold_time=0.08)
        time.sleep(0.15)

    def update_info(self):
        elapsed = time.time() - self.session_start
        rate = self.total_throws / max(elapsed, 1) * 3600
        self.info_set('本轮丢球', f'{self.throw_count} 次')
        self.info_set('总计丢球', f'{self.total_throws} 次')
        self.info_set('丢球速率', f'{rate:.0f} 次/小时')
        self.info_set('运行时长', f'{elapsed / 60:.1f} 分钟')

    # ================================================================
    # 随机参数
    # ================================================================

    def _random_throw_interval(self):
        return random.uniform(
            self.get_config('Throw Interval Min (s)'),
            self.get_config('Throw Interval Max (s)'),
        )

    def _random_hold_time(self):
        return random.uniform(
            self.get_config('Hold Time Min (s)'),
            self.get_config('Hold Time Max (s)'),
        )

    def _random_work_duration(self):
        return random.uniform(
            self.get_config('Work Duration Min (min)'),
            self.get_config('Work Duration Max (min)'),
        ) * 60

    def _random_rest_duration(self):
        return random.uniform(
            self.get_config('Rest Duration Min (s)'),
            self.get_config('Rest Duration Max (s)'),
        )

    def get_config(self, key):
        return self.config.get(key, self.default_config.get(key, 0))
