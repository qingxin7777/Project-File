"""
搜索框组件
实时过滤：输入即搜索，通过 setVisible 切换而不重建组件
"""
from PySide6.QtWidgets import QLineEdit
from PySide6.QtCore import Signal


class SearchBar(QLineEdit):
    """搜索输入框，发出 textChanged 信号供外部连接"""

    # 信号：搜索文本变化时发出
    search_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("搜索文字或图片...")
        self.setClearButtonEnabled(True)  # 右侧显示清除按钮
        self.setFixedHeight(36)

        # 绑定文本变化信号
        self.textChanged.connect(self.search_changed.emit)
