from nodes.node_base import BaseNode
from nodes.registry import registry_node


@registry_node("切换", "条件")
class SwitchNode(BaseNode):
    def __init__(self, parent=None):
        conf = {"title": "Switch", "node_type": "conditional", "size": (200, 0), "zoom_limit": "H", "always_update": True}
        super().__init__(conf, parent)
        self.add_exec_socket()

        self.add_input_socket("bool", "bool")

        self.add_input_socket("Ture", "any")
        self.add_input_socket("False", "any")

        self.add_output_socket("result", "any")

        self.init()
