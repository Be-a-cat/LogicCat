from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit
from app.base_widgets import MultiLineInputBox, PathSelectionBox, SubWindow

from nodes.registry import register_plugin_config

from utils.config_manager import global_config


DEFAULT_CONFIG = {
    "models_path": ""
}


@register_plugin_config("SD", "SD")
class StableDiffusionConfigPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        self.current_models_path = global_config.get_plugin_config("Stable_Diffusion", "models_path", DEFAULT_CONFIG["models_path"])

        self.input_box_models_path = PathSelectionBox(label_text="models path", height=100, direction="V")
        self.input_box_models_path.set_text(self.current_models_path)

        self.btn_save = QPushButton("保存设置")
        self.btn_save.clicked.connect(self.save_config)

        layout.addWidget(self.input_box_models_path)
        layout.addStretch()
        layout.addWidget(self.btn_save)

    def save_config(self):
        global_config.set_plugin_config("Stable_Diffusion", "models_path", self.input_box_models_path.get_text())
