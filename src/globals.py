from PySide6.QtCore import Signal, QObject

from ok import Logger

logger = Logger.get_logger(__name__)


class Globals(QObject):
    """全局状态管理器。

    MVP 阶段仅保留基础结构，后续如有需要可在此添加
    YOLO 模型管理、状态缓存等。
    """

    def __init__(self, exit_event):
        super().__init__()
        self.logged_in = False


if __name__ == "__main__":
    glbs = Globals(exit_event=None)
