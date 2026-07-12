import json
from nodes.node_base import BaseNode
from nodes.registry import NODE_REGISTRY
from nodes.socket import Edge


class SessionSerializer:
    def __init__(self, view):
        self.view = view
        self.scene = view.scene()

    def serialize_to_dict(self, nodes=None):
        nodes_data = {}
        if nodes:
            all_nodes = nodes
        else:
            all_nodes = [node for node in self.scene.items() if isinstance(node, BaseNode)]
        node_map = {node: node.idx for node in all_nodes}

        for node in all_nodes:
            node_index = node.idx
            node_data = node.serialize()
            nodes_data[node_index] = node_data

            node_data["edges"] = []

            for index, socked in enumerate(node.output_socket):
                for edge in socked.edges:
                    target_socket = edge.end_socket
                    target_node = target_socket.parentItem()

                    if target_node in node_map:
                        if target_socket in target_node.input_socket:
                            edges_data = {
                                "start_node": node_index,
                                "start_socket": str(index),
                                "end_node": str(node_map[target_node]),
                                "end_socket": str(target_node.input_socket.index(target_socket)),
                                "end_socket_type": "input_socket"
                            }
                            node_data["edges"].append(edges_data)
                        elif target_socket in target_node.widget_socket.values():
                            edges_data = {
                                "start_node": node_index,
                                "start_socket": str(index),
                                "end_node": str(node_map[target_node]),
                                "end_socket": str(list(target_node.widget_socket.values()).index(target_socket)),
                                "end_socket_type": "widget_socket"
                            }
                            node_data["edges"].append(edges_data)

        nodes_data = {idx: nodes_data[idx] for idx in sorted(nodes_data.keys(), key=lambda str_idx: int(str_idx))}

        return dict(nodes_data)

    def save_to_file(self, filepath):
        scene_data = self.serialize_to_dict()
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(scene_data, f, indent=4, ensure_ascii=False)
            print(f"保存成功:{filepath}")
            return True
        except Exception as e:
            print(f"保存失败:{e}")
            return False

    def load_from_dict(self, scene_data):
        self.view.reset_scene()
        BaseNode.node_max_index = 0

        created_nodes = {}
        created_edges = []

        for node_index, node_data in scene_data.items():
            class_name = node_data['type']
            if class_name in NODE_REGISTRY:
                cls = NODE_REGISTRY[class_name]['class']
                node = cls()
                node.deserialize(node_data)

                self.scene.addItem(node)
                created_nodes[node_index] = node
                created_edges.extend(node_data["edges"])
            else:
                print(f"未知节点:{class_name},跳过")
                created_nodes[node_index] = None

        BaseNode.node_max_index = max([int(node.idx) for node in created_nodes.values() if node is not None ]) + 1

        for edge_data in created_edges:
            try:
                start_node = created_nodes[edge_data['start_node']]
                start_socket = start_node.output_socket[int(edge_data['start_socket'])]

                end_node = created_nodes[edge_data['end_node']]
                if edge_data['end_socket_type'] == "input_socket":
                    end_socket = end_node.input_socket[int(edge_data['end_socket'])]
                else:
                    end_socket = list(end_node.widget_socket.values())[int(edge_data['end_socket'])]

                edge = Edge(start_socket, end_socket)
                self.scene.addItem(edge)
                start_socket.add_edge(edge)
                end_socket.add_edge(edge)
                edge.update_path()

                if hasattr(end_node, "on_input_connected"):
                    end_node.on_input_connected(end_socket)
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"{created_nodes[edge_data['start_node']].title}节点的连线恢复失败:{e}")

        return created_nodes

    def load_from_file(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                scene_data = json.load(f)
                nodes = self.load_from_dict(scene_data)
                return nodes
        except Exception as e:
            print(f"读取失败:{e}")
            return None
