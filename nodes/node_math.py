from nodes.node_base import BaseNode
from nodes.widget import ComboBox, DoubleArrowSpinBox, LineEdit
from nodes.registry import registry_node

import operator


@registry_node("运算", "运算")
class MathNode(BaseNode):
    def __init__(self, parent=None):
        conf = {"title": "Math", "node_type": "math", "size": (200, 0), "zoom_limit": "H"}
        super().__init__(conf, parent)

        self.add_exec_socket()

        self.output_result = self.add_output_socket("result", 'value')

        self.combo_mode = ComboBox("mode")
        self.combo_mode.addItems(["Add(+)", "Sub(-)", "Mul(*)", "Div((/))"])

        self.spin_box_a = DoubleArrowSpinBox("A")
        self.spin_box_b = DoubleArrowSpinBox("B")

        self.add_widget(self.combo_mode)
        self.add_widget(self.spin_box_a, "value")
        self.add_widget(self.spin_box_b, "value")

        self.init()

    def logic(self):
        val_a = self.spin_box_a.value() if self.get_input_val(1) is None else self.get_input_val(1)
        val_b = self.spin_box_b.value() if self.get_input_val(2) is None else self.get_input_val(2)
        mode = self.combo_mode.value()
        self.inputs.update({"mode": mode, "A": val_a, "B": val_b})

        result = 0
        if mode == "Add(+)":
            result = val_a + val_b
        elif mode == "Sub(-)":
            result = val_a - val_b
        elif mode == "Mul(*)":
            result = val_a * val_b
        elif mode == "Div((/))":
            if val_b == 0:
                result = 0
            else:
                result = int(val_a / val_b)
        self.set_output_val("result", result)

        super().logic()

    def get_widget_input(self):
        mode = self.combo_mode.value()
        a = self.spin_box_a.value()
        b = self.spin_box_b.value()

        return {"mode": mode, "A": a, "B": b}

    def set_widget_input(self, inputs):
        self.combo_mode.setCurrentText(inputs.get('mode', "Add(+)"))
        self.spin_box_a.set_value(inputs.get("A", 0))
        self.spin_box_b.set_value(inputs.get("B", 0))


@registry_node("比较", "运算")
class CompareNode(BaseNode):
    def __init__(self, parent=None):
        conf = {"title": "Compare", "node_type": "math", "size": (200, 0), "zoom_limit": "H", "always_update": True}
        super().__init__(conf, parent)
        self.add_exec_socket()

        self.output_result = self.add_output_socket("bool", 'bool')

        self.combo_input_type = ComboBox("mode")
        self.combo_input_type.addItems(["value", "string"])
        self.combo_input_type.currentTextChanged.connect(self.switch_input_type)

        self.combo_op = ComboBox("op")
        self.combo_op.addItems(["小于", "小于或等于", "大于", "大于或等于", "等于", "不等于"])

        self.input_box_a = DoubleArrowSpinBox("A")
        self.input_box_b = DoubleArrowSpinBox("B")

        self.add_widget(self.combo_input_type)
        self.add_widget(self.combo_op)
        self.add_widget(self.input_box_a, "value")
        self.add_widget(self.input_box_b, "value")

        self.init()

    def switch_input_type(self, input_type):
        new_input_box_a, new_input_box_b = None, None
        if input_type == "value":
            new_input_box_a = DoubleArrowSpinBox("A")
            new_input_box_b = DoubleArrowSpinBox("B")

            self.combo_op.clear()
            self.combo_op.addItems(["小于", "小于或等于", "大于", "大于或等于", "等于", "不等于"])

        elif input_type == "string":
            new_input_box_a = LineEdit("A")
            new_input_box_b = LineEdit("B")

            self.combo_op.clear()
            self.combo_op.addItems(["等于", "不等于"])

        self.replace_widget(self.input_box_a, new_input_box_a, input_type)
        self.replace_widget(self.input_box_b, new_input_box_b, input_type)
        self.input_box_a = new_input_box_a
        self.input_box_b = new_input_box_b

        self.update_node()

    @staticmethod
    def compare(a, op, b):
        ops = {
            "小于": operator.lt,
            "小于或等于": operator.le,
            "大于": operator.gt,
            "大于或等于": operator.ge,
            "等于": operator.eq,
            "不等于": operator.ne
        }
        return ops[op](a, b)

    def logic(self):
        op = self.combo_op.value()
        a = self.input_box_a.value() if self.get_input_val(2) is None else self.get_input_val(2)
        b = self.input_box_b.value() if self.get_input_val(3) is None else self.get_input_val(3)

        _bool = self.run_async_task(self.compare, a, op, b)
        self.set_output_val("bool", _bool)

    def get_widget_input(self):
        input_type = self.combo_input_type.value()
        op = self.combo_op.value()
        a = self.input_box_a.value()
        b = self.input_box_b.value()

        return {"input_type": input_type, "op": op, "A": a, "B": b}

    def set_widget_input(self, inputs):
        self.combo_input_type.setCurrentText(inputs.get('input_type', "value"))
        self.combo_op.setCurrentText(inputs.get("op", "等于"))
        self.input_box_a.set_value(inputs.get("A"))
        self.input_box_b.set_value(inputs.get("B"))
