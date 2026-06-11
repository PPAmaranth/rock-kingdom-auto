"""模拟丢球测试 — 使用 Interception 驱动向游戏窗口发送多次长按点击。

运行方式:
    python test_throw_simulation.py

此脚本不依赖 ok-script 框架，独立测试 Interception 驱动在游戏中的实际效果。
"""

import ctypes
import sys
import time

# 项目路径
sys.path.insert(0, r"H:\git-project\ok-dev\rock-kingdom-auto")

from src.interception import InterceptionController


def main():
    print("=" * 60)
    print("Interception 丢球模拟测试")
    print("=" * 60)

    # ---- 初始化 ----
    ctrl = InterceptionController()
    if not ctrl.initialize():
        print("[FAIL] Interception 驱动初始化失败")
        return 1

    print(f"[OK] 驱动就绪: {ctrl.mouse_count} mice, {ctrl.keyboard_count} keyboards")

    # ---- 查找游戏窗口 ----
    hwnd, proc, pid = ctrl.find_game_window()
    if not hwnd:
        print("[FAIL] 未找到游戏窗口 (NRC-Win64-Shipping)")
        ctrl.destroy()
        return 1

    print(f"[OK] 游戏窗口: HWND=0x{hwnd:X} Process={proc} PID={pid}")

    # ---- 计算坐标 ----
    sx, sy, ix, iy, sw, sh = ctrl.client_center_to_interception(hwnd)
    print(f"[OK] 屏幕中心: ({sx}, {sy})")
    print(f"[OK] Interception 坐标: ({ix}, {iy})")
    print(f"[OK] 屏幕: {sw}x{sh}")

    # ---- 确认 ----
    print()
    print("即将执行 5 次丢球模拟 (每次长按 0.35s，间隔 1s)")
    print("请确保游戏窗口在前台！")
    print()
    response = input("按 Enter 开始测试，输入 q 退出: ").strip()
    if response.lower() == "q":
        ctrl.destroy()
        return 0

    # ---- 丢球模拟 ----
    num_throws = 5
    hold_time = 0.35
    interval = 1.0

    print()
    print(f"开始 {num_throws} 次丢球模拟...")
    print("-" * 40)

    successes = 0
    for i in range(num_throws):
        print(f"  [{i+1}/{num_throws}] ", end="", flush=True)

        # 刷新坐标（窗口可能移动）
        if i > 0:
            try:
                _, _, ix, iy, _, _ = ctrl.client_center_to_interception(hwnd)
            except Exception:
                pass

        # 执行点击
        result = ctrl.click(ix, iy, hold_time=hold_time)
        if result:
            print(f"OK  (coords: {ix},{iy}  hold: {hold_time}s)")
            successes += 1
        else:
            print(f"FAIL")

        if i < num_throws - 1:
            time.sleep(interval)

    # ---- 结果 ----
    print("-" * 40)
    print(f"完成: {successes}/{num_throws} 次成功")
    print()
    print("请检查游戏中的效果:")
    print("  1. 角色是否面向屏幕中央?")
    print("  2. 是否看到了丢球动画?")
    print("  3. 准星是否出现了?")
    print()
    print("如果游戏没有任何反应，可能原因:")
    print("  - ACE 在内核层也拦截了 HID 注入 (不太可能)")
    print("  - 鼠标设备选错了 (当前使用第一个鼠标设备)")
    print("  - 游戏窗口坐标不对")
    print("  - 游戏不在可丢球的状态 (比如在背包界面)")

    ctrl.destroy()
    return 0


if __name__ == "__main__":
    sys.exit(main())
