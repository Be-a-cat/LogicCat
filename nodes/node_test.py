from nodes.node_base import BaseNode
from nodes.registry import registry_node
from nodes.widget import DoubleArrowSpinBox
import time


@registry_node("等待", "测试")
class WaitNode(BaseNode):
    def __init__(self, parent=None):
        conf = {"title": "Wait", "node_type": "other", "size": (200, 0), "zoom_limit": "H"}
        super().__init__(conf, parent)

        self.add_input_socket("any", "any", True)
        self.add_output_socket("any", "any")

        self.spin_box = DoubleArrowSpinBox("time:s")
        self.add_widget(self.spin_box)

        self.init()

    def on_input_connected(self, socket):
        connected_socket = socket.edges[-1].start_socket
        output_socket = self.output_socket[-1]
        output_socket.update_socket(connected_socket.name, connected_socket.data_type)

        self.update_socket_positions()
        self.update()

    def on_input_disconnected(self, socket):
        output_socket = self.output_socket[-1]
        output_socket.update_socket("any", "any")

        self.update_socket_positions()
        self.update()

    def logic(self):
        input_data = self.get_input_val("any")
        wait_time = self.spin_box.value()
        self.inputs.update({"input": input_data, "wait_time": wait_time})

        if wait_time > 0:
            self.run_async_task(time.sleep, wait_time)
        self.set_output_val(self.output_socket[-1].name, input_data)

    def get_widget_input(self):
        wait_time = self.spin_box.value()

        return {"wait_time": wait_time}

    def set_widget_input(self, inputs):
        self.spin_box.set_value(inputs.get("wait_time", 0))
