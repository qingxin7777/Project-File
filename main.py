"""
剪贴板管理器 — 入口文件
常驻 Windows 状态栏，记录文字和图片剪贴板历史。

使用方法：
    python main.py

依赖：PySide6, Pillow
"""
import sys
from PySide6.QtWidgets import QApplication

# 注意：Qt 6.7+ 中高 DPI 缩放默认启用，无需手动设置


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ClipboardManager")
    # 关键：关闭弹窗时不退出程序，托盘图标常驻
    app.setQuitOnLastWindowClosed(False)

    # ── 1. 初始化数据库 ──
    from db.database import init_db
    init_db()

    # ── 2. 系统托盘图标 ──
    from ui.tray_icon import TrayIcon
    tray = TrayIcon()
    tray.show()

    # ── 3. 剪贴板监控 ──
    from core.clipboard_monitor import ClipboardMonitor
    monitor = ClipboardMonitor()

    # ── 4. 主弹窗（需要 monitor 引用以跳过程序内复制） ──
    from ui.popup_window import PopupWindow
    popup = PopupWindow(tray, monitor)
    # 新记录 → 刷新弹窗列表
    monitor.new_item_signal.connect(popup.on_new_item)
    monitor.start()

    # 托盘点击 → 切换弹窗显示/隐藏
    tray.activated.connect(lambda reason: popup.toggle_visibility())

    # ── 5. 开机自启 ──
    from core import startup_manager
    # 初始化菜单勾选状态
    tray.update_startup_state(startup_manager.is_enabled())
    # 开机自启菜单点击 → 切换状态
    def on_toggle_startup():
        enabled = startup_manager.toggle()
        tray.update_startup_state(enabled)
    tray.startup_toggle_requested.connect(on_toggle_startup)

    # ── 启动 ──
    print("剪贴板管理器已启动 — 点击系统托盘图标打开面板")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
