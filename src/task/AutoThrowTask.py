import random
import time

from qfluentwidgets import FluentIcon

from ok import Logger, TriggerTask
from src.task.BaseRKTask import BaseRKTask

logger = Logger.get_logger(__name__)


class AutoThrowTask(BaseRKTask, TriggerTask):
    """自动丢球捕捉任务。

    功能：
    - 以随机间隔 (0.3~1.0 秒) 向屏幕中央丢出精灵球
    - 每连续工作 2~3 分钟后，休息 8~15 秒（模拟人类行为）
    - 作为 TriggerTask，勾选即开启，取消即停止

    进阶 TODO：
    - 精灵识别 + 视角对准 (YOLO)
    - 捕捉模式检测（道具模式 vs 精灵模式）
    - 高级球数量检测 + 自动补货
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "Auto Throw"
        self.group_name = "Capture"
        self.group_icon = FluentIcon.GAME
        self.description = "自动向前方丢球捕捉精灵（MVP: 固定向屏幕中央丢球）"
        self.icon = FluentIcon.CALORIES
        self.trigger_interval = 0.1

        # ========== 可配置参数 ==========
        self.default_config = {
            '_enabled': True,
            'Throw Interval Min (s)': 0.3,
            'Throw Interval Max (s)': 1.0,
            'Hold Time Min (s)': 0.15,
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

        # ========== 运行状态 ==========
        self.throw_count = 0
        self.total_throws = 0
        self.session_start = 0

    def run(self):
        """自动丢球主循环。"""
        self.throw_count = 0
        self.session_start = time.time()

        work_duration = self._random_work_duration()
        work_start = time.time()
        self.log_info(f'[开始] 自动丢球启动 | 本轮工作 {work_duration / 60:.1f} 分钟')

        while True:
            # ---- 检查是否需要休息 ----
            elapsed = time.time() - work_start
            if elapsed >= work_duration:
                rest = self._random_rest_duration()
                self.log_info(f'[休息] 已连续工作 {elapsed / 60:.1f} 分钟，休息 {rest:.1f} 秒')

                # 更新 GUI 计数信息
                self.update_info()

                self.sleep(rest)

                # 开始新一轮工作
                work_duration = self._random_work_duration()
                work_start = time.time()
                self.throw_count = 0
                self.log_info(f'[继续] 新一轮工作 {work_duration / 60:.1f} 分钟')

            # ---- 丢球 ----
            interval = self._random_throw_interval()
            self.sleep(interval)
            self._do_throw()

    def _do_throw(self):
        """执行一次丢球操作：长按鼠标左键 → 松开。"""
        hold_time = self._random_hold_time()

        # 屏幕中央坐标
        x = self.width_of_screen(0.5)
        y = self.height_of_screen(0.5)

        self.mouse_down(key='left', x=x, y=y)
        self.sleep(hold_time)
        self.mouse_up(key='left')

        self.throw_count += 1
        self.total_throws += 1

        # 周期性地输出日志（每 50 次或每 30 秒）
        if self.throw_count % 50 == 0:
            self.log_info(
                f'[丢球] 本轮 {self.throw_count} 次 | '
                f'总计 {self.total_throws} 次 | '
                f'间隔 {hold_time:.2f}s'
            )

    def update_info(self):
        """更新 GUI 面板信息。"""
        elapsed = time.time() - self.session_start
        rate = self.total_throws / max(elapsed, 1) * 3600
        self.info_set('本轮丢球', f'{self.throw_count} 次')
        self.info_set('总计丢球', f'{self.total_throws} 次')
        self.info_set('丢球速率', f'{rate:.0f} 次/小时')
        self.info_set('运行时长', f'{elapsed / 60:.1f} 分钟')

    # ========== 随机参数生成 ==========

    def _random_throw_interval(self):
        """随机丢球间隔 (秒)。"""
        min_val = self.get_config('Throw Interval Min (s)')
        max_val = self.get_config('Throw Interval Max (s)')
        return random.uniform(min_val, max_val)

    def _random_hold_time(self):
        """随机长按时间 (秒)。"""
        min_val = self.get_config('Hold Time Min (s)')
        max_val = self.get_config('Hold Time Max (s)')
        return random.uniform(min_val, max_val)

    def _random_work_duration(self):
        """随机连续工作时间 (秒)。"""
        min_val = self.get_config('Work Duration Min (min)')
        max_val = self.get_config('Work Duration Max (min)')
        return random.uniform(min_val, max_val) * 60

    def _random_rest_duration(self):
        """随机休息时间 (秒)。"""
        min_val = self.get_config('Rest Duration Min (s)')
        max_val = self.get_config('Rest Duration Max (s)')
        return random.uniform(min_val, max_val)

    def get_config(self, key):
        """获取配置值，带默认值回退。"""
        return self.config.get(key, self.default_config.get(key, 0))
