# 标签栏组件
# 水平可滚动，支持滚轮左右滑动，右键管理标签
# 「全部」标签固定在最左侧
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QScrollArea, QWidget, QHBoxLayout, QPushButton, QMenu, QInputDialog
)


class TagBar(QScrollArea):
    """水平可滚动的标签栏"""

    # 信号
    tag_selected = Signal(object)          # 选中标签 → tag_id 或 None（全部）
    new_tag_requested = Signal(str)        # 新建标签 → 名称
    rename_tag_requested = Signal(int, str)  # 重命名 → (tag_id, new_name)
    delete_tag_requested = Signal(int)     # 删除标签 → tag_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFixedHeight(40)
        self.setWidgetResizable(True)

        # 内部容器
        container = QWidget()
        self._layout = QHBoxLayout(container)
        self._layout.setContentsMargins(4, 2, 4, 2)
        self._layout.setSpacing(6)

        # ── "全部"标签（固定，始终第一个） ──
        self._all_button = QPushButton("🏠 全部")
        self._all_button.setObjectName("tagButton")
        self._all_button.setCheckable(True)
        self._all_button.setChecked(True)
        self._all_button.setFixedHeight(28)
        self._all_button.clicked.connect(lambda: self._on_clicked(None))
        self._layout.addWidget(self._all_button)

        # 占位弹簧（把标签往左推）
        self._layout.addStretch()

        self.setWidget(container)

        # 标签按钮缓存：{tag_id: QPushButton}
        self._tag_buttons: dict[int, QPushButton] = {}
        self._current_tag_id = None

        # 空白区域右键 → 新建标签
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_empty_right_click)

    def refresh(self, tags: list[dict]):
        # 根据标签数据重建标签按钮（保留「全部」按钮）
        # 移除旧标签按钮
        for btn in list(self._tag_buttons.values()):
            self._layout.removeWidget(btn)
            btn.deleteLater()
        self._tag_buttons.clear()

        # 重建标签按钮（插入到弹簧之前）
        stretch_index = self._layout.count() - 1
        for tag in tags:
            btn = QPushButton(tag["name"])
            btn.setObjectName("tagButton")
            btn.setCheckable(True)
            btn.setFixedHeight(28)

            # 捕获 tag_id 到 lambda
            tid = tag["id"]
            btn.clicked.connect(
                lambda checked, tid=tid: self._on_clicked(tid)
            )

            # 右键菜单
            btn.setContextMenuPolicy(Qt.CustomContextMenu)
            btn.customContextMenuRequested.connect(
                lambda pos, tid=tid: self._on_tag_right_click(pos, tid)
            )

            self._layout.insertWidget(stretch_index, btn)
            self._tag_buttons[tid] = btn

    def _on_clicked(self, tag_id):
        """点击标签按钮"""
        self._current_tag_id = tag_id
        # 更新按钮选中状态
        self._all_button.setChecked(tag_id is None)
        for tid, btn in self._tag_buttons.items():
            btn.setChecked(tid == tag_id)
        self.tag_selected.emit(tag_id)

    def clear_selection(self):
        # 取消所有标签选中，回到「全部」
        self._all_button.setChecked(True)
        self._current_tag_id = None
        for btn in self._tag_buttons.values():
            btn.setChecked(False)

    # ── 右键菜单 ──

    def _on_empty_right_click(self, pos):
        """右键标签栏空白区域 → 新建标签"""
        menu = QMenu(self)
        new_action = QAction("➕ 新建标签", menu)
        new_action.triggered.connect(self._prompt_new_tag)
        menu.addAction(new_action)
        menu.exec(self.mapToGlobal(pos))

    def _on_tag_right_click(self, pos, tag_id: int):
        """右键某个标签按钮 → 重命名 / 删除"""
        menu = QMenu(self)

        rename_action = QAction("✏️ 重命名", menu)
        rename_action.triggered.connect(
            lambda: self._prompt_rename_tag(tag_id)
        )
        menu.addAction(rename_action)

        delete_action = QAction("🗑️ 删除标签", menu)
        delete_action.triggered.connect(
            lambda: self.delete_tag_requested.emit(tag_id)
        )
        menu.addAction(delete_action)

        menu.exec(self.mapToGlobal(pos))

    def _prompt_new_tag(self):
        """弹窗输入新标签名"""
        name, ok = QInputDialog.getText(
            self, "新建标签", "请输入标签名称："
        )
        if ok and name.strip():
            self.new_tag_requested.emit(name.strip())

    def _prompt_rename_tag(self, tag_id: int):
        """弹窗输入新名称"""
        new_name, ok = QInputDialog.getText(
            self, "重命名标签", "请输入新名称："
        )
        if ok and new_name.strip():
            self.rename_tag_requested.emit(tag_id, new_name.strip())

    # ── 滚轮事件：支持水平滚动 ──

    def wheelEvent(self, event):
        """
        将垂直滚轮事件转换为水平滚动
        鼠标滚轮在标签栏上滚动 → 标签栏水平移动
        """
        delta = event.angleDelta().y()
        # 水平滚动条的当前值加上滚轮偏移
        current = self.horizontalScrollBar().value()
        self.horizontalScrollBar().setValue(current - delta)
        event.accept()
