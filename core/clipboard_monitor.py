"""
剪贴板监控：定时轮询剪贴板，检测文字和图片变化
每 500ms 检查一次，通过内容 hash 去重，避免重复记录
"""
import hashlib
from PySide6.QtCore import QTimer, QObject, Signal
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage

from db import item_repo
from core.image_handler import save_clipboard_image, delete_image_files

# 最大历史记录数
MAX_ITEMS = 200

# 单条文字最大存储长度（字符）
MAX_TEXT_LENGTH = 10000


class ClipboardMonitor(QObject):
    """
    剪贴板监控器
    使用 QTimer 轮询，500ms 间隔，对性能影响可忽略
    Qt 在 Windows 上没有剪贴板变化事件，轮询是标准做法
    """

    # 信号：新记录产生时发射，传递记录字典
    new_item_signal = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_hash = None  # 上次记录内容的 hash，用于去重

        # 创建定时器，每 500ms 触发一次
        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._check_clipboard)

    def start(self):
        """开始监控"""
        self._timer.start()

    def stop(self):
        """停止监控"""
        self._timer.stop()

    def notify_programmatic_copy(self, content):
        """
        通知监控器：刚刚由程序内触发了复制操作
        计算 content 的 hash 并设为 _last_hash，避免下一轮轮询时重复记录
        """
        if isinstance(content, str):
            text = content.encode("utf-8")
            self._last_hash = hashlib.sha256(text).hexdigest()
        elif isinstance(content, QImage):
            qimage_rgba = content.convertToFormat(QImage.Format_RGBA8888)
            ptr = qimage_rgba.bits()
            if ptr is not None:
                raw_bytes = ptr.tobytes()
                self._last_hash = hashlib.sha256(raw_bytes).hexdigest()

    def _check_clipboard(self):
        """检查剪贴板内容是否变化，如有变化则保存到数据库"""
        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData()

        if mime is None:
            return

        # ── 图片优先：如果同时有文字和图片（如复制网页内容），优先记录图片 ──
        if mime.hasImage():
            qimage = mime.imageData()
            if qimage is None or qimage.isNull():
                return

            # 通过图像原始字节计算 hash
            qimage_rgba = qimage.convertToFormat(QImage.Format_RGBA8888)
            ptr = qimage_rgba.bits()
            if ptr is None:
                return
            raw_bytes = ptr.tobytes()
            content_hash = hashlib.sha256(raw_bytes).hexdigest()

            # 与上次 hash 对比，相同则跳过
            if content_hash == self._last_hash:
                return
            self._last_hash = content_hash

            # 保存图片到磁盘 + 写入数据库
            try:
                img_info = save_clipboard_image(qimage)
                item = item_repo.add_item(
                    content_type="image",
                    image_path=img_info["image_path"],
                    thumbnail_path=img_info["thumbnail_path"],
                )
                # 把图片尺寸信息存入 text_content 字段（UI 展示用）
                size_text = f"{img_info['width']}x{img_info['height']}"
                item_repo.update_item(item["id"], text_content=size_text)
                item["text_content"] = size_text
            except Exception:
                return  # 图片保存失败，静默跳过

        elif mime.hasText():
            text = mime.text()
            if not text or len(text.strip()) == 0:
                return

            # 截断过长文本
            if len(text) > MAX_TEXT_LENGTH:
                text = text[:MAX_TEXT_LENGTH]

            # 通过文本 hash 去重
            content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            if content_hash == self._last_hash:
                return
            self._last_hash = content_hash

            # 写入数据库
            try:
                item = item_repo.add_item(
                    content_type="text",
                    text_content=text,
                )
            except Exception:
                return
        else:
            return  # 不支持的数据类型

        # ── 超限清理：超过 MAX_ITEMS 条时删除最旧的非置顶记录 ──
        count = item_repo.get_count()
        if count > MAX_ITEMS:
            overflow = count - MAX_ITEMS
            # 先查出要删除的记录（用于清理图片文件）
            items_to_delete = item_repo.get_items(limit=overflow, offset=0)
            # 取最旧的非置顶记录
            conn_cleanup = __import__("db.database", fromlist=["get_connection"]).get_connection()
            conn_cleanup.row_factory = __import__("sqlite3").Row
            cur = conn_cleanup.cursor()
            cur.execute(
                """SELECT * FROM clipboard_items
                   WHERE is_pinned = 0
                   ORDER BY last_used_at ASC LIMIT ?""",
                (overflow,)
            )
            old_items = cur.fetchall()
            conn_cleanup.close()
            for old in old_items:
                old_dict = dict(old)
                if old_dict.get("image_path"):
                    delete_image_files(
                        old_dict["image_path"],
                        old_dict.get("thumbnail_path", ""),
                    )
            item_repo.delete_oldest_nonpinned(overflow)

        # 通知 UI 刷新
        self.new_item_signal.emit(item)
