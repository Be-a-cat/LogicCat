from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit
from app.base_widgets import MultiLineInputBox, PathSelectionBox, SubWindow

from nodes.registry import register_plugin_config

from custom_nodes.ComfyUI.core import comfy_manager, ComfyUIThread
from utils.config_manager import global_config


DEFAULT_CONFIG = {
    "server_url": "http://127.0.0.1:8188",
    "ComfyUI_path": "",
    "models_path": ""
}


@register_plugin_config("ComfyUI", "ComfyUI")
class ComfyUIConfigPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        self.current_url = global_config.get_plugin_config("ComfyUI", "server_url", DEFAULT_CONFIG["server_url"])
        self.current_path = global_config.get_plugin_config("ComfyUI", "ComfyUI_path", DEFAULT_CONFIG["ComfyUI_path"])
        self.current_models_path = global_config.get_plugin_config("ComfyUI", "models_path", DEFAULT_CONFIG["models_path"])

        self.input_box_url = MultiLineInputBox(label_text="server url", height=75)
        self.input_box_url.set_text(self.current_url)

        self.input_box_path = PathSelectionBox(label_text="ComfyUI path", height=100, direction="V")
        self.input_box_path.set_text(self.current_path)

        self.input_box_models_path = PathSelectionBox(label_text="models path", height=100, direction="V")
        self.input_box_models_path.set_text(self.current_models_path)

        self.btn_start_comfy = QPushButton("启动ComfyUI")
        self.btn_start_comfy.clicked.connect(self.start_server)

        self.btn_stop_comfy = QPushButton("停止ComfyUI")
        self.btn_stop_comfy.clicked.connect(self.stop_server)

        self.btn_open_terminal = QPushButton("打开终端")
        self.btn_open_terminal.clicked.connect(self.on_terminal)

        self.btn_save = QPushButton("保存设置")
        self.btn_save.clicked.connect(self.save_config)

        self.label_status = QLabel()
        self.label_status.setStyleSheet("background: #ff0000;")

        layout.addWidget(self.input_box_url)
        layout.addWidget(self.input_box_path)
        layout.addWidget(self.input_box_models_path)
        layout.addStretch()
        layout.addWidget(self.btn_start_comfy)
        layout.addWidget(self.btn_stop_comfy)
        layout.addWidget(self.btn_open_terminal)
        layout.addWidget(self.btn_save)

        self.comfy_terminal = SubWindow()
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: Consolas;")
        self.comfy_terminal.add_widget(self.text_edit)

        self.comfy_manager = comfy_manager
        self.comfy_manager.set_server_url(self.current_url)

        self.comfy_thread = None

    def save_config(self):
        global_config.set_plugin_config("ComfyUI", "server_url", self.input_box_url.get_text())
        global_config.set_plugin_config("ComfyUI", "ComfyUI_path", self.input_box_path.get_text())
        global_config.set_plugin_config("ComfyUI", "models_path", self.input_box_models_path.get_text())
        self.comfy_manager.set_server_url(self.input_box_url.get_text())

    def start_server(self):
        if self.comfy_thread is None or not self.comfy_thread.isRunning():
            self.comfy_thread = ComfyUIThread(self.current_path)
            self.comfy_thread.log_signal.connect(self.update_log)
            self.comfy_thread.start()

            self.label_status.setStyleSheet("background: #00ff00;")

            self.comfy_terminal.show()

        else:
            self.comfy_terminal.hide()

    def stop_server(self):
        if self.comfy_thread and self.comfy_thread.isRunning():
            self.comfy_thread.stop()

            self.label_status.setStyleSheet("background: #ff0000;")

            self.comfy_terminal.hide()

    def on_terminal(self):
        self.comfy_terminal.show()

    def update_log(self, text):
        self.text_edit.append(text)
        scrollbar = self.text_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        pass
