import hashlib
from PIL import Image
from io import BytesIO
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QBuffer, QIODevice

import json
import base64

class BytesEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return base64.b64encode(obj).decode('utf-8')
        return super().default(obj)

def base64_to_bytes(obj: str) -> bytes:
    if isinstance(obj, str):
        try:
            return base64.b64decode(obj.encode('utf-8'))
        except (TypeError, ValueError):
            pass
    return obj

def bytes_to_pixmap(image_data: bytes) -> QPixmap:
    image = QImage.fromData(image_data)
    pixmap = QPixmap.fromImage(image)
    
    return pixmap

def pixmap_to_bytes(pixmap: QPixmap) -> bytes:
    if pixmap.isNull():
        return b''
    image = pixmap.toImage()

    buffer = QBuffer()
    buffer.open(QIODevice.ReadWrite)
    image.save(buffer, "BMP")
    bytes_data = bytes(buffer.data())
    buffer.close()
    return bytes_data

def pil_to_bytes(pil_image: Image, format='PNG', compress_level=1) -> bytes:
    image_bytes = b''
    with BytesIO() as output:
        if format == 'PNG':
            pil_image.save(output, format=format, compress_level=compress_level)
        else:
            pil_image.save(output, format=format)
        image_bytes = output.getvalue()
    return image_bytes

def pil_to_pixmap(pil_image: Image) -> QPixmap:
    if pil_image.mode == 'RGBA':
        qimage = QImage(pil_image.tobytes(), pil_image.width, pil_image.height, QImage.Format_RGBA8888)
    else:
        rgb_image = pil_image.convert('RGB')
        qimage = QImage(rgb_image.tobytes(), rgb_image.width, rgb_image.height, QImage.Format_RGB888)
    return QPixmap.fromImage(qimage)

def hash_library(library_json: str):
    hash_obj = hashlib.sha256()
    hash_obj.update(library_json.encode())
    
    return hash_obj.hexdigest()
