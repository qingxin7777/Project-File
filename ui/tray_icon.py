"""
系统托盘图标
使用程序内绘制的图标，无需外部资源文件
"""
from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction
from PySide6.QtWidgets import QSystemTrayIcon, QMenu


def _create_tray_icon() -> QIcon:
    """用代码绘制剪贴板图标 32x32"""
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # 剪贴板主体
    painter.setBrush(QColor(255, 255, 255))
    painter.setPen(QColor(70, 130, 220))
    painter.drawRoundedRect(4, 2, 24, 28, 4, 4)

    # 横线
    painter.setPen(QColor(70, 130, 220))
    painter.drawLine(9, 10, 23, 10)
    painter.drawLine(9, 15, 23, 15)
    painter.drawLine(9, 20, 17, 20)

    # 夹子
    painter.setBrush(QColor(70, 130, 220))
    painter.setPen(QColor(70, 130, 220))
    painter.drawRoundedRect(12, 0, 8, 6, 2, 2)

    painter.end()
    return QIcon(pixmap)


class TrayIcon(QSystemTrayIcon):
    """系统托盘图标，含右键菜单"""

    # 自定义信号：开机自启切换请求
    startup_toggle_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIcon(_create_tray_icon())
        self.setToolTip("剪贴板管理器")

        # 右键菜单
        self._menu = QMenu()

        # 显示/隐藏
        self._show_action = QAction("显示/隐藏")
        self._show_action.triggered.connect(self._on_toggle)
        self._menu.addAction(self._show_action)

        self._menu.addSeparator()

        # 开机自启（勾选式菜单项）
        self._startup_action = QAction("开机自启")
        self._startup_action.setCheckable(True)
        self._startup_action.triggered.connect(self._on_toggle_startup)
        self._menu.addAction(self._startup_action)

        self._menu.addSeparator()

        # 退出
        self._exit_action = QAction("退出")
        self._exit_action.triggered.connect(self._on_exit)
        self._menu.addAction(self._exit_action)

        self.setContextMenu(self._menu)

    def update_startup_state(self, enabled: bool):
        """更新开机自启菜单项的勾选状态"""
        self._startup_action.setChecked(enabled)

    def _on_toggle(self):
        """触发托盘信号 → 显示/隐藏弹窗"""
        self.activated.emit(QSystemTrayIcon.Trigger)

    def _on_toggle_startup(self):
        """切换开机自启 → 发射自定义信号"""
        self.startup_toggle_requested.emit()

    def _on_exit(self):
        """退出程序"""
        from PySide6.QtWidgets import QApplication
        QApplication.instance().quit()
