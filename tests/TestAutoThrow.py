import unittest


class TestAutoThrow(unittest.TestCase):
    """AutoThrowTask 单元测试。"""

    def test_config_defaults(self):
        """验证默认配置值是否合理。"""
        from src.task.AutoThrowTask import AutoThrowTask
        task = AutoThrowTask()
        cfg = task.default_config
        self.assertLess(cfg['Throw Interval Min (s)'], cfg['Throw Interval Max (s)'])
        self.assertLess(cfg['Hold Time Min (s)'], cfg['Hold Time Max (s)'])
        self.assertLess(cfg['Work Duration Min (min)'], cfg['Work Duration Max (min)'])
        self.assertLess(cfg['Rest Duration Min (s)'], cfg['Rest Duration Max (s)'])

    def test_random_ranges(self):
        """验证随机值在配置范围内。"""
        import random
        random.seed(42)

        from src.task.AutoThrowTask import AutoThrowTask
        task = AutoThrowTask()

        for _ in range(100):
            interval = task._random_throw_interval()
            self.assertGreaterEqual(interval, task.get_config('Throw Interval Min (s)'))
            self.assertLessEqual(interval, task.get_config('Throw Interval Max (s)'))

            hold = task._random_hold_time()
            self.assertGreaterEqual(hold, task.get_config('Hold Time Min (s)'))
            self.assertLessEqual(hold, task.get_config('Hold Time Max (s)'))

    def test_info_fields(self):
        """验证 info_set 调用不会异常。"""
        import time
        from src.task.AutoThrowTask import AutoThrowTask
        task = AutoThrowTask()
        task.throw_count = 10
        task.total_throws = 100
        task.session_start = time.time() - 120
        task.update_info()  # 不应抛异常


if __name__ == '__main__':
    unittest.main()
