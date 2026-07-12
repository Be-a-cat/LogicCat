from PySide6.QtWidgets import (QGraphicsObject, QGraphicsPathItem, QGraphicsItem)
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QPainterPath, QBrush, QPen, QColor, QPolygonF

from nodes.conf import (
    SOCKET_RADIUS, EDGE_WIDTH, COLOR_SOCKET_BORDER, COLOR_SOCKET_BORDER_ERROR, NODE_DATA_TYPE_COLORS
)


class Socket(QGraphicsObject):
    """端口（节点上的小圆圈）"""
    def __init__(self, parent, socket_type='output', data_type='any', required=False, is_exec=False):
        super().__init__(parent)
        self.setCacheMode(QGraphicsObject.DeviceCoordinateCache)
        self.radius = SOCKET_RADIUS   # 端口半径
        self.name = ""
        self.socket_type = socket_type   # 端口类型（输入或输出）
        self.data_type = data_type
        self.required = required
        self.has_error = False

        self.is_exec = is_exec
        if self.is_exec:
            self.data_type = "exec"

        self.edges = []    # 记录连接的线

        data_types = NODE_DATA_TYPE_COLORS
        self.color = QColor(data_types.get(data_type, "#ffffff"))

    def add_edge(self, edge):
        self.edges.append(edge)

    def remove_edge(self, edge):
        if edge in self.edges:
            self.edges.remove(edge)

    def remove_all_edges(self):
        self.edges.clear()

    def update_socket(self, name, data_type):
        self.name = name
        self.data_type = data_type
        data_types = NODE_DATA_TYPE_COLORS

        self.color = QColor(data_types.get(data_type, "#ffffff"))

        for edge in self.edges:
            if edge.start_socket.data_type != edge.end_socket.data_type and edge.start_socket.data_type != "any" and edge.end_socket.data_type != "any":
                edge.scene().removeItem(edge)
                edge.start_socket.remove_edge(edge)
                edge.end_socket.remove_edge(edge)
                edge.end_socket.parentItem().on_input_disconnected(edge.end_socket)
            edge.pen = QPen(self.color, EDGE_WIDTH)
            edge.setPen(edge.pen)

        self.update()

    def boundingRect(self):
        size = self.radius * 2
        return QRectF(-size/2 - 2, -size/2 - 2, size + 4, size + 4)

    def paint(self, painter, option, widget=None):
        if self.is_exec:
            painter.setBrush(QBrush(self.color))
            painter.setPen(QPen(COLOR_SOCKET_BORDER, 1))
            painter.drawRect(int(-self.radius / 2), int(-self.radius), int(self.radius), int(self.radius * 2))

        else:
            painter.setBrush(QBrush(self.color))
            painter.setPen(QPen(COLOR_SOCKET_BORDER, 1))
            painter.drawEllipse(int(-self.radius), int(-self.radius), int(self.radius * 2), int(self.radius * 2))

            if self.has_error:
                painter.setPen(QPen(COLOR_SOCKET_BORDER_ERROR, 2))
                painter.setBrush(Qt.NoBrush)
                radius = self.radius + 2
                painter.drawEllipse(int(-radius), int(-radius), int(radius * 2), int(radius * 2))


class Edge(QGraphicsPathItem):
    """连接线"""
    def __init__(self, start_socket, end_socket, parent=None):
        super().__init__(parent)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        self.start_socket = start_socket
        self.end_socket = end_socket

        self.setZValue(-1)  # 设置为最底层

        line_color = self.start_socket.color
        self.pen = QPen(line_color, EDGE_WIDTH)   # 设置线的颜色和宽度为灰色，2像素

        self.setPen(self.pen)

    def update_path(self):
        path = QPainterPath()   # 创建路径对象
        start_pos = self.start_socket.scenePos()    # 获取起点的绝对位置
        end_pos = self.end_socket.scenePos()    # 获取终点的绝对位置
        path.moveTo(start_pos)

        dx = end_pos.x() - start_pos.x()
        ctrl1 = QPointF(start_pos.x() + dx * 0.5, start_pos.y())
        ctrl2 = QPointF(end_pos.x() - dx * 0.5, end_pos.y())

        path.cubicTo(ctrl1, ctrl2, end_pos)
        self.setPath(path)

    def __repr__(self):
        return f"<{self.__class__.__name__}->start_socket:{self.start_socket.name}, end_socket:{self.end_socket.name}>"
