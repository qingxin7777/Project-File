"""
记录列表组件
包含 "置顶区" 和 "最近记录" 两个分组，支持滚动和过滤
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QScrollArea, QWidget, QVBoxLayout, QGroupBox, QLabel, QSizePolicy
)
from ui.item_widget import ItemWidget


class ItemList(QScrollArea):
    """可滚动的记录列表"""

    # 信号：转发 ItemWidget 的操作信号
    copy_requested = Signal(int)
    pin_requested = Signal(int)
    delete_requested = Signal(int)
    tag_add_requested = Signal(int, int)
    selection_changed = Signal(int)  # 选中数量变化

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 内部容器
        container = QWidget()
        self._main_layout = QVBoxLayout(container)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(4)

        # ── 置顶区 ──
        self._pinned_group = QGroupBox("📌 置顶")
        self._pinned_layout = QVBoxLayout(self._pinned_group)
        self._pinned_layout.setContentsMargins(4, 4, 4, 4)
        self._pinned_layout.setSpacing(2)
        self._main_layout.addWidget(self._pinned_group)
        self._pinned_group.hide()  # 默认无置顶时不显示

        # ── 最近记录区 ──
        self._recent_group = QGroupBox("🕒 最近记录")
        self._recent_layout = QVBoxLayout(self._recent_group)
        self._recent_layout.setContentsMargins(4, 4, 4, 4)
        self._recent_layout.setSpacing(2)
        self._main_layout.addWidget(self._recent_group)

        # 底部弹簧（内容不足时填充空间）
        self._main_layout.addStretch()

        self.setWidget(container)

        # 追踪所有 ItemWidget
        self._all_widgets: list[ItemWidget] = []
        self._selected_ids: set[int] = set()

    def rebuild(self, items: list[dict]):
        """
        根据数据重建整个列表
        置顶项放在 pinned_group，非置顶项放在 recent_group
        """
        # 清空所有现有组件
        self._clear_all()

        pinned_items = [i for i in items if i.get("is_pinned")]
        recent_items = [i for i in items if not i.get("is_pinned")]

        # 构建置顶区
        if pinned_items:
            for item_data in pinned_items:
                widget = self._create_item_widget(item_data)
                self._pinned_layout.addWidget(widget)
            self._pinned_group.show()
        else:
            self._pinned_group.hide()

        # 构建最近区
        for item_data in recent_items:
            widget = self._create_item_widget(item_data)
            self._recent_layout.addWidget(widget)

    def _create_item_widget(self, item_data: dict) -> ItemWidget:
        """创建并连接一个 ItemWidget"""
        widget = ItemWidget(item_data)
        widget.copy_clicked.connect(self.copy_requested.emit)
        widget.pin_clicked.connect(self.pin_requested.emit)
        widget.delete_clicked.connect(self.delete_requested.emit)
        widget.tag_added.connect(self.tag_add_requested.emit)
        widget.checked_changed.connect(self._on_item_checked)
        self._all_widgets.append(widget)
        return widget

    def filter_items(self, search_text: str):
        """
        实时过滤：通过 setVisible 切换而不重建组件
        同时处理分组可见性
        """
        has_visible_pinned = False
        has_visible_recent = False
        lowered = search_text.lower()

        for widget in self._all_widgets:
            item = widget._item
            # 搜索范围：文字内容 + 图片路径 + 标签名
            match = False
            content_type = item.get("content_type", "text")

            if content_type == "text":
                text = item.get("text_content", "").lower()
                if lowered in text:
                    match = True
            elif content_type == "image":
                # 搜索图片路径和尺寸信息
                path = item.get("image_path", "").lower()
                size_text = item.get("text_content", "").lower()
                if lowered in path or lowered in size_text:
                    match = True

            # 也搜索标签
            if not match:
                from db import item_repo as repo
                tags = repo.get_tags_for_item(item["id"])
                for tag in tags:
                    if lowered in tag["name"].lower():
                        match = True
                        break

            widget.setVisible(match)

            # 判断所属分组
            if match and widget.isVisible():
                if item.get("is_pinned"):
                    has_visible_pinned = True
                else:
                    has_visible_recent = True

        # 更新分组可见性
        self._pinned_group.setVisible(has_visible_pinned)
        self._recent_group.setVisible(has_visible_recent)

    # ── 选择模式 ──

    def set_selection_mode(self, enabled: bool):
        """进入/退出选择模式"""
        self._selected_ids.clear()
        for widget in self._all_widgets:
            widget.set_selection_mode(enabled)
        self.selection_changed.emit(0)

    def get_selected_ids(self) -> list[int]:
        """获取所有已选中的 item ID"""
        return list(self._selected_ids)

    def get_selected_count(self) -> int:
        return len(self._selected_ids)

    def select_all(self):
        """勾选所有可见的记录"""
        for widget in self._all_widgets:
            if widget.isVisible() and not widget._checkbox.isChecked():
                widget._checkbox.setChecked(True)

    def deselect_all(self):
        """取消所有勾选"""
        for widget in self._all_widgets:
            if widget._checkbox.isChecked():
                widget._checkbox.setChecked(False)

    def _on_item_checked(self, item_id: int, checked: bool):
        """复选框状态变化回调"""
        if checked:
            self._selected_ids.add(item_id)
        else:
            self._selected_ids.discard(item_id)
        self.selection_changed.emit(len(self._selected_ids))

    def _clear_all(self):
        """清空所有 ItemWidget"""
        self._selected_ids.clear()
        for widget in self._all_widgets:
            widget.deleteLater()
        self._all_widgets.clear()

        # 清空布局中的残留 widget
        for layout in [self._pinned_layout, self._recent_layout]:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
