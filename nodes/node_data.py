from nodes.node_base import BaseNode
from nodes.registry import registry_node
from nodes.widget import ComboBox, LineEdit


@registry_node("放入存储桶", "数据")
class PutInfoStorageBucketNode(BaseNode):
    def __init__(self, parent=None):
        conf = {"title": "放入存储桶", "node_type": "other", "size": None, "zoom_limit": "H", "is_terminator": True, "execution_priority": 0}
        super().__init__(conf, parent)
        self.add_exec_socket(only_input=True)

        self.input_data = self.add_input_socket("data", data_type="value")

        self.combo_input_type = ComboBox("type")
        types = ["value", "string", "image"]
        self.combo_input_type.addItems(types)
        self.combo_input_type.currentTextChanged.connect(self.switch_input_type)

        self.text_edit_name = LineEdit("name")

        self.add_widget(self.combo_input_type)
        self.add_widget(self.text_edit_name)

        self.init()

    def switch_input_type(self, data_type):
        self.input_data.update_socket("data", data_type=data_type)

    def logic(self):
        pass

    def get_widget_input(self):
        input_type = self.combo_input_type.value()
        name = self.text_edit_name.value()

        return {"input_type": input_type, "name": name}

    def set_widget_input(self, inputs):
        self.combo_input_type.setCurrentText(inputs.get("input_type", "value"))
        self.text_edit_name.setText(inputs.get("name", ""))

        self.switch_input_type(self.combo_input_type.value())


@registry_node("存储桶", "数据")
class StorageBucketNode(BaseNode):
    def __init__(self, parent=None):
        conf = {"title": "存储桶", "node_type": "other", "size": None, "zoom_limit": "H", "execution_priority": 20}
        super().__init__(conf, parent)
        self.add_exec_socket(only_output=True)

        self.output_data = self.add_output_socket("data", data_type="value")

        self.combo_data_type = ComboBox("type")
        types = ["value", "string", "image"]
        self.combo_data_type.addItems(types)
        self.combo_data_type.currentTextChanged.connect(self.switch_data_type)

        self.text_edit_name = LineEdit("name")

        self.add_widget(self.combo_data_type)
        self.add_widget(self.text_edit_name)

        self.init()

    def switch_data_type(self, data_type):
        self.output_data.update_socket("data", data_type=data_type)

    def logic(self):
        pass

    def get_widget_input(self):
        data_type = self.combo_data_type.value()
        name = self.text_edit_name.value()

        return {"data_type": data_type, "name": name}

    def set_widget_input(self, inputs):
        self.combo_data_type.setCurrentText(inputs.get("data_type", "value"))
        self.text_edit_name.setText(inputs.get("name", ""))

        self.switch_data_type(self.combo_input_type.value())
