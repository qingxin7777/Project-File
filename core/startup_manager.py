"""
开机自启管理
通过 Windows 启动文件夹中的 VBS 脚本实现开机自动运行
"""
import os
import sys
from pathlib import Path


# 启动文件夹路径（用户级）
STARTUP_FOLDER = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"

# 启动脚本名称
STARTUP_SCRIPT = "ClipboardManager.vbs"


def is_enabled() -> bool:
    """检查是否已设置开机自启"""
    script_path = STARTUP_FOLDER / STARTUP_SCRIPT
    return script_path.exists()


def enable():
    """启用开机自启：在启动文件夹创建 VBS 启动脚本"""
    STARTUP_FOLDER.mkdir(parents=True, exist_ok=True)
    script_path = STARTUP_FOLDER / STARTUP_SCRIPT

    # 找到 pythonw.exe（无控制台窗口），找不到则用 python.exe
    python_dir = Path(sys.executable).parent
    pythonw = python_dir / "pythonw.exe"
    python_exe = pythonw if pythonw.exists() else python_dir / "python.exe"

    # 项目路径
    project_dir = Path(__file__).parent.parent.resolve()
    main_script = project_dir / "main.py"

    # VBS 脚本内容：静默运行，不显示控制台窗口
    vbs_content = (
        f'Set WshShell = CreateObject("WScript.Shell")\n'
        f'WshShell.CurrentDirectory = "{project_dir}"\n'
        f'WshShell.Run """{python_exe}"" ""{main_script}""", 0, False\n'
    )

    try:
        script_path.write_text(vbs_content, encoding="utf-8")
        return True
    except Exception:
        return False


def disable():
    """禁用开机自启：删除启动文件夹中的脚本"""
    script_path = STARTUP_FOLDER / STARTUP_SCRIPT
    try:
        if script_path.exists():
            script_path.unlink()
        return True
    except Exception:
        return False


def toggle() -> bool:
    """切换开机自启状态，返回切换后的新状态"""
    if is_enabled():
        disable()
        return False
    else:
        enable()
        return True
