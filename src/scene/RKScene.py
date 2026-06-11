from ok import Logger, BaseScene

logger = Logger.get_logger(__name__)


class RKScene(BaseScene):
    """洛克王国场景状态管理。

    MVP 阶段暂时为空壳，后续可在此添加：
    - 是否在游戏世界中 (in_world)
    - 是否在商城界面 (in_shop)
    - 捕捉模式检测 (is_throw_mode)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._in_world = None

    def reset(self):
        self._in_world = None
