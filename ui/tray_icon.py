"""
系统托盘图标
使用程序内绘制的图标，无需外部资源文件
"""
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction
from PySide6.QtWidgets import QSystemTrayIcon, QMenu


def _create_tray_icon() -> QIcon:
    """
    用代码绘制一个剪贴板图标（避免依赖外部 .ico 文件）
    32x32 像素，白底 + 蓝色边框的剪贴板图形
    """
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor(0, 0, 0, 0))  # 透明背景

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # 剪贴板主体（白色圆角矩形）
    painter.setBrush(QColor(255, 255, 255))
    painter.setPen(QColor(70, 130, 220))  # 蓝色边框
    painter.drawRoundedRect(4, 2, 24, 28, 4, 4)

    # 剪贴板上的横线（表示文字行）
    painter.setPen(QColor(70, 130, 220))
    painter.drawLine(9, 10, 23, 10)
    painter.drawLine(9, 15, 23, 15)
    painter.drawLine(9, 20, 17, 20)

    # 顶部的夹子
    painter.setBrush(QColor(70, 130, 220))
    painter.setPen(QColor(70, 130, 220))
    painter.drawRoundedRect(12, 0, 8, 6, 2, 2)

    painter.end()
    return QIcon(pixmap)


class TrayIcon(QSystemTrayIcon):
    """系统托盘图标，含右键菜单"""

    def __init__(self, parent=None):
        super().__init__(parent)
        icon = _create_tray_icon()
        self.setIcon(icon)
        self.setToolTip("剪贴板管理器")

        # 右键菜单
        menu = QMenu()
        self._show_action = QAction("显示/隐藏")
        self._show_action.triggered.connect(self._on_toggle)
        menu.addAction(self._show_action)

        menu.addSeparator()
        exit_action = QAction("退出")
        exit_action.triggered.connect(self._on_exit)
        menu.addAction(exit_action)

        self.setContextMenu(menu)

    def _on_toggle(self):
        """托盘图标点击 → 触发 activated 信号，由外部处理显示/隐藏"""
        self.activated.emit(QSystemTrayIcon.Trigger)

    def _on_exit(self):
        """退出程序"""
        from PySide6.QtWidgets import QApplication
        QApplication.instance().quit()
