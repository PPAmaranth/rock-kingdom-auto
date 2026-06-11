from ok import BaseTask, Logger, og

logger = Logger.get_logger(__name__)


class BaseRKTask(BaseTask):
    """洛克王国自动化基础任务类。

    继承自 ok-script 的 BaseTask，拥有所有基础能力：
    - 画面捕获 (WGC/BitBlt)
    - 模板匹配 (find_one / find_feature)
    - 输入模拟 (click / send_key / mouse_down / mouse_up)
    - 日志输出 (log_info / log_debug / log_error)
    - OCR 文字识别 (ocr)

    后续可在此添加洛克王国通用的工具方法：
    - 场景判断 (in_world, in_shop, is_throw_mode)
    - 道具补充逻辑
    - 精灵识别 (YOLO)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.key_config = self.get_global_config('Game Hotkey')
        self.scene = None

    def validate(self, key, value):
        message = self.validate_config(key, value)
        if message:
            return False, message
        else:
            return True, None

    @property
    def logged_in(self):
        return og.my_app.logged_in

    @logged_in.setter
    def logged_in(self, value):
        og.my_app.logged_in = value
