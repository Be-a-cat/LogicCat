import uuid
from typing import Optional
from PIL import Image
GLOBAL_DATA_POOL = {}
GLOBAL_IMAGE_POOL = {}


def add_to_data_pool(name, data):
    GLOBAL_DATA_POOL[name] = data


def get_from_data_pool(name):
    data = GLOBAL_DATA_POOL.get(name, None)
    return data


def add_to_image_pool(pil_image: Image.Image) -> Optional[str]:
    if pil_image is None:
        return
    image_id = f"img_{uuid.uuid4().hex[:8]}"
    GLOBAL_IMAGE_POOL[image_id] = pil_image
    return image_id


def get_from_image_pool(image_id: str) -> Optional[Image.Image]:
    if image_id and image_id in GLOBAL_IMAGE_POOL:
        return GLOBAL_IMAGE_POOL[image_id]
    return None
