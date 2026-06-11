# Rock Kingdom Auto — 开发日志

## 项目信息

| 项目 | 详情 |
|------|------|
| **项目名** | rock-kingdom-auto |
| **目标游戏** | 洛克王国：世界 (Rock Kingdom: World) |
| **游戏引擎** | Unity |
| **GitHub** | https://github.com/PPAmaranth/rock-kingdom-auto |
| **本地路径** | `F:\git-project\github\ok-dev\rock-kingdom-auto` |
| **参考项目** | [ok-wuthering-waves](https://github.com/ok-oldking/ok-wuthering-waves) |
| **核心框架** | [ok-script](https://github.com/ok-oldking/ok-script) |
| **开发目标** | 个人使用/学习 |
| **目标分辨率** | 2560×1440 (16:9) |

---

## 功能规划（渐进式迭代）

### Phase 1 — MVP（当前）✅

- [x] 项目骨架搭建（参考 ok-ww 结构）
- [x] `AutoThrowTask` — 触发式自动丢球任务
  - [x] 随机间隔丢球（0.3~1.0 秒）
  - [x] 定时休息（连续工作 2~3 分钟 → 休息 8~15 秒）
  - [x] 所有参数可配置（GUI 面板调整）
  - [x] 日志输出（丢球计数、速率、运行时长）
  - [x] 勾选启用/取消停止（TriggerTask 模式）
- [x] Git 初始化 + GitHub 推送
- [ ] 待确认：Unity 窗口类名
- [ ] 待确认：游戏 exe 文件名
- [ ] 待确认：丢球操作方式（左键/右键、长按/点按）

### Phase 2 — 精灵识别 + 视角对准

- [ ] 研究目标精灵"噼啪鸟"的视觉特征
- [ ] 标注训练数据（截图 + 标注精灵位置）
- [ ] 训练 YOLOv8 模型（或使用模板匹配）
- [ ] 实现视角调整（检测精灵位置 → 移动鼠标对准）
- [ ] 日志增强：识别置信度、成功/失败统计

### Phase 3 — 界面状态识别

- [ ] 捕捉模式 vs 精灵模式识别
  - [ ] 屏幕左边精灵栏高亮 = 精灵战斗模式
  - [ ] 右下角道具图标 = 道具捕捉模式
- [ ] 高级球数量检测
- [ ] 道具不足自动去商店（或弹窗提醒）

### Phase 4 — 完善

- [ ] 错误恢复（掉线重连、场景异常退出）
- [ ] 多精灵支持
- [ ] 打包为 exe

---

## 技术架构

```
rock-kingdom-auto/
├── config.py                 # 全局配置（窗口、分辨率、任务注册）
├── main.py                   # Release 入口
├── main_debug.py             # Debug 入口
├── requirements.txt          # 依赖（ok-script + opencv + onnxocr）
├── src/
│   ├── __init__.py           # 通用常量
│   ├── globals.py            # 全局状态管理
│   ├── scene/
│   │   └── RKScene.py        # 场景状态（MVP: 空壳）
│   └── task/
│       ├── BaseRKTask.py     # 基础任务类
│       └── AutoThrowTask.py  # 核心：自动丢球逻辑
└── tests/
    └── TestAutoThrow.py      # 单元测试
```

### 继承链（参考 ok-ww）

```
ok-script BaseTask
  └── BaseRKTask              ← 洛克王国通用基础
        └── AutoThrowTask     ← 自动丢球（+ ok-script TriggerTask）
```

### 识别体系（当前状态）

| 识别方式 | MVP 状态 | 说明 |
|---------|:---:|------|
| 模板匹配 (COCO) | ❌ | MVP 不需要，Phase 2 开始标注 |
| 颜色检测 | ❌ | Phase 3 开始用于模式识别 |
| YOLO 模型 | ❌ | Phase 2 精灵识别 |
| OCR 文字 | ❌ | Phase 3 道具数量识别 |

---

## 关键决策记录

| 日期 | 决策 | 原因 |
|------|------|------|
| 2026-06-11 | 选择方案 A（ok-script 骨架精简版） | 基建免费，结构清晰，后续扩展方便，Effort: S |
| 2026-06-11 | MVP 不做精灵识别 | 先跑通基础丢球流程，能用最重要 |
| 2026-06-11 | MVP 不做模式识别 | 用户手动确保在捕捉模式 |
| 2026-06-11 | 丢球节奏：0.3~1s 间隔 + 2~3分钟工作 + 8~15s 休息 | 模拟人类操作，降低反作弊检测风险 |
| 2026-06-11 | 使用 PostMessage 后台模式 | 支持窗口最小化/遮挡时继续运行 |
| 2026-06-11 | 目标分辨率 2560×1440 | 个人使用，不需要多分辨率适配 |
| 2026-06-11 | 开发目标：个人使用/学习 | 不需要考虑多用户、多语言、分发渠道 |

---

## 参考来源

| 来源 | 用途 |
|------|------|
| `ok-wuthering-waves/config.py` | 窗口配置、任务注册模式 |
| `ok-wuthering-waves/src/task/BaseWWTask.py` | 基础任务类模式 |
| `ok-wuthering-waves/src/task/AutoCombatTask.py` | TriggerTask 参考 |
| `ok-wuthering-waves/src/task/FarmEchoTask.py` | 循环任务 + 日志输出参考 |
| `ok-wuthering-waves/src/scene/WWScene.py` | 场景管理参考 |
| `ok-wuthering-waves/src/globals.py` | 全局状态管理参考 |

---

## 相关文档

| 文档 | 路径 |
|------|------|
| ok-ww 技术架构 | `../ok-wuthering-waves-architecture.md` |
| ok-ww 后台模式原理 | `../ok-wuthering-waves-background-mode.md` |
| ok-ww 识别系统设计 | `../ok-wuthering-waves-recognition-system.md` |
| ok-ww AI 模型调查 | `../ok-wuthering-waves-ai-model.md` |
| gstack 开发流程指南 | `../gstack-for-game-automation.md` |
