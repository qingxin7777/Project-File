# 📋 剪贴板管理器

Windows 状态栏常驻剪贴板管理工具，自动记录文字和图片剪贴板历史，支持搜索、标签分类和置顶。

## ✨ 功能

- **自动记录** — 后台监控剪贴板变化，自动保存文字和图片（截图）内容
- **图片支持** — 微信截图、Snipaste 等工具的截图自动保存，生成缩略图预览
- **搜索过滤** — 实时搜索文字内容、图片文件名和标签名
- **标签分类** — 自定义标签，给记录打标签方便归类查找
- **置顶功能** — 重要记录一键置顶，始终显示在列表最上方
- **本地存储** — SQLite 数据库，最多保存 200 条记录，自动清理旧数据
- **开机自启** — 支持开机自动启动（可选），托盘右键菜单一键开关
- **暗色主题** — 深色界面风格，与 Windows 暗色模式搭配
- **轻量无依赖** — 仅需 Python 3.12+ 和两个第三方库

## 🖥️ 界面

```
┌─────────────────────────────┐
│  🔍 搜索剪贴板记录...        │  ← 搜索栏
├─────────────────────────────┤
│  📌 置顶                      │
│  ├─ 📄 重要文字内容...       │  ← 置顶区
│                              │
│  🕒 最近记录                  │
│  ├─ 🖼️ 截图_20260523.png    │  ← 最近区
│  ├─ 📄 复制的文字...         │
│  └─ ...                      │
├─────────────────────────────┤
│  🏠全部 │ 🏷️标签1 │ 标签2   │  ← 标签栏
└─────────────────────────────┘
```

## 📦 安装

### 环境要求

- Windows 10/11
- Python 3.12+
- pip

### 步骤

```bash
# 1. 克隆项目
git clone https://github.com/qingxin7777/clipboard-manager.git
cd clipboard-manager

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行
python main.py
```

程序启动后，状态栏会出现剪贴板图标，点击图标打开面板。

### 创建桌面快捷方式

已内置 `剪贴板管理器.lnk`，双击即可启动。也可拖到桌面或任务栏。

## 🔧 使用说明

| 操作 | 方式 |
|------|------|
| 打开/隐藏面板 | 左键点击状态栏图标 |
| 复制记录内容 | 悬停记录 → 点击 📋 按钮 |
| 置顶/取消置顶 | 悬停记录 → 点击 📌 按钮 |
| 右键菜单 | 右键点击记录 → 复制/置顶/标签/删除 |
| 搜索 | 在顶部搜索框输入关键词 |
| 按标签过滤 | 点击底部标签 |
| 新建标签 | 右键点击底部标签栏空白处 |
| 开机自启 | 右键状态栏图标 → 勾选「开机自启」 |
| 退出程序 | 右键状态栏图标 → 点击「退出」 |

## 🗄️ 数据存储

- **数据库**：`%LOCALAPPDATA%\ClipboardManager\clipboard.db`
- **图片/缩略图**：`%LOCALAPPDATA%\ClipboardCache\`
- **开机自启脚本**：`%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\ClipboardManager.vbs`

## 🏗️ 项目结构

```
clipboard-manager/
├── main.py                    # 入口文件
├── requirements.txt           # Python 依赖
│
├── core/
│   ├── clipboard_monitor.py   # 剪贴板监控（500ms 轮询 + hash 去重）
│   ├── image_handler.py       # 图片保存 + 120x120 缩略图生成
│   └── startup_manager.py     # 开机自启管理（Startup 文件夹 VBS）
│
├── db/
│   ├── database.py            # SQLite 连接 + 建表
│   ├── item_repo.py           # 剪贴板记录 CRUD
│   └── tag_repo.py            # 标签 CRUD
│
└── ui/
    ├── tray_icon.py           # 系统托盘图标 + 右键菜单
    ├── popup_window.py        # 主弹窗
    ├── search_bar.py          # 搜索框
    ├── item_list.py           # 记录列表（置顶区 + 最近区）
    ├── item_widget.py         # 单条记录组件
    ├── tag_bar.py             # 水平标签栏
    └── styles.py              # 暗色主题样式
```

## 🛠️ 技术栈

- **语言**：Python 3.12
- **GUI**：PySide6（Qt for Python）
- **图片处理**：Pillow
- **数据库**：SQLite（WAL 模式 + 外键约束）
- **托盘图标**：程序内 QPainter 绘制，无需外部资源文件

## 📄 License

MIT
