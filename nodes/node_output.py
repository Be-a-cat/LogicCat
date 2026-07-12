from nodes.node_base import BaseNode
from nodes.registry import registry_node
from nodes.conf import NODE_TITLE_HEIGHT, SOCKET_RADIUS


@registry_node("输出", "输出")
class OutputNode(BaseNode):
    def __init__(self, parent=None):
        conf = {"title": "Output", "node_type": "other", "size": None, "zoom_limit": False, "is_terminator": True, "execution_priority": 0}
        super().__init__(conf, parent)

        self.input_out = self.add_input_socket("", 'any')

        self.init()

    def on_input_connected(self, socket):
        last_input_socket = self.input_socket[-1]
        connected_socket = socket.edges[-1].start_socket
        if socket == last_input_socket:
            last_input_socket.update_socket(connected_socket.name, connected_socket.data_type)
            self.add_input_socket("", "any")
            if self.is_collapsed:
                new_height = max(30, len(self.input_socket) * 14 + SOCKET_RADIUS)
                self.height = new_height
                self.update_node()
            else:
                new_height = NODE_TITLE_HEIGHT + (len(self.input_socket) + 1) * 20
                if new_height >= self.height:
                    self.height = new_height
                    self.update_node()
            self.expanded_height = NODE_TITLE_HEIGHT + (len(self.input_socket) + 1) * 20

        else:
            socket.update_socket(connected_socket.name, connected_socket.data_type)
            self.update_node()

        super().on_input_connected(socket)

    def on_input_disconnected(self, socket):
        self.delete_socket(socket)
        if self.is_collapsed:
            new_height = max(30, len(self.input_socket) * 14 + SOCKET_RADIUS)
            self.height = new_height
            self.update_node()
        else:
            new_height = NODE_TITLE_HEIGHT + (len(self.input_socket) + 1) * 20
            if new_height < self.minimum_height:
                self.height = self.minimum_height
            else:
                self.height = new_height
                self.update_node()
            self.expanded_height = NODE_TITLE_HEIGHT + (len(self.input_socket) + 1) * 20

        super().on_input_connected(socket)

    def logic(self):
        for socket in self.input_socket:
            if socket.edges:
                name = socket.name
                self.results[name] = self.get_input_val(name)
        super().logic()

    def get_widget_input(self):
        input_count = len(self.input_socket)

        return {"input_count": input_count}

    def set_widget_input(self, inputs):
        input_count = inputs.get("input_count", 1)
        for i in range(input_count-1):
            self.add_input_socket("", "any")

        new_height = NODE_TITLE_HEIGHT + (len(self.input_socket) + 1) * 20
        if new_height >= self.height:
            self.height = new_height
            self.update_node()
