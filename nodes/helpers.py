from PySide6.QtGui import QPixmap, QImage, QColor
from PySide6.QtCore import QBuffer, QByteArray, QIODevice

import json
import base64

from PIL import Image
from PIL.PngImagePlugin import PngInfo

from io import BytesIO


def add_metadata_to_pil(pil_image, metadata_dict):
    pil_image._metadata = metadata_dict
    return pil_image


def save_image_with_metadata(pil_image, filepath):
    metadata_dict = getattr(pil_image, "_metadata", {})

    json_str = json.dumps(metadata_dict, ensure_ascii=False)

    metadata = PngInfo()
    metadata.add_text("metadata", json_str)

    pil_image.save(filepath, "PNG", pnginfo=metadata)


def read_image_with_metadata(filepath):
    try:
        with Image.open(filepath) as img:
            metadata = json.loads(img.text.get("metadata", "{}"))
            return img, metadata
    except Exception as e:
        print(f"读取元数据失败！:{e}")
        return img, {}


def pixmap_to_base64(pixmap: QPixmap, format="PNG") -> str:
    if pixmap.isNull():
        return ""

    image = pixmap.toImage()
    byte_array = QByteArray()
    buffer = QBuffer(byte_array)
    buffer.open(QIODevice.WriteOnly)
    image.save(buffer, format)

    return str(base64.b64encode(byte_array.data()), 'utf-8')


def base64_to_pixmap(base64_str: str) -> QPixmap:
    if not base64_str:
        return QPixmap()

    byte_data = base64.b64decode(base64_str)
    image = QImage()
    image.loadFromData(byte_data)

    return QPixmap.fromImage(image)


def pil_to_pixmap(pil_image):
    if pil_image is None:
        return QPixmap()
    if pil_image.mode != "RGBA":
        pil_image = pil_image.convert("RGBA")
    data = pil_image.tobytes("raw", "RGBA")
    qim = QImage(data, pil_image.width, pil_image.height, QImage.Format_RGBA8888)
    return QPixmap.fromImage(qim)


def pil_to_base64(pil_image):
    if pil_image is None:
        return ""
    buffered = BytesIO()
    pil_image.save(buffered, format="PNG")
    return str(base64.b64encode(buffered.getvalue()), 'utf-8')


def base64_to_pil(base64_str):
    if not base64_str:
        return None
    image_data = base64.b64decode(base64_str)
    return Image.open(BytesIO(image_data))


def color_to_hex(color: QColor) -> str:
    if not color.isValid():
        return "#000000"
    return color.name(QColor.HexArgb)


def hex_to_color(hex_str: str) -> QColor:
    return QColor(hex_str)
