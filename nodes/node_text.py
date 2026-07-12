from nodes.node_base import BaseNode
from nodes.registry import registry_node
from nodes.widget import PlainTextEdit, MultiLineTextEdit, DoubleArrowComBoBox


@registry_node("值转为字符串", "文本")
class ValueToStringNode(BaseNode):
    def __init__(self, parent=None):
        conf = {"title": "Value To String", "node_type": "string", "size": (200, 0), "zoom_limit": "H"}
        super().__init__(conf, parent)
        self.add_exec_socket()

        self.data_in = self.add_input_socket("value", 'value')
        self.data_out = self.add_output_socket("string", "string")

        self.init()

    def logic(self):
        value = self.get_input_val('value')
        self.inputs.update({"value": value})

        out_data = str(value)
        self.set_output_val("string", out_data)

        super().logic()


@registry_node("合并字符串", "文本")
class StringConcatenateNode(BaseNode):
    def __init__(self, parent=None):
        conf = {"title": "String Concatenate", "node_type": "string", "size": (200, 0), "zoom_limit": "HV"}
        super().__init__(conf, parent)
        self.add_exec_socket()

        self.output_string = self.add_output_socket("string", "string")
        self.output_string_1 = self.add_output_socket("string_1", "string")
        self.output_string_2 = self.add_output_socket("string_2", "string")

        self.string_1 = MultiLineTextEdit("string_1")
        self.string_1.resize(300, 50)
        self.string_2 = MultiLineTextEdit("string_2")
        self.string_2.resize(300, 50)

        self.add_widget(self.string_1, "string")
        self.add_widget(self.string_2, "string")

        self.init()

    @staticmethod
    def join_strings(string_list):
        if string_list:
            return ",".join(string_list)

    def logic(self):
        string_1 = self.string_1.value() if self.get_input_val(0) is None else self.get_input_val(0)
        string_2 = self.string_2.value() if self.get_input_val(1) is None else self.get_input_val(1)
        strings = [string_1, string_2]

        string = self.run_async_task(self.join_strings, strings)

        self.set_output_val("string", string)
        self.set_output_val("string_1", string_1)
        self.set_output_val("string_2", string_2)

        super().logic()

    def get_widget_input(self):
        string_1 = self.string_1.value()
        string_2 = self.string_2.value()

        return {"string_1": string_1, "string_2": string_2}

    def set_widget_input(self, inputs):
        self.string_1.set_text(inputs.get("string_1", ""))
        self.string_2.set_text(inputs.get("string_2", ""))


@registry_node("拼接字符串", "文本")
class StringJoinNode(BaseNode):
    def __init__(self, parent=None):
        conf = {"title": "String Join", "node_type": "string", "size": (200, 0), "zoom_limit": "H"}
        super().__init__(conf, parent)
        self.add_exec_socket()

        self.input_string_1 = self.add_input_socket("string_1", "string")
        self.input_string_2 = self.add_input_socket("string_2", "string")
        self.input_string_3 = self.add_input_socket("string_3", "string")
        self.input_string_4 = self.add_input_socket("string_4", "string")

        self.output_string = self.add_output_socket("string", "string")

        self.conbo_delimiter = DoubleArrowComBoBox("delimiter")
        delimiters = [",", ".", ";", r"\n"]
        self.conbo_delimiter.add_items(delimiters)

        self.add_widget(self.conbo_delimiter)

        self.init()

    @staticmethod
    def join_strings(string_list, delimiter):
        if string_list:
            print(string_list, delimiter)
            return f"{delimiter}".join(string_list)

    def logic(self):
        string_1 = self.get_input_val("string_1")
        string_2 = self.get_input_val("string_2")
        string_3 = self.get_input_val("string_3")
        string_4 = self.get_input_val("string_4")
        strings = [string_1, string_2, string_3, string_4]
        strings = [string for string in strings if string]
        print(strings)

        delimiter = self.conbo_delimiter.value()
        print(delimiter)

        string = self.run_async_task(self.join_strings, strings, delimiter)

        self.set_output_val("string", string)

        super().logic()

    def get_widget_input(self):
        delimiter = self.conbo_delimiter.value()

        return {"delimiter": delimiter}

    def set_widget_input(self, inputs):
        self.conbo_delimiter.set_current_text(inputs.get("delimiter", ","))


@registry_node("显示文本", "文本")
class TextShowNode(BaseNode):
    def __init__(self, parent=None):
        conf = {"title": "Text Show", "node_type": "string", "size": (300, 150), "zoom_limit": "HV", "is_terminator": True, "execution_priority": 0}
        super().__init__(conf, parent)
        self.add_exec_socket(only_input=True)

        self.input_text = self.add_input_socket("text", "string")

        self.text_box = PlainTextEdit("text")

        self.add_widget(self.text_box)

        self.init()

        self.text = ""

    def logic(self):
        text = self.get_input_val("text")

        self.results.update({"text": text})

        super().logic()

    def get_widget_input(self):
        text = self.text

        return {"text": text}

    def set_widget_input(self, inputs):
        self.text = inputs.get("text", "")
        self.text_box.setPlainText(self.text)

    def post_execute(self, data):
        self.text = data["results"].get("text", "")
        self.text_box.setPlainText(self.text)
