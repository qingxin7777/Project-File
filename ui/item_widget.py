"""
单条剪贴板记录组件
显示缩略图/文字预览，悬停时显示操作按钮，支持右键菜单
"""
import os
from datetime import datetime
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QPixmap, QIcon, QAction
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QMenu, QSizePolicy
)
from db import item_repo, tag_repo
from ui.styles import (
    ITEM_HEIGHT, TEXT_SECONDARY, ACCENT, PIN_COLOR, DELETE_COLOR
)


def _format_time(time_str: str) -> str:
    """将数据库时间字符串转为友好的显示格式"""
    try:
        dt = datetime.fromisoformat(time_str)
        now = datetime.now()
        diff = now - dt
        if diff.days == 0:
            return dt.strftime("%H:%M")
        elif diff.days == 1:
            return "昨天"
        elif diff.days < 7:
            return f"{diff.days}天前"
        else:
            return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return time_str or ""


class ItemWidget(QFrame):
    """单条剪贴板记录组件"""

    # 信号
    copy_clicked = Signal(int)       # 复制按钮点击 → item_id
    pin_clicked = Signal(int)        # 置顶按钮点击 → item_id
    delete_clicked = Signal(int)     # 删除操作 → item_id
    tag_added = Signal(int, int)     # 给记录添加标签 → (item_id, tag_id)

    def __init__(self, item_data: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("itemWidget")
        self._item = item_data       # 数据库记录字典
        self._item_id = item_data["id"]
        self._is_pinned = bool(item_data.get("is_pinned", 0))

        self.setFixedHeight(ITEM_HEIGHT)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # 主布局
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(6, 4, 6, 4)
        root_layout.setSpacing(8)

        # ── 左侧：缩略图/图标区域 ──
        self._build_thumbnail(root_layout)

        # ── 中间：文字信息 ──
        self._build_text_info(root_layout)

        # ── 右侧：操作按钮（默认隐藏，悬停显示） ──
        self._build_action_buttons(root_layout)

        # 悬停事件
        self._action_widget.hide()  # 默认不显示操作按钮

        # 右键菜单
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    # ── 构建子组件 ──

    def _build_thumbnail(self, layout):
        """左侧缩略图或类型图标"""
        self._thumb_label = QLabel()
        self._thumb_label.setFixedSize(48, 48)
        self._thumb_label.setAlignment(Qt.AlignCenter)

        content_type = self._item.get("content_type", "text")
        if content_type == "image":
            thumb_path = self._item.get("thumbnail_path", "")
            if thumb_path and os.path.exists(thumb_path):
                pixmap = QPixmap(thumb_path)
                pixmap = pixmap.scaled(
                    48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self._thumb_label.setPixmap(pixmap)
            else:
                self._thumb_label.setText("🖼️")
        else:
            self._thumb_label.setText("📄")

        layout.addWidget(self._thumb_label)

    def _build_text_info(self, layout):
        """中间文字信息区：预览 + 时间"""
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 2, 0, 2)
        info_layout.setSpacing(2)

        # 内容预览（前80个字符）
        content_type = self._item.get("content_type", "text")
        if content_type == "image":
            size_text = self._item.get("text_content", "")
            filename = os.path.basename(
                self._item.get("image_path", "")
            )
            preview = f"🖼️ {filename}  {size_text}"
        else:
            text = self._item.get("text_content", "")
            if len(text) > 80:
                text = text[:80] + "..."
            # 把换行替换为空格，单行显示
            text = text.replace("\n", " ")
            preview = text

        self._preview_label = QLabel(preview)
        self._preview_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        self._preview_label.setWordWrap(False)
        info_layout.addWidget(self._preview_label)

        # 时间
        time_str = _format_time(
            self._item.get("last_used_at", self._item.get("created_at", ""))
        )
        self._time_label = QLabel(time_str)
        self._time_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 11px;"
        )
        info_layout.addWidget(self._time_label)

        layout.addLayout(info_layout, stretch=1)

    def _build_action_buttons(self, layout):
        """右侧操作按钮区域"""
        self._action_widget = QFrame()
        action_layout = QHBoxLayout(self._action_widget)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(4)

        # 复制按钮
        self._copy_btn = QPushButton("📋")
        self._copy_btn.setObjectName("actionButton")
        self._copy_btn.setToolTip("复制内容")
        self._copy_btn.setFixedSize(28, 28)
        self._copy_btn.clicked.connect(
            lambda: self.copy_clicked.emit(self._item_id)
        )
        action_layout.addWidget(self._copy_btn)

        # 置顶按钮
        pin_icon = "📌" if not self._is_pinned else "📌"
        self._pin_btn = QPushButton(pin_icon)
        self._pin_btn.setObjectName("actionButton")
        self._pin_btn.setToolTip(
            "取消置顶" if self._is_pinned else "置顶"
        )
        if self._is_pinned:
            self._pin_btn.setStyleSheet(
                f"QPushButton#actionButton {{ color: {PIN_COLOR}; }}"
            )
        self._pin_btn.setFixedSize(28, 28)
        self._pin_btn.clicked.connect(
            lambda: self.pin_clicked.emit(self._item_id)
        )
        action_layout.addWidget(self._pin_btn)

        layout.addWidget(self._action_widget)

    # ── 悬停事件 ──

    def enterEvent(self, event):
        """鼠标进入 → 显示操作按钮"""
        self._action_widget.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开 → 隐藏操作按钮"""
        self._action_widget.hide()
        super().leaveEvent(event)

    # ── 右键菜单 ──

    def _show_context_menu(self, pos):
        """右键菜单：复制 / 置顶 / 加入标签 / 删除"""
        menu = QMenu(self)

        # 复制
        copy_action = QAction("📋 复制内容", menu)
        copy_action.triggered.connect(
            lambda: self.copy_clicked.emit(self._item_id)
        )
        menu.addAction(copy_action)

        # 置顶 / 取消置顶
        pin_text = "📌 取消置顶" if self._is_pinned else "📌 置顶"
        pin_action = QAction(pin_text, menu)
        pin_action.triggered.connect(
            lambda: self.pin_clicked.emit(self._item_id)
        )
        menu.addAction(pin_action)

        menu.addSeparator()

        # 加入标签子菜单
        tag_menu = QMenu("🏷️ 加入标签", menu)
        all_tags = tag_repo.get_all_tags()
        current_tags = item_repo.get_tags_for_item(self._item_id)
        current_tag_ids = {t["id"] for t in current_tags}

        for tag in all_tags:
            tag_action = QAction(tag["name"], tag_menu)
            tag_action.setCheckable(True)
            tag_action.setChecked(tag["id"] in current_tag_ids)
            tid = tag["id"]
            if tag["id"] in current_tag_ids:
                # 已打标签 → 点击移除
                tag_action.triggered.connect(
                    lambda checked, tid=tid: tag_repo.remove_tag_from_item(
                        self._item_id, tid
                    )
                )
            else:
                # 未打标签 → 点击添加
                tag_action.triggered.connect(
                    lambda checked, tid=tid: self.tag_added.emit(
                        self._item_id, tid
                    )
                )
            tag_menu.addAction(tag_action)

        if not all_tags:
            no_tag = QAction("（暂无标签，请先创建）", tag_menu)
            no_tag.setEnabled(False)
            tag_menu.addAction(no_tag)

        menu.addMenu(tag_menu)

        menu.addSeparator()

        # 删除
        delete_action = QAction("🗑️ 删除", menu)
        delete_action.triggered.connect(
            lambda: self.delete_clicked.emit(self._item_id)
        )
        menu.addAction(delete_action)

        menu.exec(self.mapToGlobal(pos))
