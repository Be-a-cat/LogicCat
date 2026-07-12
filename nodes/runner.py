from PySide6.QtCore import QObject, Signal, QTimer
from nodes.registry import NODE_REGISTRY
from nodes.socket import Edge

import time
from collections import deque


class GraphRunner(QObject):
    node_status_changed = Signal(str, str, object, float)
    node_log_message = Signal(str)
    queue_completed = Signal()
    data_delivery = Signal(object, object)

    def __init__(self):
        super().__init__()
        self.virtual_nodes = {}
        self.virtual_edges = []

        self.execution_queue = []
        self.virtual_cache = {}
        self.interrupted_nodes = []

        self.is_running = False
        self.is_looping = False
        self.is_interrupt = False

        self.run_start_time = 0
        self.run_end_time = 0
        self.run_time = 0

    def run(self, virtual_data):
        print("正在构建虚拟工作流···")
        self.cleanup_virtual()

        self.virtual_nodes = {}
        self.virtual_edges = []

        for node_idx, node_data in virtual_data.items():
            class_name = node_data["type"]
            if class_name in NODE_REGISTRY:
                cls = NODE_REGISTRY[class_name]["class"]
                node = cls()
                node.deserialize(node_data)

                node.runner = self

                node.original_set_status = node.set_state
                node.set_state = lambda s, n=node: self.intercept_status(n, s)

                node.log_generated.connect(self.emit_log)

                self.virtual_nodes[node_idx] = node
                self.virtual_edges.extend(node_data["edges"])

        in_degree = {idx: 0 for idx in self.virtual_nodes}
        directed_adj = {idx: [] for idx in self.virtual_nodes}
        undirected_adj = {idx: [] for idx in self.virtual_nodes}

        for edge_data in self.virtual_edges:
            try:
                u_idx = edge_data["start_node"]
                v_idx = edge_data["end_node"]

                directed_adj[u_idx].append(v_idx)
                in_degree[v_idx] += 1

                undirected_adj[u_idx].append(v_idx)
                undirected_adj[v_idx].append(u_idx)

                start_node = self.virtual_nodes[u_idx]
                start_socket = start_node.output_socket[int(edge_data['start_socket'])]
                end_node = self.virtual_nodes[v_idx]
                if edge_data['end_socket_type'] == "input_socket":
                    end_socket = end_node.input_socket[int(edge_data['end_socket'])]
                else:
                    end_socket = list(end_node.widget_socket.values())[int(edge_data['end_socket'])]

                edge = Edge(start_socket, end_socket)
                start_socket.add_edge(edge)
                end_socket.add_edge(edge)
            except Exception as e:
                print(f"虚拟节点连接失败：{e}")

        visited = set()
        islands = []

        for idx in self.virtual_nodes:
            if idx not in visited and not getattr(self.virtual_nodes[idx], "is_terminator"):
                island = []
                queue = deque([idx])
                visited.add(idx)

                while queue:
                    curr = queue.popleft()
                    island.append(curr)
                    for neighbor in undirected_adj[curr]:
                        if neighbor not in visited and not getattr(self.virtual_nodes[neighbor], "is_terminator"):
                            visited.add(neighbor)
                            queue.append(neighbor)
                        if getattr(self.virtual_nodes[neighbor], "is_terminator"):
                            island.append(neighbor)
                islands.append(island)

        islands.sort(key=lambda isl: min(self.virtual_nodes[i].y() for i in isl))

        print(islands)

        self.execution_queue = []
        preparation = []
        for island in islands:
            for idx in [idx for idx in island if in_degree[idx] == 0]:
                preparation.append(idx)
                island.remove(idx)
                for neighbor_node in directed_adj[idx]:
                    in_degree[neighbor_node] -= 1

        self.execution_queue.append(preparation)

        for island in islands:
            ready_queue = [idx for idx in island if in_degree[idx] == 0]
            island_execution = []

            while ready_queue:
                current_node_idx = ready_queue.pop(0)
                island_execution.append(current_node_idx)

                for neighbor_node in directed_adj[current_node_idx]:
                    in_degree[neighbor_node] -= 1

                    if in_degree[neighbor_node] == 0:
                        ready_queue.append(neighbor_node)

                ready_queue.sort(key=lambda idx: self.virtual_nodes[idx].execution_priority)

            self.execution_queue.append(island_execution)
        self.execution_queue = [idx for queue in self.execution_queue for idx in queue]
        print(self.execution_queue)
        print(f"虚拟工作流构建完成，开始执行！")
        self.run_start_time = time.time()
        QTimer.singleShot(0, self.execute_next)

    def execute_next(self):
        if self.is_interrupt:
            print("运行中断!!!")
            self.run_end_time = time.time()
            self.run_time = self.run_end_time - self.run_start_time
            self.is_running = False
            self.queue_completed.emit()
            self.is_interrupt = False
            return

        if self.execution_queue:
            node_index = self.execution_queue.pop(0)
            node = self.virtual_nodes[node_index]

            node.pre_execute()
            self.data_delivery.emit(node_index, node.serialize())

            try:
                if not self.is_looping:
                    node_hash = node.calculate_hash()
                    if node.idx in self.virtual_cache:
                        cached = self.virtual_cache[node.idx]
                        if cached["hash"] == node_hash and not getattr(node, "always_update", False):

                            node.output_data = cached["output"]

                            node.running_record = cached["running_record"]

                            print(f"节点{node.title}的input相同,跳过执行!output:{node.output_data}")

                            self.intercept_status(node, "IDLE")

                            QTimer.singleShot(0, self.execute_next)
                            return

                node.compute()
                if not self.is_looping:
                    self.virtual_cache[node.idx] = {
                        "hash": node.current_hash,
                        "output": node.output_data.copy(),
                        "running_record": node.running_record
                    }

            except Exception as e:
                import traceback
                print(f"节点：{node.title}出现情况")
                print(e)
                traceback.print_exc()
                return

            QTimer.singleShot(0, self.execute_next)

        else:
            if self.interrupted_nodes:
                self.execution_queue = self.interrupted_nodes.pop()
                QTimer.singleShot(0, self.execute_next)
                return
            else:
                print("运行完成!")
                self.run_end_time = time.time()
                self.run_time = self.run_end_time - self.run_start_time
                self.is_running = False
                self.queue_completed.emit()

    def intercept_status(self, node, status):
        duration = 0.0
        if status == "RUNNING":
            node.start_run_time = time.time()
        elif node.start_run_time:
            duration = time.time() - node.start_run_time

        running_record = node.running_record
        self.node_status_changed.emit(node.idx, status, running_record, duration)

    def interrupt(self):
        self.is_interrupt = True
        print("主动中断运行！")

    def emit_log(self, msg):
        self.node_log_message.emit(msg)

    def cleanup_virtual(self):
        for node in self.virtual_nodes.values():
            if node:
                node.log_generated.disconnect()
                node.deleteLater()
        self.virtual_nodes.clear()
