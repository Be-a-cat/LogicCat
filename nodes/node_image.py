from PySide6.QtWidgets import QFileDialog

from nodes.node_base import BaseNode
from nodes.widget import PushButton, LineEdit, ImageShowBox
from nodes.registry import registry_node
from nodes.helpers import pil_to_pixmap, save_image_with_metadata

from utils.config_manager import global_config
from utils.buffer_pool import add_to_image_pool, get_from_image_pool

import os
from PIL import Image
from datetime import datetime


@registry_node("加载图像", "图像")
class ImageLoadNode(BaseNode):
    def __init__(self, parent=None):
        conf = {"title": "Image Load", "node_type": "image", "size": (200, 0), "zoom_limit": "HV", "execution_priority": 0}
        super().__init__(conf, parent)
        self.add_exec_socket(only_input=True)

        self.output_image = self.add_output_socket("image", "image")
        self.output_width = self.add_output_socket("width", "value")
        self.output_height = self.add_output_socket("height", "value")

        self.lineedit = LineEdit("Path")

        self.button = PushButton("upload", self.load_image)

        self.image_box = ImageShowBox("image")

        self.add_widget(self.lineedit)
        self.add_widget(self.button)
        self.add_widget(self.image_box)

        self.init()

        self.image = None
        self.image_path = ""
        self.image_width = 0
        self.image_height = 0

    def load_image(self):
        image_path, _ = QFileDialog.getOpenFileName(None, "选择图片", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if image_path:
            self.lineedit.setText(image_path)
            self.show_image(image_path)

    def show_image(self, image_path):
        if image_path:
            self.image = Image.open(image_path)
            self.image_box.set_image(self.image)

            pixmap = pil_to_pixmap(self.image)
            self.image_width, self.image_height = pixmap.width(), pixmap.height()

    def logic(self):
        if self.image and self.image_width and self.image_height:
            self.set_output_val("image", self.image)
            self.set_output_val("width", self.image_width)
            self.set_output_val("height", self.image_height)
        else:
            self.set_output_val("image", None)
            self.set_output_val("width", 0)
            self.set_output_val("height", 0)
        super().logic()

    def get_widget_input(self):
        image_path = self.lineedit.text()

        return {"image_path": image_path}

    def set_widget_input(self, inputs):
        self.lineedit.setText(inputs.get("image_path", ""))
        self.show_image(inputs.get("image_path", None))


@registry_node("显示图像", "图像")
class ImageShowNode(BaseNode):
    def __init__(self, parent=None):
        conf = {"title": "Image Show", "node_type": "image", "size": (200, 0), "zoom_limit": "HV", "is_terminator": True, "execution_priority": 0}
        super().__init__(conf, parent)
        self.add_exec_socket(only_input=True)

        self.add_input_socket("image", "image")

        self.image_box = ImageShowBox("image")

        self.add_widget(self.image_box)

        self.init()

        self.image, self.pixmap, self.image_width, self.image_height = None, None, None, None
        self.image_id = None

    def logic(self):
        image = self.get_input_val("image")
        image_id = add_to_image_pool(image)

        self.results.update({"image_id": image_id})

    def get_widget_input(self):
        image_id = self.image_id

        return {"image_id": image_id}

    def set_widget_input(self, inputs):
        self.image_id = inputs.get("image_id", None)
        self.image_box.set_image(get_from_image_pool(self.image_id))

    def post_execute(self, data):
        self.image_id = data["results"].get("image_id", None)
        self.image_box.set_image(get_from_image_pool(self.image_id))


@registry_node("保存图像", "图像")
class ImageSaveNode(BaseNode):
    def __init__(self, parent=None):
        conf = {"title": "Image Save", "node_type": "image", "size": (200, 0), "zoom_limit": "HV", "is_terminator": True, "execution_priority": 0}
        super().__init__(conf, parent)
        self.add_exec_socket(only_input=True)

        self.input_image = self.add_input_socket("image", "image")

        self.lineedit = LineEdit("Path")

        self.image_box = ImageShowBox("image")

        self.add_widget(self.lineedit)
        self.add_widget(self.image_box)

        self.init()

        self.image, self.pixmap, self.image_width, self.image_height = None, None, None, None
        self.image_path = None

    def save_image(self, pil_image, save_path="", save_name=""):
        if pil_image:
            save_path = save_path if save_path else global_config.get("paths", "dirs", "image_save")
            save_name = save_name if save_name else datetime.now().strftime("%Y%m%d%H%M%S")
            ext = ".png"
            self.image_path = os.path.join(save_path, save_name + ext)
            save_image_with_metadata(pil_image, self.image_path)
        return self.image_path

    def show_image(self, image_path):
        if image_path and os.path.exists(image_path):
            self.lineedit.setText(self.image_path)
            self.image = Image.open(image_path)

            self.image_box.set_image(self.image)

            self.pixmap = pil_to_pixmap(self.image)
            self.image_width, self.image_height = self.pixmap.width(), self.pixmap.height()

    def logic(self):
        image = self.get_input_val("image")
        image_path = self.save_image(image)
        self.results.update({"image_path": image_path})

        super().logic()

    def get_widget_input(self):
        image_path = self.image_path

        return {"image_path": image_path}

    def set_widget_input(self, inputs):
        self.image_path = inputs.get("image_path", None)
        self.show_image(self.image_path)

    def post_execute(self, data):
        self.image_path = data["results"].get("image_path", None)
        self.show_image(self.image_path)
