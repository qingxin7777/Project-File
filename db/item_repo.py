"""
剪贴板记录 CRUD 操作
操作 clipboard_items 表
"""
from db.database import get_connection


def add_item(content_type: str, text_content: str = None,
             image_path: str = None, thumbnail_path: str = None) -> dict:
    """添加一条剪贴板记录，返回包含 id 的字典"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO clipboard_items (content_type, text_content, image_path, thumbnail_path)
           VALUES (?, ?, ?, ?)""",
        (content_type, text_content, image_path, thumbnail_path)
    )
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    return get_item(item_id)


def get_item(item_id: int) -> dict | None:
    """根据 ID 获取单条记录"""
    conn = get_connection()
    conn.row_factory = sqlite3.Row  # 让查询结果支持字典式访问
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clipboard_items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_items(limit: int = 200, offset: int = 0,
              search_text: str = None, tag_id: int = None) -> list[dict]:
    """
    获取记录列表，支持搜索和标签过滤
    排序规则：置顶优先 → 最后使用时间倒序
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 构建查询条件
    conditions = []
    params = []

    if search_text:
        # 搜索文字内容、图片路径、标签名
        conditions.append(
            """(ci.text_content LIKE ? OR ci.image_path LIKE ?
              OR ci.id IN (
                  SELECT it.item_id FROM item_tags it
                  JOIN tags t ON t.id = it.tag_id
                  WHERE t.name LIKE ?
              ))"""
        )
        like_pattern = f"%{search_text}%"
        params.extend([like_pattern, like_pattern, like_pattern])

    if tag_id is not None:
        conditions.append(
            """ci.id IN (SELECT item_id FROM item_tags WHERE tag_id = ?)"""
        )
        params.append(tag_id)

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    query = f"""
        SELECT ci.* FROM clipboard_items ci
        {where_clause}
        ORDER BY ci.is_pinned DESC, ci.last_used_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_item(item_id: int, **kwargs):
    """更新记录字段（如 is_pinned, last_used_at, text_content 等）"""
    if not kwargs:
        return
    conn = get_connection()
    cursor = conn.cursor()
    set_clause = ", ".join(f"{key} = ?" for key in kwargs.keys())
    values = list(kwargs.values())
    values.append(item_id)
    cursor.execute(
        f"UPDATE clipboard_items SET {set_clause} WHERE id = ?", values
    )
    conn.commit()
    conn.close()


def delete_item(item_id: int):
    """删除一条记录（关联的 item_tags 通过 CASCADE 自动删除）"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clipboard_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()


def delete_oldest_nonpinned(count: int):
    """删除最旧的 N 条非置顶记录（用于超限清理）"""
    if count <= 0:
        return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """DELETE FROM clipboard_items WHERE id IN (
               SELECT id FROM clipboard_items
               WHERE is_pinned = 0
               ORDER BY last_used_at ASC
               LIMIT ?
           )""",
        (count,)
    )
    conn.commit()
    conn.close()


def get_count() -> int:
    """获取记录总数"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM clipboard_items")
    count = cursor.fetchone()[0]
    conn.close()
    return count


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
