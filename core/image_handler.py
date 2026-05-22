"""
图片处理：保存剪贴板图片 + 生成缩略图
存储目录：%LOCALAPPDATA%/ClipboardCache/
"""
import os
import uuid
from pathlib import Path
from PySide6.QtGui import QImage
from PIL import Image


# 图片缓存目录
CACHE_DIR = Path(os.environ["LOCALAPPDATA"]) / "ClipboardCache"

# 缩略图尺寸（像素）
THUMB_SIZE = 120

# 单张图片最大体积（字节）
MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20MB


def _qimage_to_pil(qimage: QImage) -> Image.Image:
    """
    将 Qt 的 QImage 转换为 Pillow 的 Image 对象
    转换链路：QImage → RGBA8888 格式 → 原始字节 → Pillow Image
    这是最可靠的内存内转换方式，不需要写入磁盘中转
    """
    # 统一转换到 RGBA8888 格式（每种颜色 8 位共 4 通道）
    qimage = qimage.convertToFormat(QImage.Format_RGBA8888)
    width = qimage.width()
    height = qimage.height()
    ptr = qimage.bits()  # 获取图像数据的内存指针

    # 从原始字节构建 Pillow Image
    pil_image = Image.frombytes("RGBA", (width, height), ptr.tobytes())
    return pil_image


def save_clipboard_image(qimage: QImage) -> dict:
    """
    保存剪贴板图片到磁盘，生成缩略图
    参数：qimage — Qt 从剪贴板获取的 QImage 对象
    返回：{"image_path": 原图路径, "thumbnail_path": 缩略图路径, "width": 宽, "height": 高}
    """
    # 确保缓存目录存在
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # 生成唯一文件名（12位十六进制足够避免冲突）
    file_id = uuid.uuid4().hex[:12]

    # 步骤1：QImage 转 Pillow Image
    pil_image = _qimage_to_pil(qimage)
    orig_width = pil_image.width
    orig_height = pil_image.height

    # 步骤2：保存原图为 PNG（无损，保留截图质量）
    original_path = CACHE_DIR / f"{file_id}.png"
    pil_image.save(str(original_path), "PNG")

    # 步骤3：生成 120x120 缩略图（居中裁剪填充）
    thumb_path = CACHE_DIR / f"{file_id}_thumb.jpg"
    thumb = pil_image.copy()
    # 按比例缩放，长边不超过 120
    thumb.thumbnail((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS)
    # 在 120x120 画布上居中放置（保持所有缩略图统一尺寸）
    canvas = Image.new("RGBA", (THUMB_SIZE, THUMB_SIZE), (0, 0, 0, 0))
    offset_x = (THUMB_SIZE - thumb.width) // 2
    offset_y = (THUMB_SIZE - thumb.height) // 2
    canvas.paste(thumb, (offset_x, offset_y))
    # JPEG 不支持透明通道，转 RGB
    canvas = canvas.convert("RGB")
    canvas.save(str(thumb_path), "JPEG", quality=85)

    return {
        "image_path": str(original_path),
        "thumbnail_path": str(thumb_path),
        "width": orig_width,
        "height": orig_height,
    }


def delete_image_files(image_path: str, thumbnail_path: str):
    """删除图片文件（用于清理记录时同步删除磁盘文件）"""
    try:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
        if thumbnail_path and os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
    except OSError:
        pass  # 文件已被删除或无权限，忽略
