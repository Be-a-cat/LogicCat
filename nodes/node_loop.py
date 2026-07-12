from nodes.node_base import BaseNode
from nodes.registry import registry_node


@registry_node("循环开始", "循环", visible=False)
class LoopStartNode(BaseNode):
    def __init__(self, parent=None):
        conf = {"title": "Loop Start", "node_type": "other", "size": (200, 0), "zoom_limit": "H"}
        super().__init__(conf, parent)
        self.add_exec_socket(only_output=True, is_auxiliary=False)

        self.add_input_socket("data", "any")

        self.add_output_socket("data", "any")

        self.init()

        self.first_run = True

    @staticmethod
    def get_loop_nodes(start_node):
        loop_nodes = []
        current_node = start_node
        while current_node:
            loop_nodes.append(current_node)
            if current_node.output_socket and current_node.output_socket[0].is_exec and current_node.output_socket[0].edges:
                next_node = current_node.output_socket[0].edges[0].end_socket.parentItem()
                current_node = next_node
            else:
                current_node = None
        return loop_nodes

    def logic(self):
        if self.first_run:
            data = self.get_input_val("data")
            self.first_run = False
        else:
            data = self.output_data.get(1, None)
            print(data)
        self.set_output_val("data", data)


@registry_node("循环结束", "循环", visible=False)
class LoopEndNode(BaseNode):
    def __init__(self, parent=None):
        conf = {"title": "Loop End", "node_type": "other", "size": (200, 0), "zoom_limit": "H", "is_terminator": True, "execution_priority": 20, "always_update": True}
        super().__init__(conf, parent)
        self.add_exec_socket(only_input=True, is_auxiliary=False)

        self.add_input_socket("bool", "bool")
        self.add_input_socket("data", "any")

        self.add_output_socket("data", "any")

        self.init()

    @staticmethod
    def get_loop_nodes(start_node):
        loop_nodes = set()
        next_nodes = set()
        visited = set()
        current_node = start_node
        while current_node:
            loop_nodes.add(current_node)
            all_edge = []
            if current_node.input_socket and current_node.input_socket[0].is_exec:
                all_edge += current_node.input_socket[0].edges
            if current_node.output_socket and current_node.output_socket[0].is_exec:
                all_edge += current_node.output_socket[0].edges
            for edge in all_edge:
                if edge not in visited:
                    visited.add(edge)
                    for node in [edge.start_socket.parentItem(), edge.end_socket.parentItem()]:
                        if node not in loop_nodes:
                            next_nodes.add(node)

            current_node = next_nodes.pop() if next_nodes else None

        loop_nodes_idx = [node.idx for node in loop_nodes]
        print(loop_nodes_idx)

        in_degree = {node: 0 for node in loop_nodes}
        downstream = {node: [] for node in loop_nodes}
        for node in loop_nodes:
            for socket in node.input_socket[1:] + list(node.widget_socket.values()):
                if socket and socket.edges:
                    upstream_node = socket.edges[0].start_socket.parentItem()
                    if upstream_node in loop_nodes:
                        downstream[upstream_node].append(node)
                        in_degree[node] += 1

        ready_queue = [node for node in loop_nodes if in_degree[node] == 0]
        sorted_nodes = []

        while ready_queue:
            current_node = ready_queue.pop(0)
            sorted_nodes.append(current_node)

            for downstream_node in downstream[current_node]:
                in_degree[downstream_node] -= 1

                if in_degree[downstream_node] == 0:
                    ready_queue.append(downstream_node)

            ready_queue.sort(key=lambda node: node.execution_priority)

        loop_nodes_idx = [node.idx for node in sorted_nodes]

        return loop_nodes_idx

    def logic(self):
        is_loop = self.get_input_val("bool")
        print(is_loop)
        if is_loop:
            loop_nodes = self.run_async_task(self.get_loop_nodes, self)
            print(loop_nodes)

            self.runner.is_looping = True
            if self.runner.execution_queue:
                self.runner.interrupted_nodes.append(self.runner.execution_queue)
            self.runner.execution_queue = loop_nodes
            print(self.runner.interrupted_nodes)
        else:
            self.runner.is_looping = False

        data = self.get_input_val("data")
        self.set_output_val("data", data)

        loop_start_node_idx = self.symbiont_nodes[0]
        loop_start_node = self.runner.virtual_nodes.get(loop_start_node_idx)
        loop_start_node.output_data[1] = data


@registry_node("循环", "循环")
class LoopNode:
    pass
