"""
QSS 样式表 — 暗色主题
统一管理所有颜色、间距、圆角等视觉参数
"""

# 颜色常量
BG_DARK = "#1E1E2E"          # 面板背景
BG_INPUT = "#2A2A3C"         # 输入框背景
BG_ITEM = "#2D2D3F"          # 记录项背景
BG_ITEM_HOVER = "#3A3A52"    # 记录项悬停
BG_BUTTON = "#4A4A6A"        # 按钮背景
BG_BUTTON_HOVER = "#5A5A80"  # 按钮悬停
TEXT_PRIMARY = "#E0E0E0"     # 主文字色
TEXT_SECONDARY = "#9090A0"   # 次要文字色
ACCENT = "#4C8CFF"           # 强调色（蓝色）
ACCENT_HOVER = "#6BA0FF"     # 强调色悬停
PIN_COLOR = "#FFB347"        # 置顶色（橙色）
BORDER = "#3E3E55"           # 边框色
DELETE_COLOR = "#E05555"     # 删除按钮色
DELETE_HOVER = "#FF7070"     # 删除按钮悬停

# 间距常量
RADIUS = 8        # 圆角半径
PADDING = 8       # 内边距
SPACING = 4       # 元素间距
ITEM_HEIGHT = 56  # 每条记录的高度

# 弹窗尺寸
POPUP_WIDTH = 400
POPUP_HEIGHT = 550

STYLESHEET = f"""
/* ── 全局 ── */
* {{
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
    color: {TEXT_PRIMARY};
}}

/* ── 弹窗（popup_window 用 objectName 选择） ── */
QFrame#popupWindow {{
    background-color: {BG_DARK};
    border: 1px solid {BORDER};
    border-radius: {RADIUS}px;
}}

/* ── 搜索框 ── */
QLineEdit {{
    background-color: {BG_INPUT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    color: {TEXT_PRIMARY};
    selection-background-color: {ACCENT};
}}
QLineEdit:focus {{
    border-color: {ACCENT};
}}

/* ── 分组标题 ── */
QGroupBox {{
    font-weight: bold;
    color: {TEXT_SECONDARY};
    border: none;
    margin-top: 8px;
    padding-top: 8px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
}}

/* ── 滚动区域 ── */
QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollBar:vertical {{
    background: {BG_DARK};
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {BG_BUTTON};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {BG_BUTTON_HOVER};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background: {BG_DARK};
    height: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:horizontal {{
    background: {BG_BUTTON};
    border-radius: 3px;
    min-width: 20px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {BG_BUTTON_HOVER};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* ── 记录项 ── */
QFrame#itemWidget {{
    background-color: {BG_ITEM};
    border-radius: 6px;
    padding: 4px;
}}
QFrame#itemWidget:hover {{
    background-color: {BG_ITEM_HOVER};
}}

/* ── 通用按钮 ── */
QPushButton {{
    background-color: {BG_BUTTON};
    border: none;
    border-radius: 4px;
    padding: 4px 10px;
    color: {TEXT_PRIMARY};
}}
QPushButton:hover {{
    background-color: {BG_BUTTON_HOVER};
}}
QPushButton:pressed {{
    background-color: {BG_BUTTON};
}}

/* ── 标签按钮 ── */
QPushButton#tagButton {{
    background-color: {BG_INPUT};
    border-radius: 12px;
    padding: 4px 14px;
    font-size: 12px;
}}
QPushButton#tagButton:checked {{
    background-color: {ACCENT};
    color: white;
}}
QPushButton#tagButton:hover {{
    background-color: {BG_BUTTON_HOVER};
}}
QPushButton#tagButton:checked:hover {{
    background-color: {ACCENT_HOVER};
}}

/* ── 操作按钮（复制、置顶） ── */
QPushButton#actionButton {{
    background-color: transparent;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 14px;
    min-width: 28px;
}}
QPushButton#actionButton:hover {{
    background-color: {BG_BUTTON};
}}

/* ── 菜单 ── */
QMenu {{
    background-color: {BG_DARK};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 24px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background-color: {ACCENT};
}}
QMenu::separator {{
    height: 1px;
    background: {BORDER};
    margin: 4px 8px;
}}
"""
