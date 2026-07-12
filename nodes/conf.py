from PySide6.QtGui import QColor

# 节点的尺寸配置
GRID_SIZE = 20

NODE_WIDTH = 150            # 节点默认宽度
NODE_HEIGHT = 50            # 节点默认高度
NODE_RADIUS = 0             # 节点圆角半径
NODE_BORDER = 2             # 节点边框宽度
NODE_TITLE_HEIGHT = 25      # 节点标题栏高度
NODE_PADDING = 10           # 节点内部控件与边框的间距
SOCKET_RADIUS = 6.0         # 端口半径
SOCKET_SPACING = 20         # 端口间距
SOCkET_ADSORPTION_RING_COLOR = QColor("#ffffff")
SOCkET_ADSORPTION_RING_BORDER = 2
SOCkET_ADSORPTION_RING_PADDING = 4
EDGE_WIDTH = 3              # 连线宽度

# 节点和连线的颜色配置
COLOR_BACKGROUND = QColor("#1e1e1e")                # 场景背景颜色
COLOR_GRID = QColor("#1d1d1d")                      # 网格颜色
COLOR_GRID_MINOR = QColor("#303030")
COLOR_GRID_MAJOR = QColor("#3d3d3d")

COLOR_NODE_BACKGROUND = QColor("#303030")           # 节点背景颜色
COLOR_NODE_BORDER = QColor("#424242")               # 节点边框颜色
COLOR_NODE_FETCHING = QColor("#ffffff")
COLOR_NODE_RUNNING = QColor("#5ecc3e")
COLOR_NODE_ERROR = QColor("#bd2c1e")
COLOR_NODE_SELECTED = QColor("#FFA500")             # 节点选中时边框颜色
COLOR_NODE_SYMBIONT = QColor(255, 165, 0, 64)
COLOR_SOCKET_BORDER = QColor("#424242")
COLOR_SOCKET_BORDER_ERROR = QColor("#bd2c1e")
COLOR_EDGE_DRAG = QColor("#303030")                 # 拖拽时线的颜色

NODE_SOCKET_TYPE_COLORS = {
    "input": "#82354c",
    "math": "#246283",
    "string": "#6bad5e",
    "image": "#648dbd",
    "conditional": "#be588e",
    "other": "#1b1b1b"
}

NODE_DATA_TYPE_COLORS = {
    "exec": "#00d6a3",
    "value": "#a1a1a1",
    "string": "#9bfa88",
    "bool": "#cca6d6",
    "image": "#7fb4f0",
    "color": "#c7c729",
    "pipe": "#b19fd7",
    "any": "#333333",
    "error": "#771111"
}
