"""
标签 CRUD 操作 + 记录-标签关联操作
操作 tags 和 item_tags 表
"""
import sqlite3
from db.database import get_connection


# ── 标签 CRUD ──

def add_tag(name: str) -> dict:
    """新建标签，返回包含 id 的字典"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO tags (name) VALUES (?)", (name,))
        conn.commit()
        tag_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        # 标签名重复
        conn.close()
        raise ValueError(f"标签 '{name}' 已存在")
    conn.close()
    return {"id": tag_id, "name": name}


def get_all_tags() -> list[dict]:
    """获取所有标签，按名称排序"""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tags ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def rename_tag(tag_id: int, new_name: str):
    """重命名标签"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE tags SET name = ? WHERE id = ?", (new_name, tag_id)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError(f"标签 '{new_name}' 已存在")
    conn.close()


def delete_tag(tag_id: int):
    """删除标签（关联的 item_tags 通过 CASCADE 自动删除，不删除记录本身）"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
    conn.commit()
    conn.close()


# ── 记录-标签关联 ──

def add_tag_to_item(item_id: int, tag_id: int):
    """给记录打标签（重复添加会被忽略）"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO item_tags (item_id, tag_id) VALUES (?, ?)",
        (item_id, tag_id)
    )
    conn.commit()
    conn.close()


def remove_tag_from_item(item_id: int, tag_id: int):
    """移除记录上的某个标签"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM item_tags WHERE item_id = ? AND tag_id = ?",
        (item_id, tag_id)
    )
    conn.commit()
    conn.close()


def get_tags_for_item(item_id: int) -> list[dict]:
    """获取一条记录的所有标签"""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """SELECT t.* FROM tags t
           JOIN item_tags it ON t.id = it.tag_id
           WHERE it.item_id = ?
           ORDER BY t.name""",
        (item_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
