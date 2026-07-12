from PySide6.QtWidgets import (QApplication, QMainWindow, QGraphicsView, QGraphicsScene,  QGraphicsObject, QGraphicsPathItem, QGraphicsItem,
                               QGraphicsProxyWidget, QHBoxLayout, QVBoxLayout, QWidget, QToolBar, QLabel, QPushButton, QLineEdit, QPlainTextEdit, QSpinBox,
                               QDoubleSpinBox, QComboBox, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt, QRectF, QPointF, QEventLoop, Signal
from PySide6.QtGui import QPainter, QPainterPath, QColor, QBrush, QPen, QFont, QFontMetrics, QPolygonF

from nodes.conf import (NODE_WIDTH, NODE_HEIGHT, NODE_RADIUS, NODE_BORDER, NODE_TITLE_HEIGHT, NODE_PADDING, SOCKET_RADIUS, SOCKET_SPACING,
                        COLOR_NODE_BACKGROUND, COLOR_NODE_BORDER, COLOR_NODE_SELECTED, COLOR_NODE_FETCHING, COLOR_NODE_RUNNING, COLOR_NODE_ERROR,
                        COLOR_NODE_SYMBIONT, NODE_SOCKET_TYPE_COLORS)
from nodes.socket import Socket
from nodes.widget import Label
from nodes.worker import Worker
from nodes.conf import GRID_SIZE

import hashlib


class BaseNode(QGraphicsObject):
    node_max_index = 1
    adjusted = Signal(str)
    log_generated = Signal(str)
    logic_completed = Signal(object)

    """基础节点"""
    def __init__(self, conf, parent=None):
        super().__init__(parent)
        self.conf = conf

        self.title = self.conf.get("title", "未定义")
        self.node_type = self.conf.get("node_type", "any")
        self.size = self.conf.get("size", (NODE_WIDTH, NODE_HEIGHT))
        self.zoom_limit = self.conf.get("zoom_limit", None)
        self.is_terminator = self.conf.get("is_terminator", False)
        self.execution_priority = self.conf.get("execution_priority", 10)
        self.always_update = self.conf.get("always_update", False)

        if self.size:
            self.width, self.height = self.size
        else:
            self.width, self.height = (NODE_WIDTH, NODE_HEIGHT)
        self.width = self.width if self.width > NODE_WIDTH else NODE_WIDTH
        self.height = self.height if self.height > NODE_HEIGHT else NODE_HEIGHT

        self.minimum_width, self.minimum_height = None, None

        self.node_types = NODE_SOCKET_TYPE_COLORS
        self.title_background_color = QColor(self.node_types.get(self.node_type, "#ffffff"))

        self.idx = None
        self.status = "IDLE"
        self.current_hash = ""
        self.runner = None

        self.start_run_time = 0.0
        self.last_run_time = 0.0
        self.running_prompt = None

        self.input_socket = []
        self.output_socket = []
        self.widget_socket = {}

        self.symbiont_nodes = []

        self.is_collapsed = False
        self.expanded_width = self.width
        self.expanded_height = self.height

        self.special_socket_num = 0

        self.output_data = {}  # 输出结果

        self.inputs = {}
        self.results = {}
        self.running_record = {"inputs": self.inputs, "results": self.results}

        if self.zoom_limit:
            self.is_resizable = True        # 是否可以拖拽缩放
        else:
            self.is_resizable = False       # 是否可以拖拽缩放
        self.is_resizing = False            # 是否拖拽缩放中
        self.resize_handle_size = 10        # 检测拖拽缩放的范围
        self.socket_radius = SOCKET_RADIUS  # 端口半径

        self.widget_container = QWidget()
        self.widget_container.resize(self.width - NODE_PADDING * 2, self.height - NODE_TITLE_HEIGHT - NODE_PADDING*2)
        self.widget_container.setStyleSheet("background: transparent;")

        self.widget_layout = QVBoxLayout(self.widget_container)
        self.widget_layout.setContentsMargins(0, 0, 0, 0)
        self.widget_layout.setSpacing(5)

        self.widget_proxy = QGraphicsProxyWidget(self)
        self.widget_proxy.setWidget(self.widget_container)

        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

        self.setFlag(QGraphicsObject.ItemIsSelectable, True)            # 允许节点被选中
        self.setFlag(QGraphicsObject.ItemIsMovable, True)               # 允许节点被拖拽移动
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)    # 当几何发生变化时（比如移动）时，触发事件通知
        self.setAcceptHoverEvents(True)

    def init(self):
        """初始化"""
        self.special_socket_num = 1 if (self.input_socket
                                        and self.input_socket[0].data_type == "exec"
                                        and not self.input_socket[0].name
                                        or self.output_socket
                                        and self.output_socket[0].data_type == "exec"
                                        and not self.output_socket[0].name
                                        ) else 0

        self.widget_proxy.setPos(NODE_PADDING, NODE_TITLE_HEIGHT + (max(len(self.input_socket), len(self.output_socket)) + 1 - self.special_socket_num) * SOCKET_SPACING)
        self.minimum_width = NODE_WIDTH
        self.minimum_height = (NODE_TITLE_HEIGHT
                               + (max(len(self.input_socket), len(self.output_socket)) + 1 - self.special_socket_num) * SOCKET_SPACING
                               + sum([widget.minimumHeight() for widget in self.widget_socket]) + (len(self.widget_socket) - 1) * self.widget_layout.spacing()
                               + NODE_PADDING)

        self.width = self.width if self.width > self.minimum_width else self.minimum_width
        self.height = self.height if self.height > self.minimum_height else self.minimum_height

        self.update_node()

        self.widget_connected()

    def update_node(self):
        self.update_socket_positions()
        self.prepareGeometryChange()
        self.update()

    def hoverMoveEvent(self, event):
        """鼠标进入时触发"""
        pos = event.pos()
        btn_size = 14
        if self.is_collapsed:
            btn_rect = QRectF(18, self.height / 2 - 7, btn_size, btn_size)
        else:
            btn_rect = QRectF(8, NODE_TITLE_HEIGHT / 2 - 7, btn_size, btn_size)
        if btn_rect.contains(pos):
            self.setCursor(Qt.PointingHandCursor)

        elif self.is_resizable:
            if self.is_collapsed:
                handle_rect = QRectF(self.width - 33, self.height / 2 - 10, 13, 20)
                if handle_rect.contains(pos):
                    self.setCursor(Qt.SizeHorCursor)
                else:
                    self.setCursor(Qt.ArrowCursor)
            else:
                pos = event.pos()
                handle_rect = QRectF(self.width - self.resize_handle_size, self.height - self.resize_handle_size, self.resize_handle_size, self.resize_handle_size)
                if handle_rect.contains(pos):
                    if self.zoom_limit == "HV":
                        self.setCursor(Qt.SizeFDiagCursor)
                    elif self.zoom_limit == "H":
                        self.setCursor(Qt.SizeHorCursor)
                    elif self.zoom_limit == "V":
                        self.setCursor(Qt.SizeVerCursor)
                else:
                    self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event):
        """鼠标离开时触发"""
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        """鼠标点击时触发"""
        if event.button() == Qt.LeftButton:
            click_pos = event.pos()
            btn_size = 14
            if self.is_collapsed:
                btn_rect = QRectF(18, self.height / 2 - 7, btn_size, btn_size)
            else:
                btn_rect = QRectF(8, NODE_TITLE_HEIGHT / 2 - 7, btn_size, btn_size)
            if btn_rect.contains(click_pos):
                self.toggle_collapse()
                event.accept()
                return

            self.current_pos = self.pos()

            if self.is_resizable:
                if self.is_collapsed:
                    handle_rect = QRectF(self.width - 33, self.height / 2 - 10, 13, 20)
                    if handle_rect.contains(click_pos):
                        self.is_resizing = True
                        event.accept()
                        return
                else:
                    click_pos = event.pos()
                    handle_rect = QRectF(self.width-self.resize_handle_size, self.height-self.resize_handle_size, self.resize_handle_size, self.resize_handle_size)
                    if handle_rect.contains(click_pos):
                        self.is_resizing = True
                        event.accept()
                        return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """鼠标移动时触发"""
        if self.is_resizing:
            if self.is_collapsed:
                self.setCursor(Qt.SizeHorCursor)
                new_width = event.pos().x() + 20
                new_width = max(new_width, self.minimum_width)
                self.width = new_width
                self.expanded_width = new_width
            else:
                if self.zoom_limit == "HV":
                    self.setCursor(Qt.SizeFDiagCursor)
                    new_width, new_height = event.pos().x(), event.pos().y()
                    new_width, new_height = max(new_width, self.minimum_width), max(new_height, self.minimum_height)
                    self.width, self.height = new_width, new_height

                elif self.zoom_limit == "H":
                    self.setCursor(Qt.SizeHorCursor)
                    new_width = event.pos().x()
                    new_width = max(new_width, self.minimum_width)
                    self.width = new_width

                elif self.zoom_limit == "V":
                    self.setCursor(Qt.SizeVerCursor)
                    new_height = event.pos().y()
                    new_height = max(new_height, self.minimum_height)
                    self.height = new_height

            self.update_node()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """鼠标松开时触发"""
        if event.button() == Qt.LeftButton:
            if self.current_pos != self.pos():
                self.adjusted.emit(f"移动{self.title}节点")
            elif self.is_resizing:
                self.is_resizing = False
                self.setCursor(Qt.ArrowCursor)
                event.accept()
                self.adjusted.emit(f"缩放{self.title}节点")
                return
        super().mouseReleaseEvent(event)

    def update_socket_positions(self):
        if self.is_collapsed:
            all_inputs = [s for s in self.input_socket if s is not None] + [s for s in self.widget_socket.values() if s is not None]

            def y_pos(sockets, index):
                if len(sockets) % 2 == 1:
                    m = (len(sockets) - 1) // 2
                    return self.height / 2 + (index - m) * (SOCKET_RADIUS + 1) * 2
                else:
                    m = len(sockets) // 2
                    return self.height / 2 + (index - m + 0.5) * (SOCKET_RADIUS + 1) * 2

            for i, socket in enumerate(all_inputs):
                y = y_pos(all_inputs, i)
                socket.setPos(0, y)
                if socket.edges:
                    for edge in socket.edges:
                        edge.update_path()

            for i, socket in enumerate(self.output_socket):
                y = y_pos(self.output_socket, i)
                socket.setPos(self.width, y)
                if socket.edges:
                    for edge in socket.edges:
                        edge.update_path()

        else:
            container_new_width = self.width - NODE_PADDING * 2
            container_new_height = self.height - NODE_TITLE_HEIGHT - (max(len(self.input_socket), len(self.output_socket)) + 1 - self.special_socket_num) * SOCKET_SPACING - NODE_PADDING
            self.widget_container.setFixedSize(container_new_width, container_new_height)

            y = self.widget_container.y()
            for widget, socket in self.widget_socket.items():
                y += widget.height() / 2
                if socket:
                    socket.setPos(0, y)
                    if socket.edges:
                        for edge in socket.edges:
                            edge.update_path()
                y += widget.height() / 2 + self.widget_layout.spacing()

            i = 0
            for socket in self.input_socket:
                if socket.data_type == "exec" and not socket.name:
                    y = NODE_TITLE_HEIGHT
                else:
                    y = NODE_TITLE_HEIGHT + (i + 1) * SOCKET_SPACING
                    i += 1
                socket.setPos(0, y)
                if socket.edges:
                    for edge in socket.edges:
                        edge.update_path()

            i = 0
            for socket in self.output_socket:
                if socket.data_type == "exec" and not socket.name:
                    y = NODE_TITLE_HEIGHT
                else:
                    y = NODE_TITLE_HEIGHT + (i + 1) * SOCKET_SPACING
                    i += 1
                socket.setPos(self.width, y)
                if socket.edges:
                    for edge in socket.edges:
                        edge.update_path()

    def widget_connected(self):
        def trigger_record():
            if self.scene() and self.scene().views():
                main_window = self.scene().views()[0].window()
                if hasattr(main_window, "history"):
                    main_window.history.record(f"修改{self.title}节点")

        all_widgets = list(self.widget_socket.keys())

        for widgets in all_widgets:
            if isinstance(widgets, (QLabel, QLineEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox)) or not widgets.children():
                widgets = [widgets]
            else:
                widgets = [widget for widget in widgets.children() if not isinstance(widget, (QHBoxLayout, QVBoxLayout))]

            for widget in widgets:
                if isinstance(widget, (QLineEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox)):
                    if hasattr(widget, "editingFinished"):
                        widget.editingFinished.connect(trigger_record)
                elif isinstance(widget, QComboBox):
                    if hasattr(widget, "activated"):
                        widget.activated.connect(trigger_record)

                elif isinstance(widget, QPushButton):
                    if hasattr(widget, "clickCompleted"):
                        widget.clickCompleted.connect(trigger_record)
                elif isinstance(widget, (QWidget, QLabel)):
                    if hasattr(widget, "setCompleted"):
                        widget.setCompleted.connect(trigger_record)

    def on_input_connected(self, socket):
        """端口连接时触发"""
        if socket.has_error and self.status == "ERROR":
            socket.has_error = False
            self.status = "IDLE"

        for widget, target_socket in self.widget_socket.items():
            if socket == target_socket:
                widget.setEnabled(False)

        self.adjusted.emit(f"{self.title}添加了输入连线")

    def on_input_disconnected(self, socket):
        """端口断开连接时触发"""
        for widget, target_socket in self.widget_socket.items():
            if socket == target_socket:
                widget.setEnabled(True)

        self.adjusted.emit(f"{self.title}断开了输入连线")

    # 2
    def boundingRect(self):
        return QRectF(-10, -10, self.width + 20, self.height + 20)

    # 3
    def itemChange(self, change, value):
        """当自身的属性变化时触发，(比如:节点位置发生改变，鼠标在节点内的位置发生改变，节点的大小发生改变等)"""
        if change == QGraphicsItem.ItemPositionChange:
            modifiers = QApplication.keyboardModifiers()
            if modifiers:
                new_pos = value
                x = round(new_pos.x() / GRID_SIZE) * GRID_SIZE
                y = round(new_pos.y() / GRID_SIZE) * GRID_SIZE
                return QPointF(x, y)

        if change == QGraphicsItem.ItemPositionHasChanged:
            all_socket = (
                self.input_socket
                + self.output_socket
                + list(self.widget_socket.values())
            )
            for socket in all_socket:
                if socket:
                    for edge in socket.edges:
                        edge.update_path()

        if change == QGraphicsItem.ItemSelectedChange:
            if not self.isSelected() and self.symbiont_nodes:
                for node in self.scene().items():
                    if isinstance(node, BaseNode):
                        if node.idx in self.symbiont_nodes:
                            node.set_state("SYMBIONT")
            elif self.symbiont_nodes:
                for node in self.scene().items():
                    if isinstance(node, BaseNode):
                        if node.idx in self.symbiont_nodes:
                            node.set_state("IDLE")

        return super().itemChange(change, value)

    # 2
    def paint(self, painter, option, widget=None):
        body_rect = QRectF(0, 0, self.width, self.height)

        if self.is_collapsed:
            painter.setBrush(QBrush(self.title_background_color))

            if self.isSelected():
                # 选中时
                pen = QPen(COLOR_NODE_SELECTED, NODE_BORDER)
            elif self.status == "FETCHING":
                pen = QPen(COLOR_NODE_FETCHING, NODE_BORDER)
            elif self.status == "RUNNING":
                pen = QPen(COLOR_NODE_RUNNING, NODE_BORDER)
            elif self.status == "ERROR":
                pen = QPen(COLOR_NODE_ERROR, NODE_BORDER)
            elif self.status == "SYMBIONT":
                pen = QPen(COLOR_NODE_SYMBIONT, NODE_BORDER)
            else:
                # 未选中时
                pen = QPen(COLOR_NODE_BORDER, NODE_BORDER)

            painter.setPen(pen)
            painter.drawRoundedRect(body_rect, NODE_RADIUS, NODE_RADIUS)

            painter.setPen(Qt.white)
            y = self.height / 2
            p1 = QPointF(20, y - 5)
            p2 = QPointF(30, y)
            p3 = QPointF(20, y + 5)
            painter.drawPolygon(QPolygonF([p1, p2, p3]))

            title_rect = QRectF(35, 0, self.width - 35, self.height)
            font = QFont("Arial", 10)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(title_rect, Qt.AlignVCenter | Qt.AlignLeft, self.title)

            painter.setPen(QPen(Qt.white, 1.5))
            painter.drawLine(self.width - 28, self.height / 2 - 9, self.width - 28, self.height / 2 + 9)
            painter.drawLine(self.width - 25, self.height / 2 - 9, self.width - 25, self.height / 2 + 9)

        else:
            painter.setBrush(QBrush(COLOR_NODE_BACKGROUND))

            # 判断是否选中节点
            if self.isSelected():
                # 选中时
                pen = QPen(COLOR_NODE_SELECTED, NODE_BORDER)
            elif self.status == "FETCHING":
                pen = QPen(COLOR_NODE_FETCHING, NODE_BORDER)
            elif self.status == "RUNNING":
                pen = QPen(COLOR_NODE_RUNNING, NODE_BORDER)
            elif self.status == "ERROR":
                pen = QPen(COLOR_NODE_ERROR, NODE_BORDER)
            elif self.status == "SYMBIONT":
                pen = QPen(COLOR_NODE_SYMBIONT, NODE_BORDER)
            else:
                # 未选中时
                pen = QPen(COLOR_NODE_BORDER, NODE_BORDER)

            painter.setPen(pen)
            painter.drawRoundedRect(body_rect, NODE_RADIUS, NODE_RADIUS)

            # 标题栏矩形区域
            title_rect = QRectF(1, 1, self.width-2, NODE_TITLE_HEIGHT+NODE_PADDING)
            painter.setBrush(QBrush(self.title_background_color))
            painter.setPen(Qt.NoPen)

            path = QPainterPath()
            path.addRoundedRect(title_rect, NODE_RADIUS-1, NODE_RADIUS-1)

            clip_path = QPainterPath()
            clip_path.addRect(title_rect.adjusted(0, 0, 0, -10))
            path = path.intersected(clip_path)
            painter.drawPath(path)

            # 箭头
            painter.setBrush(Qt.NoBrush)
            painter.setPen(Qt.white)
            y = NODE_TITLE_HEIGHT / 2
            p1 = QPointF(10, y - 4)
            p2 = QPointF(20, y - 4)
            p3 = QPointF(15, y + 5)
            painter.drawPolygon(QPolygonF([p1, p2, p3]))

            # 标题
            font = QFont("Arial", 10)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(title_rect.adjusted(25, -10, -10, 0), Qt.AlignVCenter | Qt.AlignLeft, self.title)

            # 绘画端口标签
            painter.setPen(Qt.white)
            font = QFont("Arial", 10)
            font.setBold(True)
            painter.setFont(font)

            for socket in self.input_socket:
                text_rect = QRectF(socket.x() + 15, socket.y() - 10, self.width / 2 - 15, 20)
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, socket.name)

            for socket in self.output_socket:
                text_rect = QRectF(socket.x() - self.width / 2, socket.y() - 10, self.width / 2 - 15, 20)
                painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, socket.name)

            # 绘画运行计时器
            if self.last_run_time is not None and not self.running_prompt:
                time_str = f"{self.last_run_time:.2f}s"
                painter.setPen(QColor("#e5e5e5"))
                font = QFont("Arial", 10)
                painter.setFont(font)

                fm = QFontMetrics(font)
                w = fm.horizontalAdvance(time_str)
                painter.drawText(self.width - w - 10, 20, time_str)
            else:
                painter.setPen(QColor("#e5e5e5"))
                font = QFont("Arial", 10)
                painter.setFont(font)

                fm = QFontMetrics(font)
                w = fm.horizontalAdvance(self.running_prompt)
                painter.drawText(self.width - w - 10, 20, self.running_prompt)

    def toggle_collapse(self):
        self.is_collapsed = not self.is_collapsed

        if self.is_collapsed:
            self.expanded_width = self.width
            self.expanded_height = self.height
            self.widget_proxy.hide()

            all_inputs = [s for s in self.input_socket if s is not None] + [s for s in self.widget_socket.values() if s is not None]
            max_sockets = max(len(all_inputs), len(self.output_socket))
            self.height = max(40, max_sockets * 14 + SOCKET_RADIUS)

        else:
            self.width = self.expanded_width
            self.height = self.expanded_height
            self.widget_proxy.show()

        self.update_node()
        self.adjusted.emit(f"{'折叠' if self.is_collapsed else '展开'}{self.title}节点")

    def set_state(self, new_status):
        """设置运行状态"""
        self.status = new_status
        self.update_socket_positions()
        self.update()
        QApplication.processEvents()

    def reset_state(self):
        self.status = "IDLE"
        self.start_run_time = 0.0
        self.last_run_time = 0.0
        self.running_prompt = None
        for socket in self.input_socket + list(self.widget_socket.values()):
            if socket:
                socket.has_error = False
        self.update_socket_positions()
        self.update()

    def add_widget(self, widget, data_type=None):
        """添加组件"""
        self.widget_layout.addWidget(widget)
        self.widget_socket[widget] = self.add_widget_socket(data_type) if data_type else None
        return widget

    def replace_widget(self, old_widget, new_widget, data_type=None):
        self.widget_layout.replaceWidget(old_widget, new_widget)
        self.widget_socket.pop(old_widget, None)
        self.widget_socket[new_widget] = self.add_widget_socket(data_type) if data_type else None
        return new_widget

    def remove_widget(self, widget):
        self.widget_layout.removeWidget(widget)
        self.widget_socket.pop(widget, None)
        return widget

    def add_widget_socket(self, data_type):
        """添加控件端口"""
        socket = Socket(self, socket_type="input", data_type=data_type)
        return socket

    def add_exec_socket(self, only_input=False, only_output=False, is_auxiliary=True):
        for _type, x, _list in zip(["input", "output"], [0, self.width], [self.input_socket, self.output_socket]):
            if only_output:
                only_output = False
                continue
            if not _list or _list[0].data_type != "exec":
                socket = Socket(self, socket_type=_type, data_type="exec", is_exec=True)
                if not is_auxiliary:
                    socket.name = "exec"
                y = NODE_TITLE_HEIGHT
                socket.setPos(x, y)
                _list.insert(0, socket)
            if only_input:
                break

    def add_input_socket(self, name, data_type, required=False):
        """添加输入端口"""
        socket = Socket(self, socket_type="input", data_type=data_type, required=required)
        socket.name = name
        y = NODE_TITLE_HEIGHT + (len(self.input_socket) + 1) * SOCKET_SPACING
        socket.setPos(0, y)
        self.input_socket.append(socket)
        return socket

    def add_output_socket(self, name, data_type):
        """添加输出端口"""
        socket = Socket(self, socket_type="output", data_type=data_type)
        socket.name = name
        y = NODE_TITLE_HEIGHT + (len(self.output_socket) + 1) * SOCKET_SPACING
        socket.setPos(self.width, y)
        self.output_socket.append(socket)

        socket_index = self.output_socket.index(socket)
        self.output_data[socket_index] = None
        return socket

    def delete_socket(self, socket):
        if socket in self.input_socket:
            self.input_socket.remove(socket)
        elif socket in self.output_socket:
            self.output_socket.remove(socket)
        self.scene().removeItem(socket)
        self.update_node()

    def validate(self):
        for socket in self.input_socket:
            if socket.required and len(socket.edges) == 0:
                self.status = "ERROR"
                error_msg = f"节点[{socket.parentItem().title}]的必要端口：[{socket.name}]未连接"
                print(error_msg)
                self.log(error_msg)
                socket.has_error = True
                self.update_socket_positions()
                self.update()
                return False

        for widget, socket in self.widget_socket.items():
            if hasattr(widget, "required"):
                if widget.required and socket:
                    if not widget.value() and not socket.edges:
                        self.status = "ERROR"
                        error_msg = f"节点[{socket.parentItem().title}]的必要参数：[{widget.name}]未输入"
                        print(error_msg)
                        self.log(error_msg)
                        socket.has_error = True
                        self.update_socket_positions()
                        self.update()
                        return False

        if self.status == "ERROR":
            self.status = "IDLE"
            self.update_socket_positions()
            self.update()
        return True

    def get_socket_by_name(self, name, is_input=True):
        """通过端口名称获取端口"""
        socket_list = self.input_socket if is_input else self.output_socket
        for socket in socket_list:
            if socket.name == name:
                return socket
        return None

    def get_socket_by_sequence(self, sequence):
        """通过控件排列顺序获取端口"""
        if sequence < len(list(self.widget_socket.values())):
            return list(self.widget_socket.values())[sequence]
        return None

    def get_input_val(self, index):
        """获取输入值"""
        if isinstance(index, str):
            socket = self.get_socket_by_name(index, is_input=True)
        else:
            socket = self.get_socket_by_sequence(index)

        if socket:
            if not socket.edges:
                return None
        else:
            return None

        edge = socket.edges[0]
        prev_socket = edge.start_socket
        prev_node = prev_socket.parentItem()
        prev_socket_index = prev_node.output_socket.index(prev_socket)
        socket_input = prev_node.output_data.get(prev_socket_index, None)

        return socket_input

    def set_output_val(self, name, value):
        """设置输出值"""
        socket = self.get_socket_by_name(name, is_input=False)
        if socket:
            socket_index = self.output_socket.index(socket)
            self.output_data[socket_index] = value
            self.results[name] = value
            print(self.running_record)
        else:
            print(f"未找到{name}端口,值设置失败！")

    def log(self, message):
        full_msg = f"[{self.title}]{message}"
        self.log_generated.emit(full_msg)
        print(f"[{self.title}]{message}")

    def run_async_task(self, func, *args, **kwargs):
        self.set_state("RUNNING")
        loop = QEventLoop()
        worker = Worker(func, *args, **kwargs)

        result = {"data": None, "error": None}

        def on_finished(data):
            result["data"] = data
            loop.quit()

        def on_error(err_msg):
            result["error"] = err_msg
            loop.quit()

        worker.finished_signal.connect(on_finished)
        worker.error_signal.connect(on_error)

        worker.start()
        loop.exec()

        if result["error"]:
            print(f"{self.title}异步执行出错:{result['error']}")
            self.log(f"{self.title}异步执行出错:{result['error']}")
            self.set_state("ERROR")
            return None
        self.set_state("IDLE")
        return result["data"]

    def logic(self):
        return NotImplementedError("每个节点必须实现compute方法")

    def compute(self):
        try:
            self.set_state("RUNNING")
            self.logic()
            # self.logic_completed.emit()
            self.set_state("IDLE")
            print(f"节点：{self.title}执行完毕, 返回：{list(self.output_data.values())}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.log(f"[error]{e}")
            print(e)

    def serialize(self):
        width = self.expanded_width if self.is_collapsed else self.width
        height = self.expanded_height if self.is_collapsed else self.height

        return {
            "title": self.title,
            "type": self.__class__.__name__,
            "idx": self.idx,
            "inputs": self.get_widget_input(),
            "symbiont": self.symbiont_nodes,
            "geometry": [self.scenePos().x(), self.scenePos().y(), width, height],
            "is_collapsed": self.is_collapsed
        }

    def deserialize(self, data):
        self.title = data.get("title", self.title)
        self.idx = data["idx"]
        self.set_widget_input(data["inputs"])
        self.symbiont_nodes = data.get("symbiont", [])

        if data.get("geometry", None):
            self.setPos(data["geometry"][0], data["geometry"][1])
            self.width, self.height = data["geometry"][2], data["geometry"][3]
            self.expanded_width, self.expanded_height = self.width, self.height

        self.is_collapsed = data.get("is_collapsed", False)
        if self.is_collapsed:
            self.widget_proxy.hide()
            all_inputs = [s for s in self.input_socket if s is not None] + [s for s in self.widget_socket.values() if s is not None]
            max_sockets = max(len(all_inputs), len(self.output_socket))
            self.height = max(40, max_sockets * 14 + SOCKET_RADIUS)

        self.update_node()

    def calculate_hash(self):
        if self.always_update:
            import time
            self.current_hash = hashlib.md5(str(time.time()).encode('utf-8')).hexdigest()
            return self.current_hash

        params = self.get_widget_input()

        upstream_hashes = []
        for socket in self.input_socket + list(self.widget_socket.values()):
            if socket:
                if socket.edges:
                    prev_node = socket.edges[0].start_socket.parentItem()
                    upstream_hashes.append(getattr(prev_node, "current_hash", "None"))

        raw_string = f"{self.__class__.__name__}_{params}_{'_'.join(upstream_hashes)}"
        self.current_hash = hashlib.md5(raw_string.encode('utf-8')).hexdigest()
        return self.current_hash

    def get_widget_input(self):
        pass

    def set_widget_input(self, inputs):
        """加载工作流和创建影子节点时重写和调用"""
        pass

    def pre_execute(self, data=None):
        """运行开始前执行"""
        pass

    def post_execute(self, data):
        """运行结束后执行"""
        pass

    def get_geometry(self):
        return [self.x(), self.y(), self.width, self.height]


class NullNode(QGraphicsObject):
    def boundingRect(self):
        return QRectF

    def paint(self, painter: QPainter, option, widget: QWidget | None = ...):
        pass
