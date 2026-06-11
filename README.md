# 洛克王国：世界 自动化工具 (Rock Kingdom Auto)

基于 [ok-script](https://github.com/ok-oldking/ok-script) 框架的游戏自动化工具，参考 [ok-wuthering-waves](https://github.com/ok-oldking/ok-wuthering-waves) 项目开发。

## 功能

- **MVP**: 自动向屏幕中央丢球捕捉精灵（定时随机间隔）
- 支持后台运行（窗口最小化/遮挡状态下继续工作）
- 模拟人类操作节奏：随机间隔丢球 + 定时休息

## 环境要求

- Windows 10+
- Python 3.12
- 2560×1440 分辨率（16:9）

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行 Release 版本
python main.py

# 运行 Debug 版本（显示调试信息）
python main_debug.py
```

## 项目结构

```
rock-kingdom-auto/
├── config.py                 # 全局配置
├── main.py                   # 入口
├── main_debug.py             # Debug 入口
├── src/
│   ├── globals.py            # 全局状态
│   ├── scene/RKScene.py      # 场景管理
│   └── task/
│       ├── BaseRKTask.py     # 基础任务类
│       └── AutoThrowTask.py  # 自动丢球任务
└── tests/
```

## 免责声明

本软件仅供个人学习 Python 编程、计算机视觉、UI 自动化使用。使用本软件可能违反游戏服务条款，请自行评估风险。

## License

MIT
