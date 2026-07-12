from PySide6.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsPathItem, QGraphicsEllipseItem,
                               QMenu, QMessageBox)
from PySide6.QtCore import Qt, QRectF, QPointF, QLineF, Signal, QVariantAnimation
from PySide6.QtGui import QPainter, QPainterPath, QPen, QAction, QCursor, QShortcut, QKeySequence

from nodes.conf import (GRID_SIZE, COLOR_BACKGROUND, EDGE_WIDTH, SOCkET_ADSORPTION_RING_COLOR, SOCkET_ADSORPTION_RING_BORDER,
                        SOCkET_ADSORPTION_RING_PADDING, COLOR_GRID_MINOR, COLOR_GRID_MAJOR)
from nodes.socket import Socket, Edge
from nodes.node_base import BaseNode
from nodes.registry import NODE_REGISTRY

from nodes.node_loop import LoopNode

import re


class NodeScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundBrush(COLOR_BACKGROUND)

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)

        left = int(rect.left()) - (int(rect.left()) % GRID_SIZE)
        top = int(rect.top()) - (int(rect.top()) % GRID_SIZE)
        right = int(rect.right())
        bottom = int(rect.bottom())

        lines_minor = []
        lines_major = []

        for x in range(left, right, GRID_SIZE):
            line = QLineF(x, rect.top(), x, rect.bottom())
            if x % (GRID_SIZE * 5) == 0:
                lines_major.append(line)
            else:
                lines_minor.append(line)

        for y in range(top, bottom, GRID_SIZE):
            line = QLineF(rect.left(), y, rect.right(), y)
            if y % (GRID_SIZE * 5) == 0:
                lines_major.append(line)
            else:
                lines_minor.append(line)

        painter.setPen(QPen(COLOR_GRID_MINOR, 1))
        painter.drawLines(lines_minor)

        painter.setPen(QPen(COLOR_GRID_MAJOR, 1.5))
        painter.drawLines(lines_major)


class GraphicsView(QGraphicsView):
    def __init__(self, scene=None):
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing)   # 开启抗锯齿
        self.setDragMode(QGraphicsView.RubberBandDrag)  # 设置拖拽模式
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)    # 设置缩放中心为鼠标所在位置
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)    # 设置调整大小中心，当窗口大小改变时，保持视野中心不变
        self.original_drag_mode = QGraphicsView.RubberBandDrag  # 默认模式
        self.middle_button_pressed = False  # 记录鼠标中间是否按下
        self.last_mouse_pos = None  # 上一次鼠标的位置

    def mousePressEvent(self, event):
        """鼠标按下时触发"""
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.NoDrag)  # 暂时关闭拖拽模式
            self.middle_button_pressed = True
            self.last_mouse_pos = event.position().toPoint()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """鼠标移动时触发"""
        if self.middle_button_pressed and self.last_mouse_pos is not None:
            delta = event.position().toPoint() - self.last_mouse_pos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self.last_mouse_pos = event.position().toPoint()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """鼠标松开时触发"""
        if event.button() == Qt.MiddleButton:
            self.setDragMode(self.original_drag_mode)   # 恢复为拖拽模式
            self.middle_button_pressed = False
            self.last_mouse_pos = None
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        """鼠标滚轮滚动时触发"""
        delta = event.angleDelta().y()
        if delta == 0:
            super().wheelEvent(event)
            return
        scale_factor = 1.1 ** (delta / 120.0)
        self.scale(scale_factor, scale_factor)
        event.accept()

    def move_to(self, target_pos):
        current_center = self.mapToScene(self.viewport().rect().center())

        self.move_anim = QVariantAnimation()
        self.move_anim.setStartValue(current_center)
        self.move_anim.setEndValue(target_pos)
        self.move_anim.setDuration(300)

        self.move_anim.valueChanged.connect(lambda pos: self.centerOn(pos))

        self.move_anim.start()
        return self.move_anim

    def zoom_to(self, target_rect):
        current_rect = self.viewport().rect()
        scale_x = current_rect.width() / target_rect.width()
        scale_y = current_rect.height() / target_rect.height()
        target_scale = min(scale_x, scale_y)

        self.zoom_anim = QVariantAnimation()
        self.zoom_anim.setStartValue(0.0)
        self.zoom_anim.setEndValue(1.0)
        self.zoom_anim.setDuration(300)

        current_scale = self.transform().m11()

        def on_update(t):
            s = current_scale + (target_scale - current_scale) * t
            self.resetTransform()
            self.scale(s, s)

        self.zoom_anim.valueChanged.connect(on_update)
        self.zoom_anim.start()
        return self.zoom_anim


class NodeGraphView(GraphicsView):
    node_adjusted = Signal(str)

    def __init__(self, scene):
        super().__init__(scene)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        # self.setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)
        self.setAcceptDrops(True)

        self.temp_edge = None
        self.edge_from_socket = None
        self.is_adsorption = None
        self.current_mouse_scene_pos = QPointF(0, 0)
        self.clipboard = []

        self.focus_node = None
        self.selected_nodes = []

        self.adsorption_ring = QGraphicsEllipseItem(0, 0, 20, 20)
        self.adsorption_ring.setPen(QPen(SOCkET_ADSORPTION_RING_COLOR, SOCkET_ADSORPTION_RING_BORDER))
        self.adsorption_ring.setBrush(Qt.NoBrush)
        self.adsorption_ring.setZValue(0)
        self.adsorption_ring.hide()
        self.scene().addItem(self.adsorption_ring)

        self.max_z = 0

        self.bind_shortcut_key()

    def bind_shortcut_key(self):
        shortcut_period = QShortcut(QKeySequence("."), self)

        def period_key_event():
            select_items = self.scene().selectedItems()
            if not select_items:
                return
            nodes = [node for node in select_items if isinstance(node, BaseNode)]

            padding = 50
            left_pos = min(node.x() for node in nodes) - padding
            top_pos = min(node.y() for node in nodes) - padding
            right_pos = max(node.x() + node.width for node in nodes) + padding
            bottom_pos = max(node.y() + node.height for node in nodes) + padding

            self.move_to(QPointF((left_pos + right_pos) / 2, (top_pos + bottom_pos) / 2))
            self.zoom_to(QRectF(left_pos, top_pos, right_pos - left_pos, bottom_pos - top_pos))
            return

        shortcut_period.activated.connect(period_key_event)

    def reset_scene(self):
        rect = self.scene().sceneRect()

        self.scene().clear()

        self.scene().setSceneRect(rect)

        self.adsorption_ring = QGraphicsEllipseItem(0, 0, 20, 20)
        self.adsorption_ring.setPen(QPen(SOCkET_ADSORPTION_RING_COLOR, SOCkET_ADSORPTION_RING_BORDER))
        self.adsorption_ring.setBrush(Qt.NoBrush)
        self.adsorption_ring.setZValue(0)
        self.adsorption_ring.hide()
        self.scene().addItem(self.adsorption_ring)

    def create_temp_edge(self, mouse_pos, edge_color):
        """创建临时线"""
        self.temp_edge = QGraphicsPathItem()
        # 设置预览线的颜色为端口颜色，线的宽度为3像素
        self.temp_edge.setPen(QPen(edge_color, EDGE_WIDTH))
        self.scene().addItem(self.temp_edge)

        self.update_temp_path(mouse_pos)

    def update_temp_path(self, mouse_pos):
        """更新临时线"""
        if not self.edge_from_socket or not self.temp_edge:
            return
        path = QPainterPath()
        # 起点固定在端口位置
        start_pos = self.edge_from_socket.scenePos()
        # 终点跟随鼠标当前位置
        end_pos = self.mapToScene(mouse_pos)

        items_nearby = self.scene().items(QRectF(end_pos.x() - 10, end_pos.y() - 10, 20, 20))

        for item in items_nearby:
            if isinstance(item, Socket):
                if item == self.edge_from_socket:
                    continue
                if item.parentItem() == self.edge_from_socket.parentItem():
                    continue
                if item.socket_type == self.edge_from_socket.socket_type:
                    continue
                end_pos = item.scenePos()
                self.is_adsorption = item
                radius = item.radius + SOCkET_ADSORPTION_RING_PADDING
                self.adsorption_ring.setRect(end_pos.x() - radius, end_pos.y() - radius, radius * 2, radius * 2)
                self.max_z += 1
                self.adsorption_ring.setZValue(self.max_z)
                self.adsorption_ring.show()
                break
            else:
                self.is_adsorption = None
                self.adsorption_ring.hide()

        path.moveTo(start_pos)
        # 计算贝塞尔曲线控制点
        dx = end_pos.x() - start_pos.x()
        ctrl1 = QPointF(start_pos.x() + dx * 0.5, start_pos.y())
        ctrl2 = QPointF(end_pos.x() - dx * 0.5, end_pos.y())
        # 绘制曲线到鼠标位置
        path.cubicTo(ctrl1, ctrl2, end_pos)
        self.temp_edge.setPath(path)

    def mousePressEvent(self, event):
        """鼠标点击时触发"""
        if event.button() == Qt.LeftButton:
            # 获取当前鼠标位置下的最上层图元
            item = self.itemAt(event.position().toPoint())
            if isinstance(item, BaseNode):
                self.max_z += 1
                item.setZValue(self.max_z)
                self.focus_node = item
                self.window().drawer_panel.update_properties_panel(self.focus_node)
                self.window().outliner_panel.update_properties(self.focus_node)

            # 判断点击项是否为端口
            elif isinstance(item, Socket):
                if item.socket_type == "input":
                    # 如果点击的端口连着线的话
                    if item.edges:
                        old_edge = item.edges[0]
                        # 与点击的端口相连的另一个端口
                        other_socket = old_edge.start_socket
                        # 移除原来相连线
                        self.scene().removeItem(old_edge)
                        old_edge.start_socket.remove_edge(old_edge)
                        item.remove_edge(old_edge)

                        node = item.parentItem()
                        if hasattr(node, "on_input_disconnected"):
                            node.on_input_disconnected(item)

                        # 创建新的预览线
                        self.edge_from_socket = other_socket
                        self.create_temp_edge(event.position().toPoint(), self.edge_from_socket.color)
                        return
                    else:
                        self.edge_from_socket = item
                        self.create_temp_edge(event.position().toPoint(), self.edge_from_socket.color)
                        return

                elif item.socket_type == "output":
                    self.edge_from_socket = item
                    self.create_temp_edge(event.position().toPoint(), self.edge_from_socket.color)
                    return

            else:
                self.focus_node = None

        if event.button() == Qt.RightButton:
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """鼠标移动时触发"""
        if self.focus_node:
            self.window().drawer_panel.update_properties_panel(self.focus_node)
            self.window().outliner_panel.update_properties(self.focus_node)

        self.current_mouse_scene_pos = self.mapToScene(event.position().toPoint())
        if self.edge_from_socket and self.temp_edge:
            self.update_temp_path(event.position().toPoint())
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """鼠标松开时触发"""
        if self.edge_from_socket and self.temp_edge or self.is_adsorption and self.temp_edge:
            target_socket = None
            if self.is_adsorption:
                target_socket = self.is_adsorption

            elif self.edge_from_socket:
                # 获取鼠标松开位置下的所有图元
                items_at_pos = self.items(event.position().toPoint())
                # 获取端口
                for item in items_at_pos:
                    if isinstance(item, Socket):
                        target_socket = item
                        print(target_socket)
                        break

            if target_socket:
                start_socket, end_socket = None, None
                # 保证线的开始端口一定是output类型，结束端口一定是input类型
                if self.edge_from_socket.socket_type == "output" and target_socket.socket_type == "input":
                    start_socket, end_socket = self.edge_from_socket, target_socket
                elif self.edge_from_socket.socket_type == "input" and target_socket.socket_type == "output":
                    start_socket, end_socket = target_socket, self.edge_from_socket

                if start_socket and end_socket:
                    if start_socket.parentItem() != end_socket.parentItem():
                        type_start = start_socket.data_type
                        type_end = end_socket.data_type
                        is_compatible = ((type_start == type_end)
                                         or (type_start == "any" and type_end != "exec")
                                         or (type_end == "any" and type_start != "exec"))
                        if is_compatible:
                            if end_socket.edges and end_socket.data_type != "exec":
                                old_edge = end_socket.edges[0]
                                self.scene().removeItem(old_edge)
                                old_edge.start_socket.remove_edge(old_edge)
                                end_socket.remove_edge(old_edge)

                            edge = Edge(start_socket, end_socket)
                            self.scene().addItem(edge)
                            start_socket.add_edge(edge)
                            end_socket.add_edge(edge)
                            edge.update_path()

                            node = end_socket.parentItem()
                            if hasattr(node, "on_input_connected"):
                                node.on_input_connected(end_socket)

                        else:
                            print("端口类型不兼容！")

        self.scene().removeItem(self.temp_edge)
        self.temp_edge = None
        self.edge_from_socket = None
        self.is_adsorption = None
        self.adsorption_ring.hide()

        super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().drawMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if not urls:
                return

            filepath = urls[0].toLocalFile()

            if filepath.lower().endswith('.json'):
                mian_window = self.window()

                reply = QMessageBox.question(mian_window, "确认", "是否清空当前工作流并打开新工作流？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    nodes = mian_window.serializer.load_from_file(filepath)
                    for node in nodes.values():
                        node.adjusted.connect(mian_window.history.record)
                    mian_window.history.record("打开工作流")

            elif filepath.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp')):
                pass

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            select_items = self.scene().selectedItems()
            if not select_items:
                return
            nodes = [node for node in select_items if isinstance(node, BaseNode)]
            self.delete_node(nodes)
            return

        super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        """设置右键菜单"""

        mouse_pos = self.mapToScene(event.pos())
        select_items = self.scene().selectedItems()
        nodes = [node for node in select_items if isinstance(node, BaseNode)]

        menu = QMenu(self)
        if nodes:
            action_del = QAction("删除节点", self)
            action_del.triggered.connect(lambda: self.delete_node(nodes))
            menu.addAction(action_del)

            action_disconnect = QAction("清空连线", self)
            action_disconnect.triggered.connect(lambda: self.disconnect_node_edge(nodes))
            menu.addAction(action_disconnect)

            action_copy = QAction("复制节点", self)
            action_copy.triggered.connect(lambda: self.copy_node(nodes, mouse_pos))
            menu.addAction(action_copy)

            action_paste = QAction("粘贴节点", self)
            action_paste.triggered.connect(self.paste_node)
            menu.addAction(action_paste)
            if self.clipboard:
                action_paste.setEnabled(True)
            else:
                action_paste.setEnabled(False)

        else:
            add_menu = menu.addMenu("新建节点")

            menu_tree = {}

            def add_to_menu(tree, path_list, data):
                current_level = path_list[0]
                if current_level not in tree:
                    tree[current_level] = {"nodes": [], "sub": {}}
                if len(path_list) == 1:
                    tree[current_level]["nodes"].append(data)
                else:
                    add_to_menu(tree[current_level]["sub"], path_list[1:], data)

            for node_data in NODE_REGISTRY.values():
                if node_data["visible"]:
                    path_list = node_data['category'].split("/")
                    add_to_menu(menu_tree, path_list, node_data)

            def build_menu(parent_menu, tree_dict):
                for cat_name in tree_dict.keys():
                    sub_menu = parent_menu.addMenu(cat_name)

                    for node_data in tree_dict[cat_name]["nodes"]:
                        title = node_data['title']
                        node_cls = node_data['class']
                        scene_pos = self.mapToScene(event.pos())
                        action = QAction(title, self)
                        action.triggered.connect(lambda checked=False, cls=node_cls: self.add_node(cls, scene_pos))
                        sub_menu.addAction(action)

                    if tree_dict[cat_name]["sub"]:
                        build_menu(sub_menu, tree_dict[cat_name]["sub"])

            build_menu(add_menu, menu_tree)

            action_paste = QAction("粘贴节点", self)
            action_paste.triggered.connect(self.paste_node)
            menu.addAction(action_paste)
            if self.clipboard:
                action_paste.setEnabled(True)
            else:
                action_paste.setEnabled(False)

        menu.exec(event.globalPos())

    def delete_node(self, node):
        self.window().history.suspend()

        nodes = set()
        nodes.update(node if isinstance(node, list) else [node])
        symbiont_nodes = [node.symbiont_nodes for node in nodes if node.symbiont_nodes]
        nodes.update(self.get_nodes_by_idx([idx for nodes_idx in symbiont_nodes for idx in nodes_idx]))

        self.scene().blockSignals(True)
        self.setUpdatesEnabled(False)
        try:
            for i in nodes:
                for socket in i.input_socket + i.output_socket + list(i.widget_socket.values()):
                    if socket:
                        for edge in list(socket.edges):
                            self.remove_edge(edge)
                self.scene().removeItem(i)
        finally:
            self.scene().blockSignals(False)
            self.setUpdatesEnabled(True)
            self.update()

        nodes_title = ",".join([i.title for i in nodes])

        self.window().history.resume()
        self.emit_node_adjusted(f"删除{nodes_title}节点")

    def disconnect_node_edge(self, node):
        self.window().history.suspend()

        nodes = node if isinstance(node, list) else [node]

        for node in nodes:
            for socket in node.input_socket + node.output_socket + list(node.widget_socket.values()):
                if socket:
                    for edge in socket.edges:
                        self.remove_edge(edge)

        self.window().history.resume()
        self.emit_node_adjusted(f"清除{node.title}节点连线")

    def copy_node(self, nodes, mouse_pos):
        self.clipboard.clear()
        for node in nodes:
            dx = node.x() - mouse_pos.x()
            dy = node.y() - mouse_pos.y()
            self.clipboard.append({
                "data": node.serialize(),
                "offset": (dx, dy)
            })

    def paste_node(self):
        if not self.clipboard:
            return
        self.window().history.suspend()

        global_pos = QCursor.pos()
        view_pos = self.mapFromGlobal(global_pos)
        mouse_pos = self.mapToScene(view_pos)

        nodes = []

        self.scene().clearSelection()
        for clip_item in self.clipboard:
            data = clip_item["data"]
            dx, dy = clip_item["offset"]

            class_name = data["type"]
            if class_name in NODE_REGISTRY:

                node_cls = NODE_REGISTRY[class_name]['class']
                node = node_cls()
                node.adjusted.connect(self.emit_node_adjusted)

                self.max_z += 1
                node.setZValue(self.max_z)

                data["idx"] = str(BaseNode.node_max_index)
                BaseNode.node_max_index += 1
                node.deserialize(data)

                node.title = self.get_unique_node_title(node.title)

                node.setPos(mouse_pos.x() + dx, mouse_pos.y() + dy)

                self.scene().addItem(node)

                node.setSelected(True)
                nodes.append(node)

            nodes_title = ",".join([node.title for node in nodes])

            self.window().history.resume()
            self.emit_node_adjusted(f"复制{nodes_title}节点")

    def remove_edge(self, edge):
        self.scene().removeItem(edge)
        edge.start_socket.remove_edge(edge)
        edge.end_socket.remove_edge(edge)

        end_node = edge.end_socket.parentItem()
        if hasattr(end_node, "on_input_disconnected"):
            end_node.on_input_disconnected(edge.end_socket)

    def get_unique_node_title(self, base_list):
        match = re.match(r"^(.*?)(?:\.\d+)?$", base_list)
        root_title = match.group(1) if match else base_list
        existing_titles = [item.title for item in self.scene().items() if hasattr(item, "title")]

        if root_title not in existing_titles:
            return root_title

        i = 1
        while True:
            candidate = f"{root_title}.{i:03d}"
            if candidate not in existing_titles:
                return candidate
            i += 1

    def add_node(self, node_cls, scene_pos):
        if issubclass(node_cls, LoopNode):
            loop_start_node = self.add_node(NODE_REGISTRY["LoopStartNode"]["class"], QPointF(scene_pos.x() - 150, scene_pos.y()))
            loop_end_node = self.add_node(NODE_REGISTRY["LoopEndNode"]["class"], QPointF(scene_pos.x() + 150, scene_pos.y()))
            loop_start_node.symbiont_nodes.append(loop_end_node.idx)
            loop_end_node.symbiont_nodes.append(loop_start_node.idx)
            return

        node = node_cls()
        node.adjusted.connect(self.emit_node_adjusted)

        self.max_z += 1
        node.setZValue(self.max_z)

        node.title = self.get_unique_node_title(node.title)

        node.idx = str(BaseNode.node_max_index)
        BaseNode.node_max_index += 1

        node.setPos(scene_pos)
        node.setSelected(True)
        self.scene().addItem(node)

        self.emit_node_adjusted(f"添加{node.title}节点")

        return node

    def get_nodes_by_idx(self, idx_list):
        nodes = []
        for node in self.scene().items():
            if isinstance(node, BaseNode):
                if node.idx in idx_list:
                    nodes.append(node)
        return nodes

    def emit_node_adjusted(self, action_name):
        self.node_adjusted.emit(action_name)
