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
    image = pixmap.toImage()

    buffer = QBuffer()
    buffer.open(QIODevice.ReadWrite)
    image.save(buffer, "PNG")
    bytes_data = bytes(buffer.data())
    buffer.close()
    return bytes_data

def pil_to_bytes(pil_image: Image) -> bytes:
    image_bytes = b''
    with BytesIO() as output:
        pil_image.save(output, format='PNG')
        image_bytes = output.getvalue()
    return image_bytes

def hash_library(library_json: str):
    hash_obj = hashlib.sha256()
    hash_obj.update(library_json.encode())
    
    return hash_obj.hexdigest()
