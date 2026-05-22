"""
数据库连接管理 + 建表
存储位置：%LOCALAPPDATA%/ClipboardManager/clipboard.db
"""
import os
import sqlite3
from pathlib import Path


# 数据库文件路径
DB_DIR = Path(os.environ["LOCALAPPDATA"]) / "ClipboardManager"
DB_PATH = DB_DIR / "clipboard.db"


def get_connection() -> sqlite3.Connection:
    """获取数据库连接（自动创建目录和文件）"""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")       # WAL 模式：更好的读写性能
    conn.execute("PRAGMA foreign_keys=ON")          # 启用外键约束
    return conn


def init_db():
    """初始化数据库：创建所有表（如果不存在）"""
    conn = get_connection()
    cursor = conn.cursor()

    # 剪贴板记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clipboard_items (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            content_type    TEXT NOT NULL CHECK(content_type IN ('text', 'image')),
            text_content    TEXT,
            image_path      TEXT,
            thumbnail_path  TEXT,
            is_pinned       INTEGER NOT NULL DEFAULT 0,
            created_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            last_used_at    TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # 索引：加速按置顶/时间排序查询
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_items_pinned "
        "ON clipboard_items(is_pinned)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_items_created "
        "ON clipboard_items(created_at)"
    )

    # 标签表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # 记录-标签关联表（多对多）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS item_tags (
            item_id INTEGER NOT NULL,
            tag_id  INTEGER NOT NULL,
            PRIMARY KEY (item_id, tag_id),
            FOREIGN KEY (item_id) REFERENCES clipboard_items(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id)  REFERENCES tags(id) ON DELETE CASCADE
        )
    """)
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_item_tags_item ON item_tags(item_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_item_tags_tag ON item_tags(tag_id)"
    )

    conn.commit()
    conn.close()
