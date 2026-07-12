from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QLineEdit, QListWidget, QComboBox, QToolBar, QDockWidget,
                               QStackedWidget, QDialog, QMessageBox, QMenu, QFileSystemModel, QFileIconProvider,
                               QStyledItemDelegate, QStyle, QTreeWidget, QTreeWidgetItem, QTreeView, QListView, QSplitter, QScrollArea)
from PySide6.QtCore import Qt, QDir, QRect, QSize, QStandardPaths, QObject, Signal, QThreadPool, QRunnable
from PySide6.QtGui import QAction, QKeySequence, QIcon, QPixmap, QColor, QImage, QPainter

from app.base_widgets import (PushButton, TextEdit, PlainTextEdit, ListWidget, LayoutWidget, InputBox, MultiLineInputBox, PathSelectionBox,
                              ApiKeyInputBox, ImagePreviewerWidget)

from nodes.registry import NODE_REGISTRY
from nodes.scene import NodeScene, NodeGraphView

from utils.config_manager import global_config
from nodes.helpers import read_image_with_metadata

import os


class LogicCatUI(object):
    def __init__(self, main_window, app):
        super().__init__()
        self.app = app
        self._width, self._height = 1200, 800

        self.main_window = main_window
        self.main_window .setWindowTitle("逻辑猫")
        screen = self.app.primaryScreen()
        screen_geometry = screen.geometry()
        screenwidth = screen_geometry.width()
        screenheight = screen_geometry.height()
        self.main_window.setGeometry(screenwidth // 2 - self._width / 2, screenheight // 2 - self._height / 2, self._width, self._height)

        widget = LayoutWidget(self.main_window, direction="V", margins=(0, 0, 0, 0))
        self.main_window.setCentralWidget(widget)
        self.scene = NodeScene()
        self.scene.setSceneRect(-6400, -6400, 12800, 12800)
        self.view = NodeGraphView(self.scene)
        widget.add_widgets([self.view])

        self.menubar = MenuBar(self.main_window)
        self.statusbar = StatusBar(self.main_window)
        self.toolbar = ToolBar(self.main_window)
        self.drawer_panel = DrawerPanel("属性", self.main_window)

        self.bottom_panel = BottomPanel(self.main_window)

        self.outliner_panel = OutlinerPanel(self.main_window, self.scene, self.view)
        self.scene.selectionChanged.connect(self.outliner_panel.sync_selection_from_scene)
        self.scene.selectionChanged.connect(self.outliner_panel.refresh)
        self.view.node_adjusted.connect(self.outliner_panel.refresh)


class MenuBar:
    def __init__(self, main_window):
        self.main_window = main_window
        self.menubar = self.main_window.menuBar()
        self.menubar.setStyleSheet("color: #e5e5e5; background: #303030; border: 1px solid #1e1f22;")

        menu_file = QMenu("文件", self.main_window)
        self.menubar.addMenu(menu_file)

        self.action_save = QAction("保存", self.main_window)
        self.action_save.setShortcut(QKeySequence.Save)
        menu_file.addAction(self.action_save)

        self.action_save_as = QAction("另保存", self.main_window)
        self.action_save_as.setShortcut("Ctrl+Shift+S")
        menu_file.addAction(self.action_save_as)

        self.action_open = QAction("打开", self.main_window)
        self.action_open.setShortcut(QKeySequence.Open)
        menu_file.addAction(self.action_open)

        self.action_open_last = QAction("最后一次会话", self.main_window)
        self.action_open_last.setShortcut("Ctrl+Shift+O")
        menu_file.addAction(self.action_open_last)

        menu_edit = QMenu("编辑", self.main_window)
        self.menubar.addMenu(menu_edit)

        self.action_setting = QAction("设置", self.main_window)
        self.action_setting.setShortcut("F1")
        menu_edit.addAction(self.action_setting)


class StatusBar:
    def __init__(self, main_window):
        self.main_window = main_window
        self.statusbar = self.main_window.statusBar()
        self.statusbar.setStyleSheet("color: #e5e5e5; background: #303030; border: 1px solid #1e1f22;")

        self.status_label = QLabel("就绪")
        self.statusbar.addWidget(self.status_label)

    def set_text(self, text):
        self.status_label.setText(text)


class ToolBar(QToolBar):
    def __init__(self, main_window, *, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.main_window.addToolBar(Qt.LeftToolBarArea, self)

        self.setFloatable(True)
        self.setMovable(False)
        self.setAllowedAreas(Qt.AllToolBarAreas)
        self.setStyleSheet("""
            QToolBar {color: #e5e5e5; background-color: #303030; border: 1px solid #1e1f22; border-radius: 5px; spacing: 5px; padding: 5px;}
            QLabel {color: #e5e5e5; background-color: #79a5f3; border: 1px solid #1e1f22; border-radius: 5px; min-width: 50px; max-width: 50px; min-height: 20px; max-height: 20px;}
            QPushButton {color: #e5e5e5; background-color: #545454; border: 1px solid #1e1f22; border-radius: 5px; min-width: 50px; max-width: 50px; min-height: 50px; max-height: 50px;}
            QPushButton:hover {background-color: #656565;}
            QPushButton:pressed {background-color: #797979;}
        """)

        self.label_queue_number = QLabel("0")
        self.label_queue_number.setAlignment(Qt.AlignCenter)

        self.btn_run = QPushButton("运行")
        self.btn_stop = QPushButton("停止")
        self.btn_properties = QPushButton("属性")
        self.btn_workflow = QPushButton("工作流")
        self.btn_versatile = QPushButton("多功能")

        self.addWidget(self.label_queue_number)
        self.addWidget(self.btn_run)
        self.addWidget(self.btn_stop)
        self.addWidget(self.btn_properties)
        self.addWidget(self.btn_workflow)
        self.addWidget(self.btn_versatile)


class BottomPanel(QDockWidget):
    def __init__(self, main_window, *, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.main_window.addDockWidget(Qt.BottomDockWidgetArea, self)
        self.main_window.resizeDocks([self], [170], Qt.Vertical)

        self.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)

        self.setStyleSheet("""
            QWidget {background-color: #303030; border: 1px solid #1e1f22; border-radius: 5px}
            QComboBox {background-color: #1e1e1e; padding-left: 5px;}
            QComboBox QAbstractItemView {background-color: #1e1e1e;}
        """)

        _widget = QWidget()
        _widget.setMaximumHeight(0)
        self.setTitleBarWidget(_widget)

        widget = LayoutWidget(direction="V", margins=(0, 0, 0, 0))
        title_widget = LayoutWidget(direction="H", margins=(5, 5, 0, 5))

        combo_panel = QComboBox()
        combo_panel.setFixedSize(150, 25)
        panel_list = ["Log", "AssetManager"]
        combo_panel.addItems(panel_list)
        combo_panel.currentIndexChanged.connect(lambda index=combo_panel.currentIndex(): self.stacked_widget.setCurrentIndex(index))

        title_widget.add_widgets([combo_panel, None])

        self.stacked_widget = QStackedWidget()
        self.log_panel = LogPanel()
        self.asset_panel = AssetManagerPanel()
        self.stacked_widget.addWidget(self.log_panel)
        self.stacked_widget.addWidget(self.asset_panel)

        widget.add_widgets([title_widget, self.stacked_widget])
        self.setWidget(widget)

    def visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()


class OutlinerPanel(QDockWidget):
    def __init__(self, main_window, scene, view, *, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.main_window.addDockWidget(Qt.RightDockWidgetArea, self)
        self.main_window.resizeDocks([self], [225], Qt.Horizontal)

        self.scene = scene
        self.view = view

        self.setStyleSheet("""
            QWidget {color: #e5e5e5; background-color: #303030; padding: 5px;}
            QTreeWidget {background-color: #3d3d3d; font-size: 12px;}
            QTreeWidget::item:alternate {background-color: #3d3d3d;}
            QTreeWidget::item {background-color: #303030;}
            QTreeWidget::item:hover {border: 1px solid #FFA500;}
            QTreeWidget::item:selected {border: 1px solid #FFA500;}
            QLabel {background-color: #3d3d3d; ; border: 1px solid #1e1f22;}
            QLineEdit {background-color: #545454; border-radius: 0px;}
        """)

        splitter = QSplitter(Qt.Orientation.Vertical)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QTreeWidget.ExtendedSelection)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.properties_area = LayoutWidget(direction="V", margins=(0, 5, 0, 5), spacing=5)

        self.properties_widgets = []

        tag_widget = 60
        self.input_box_title = InputBox(label_text="title", tag_width=tag_widget)
        self.input_box_class = InputBox(label_text="class", tag_width=tag_widget)
        self.input_box_idx = InputBox(label_text="idx", tag_width=tag_widget)
        self.properties_widgets.extend([self.input_box_title, self.input_box_class, self.input_box_idx])

        self.geometry_widget = {"X": None, "Y": None, "W": None, "H": None}
        for i in self.geometry_widget:
            self.geometry_widget[i] = InputBox(label_text=i, tag_width=tag_widget)
            self.properties_widgets.append(self.geometry_widget[i])

        self.properties_widgets.append(None)

        self.properties_area.add_widgets(self.properties_widgets)

        scroll.setWidget(self.properties_area)

        splitter.addWidget(self.tree)
        splitter.addWidget(scroll)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        self.setWidget(splitter)

        self.tree.itemSelectionChanged.connect(self.on_outliner_selection_changed)

    def update_properties(self, node=None):
        if node:
            self.input_box_title.set_text(node.title)
            self.input_box_class.set_text(type(node).__name__)
            self.input_box_idx.set_text(node.idx)

            for input_box, val in zip(self.geometry_widget.values(), node.get_geometry()):
                if isinstance(val, int):
                    input_box.set_text(str(val))
                else:
                    input_box.set_text(f"{val:.2f}")

        else:
            for widget in self.properties_widgets:
                if widget:
                    widget.clear()

    def refresh(self):
        self.tree.blockSignals(True)
        self.tree.clear()

        nodes = [item for item in self.scene.items() if hasattr(item, "idx")]
        nodes.sort(key=lambda n: n.title)

        for node in nodes:
            item = QTreeWidgetItem(self.tree)
            item.setText(0, node.title)
            item.setData(0, Qt.UserRole, node.idx)

            if node.isSelected():
                item.setSelected(True)

        self.tree.blockSignals(False)

    def sync_selection_from_scene(self):
        self.tree.blockSignals(True)
        self.tree.clearSelection()

        selected_ids = [item for item in self.scene.selectedItems() if hasattr(item, "idx")]

        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            node_idx = item.data(0, Qt.UserRole)
            if node_idx in selected_ids:
                item.setSelected(True)

        self.tree.blockSignals(False)

    def on_outliner_selection_changed(self):
        self.scene.blockSignals(True)
        self.scene.clearSelection()

        selection_items = self.tree.selectedItems()
        last_selected_node = None

        for item in selection_items:
            node_idx = item.data(0, Qt.UserRole)
            for scene_item in self.scene.items():
                if hasattr(scene_item, "idx") and scene_item.idx == node_idx:
                    scene_item.setSelected(True)
                    last_selected_node = scene_item
                    break

        self.scene.blockSignals(False)

        if last_selected_node:
            self.view.focus_node = last_selected_node
            self.update_properties(last_selected_node)


class DrawerPanel(QDockWidget):
    def __init__(self, title, main_window, *, parent=None):
        super().__init__(title, parent)
        self.main_window = main_window
        self.main_window.addDockWidget(Qt.LeftDockWidgetArea, self)
        self.hide()

        self.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("""
            QStackedWidget {color: #e5e5e5; background-color: #303030; border: 1px solid #1e1f22; border-radius: 5px;}
            QWidget {background-color: #3d3d3d;}
            QLineEdit {background-color: #545454;}
        """)

        self.widget_properties = LayoutWidget(direction="V", margins=(10, 10, 10, 10), spacing=5)

        self.properties_dock_widgets = []

        self.input_box_name = InputBox(label_text="name")
        self.input_box_class = InputBox(label_text="class")
        self.input_box_idx = InputBox(label_text="idx")
        self.properties_dock_widgets.extend([self.input_box_name, self.input_box_class, self.input_box_idx])

        self.geometry_widget = {"X": None, "Y": None, "W": None, "H": None}
        for i in self.geometry_widget:
            self.geometry_widget[i] = InputBox(label_text=i)
            self.properties_dock_widgets.append(self.geometry_widget[i])

        self.properties_edit = PlainTextEdit()
        self.properties_edit.setReadOnly(True)
        self.properties_dock_widgets.append(self.properties_edit)

        self.widget_properties.add_widgets(self.properties_dock_widgets)
        self.widget_properties.add_stretch()

        self.stacked_widget.addWidget(self.widget_properties)

        self.workflow_list = ListWidget()

        self.stacked_widget.addWidget(self.workflow_list)

        self.setWidget(self.stacked_widget)

    def toggle_side_panel(self, index):
        if self.isVisible():
            self.hide()
        else:
            self.stacked_widget.setCurrentIndex(index)
            self.show()

    def update_properties_panel(self, node=None):
        if node:
            self.input_box_name.set_text(node.title)
            self.input_box_class.set_text(type(node).__name__)
            self.input_box_idx.set_text(node.idx)

            for input_box, val in zip(self.geometry_widget.values(), node.get_geometry()):
                if isinstance(val, int):
                    input_box.set_text(str(val))
                else:
                    input_box.set_text(f"{val:.2f}")

            if node.results:
                output = "\n".join(str(result) for result in list(node.results.values()))
                self.properties_edit.setPlainText(output)
            else:
                self.properties_edit.setPlainText("没有返回值")

        else:
            for widget in self.properties_dock_widgets:
                widget.clear()

    def update_workflow_panel(self, workflow_list):
        self.workflow_list.clear()
        self.workflow_list.addItems(workflow_list)


class LogPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QWidget {color: #e5e5e5; background-color: #303030; border: 1px solid #1e1f22;}
            QPushButton {color: #e5e5e5; background-color: #303030;}
            QPushButton:hover {background-color: #656565;}
            QPushButton:pressed {background-color: #797979;}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        bar_widget = QWidget()
        bar_widget.setFixedWidth(40)
        bar_layout = QVBoxLayout(bar_widget)
        bar_layout.setContentsMargins(5, 5, 5, 5)
        bar_layout.setSpacing(5)

        btn_log = PushButton("日志")
        btn_log.setToolTip("运行日志")

        btn_history = PushButton("历史")
        btn_history.setToolTip("历史步骤")

        bar_layout.addWidget(btn_log)
        bar_layout.addWidget(btn_history)
        bar_layout.addStretch()

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setMinimumHeight(100)

        self.log_text = TextEdit()
        self.log_text.setReadOnly(True)

        self.history_list = ListWidget(show_row_count=True)

        self.stacked_widget.addWidget(self.log_text)
        self.stacked_widget.addWidget(self.history_list)

        btn_log.clicked.connect(lambda: self.switch_page(0, "运行日志"))
        btn_history.clicked.connect(lambda: self.switch_page(1, "历史步骤"))

        layout.addWidget(bar_widget)
        layout.addWidget(self.stacked_widget)

    def switch_page(self, index, title):
        self.stacked_widget.setCurrentIndex(index)
        self.setWindowTitle(title)

    def append_msg(self, msg):
        self.log_text.append(msg)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())


class IconModeDelegate(QStyledItemDelegate):
    ITEM_WIDGET = 90
    ITEM_HEIGHT = 120
    ICON_SIZE = QSize(84, 84)
    ICON_AREA_HEIGHT = 84
    PADDING_TOP = 8
    TEXT_HEIGHT = 20

    def __init__(self, parent=None, manager=None):
        super().__init__(parent)
        self.manager = manager

    def itemSize(self, _):
        return QSize(self.ITEM_WIDGET, self.ITEM_HEIGHT)

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRect(option.rect)
        rect.adjust(0, 0, -1, -1)

        painter.setPen(Qt.PenStyle.NoPen)
        if option.state & QStyle.StateFlag.State_Selected:
            painter.setBrush(QColor(0, 120, 215, 50))
            painter.drawRect(rect)
        elif option.state & QStyle.StateFlag.State_MouseOver:
            painter.setBrush(QColor(0, 0, 0, 15))
            painter.drawRect(rect)

        icon_x = rect.left() + (rect.width() - self.ICON_SIZE.width()) // 2
        icon_y = rect.top() + self.PADDING_TOP
        icon_rect = QRect(icon_x, icon_y, self.ICON_SIZE.width(), self.ICON_SIZE.height())

        model = index.model()
        path = ""
        if hasattr(model, "filePath"):
            path = model.filePath(index)

        icon = None
        if self.manager and path and path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp')):
            icon = self.manager.get_icon(path)

        if not icon:
            data = index.data(Qt.ItemDataRole.DecorationRole)
            icon = data if isinstance(data, QIcon) else QIcon()

        actual_size = icon.actualSize(self.ICON_SIZE)
        raw = icon.pixmap(actual_size)

        if not raw.isNull():
            draw_size = raw.size()
            if draw_size.width() > self.ICON_SIZE.width() or draw_size.height() > self.ICON_SIZE.height():
                draw_size = draw_size.scaled(self.ICON_SIZE, Qt.AspectRatioMode.KeepAspectRatio)
            ox = (self.ICON_SIZE.width() - draw_size.width()) // 2
            oy = (self.ICON_SIZE.height() - draw_size.height()) // 2

            painter.drawPixmap(icon_rect.left() + ox, icon_rect.top() + oy, draw_size.width(), draw_size.height(), raw)

        text = index.data(Qt.ItemDataRole.DisplayRole)
        if text:
            text_rect = QRect(rect.left(), icon_y + self.ICON_AREA_HEIGHT, rect.width(), self.TEXT_HEIGHT + 6)
            painter.setPen(Qt.GlobalColor.white)
            painter.setFont(option.font)
            self._draw_fitted_text(painter, text, text_rect, option)

        painter.restore()

    def _draw_fitted_text(self, painter, text, rect, option):
        font = painter.font()
        fs = font.pointSize()
        for size in range(fs, 6, -1):
            f = font
            f.setPointSize(size)
            painter.setFont(f)
            fm = option.fontMetrics
            elided = fm.elidedText(text, Qt.TextElideMode.ElideRight, rect.width() - 4)
            if fm.boundingRect(elided).width() <= rect.width() - 4:
                painter.drawText(rect, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, elided)
                return
        painter.drawText(rect, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, text)

    def sizeHint(self, option, index):
        return QSize(self.ITEM_WIDGET, self.ITEM_HEIGHT)


class ThumbnailManager(QObject):
    ready = Signal(str)
    cache = {}
    loading = set()

    def __init__(self, icon_size=QSize(64, 64)):
        super().__init__()
        self.icon_size = icon_size
        self.pool = QThreadPool.globalInstance()

    def get_icon(self, path):
        path = os.path.normpath(path)
        if path in self.cache:
            item = self.cache[path]
            if isinstance(item, QImage):
                icon = QIcon(QPixmap.fromImage(item))
                self.cache[path] = icon
                return icon
            return item

        if path not in self.loading:
            self.loading.add(path)
            self.pool.start(self.Loader(path, self.icon_size, self))
        return None

    class Loader(QRunnable):
        def __init__(self, path, size, manager):
            super().__init__()
            self.path, self.size, self.manager = path, size, manager

        def run(self):
            try:
                img = QImage(self.path)
                if not img.isNull():
                    scaled = img.scaled(self.size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    ThumbnailManager.cache[self.path] = scaled
                    self.manager.ready.emit(self.path)
            except Exception:
                pass
            finally:
                ThumbnailManager.loading.discard(self.path)


class AsyncIconProvider(QFileIconProvider):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    def icon(self, file_info):
        path = file_info.absoluteFilePath()
        if file_info.suffix().lower() in ['jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp']:
            icon = self.manager.get_icon(path)
            if icon:
                return icon
        return super().icon(file_info)


class AssetManagerPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QWidget {color: #e5e5e5; background-color: #303030; border: 1px solid #1e1f22;}
            QPushButton {color: #e5e5e5; background-color: #303030;}
            QPushButton:hover {background-color: #656565;}
            QPushButton:pressed {background-color: #797979;}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.thumb_manager = ThumbnailManager(IconModeDelegate.ICON_SIZE)
        self.thumb_manager.ready.connect(self.on_thumbnail_ready)

        root_path = global_config.get("paths", "dirs", "root")

        self.model = QFileSystemModel()
        self.model.setRootPath(root_path)

        self.provider = AsyncIconProvider(self.thumb_manager)
        self.model.setIconProvider(self.provider)

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        for col in range(1, self.model.columnCount()):
            self.tree.hideColumn(col)
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(10)

        self.list = QListView()
        self.list.setModel(self.model)
        self.list.setViewMode(QListView.IconMode)
        self.list.setMovement(QListView.Snap)

        self.delegate = IconModeDelegate(self.list, self.thumb_manager)
        self.list.setItemDelegate(self.delegate)

        self.list.setSpacing(0)

        self.list.setIconSize(IconModeDelegate.ICON_SIZE)
        self.list.setGridSize(QSize(IconModeDelegate.ITEM_WIDGET, IconModeDelegate.ITEM_HEIGHT))

        self.list.setResizeMode(QListView.ResizeMode.Adjust)
        self.list.setWordWrap(False)
        self.list.setUniformItemSizes(True)

        self.tree.selectionModel().currentChanged.connect(self.on_tree_selection_changed)
        self.list.doubleClicked.connect(self.on_list_double_clicked)

        tree_area = LayoutWidget(direction="V", margins=(0, 0, 0, 0), spacing=0)

        btn_area = LayoutWidget(direction="H", margins=(0, 0, 0, 0), spacing=0)
        self.btn_computer = PushButton("磁盘")
        self.btn_computer.clicked.connect(lambda: self.set_root_path(path=None))
        self.btn_desktop = PushButton("桌面")
        self.btn_desktop.clicked.connect(lambda: self.set_root_path(path="desktop"))
        self.btn_root = PushButton("根目录")
        self.btn_root.clicked.connect(lambda: self.set_root_path(path="root"))
        self.btn_refresh = PushButton("刷新")
        self.btn_refresh.clicked.connect(self.refresh)

        btn_area.add_widgets([self.btn_computer, self.btn_desktop, self.btn_root, self.btn_refresh])

        tree_area.add_widgets([btn_area, self.tree])

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(tree_area)
        splitter.addWidget(self.list)
        splitter.setSizes([100, 900])

        layout.addWidget(splitter)

        root_index = self.model.index(root_path)

        self.tree.setRootIndex(root_index)
        self.list.setRootIndex(root_index)

    def on_thumbnail_ready(self, path):
        idx = self.model.index(QDir.toNativeSeparators(path))
        if idx.isValid():
            self.model.dataChanged.emit(idx, idx, [Qt.ItemDataRole.DecorationRole])

        self.list.viewport().update()
        self.tree.viewport().update()

    def on_tree_selection_changed(self, current, _):
        if current.isValid() and self.model.isDir(current):
            self.list.setRootIndex(current)

    def on_list_double_clicked(self, index):
        path = self.model.filePath(index)
        if self.model.isDir(index):
            self.list.setRootIndex(index)
            self.tree.setCurrentIndex(index)
        elif path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp')):
            _, metadata = read_image_with_metadata(path)
            positive_prompt = metadata.get("positive", "")
            negative_prompt = metadata.get("negative", "")

            self.image_previewer_window = ImagePreviewerWindow(path, positive_prompt, negative_prompt)
            self.image_previewer_window.show()

    def refresh(self):
        current = self.model.rootPath()
        self.model.setRootPath("")
        self.model.setRootPath(current)

    def set_root_path(self, path=None):
        if path is None:
            root_path = ""
        elif path == "desktop":
            root_path = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)
        elif path == "root":
            root_path = global_config.get("paths", "dirs", "root")
        else:
            root_path = os.path.abspath(path)
            if not os.path.exists(root_path):
                print("路径不存在")
                return

        self.model.setRootPath(root_path)
        root_index = self.model.index(root_path)
        self.tree.setRootIndex(root_index)
        self.list.setRootIndex(root_index)


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setFixedSize(800, 600)
        self.setStyleSheet("""
            QDialog {color: #e5e5e5; background-color: #303030; border: 1px solid #1e1f22;}
            QLabel {color: #e5e5e5; background-color: #303030; border: 1px solid #1e1f22;}
            QPushButton {color: #e5e5e5; background-color: #303030; border: 1px solid #545454; border-radius: 5px;}
            QPushButton:hover {background-color: #656565;}
            QPushButton:pressed {background-color: #797979;}
            QLineEdit {color: #e5e5e5; background-color: #1e1e1e; border: 1px solid #1e1f22;}
            QListWidget {color: #e5e5e5; background-color: #303030; border: 1px solid #1e1f22;}
            QListWidget::item {border-bottom: 1px solid #1e1f22; height: 30px;}
            QListWidget::item:selected {background-color: #545454;}
            QStackedWidget {border: 1px solid #1e1f22;}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(0)

        self.nav_list = ListWidget()
        self.nav_list.setFixedWidth(150)
        self.nav_list.addItems(["系统", "路径", "API密钥"])

        settings_area = LayoutWidget(direction="H", margins=(0, 0, 0, 0), spacing=5)

        self.stack = QStackedWidget()
        page_system = LayoutWidget(direction="V", spacing=5)
        self.stack.addWidget(page_system)

        page_paths = LayoutWidget(direction="V", margins=(5, 5, 5, 5), spacing=5)
        self.llm_models_dir_selection_box = PathSelectionBox("LLM模型", global_config.get("paths", "dirs", "llm_models"))
        self.sd_models_dir_selection_box = PathSelectionBox("SD模型", global_config.get("paths", "dirs", "sd_models"))
        self.image_save_dir_selection_box = PathSelectionBox("图片保存", global_config.get("paths", "dirs", "image_save"))

        page_paths.add_widgets([self.llm_models_dir_selection_box, self.sd_models_dir_selection_box, self.image_save_dir_selection_box])
        page_paths.add_stretch()
        self.stack.addWidget(page_paths)

        page_apikey = LayoutWidget(direction="V", margins=(5, 5, 5, 5), spacing=5)
        self.free_chatgpt_api_input_box = ApiKeyInputBox("ChatGPT-free", "https://github.com/popjane/free_chatgpt_api")
        self.free_chatgpt_api_input_box.set_text(global_config.get("apikey", "free_chatgpt"))
        self.modelscope_api_input_box = ApiKeyInputBox("ModelScope", "https://www.modelscope.cn/my/overview")
        self.modelscope_api_input_box.set_text(global_config.get("apikey", "modelscope"))
        self.baidu_translate_api_input_box = ApiKeyInputBox("百度翻译", "https://fanyi-api.baidu.com/?ext_channel=DuSearch&fr=pcHeader")
        self.baidu_translate_api_input_box.set_text(global_config.get("apikey", "baidu_translate"))

        page_apikey.add_widgets([self.free_chatgpt_api_input_box, self.modelscope_api_input_box, self.baidu_translate_api_input_box])
        page_apikey.add_stretch()
        self.stack.addWidget(page_apikey)

        settings_area.add_widgets([self.nav_list, self.stack])

        btn_area = LayoutWidget(direction="H", margins=(5, 5, 5, 5), spacing=5, height=30)
        btn_area.add_stretch()

        btn_save_settings = PushButton("保存", width=70)
        btn_save_settings.clicked.connect(self.save_settings)

        btn_area.add_widgets([btn_save_settings])

        layout.addWidget(settings_area)
        layout.addWidget(btn_area)

        self.nav_list.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.nav_list.setCurrentRow(0)

    def save_settings(self):
        reply = QMessageBox.question(self, "确认", "确认保存设置？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            global_config.set("paths", "dirs", "llm_models", value=self.llm_models_dir_selection_box.get_text())
            global_config.set("paths", "dirs", "sd_models", value=self.sd_models_dir_selection_box.get_text())
            global_config.set("paths", "dirs", "images_save", value=self.image_save_dir_selection_box.get_text())

            global_config.set("apikey", "free_chatgpt", value=self.free_chatgpt_api_input_box.get_text())
            global_config.set("apikey", "modelscope", value=self.modelscope_api_input_box.get_text())
            global_config.set("apikey", "baidu_translate", value=self.baidu_translate_api_input_box.get_text())
            print("保存成功！")
            pass


class ImagePreviewerWindow(QWidget):
    def __init__(self, image_path, positive_prompt="", negative_prompt="", parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.image, self.pixmap, self.image_width, self.image_height = None, None, None, None

        self.setStyleSheet("""
            QWidget {color: #e5e5e5; background-color: #303030; border: 1px solid #1e1f22;}
            QLabel {color: #e5e5e5; background-color: #303030; border: 1px solid #1e1f22;}
            QPlainTextEdit {color: #e5e5e5; background-color: #1e1e1e; border: 1px solid #1e1f22;}
        """)

        self.resize(800, 600)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        data_area = LayoutWidget(direction="V", margins=(0, 0, 0, 0), spacing=10)

        self.text_positive_prompt = MultiLineInputBox(label_text="正向提示词", height=200)
        self.text_positive_prompt.set_text(positive_prompt)
        self.text_negative_prompt = MultiLineInputBox(label_text="反向提示词", height=200)
        self.text_negative_prompt.set_text(negative_prompt)

        data_area.add_widgets([self.text_positive_prompt, self.text_negative_prompt, None])

        self.image_previewer_widget = ImagePreviewerWidget(image_path=image_path)

        if self.text_positive_prompt.get_text() or self.text_negative_prompt.get_text():
            splitter.addWidget(data_area)

        splitter.addWidget(self.image_previewer_widget)

        splitter.setSizes([400, 400])

        layout.addWidget(splitter)


class SearchBox(QWidget):
    def __init__(self, parent=None, callback=None):
        super().__init__(parent, Qt.Popup)
        self.callback = callback
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.input = QLineEdit()
        self.input.setPlaceholderText("搜索节点...")
        self.input.textChanged.connect(self.update_list)
        self.input.returnPressed.connect(self.confirm)

        self.list = QListWidget()
        self.list.itemClicked.connect(self.confirm)

        layout.addWidget(self.input)
        layout.addWidget(self.list)

        self.update_list("")

    def update_list(self, text):
        self.list.clear()
        for name, data in NODE_REGISTRY.items():
            title = data['title']
            if text.lower() in title.lower():
                self.list.addItem(title)

    def confirm(self, item=None):
        if not item:
            if self.list.count() > 0:
                item = self.list.item(0)
            else:
                return

        title = item.text() if hasattr(item, 'text') else self.list.currentItem().text()

        for name, data in NODE_REGISTRY.items():
            if data['title'] == title:
                self.callback(data['class'])
                self.close()
                break
