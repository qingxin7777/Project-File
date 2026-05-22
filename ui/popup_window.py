"""
主弹窗：搜索栏 + 记录列表 + 标签栏
无边框、不在任务栏显示、失去焦点时自动隐藏
"""
from PySide6.QtCore import Qt, Signal, QTimer, QEvent
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QApplication, QSystemTrayIcon, QInputDialog, QMessageBox
)
from PySide6.QtGui import QImage

from db import item_repo, tag_repo
from core.image_handler import delete_image_files
from ui.search_bar import SearchBar
from ui.item_list import ItemList
from ui.tag_bar import TagBar
from ui.styles import STYLESHEET, POPUP_WIDTH, POPUP_HEIGHT


class PopupWindow(QFrame):
    """剪贴板管理器主弹窗"""

    def __init__(self, tray_icon: QSystemTrayIcon, monitor, parent=None):
        super().__init__(parent)
        self.setObjectName("popupWindow")
        self._tray_icon = tray_icon
        self._monitor = monitor  # 用于通知监控器跳过程序内复制

        # 窗口标志：无边框 + 工具提示级别（不在任务栏显示 + 不抢焦点）
        self.setWindowFlags(
            Qt.ToolTip | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedSize(POPUP_WIDTH, POPUP_HEIGHT)

        # 应用样式
        self.setStyleSheet(STYLESHEET)

        # ── 布局 ──
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # 搜索栏
        self._search_bar = SearchBar()
        self._search_bar.search_changed.connect(self._on_search)
        main_layout.addWidget(self._search_bar)

        # 记录列表
        self._item_list = ItemList()
        self._item_list.copy_requested.connect(self._copy_item)
        self._item_list.pin_requested.connect(self._toggle_pin)
        self._item_list.delete_requested.connect(self._delete_item)
        self._item_list.tag_add_requested.connect(self._add_tag_to_item)
        main_layout.addWidget(self._item_list, stretch=1)

        # 标签栏
        self._tag_bar = TagBar()
        self._tag_bar.tag_selected.connect(self._on_tag_filter)
        self._tag_bar.new_tag_requested.connect(self._create_tag)
        self._tag_bar.rename_tag_requested.connect(self._rename_tag)
        self._tag_bar.delete_tag_requested.connect(self._delete_tag)
        main_layout.addWidget(self._tag_bar)

        # 安装全局事件过滤器（失去焦点时隐藏）
        QApplication.instance().installEventFilter(self)

    # ── 显示/隐藏/定位 ──

    def toggle_visibility(self):
        """切换弹窗显示/隐藏"""
        if self.isVisible():
            self.hide()
        else:
            self._position_near_tray()
            self._refresh_all()
            self.show()

    def _position_near_tray(self):
        """
        将弹窗定位在任务栏托盘上方
        智能判断任务栏位置（顶部/底部/左侧/右侧）
        """
        tray_geo = self._tray_icon.geometry()
        screen = QApplication.primaryScreen().availableGeometry()

        # 判断任务栏位置
        if tray_geo.top() < screen.height() // 3:
            y = tray_geo.bottom() + 10
        elif tray_geo.left() > screen.width() // 2:
            x = tray_geo.left() - self.width() - 10
            y = tray_geo.bottom() - self.height()
            x = max(screen.left(), min(x, screen.right() - self.width()))
            y = max(screen.top(), min(y, screen.bottom() - self.height()))
            self.move(x, y)
            return
        else:
            y = tray_geo.top() - self.height() - 10

        x = tray_geo.center().x() - self.width() // 2
        x = max(screen.left(), min(x, screen.right() - self.width()))
        y = max(screen.top(), min(y, screen.bottom() - self.height()))
        self.move(x, y)

    def eventFilter(self, obj, event):
        """
        全局事件过滤器：弹窗失去焦点时自动隐藏
        延迟 100ms 确保内部点击事件能正常触发
        """
        if event.type() == QEvent.WindowDeactivate and self.isVisible():
            if obj is self:
                QTimer.singleShot(100, self._hide_if_lost_focus)
        return super().eventFilter(obj, event)

    def _hide_if_lost_focus(self):
        """如果没有子控件持有焦点，则隐藏"""
        if not self.isActiveWindow:
            self.hide()

    # ── 数据刷新 ──

    def _refresh_all(self):
        """刷新列表和标签栏"""
        self._refresh_item_list()
        self._refresh_tag_bar()

    def _refresh_item_list(self, search_text: str = None, tag_id: int = None):
        """从数据库加载记录并刷新列表"""
        items = item_repo.get_items(
            search_text=search_text, tag_id=tag_id
        )
        self._item_list.rebuild(items)

    def _refresh_tag_bar(self):
        """刷新标签栏"""
        tags = tag_repo.get_all_tags()
        self._tag_bar.refresh(tags)

    # ── 操作处理 ──

    def _on_search(self, text: str):
        """搜索框文本变化 → 过滤列表"""
        self._item_list.filter_items(text)
        # 也更新标签栏的高亮状态：如果有搜索文字，取消标签选中
        if text:
            self._tag_bar.clear_selection()

    def _on_tag_filter(self, tag_id):
        """标签栏选中标签 → 按标签过滤"""
        self._search_bar.clear()
        self._refresh_item_list(tag_id=tag_id)

    def on_new_item(self, item: dict):
        """剪贴板监控发现新记录时调用"""
        self._refresh_item_list()

    def _copy_item(self, item_id: int):
        """复制记录内容到剪贴板"""
        item = item_repo.get_item(item_id)
        if not item:
            return

        clipboard = QApplication.clipboard()
        if item["content_type"] == "text":
            text = item["text_content"] or ""
            clipboard.setText(text)
            # 通知监控器跳过此次复制（避免重复记录）
            self._monitor.notify_programmatic_copy(text)
        elif item["content_type"] == "image" and item["image_path"]:
            import os
            if os.path.exists(item["image_path"]):
                qimage = QImage(item["image_path"])
                if not qimage.isNull():
                    clipboard.setImage(qimage)
                    self._monitor.notify_programmatic_copy(qimage)

        # 更新最后使用时间
        from datetime import datetime
        now = datetime.now().isoformat(sep=" ", timespec="seconds")
        item_repo.update_item(item_id, last_used_at=now)
        self._refresh_item_list()

    def _toggle_pin(self, item_id: int):
        """切换置顶状态"""
        item = item_repo.get_item(item_id)
        if item:
            new_state = 1 if not item.get("is_pinned") else 0
            item_repo.update_item(item_id, is_pinned=new_state)
            self._refresh_item_list()

    def _add_tag_to_item(self, item_id: int, tag_id: int):
        """给记录添加标签"""
        tag_repo.add_tag_to_item(item_id, tag_id)
        self._refresh_item_list()

    def _delete_item(self, item_id: int):
        """删除记录（含图片文件）"""
        item = item_repo.get_item(item_id)
        if item and item.get("image_path"):
            delete_image_files(
                item["image_path"], item.get("thumbnail_path", "")
            )
        item_repo.delete_item(item_id)
        self._refresh_item_list()

    def _create_tag(self, name: str):
        """新建标签"""
        try:
            tag_repo.add_tag(name)
            self._refresh_tag_bar()
        except ValueError as e:
            pass  # 标签已存在，忽略

    def _rename_tag(self, tag_id: int, new_name: str):
        """重命名标签"""
        try:
            tag_repo.rename_tag(tag_id, new_name)
            self._refresh_all()
        except ValueError:
            pass

    def _delete_tag(self, tag_id: int):
        """删除标签（只解除关联，不删除记录）"""
        tag_repo.delete_tag(tag_id)
        self._refresh_all()
