from nodes.node_base import BaseNode
from nodes.widget import ColorLabel, DoubleArrowSpinBox, PlainTextEdit
from nodes.registry import registry_node

from utils.helpers import punct_mapping

import time


@registry_node("值", "输入")
class ValueNode(BaseNode):
    def __init__(self, parent=None):
        conf = {"title": "Value", "node_type": "input", "size": (200, 50), "zoom_limit": "H", "execution_priority": 0}
        super().__init__(conf, parent)

        self.output_value = self.add_output_socket("value", 'value')

        self.spin_box = DoubleArrowSpinBox("value")

        self.add_widget(self.spin_box)

        self.init()

    def logic(self):
        value = self.spin_box.value()

        self.set_output_val("value", value)

        super().logic()

    def get_widget_input(self):
        value = self.spin_box.value()

        return {"value": value}

    def set_widget_input(self, inputs):
        self.spin_box.set_value(inputs.get("value", 0))


@registry_node("字符串", "输入")
class StringNode(BaseNode):
    def __init__(self, parent=None):
        conf = {"title": "String", "node_type": "input", "size": (200, 100), "zoom_limit": "HV", "execution_priority": 0}
        super().__init__(conf, parent)

        self.data_out = self.add_output_socket("string", "string")

        self.text_edit = PlainTextEdit("string", text="hello,world")

        self.add_widget(self.text_edit)

        self.init()

    def logic(self):
        string = punct_mapping(self.text_edit.toPlainText())

        self.set_output_val("string",  string)

        super().logic()

    def get_widget_input(self):
        string = self.text_edit.toPlainText()

        return {"string": string}

    def set_widget_input(self, inputs):
        self.text_edit.setPlainText(inputs.get("string", ""))


@registry_node("颜色", "输入")
class ColorNode(BaseNode):
    def __init__(self, parent=None):
        conf = {"title": " Color", "node_type": "input", "size": (200, 100), "zoom_limit": "H", "execution_priority": 0}
        super().__init__(conf, parent)

        self.data_out = self.add_output_socket("color", "color")

        self.color_label = ColorLabel("color")

        self.add_widget(self.color_label)

        self.init()

    def logic(self):
        color = self.color_label.get_color()

        self.set_output_val("color", color)

        super().logic()

    def get_widget_input(self):
        color = self.color_label.get_color()

        return {"color": color}

    def set_widget_input(self, inputs):
        color = inputs.get("color", "#ffffff")
        self.color_label.set_color(color)


@registry_node("运行时长", "输入")
class ExecutionTimeNode(BaseNode):
    def __init__(self, parent=None):
        conf = {"title": "Execution Time", "node_type": "input", "size": (200, 0), "zoom_limit": "H", "execution_priority": 0}
        super().__init__(conf, parent)
        self.add_exec_socket(only_output=True)

        self.output_value = self.add_output_socket("seconds", 'value')

        self.init()

    def logic(self):
        seconds = int(time.time() - self.runner.run_start_time)

        self.set_output_val("seconds", seconds)

        super().logic()
