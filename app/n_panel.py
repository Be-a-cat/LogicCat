from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QFrame, QScrollArea
from PySide6.QtCore import Qt, QRect, QEvent
from app.base_widgets import LayoutWidget, VerticalPushButton
from nodes.registry import PLUGIN_CONFIGS


class NPanel(QWidget):
    def __init__(self, parent_view):
        super().__init__(parent_view)
        self.view = parent_view

        self.is_expanded = False
        self.active_plugin_name = None
        self.buttons = []

        self.setStyleSheet("""
            QFrame {color: #e5e5e5; background-color: #303030; border: 1px solid #1e1f22;}
            QPushButton {color: #e5e5e5; background-color: #303030; border: 1px solid #1e1f22;}
            QPushButton:hover {background-color: #656565;}
            QPushButton:pressed {background-color: #797979;}
            QLineEdit {background-color: #545454;}
            QPlainTextEdit {color: #e5e5e5; background-color: #1e1e1e; border: 1px solid #1e1f22;}
        """)

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.container = QFrame()
        self.container.setObjectName("container_widget")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(10, 10, 10, 10)

        self.container_scroll = QScrollArea()
        self.container_scroll.setWidgetResizable(True)
        self.container_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.container_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.container_scroll.setStyleSheet("""
            QScrollArea {border: none; background: transparent;}
            QScrollBar:vertical {width: 5px; background: transparent; margin: 0px;}
            QScrollBar::handle:vertical {background: #555; border-radius:3px; min-height: 20px;}
            QScrollBar::handle:vertical:hover {background: #777;}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {height: 0px;}
        """)

        self.stacked_widget = QStackedWidget()
        self.container_scroll.setWidget(self.stacked_widget)
        self.container_layout.addWidget(self.container_scroll)
        self.container.setFixedWidth(250)
        self.container.hide()

        self.tabs_scroll = QScrollArea()
        self.tabs_scroll.setWidgetResizable(True)
        self.tabs_scroll.setFixedWidth(25)

        self.tabs_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tabs_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.tabs_scroll.setStyleSheet("border: none; background: transparent;")

        self.tabs_widget = QWidget()
        self.tabs_layout = QVBoxLayout(self.tabs_widget)
        self.tabs_layout.setContentsMargins(0, 0, 0, 0)
        self.tabs_layout.setSpacing(2)
        self.tabs_layout.addStretch()

        self.tabs_scroll.setWidget(self.tabs_widget)

        self.main_layout.addWidget(self.container)
        self.main_layout.addWidget(self.tabs_scroll)

        self.load_plugin_panels()

        self.view.installEventFilter(self)
        self.adjust_position()

    def load_plugin_panels(self):
        for idx, (plugin_name, info) in enumerate(PLUGIN_CONFIGS.items()):
            btn = VerticalPushButton(info["title"])
            btn.setCheckable(True)
            btn.setFixedWidth(25)
            btn.setToolTip(info["title"])
            btn.setProperty("plugin_index", idx)
            btn.setProperty("plugin_name", plugin_name)
            btn.clicked.connect(self.on_tab_clicked)
            btn.setProperty("class", "tab_btn")
            btn.setCursor(Qt.PointingHandCursor)

            self.tabs_layout.insertWidget(self.tabs_layout.count() - 1, btn)
            self.buttons.append(btn)

            panel_widget = info["class"](self)
            self.stacked_widget.addWidget(panel_widget)

        if not PLUGIN_CONFIGS:
            self.hide()

    def on_tab_clicked(self):
        sender = self.sender()
        idx = sender.property("plugin_index")
        plugin_name = sender.property("plugin_name")

        if self.is_expanded and getattr(self, "active_plugin_name", None) == plugin_name:
            self.container.hide()
            self.is_expanded = False
            self.active_plugin_name = None
            sender.setChecked(False)
        else:
            for btn in self.buttons:
                btn.setChecked(btn == sender)
            self.stacked_widget.setCurrentIndex(idx)
            self.container.show()
            self.is_expanded = True
            self.active_plugin_name = plugin_name

        self.adjust_position()

    def adjust_position(self):
        view_width = self.view.width()
        view_height = self.view.height()

        self.setFixedHeight(view_height - 40)
        width = 25 + (250 if self.is_expanded else 0)
        self.setFixedWidth(width)
        self.move(view_width - width - 10, 20)

    def eventFilter(self, obj, event):
        if obj == self.view and event.type() == QEvent.Resize:
            self.adjust_position()
        return super().eventFilter(obj, event)
