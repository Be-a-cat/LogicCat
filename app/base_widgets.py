from PySide6.QtWidgets import (QWidget, QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit, QPlainTextEdit, QComboBox,
                               QListWidget, QToolBar, QDockWidget, QStackedWidget, QStyleOptionViewItem, QFileDialog)
from PySide6.QtCore import Qt, QRect, QPointF, QSize
from PySide6.QtGui import QAction, QKeySequence, QCursor, QPainter, QColor, QPixmap, QFontMetrics, QPen, QGuiApplication


class Label(QLabel):
    def __init__(self, parent=None, *, text="", url="", align="", width=None, height=25):
        super().__init__(parent)
        if width:
            self.setFixedWidth(width)
        if height:
            self.setFixedHeight(height)
        if text:
            self.setText(text)
        if url:
            self.setOpenExternalLinks(True)
            self.setText(f"<a href={url}> {url} </a>")

        if align == "L":
            self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        elif align == "R":
            self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        else:
            self.setAlignment(Qt.AlignCenter)

    def set_text(self, text):
        self.setText(text)

    def set_url(self, url):
        self.setOpenExternalLinks(True)
        self.setText(f"<a href={url}> {url} </a>")


class PushButton(QPushButton):
    def __init__(self, text, parent=None, *, width=None, height=25):
        super().__init__(parent)
        if width:
            self.setFixedWidth(width)
        if height:
            self.setFixedHeight(height)
        self.setText(text)


class VerticalPushButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self._text = text
        self.setFixedWidth(25)
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.update_height()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.isChecked():
            bg_color = QColor("#4772b3")
        elif self.underMouse():
            bg_color = QColor("#656565")
        else:
            bg_color = QColor("#303030")
        painter.fillRect(self.rect(), bg_color)

        pen = QPen(QColor("#1e1f22"))
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

        painter.save()
        painter.setPen(QColor("#e5e5e5"))

        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(90)

        fm = QFontMetrics(self.font())
        text_height = fm.height()

        rect = QRect(
            -self.height() // 2,
            -text_height // 2,
            self.height(),
            text_height
        )

        painter.drawText(rect, Qt.AlignCenter, self._text)
        painter.restore()

    def setText(self, text):
        super().setText(text)
        self._text = text
        self.update_height()

    def update_height(self):
        fm = QFontMetrics(self.font())
        text_width = fm.horizontalAdvance(self._text)
        self.setFixedHeight(text_width + 20)


class TextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("""
           QTextEdit {
               color: #e5e5e5;
               background-color: #1e1e1e;
               border: 1px solid #1e1f22;
               font-family: Consolas;
               font-size: 12px;
               border: none;
           }
        """)


class PlainTextEdit(QPlainTextEdit):
    def __init__(self, parent=None, *, fixed_widget=None, fixed_height=150):
        super().__init__(parent)
        if fixed_widget:
            self.setFixedWidth(fixed_widget)
        if fixed_height:
            self.setFixedHeight(fixed_height)
        self.setReadOnly(True)
        self.setStyleSheet("""
           QPlainTextEdit {
               color: #e5e5e5;
               background-color: #2b2b2b;
               font-family: Consolas;
               font-size: 12px;
               border: none;
           }
        """)


class ListWidget(QListWidget):
    def __init__(self, *, parent=None, show_row_count=False):
        super().__init__(parent)
        self.show_row_count = show_row_count
        if self.show_row_count:
            self.setStyleSheet("""
                QListWidget {
                    color: #e5e5e5;
                }
                QListWidget::item {
                    padding-left: 20px;
                }
            """)
        else:
            self.setStyleSheet("""
                QListWidget {
                    color: #e5e5e5;
                }
            """)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.show_row_count:
            painter = QPainter(self.viewport())
            painter.setPen(QColor(128, 128, 128))
            for i in range(self.count()):
                item_rect = self.visualItemRect(self.item(i))
                if item_rect.isValid():
                    rect = QRect(2, item_rect.y(), 30, item_rect.height())
                    painter.drawText(rect, Qt.AlignLeft | Qt.AlignVCenter, f"[{str(i)}]:")


class DockWidget(QDockWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QWidget {color: #e5e5e5; background-color: #303030; border: 1px solid #1e1f22;}
            QPushButton {color: #e5e5e5; background-color: #303030;}
            QPushButton:hover {background-color: #656565;}
            QPushButton:pressed {background-color: #797979;}
        """)
        widget = LayoutWidget(direction="H", margins=(5, 0, 5, 0), spacing=0)
        widget.setStyleSheet("color: #e5e5e5; background-color: #303030; border: 1px solid #1e1f22;")
        self.setTitleBarWidget(widget)

        self.combo = QComboBox()
        self.combo.setFixedWidth(200)

        self.btn_close = PushButton("X")
        self.btn_close.setFixedWidth(25)
        self.btn_close.clicked.connect(self.close)

        widget.add_widgets([self.combo, None, self.btn_close])


class LayoutWidget(QWidget):
    def __init__(self, parent=None, *, width=None, height=None, direction="H", margins=(0, 0, 0, 0), spacing=0):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        if width:
            self.setFixedWidth(width)
        if height:
            self.setFixedHeight(height)
        self.layout = QVBoxLayout(self) if direction == "V" else QHBoxLayout(self)
        self.set_margins(margins)
        self.set_spacing(spacing)
        self.widgets = []

    def set_margins(self, margins):
        left, top, right, bottom = margins
        self.layout.setContentsMargins(left, top, right, bottom)

    def set_spacing(self, spacing):
        self.layout.setSpacing(spacing)

    def add_widget(self, widget):
        self.layout.addWidget(widget)
        self.widgets.append(widget)

    def add_widgets(self, widget_list):
        for widget in widget_list:
            if widget is None:
                self.layout.addStretch()
            else:
                self.layout.addWidget(widget)
                self.widgets.append(widget)

    def add_layout(self, layout):
        self.layout.addLayout(layout)

    def add_stretch(self):
        self.layout.addStretch()

    def get_widgets(self):
        return self.widgets


class InputBox(QWidget):
    def __init__(self, parent=None, *, label_text="", tag_width=50, width=None, height=25):
        super().__init__(parent)
        if width:
            self.setFixedWidth(width)
        if height:
            self.setFixedHeight(height)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.label = Label(text=label_text + " : ", align="R", width=tag_width, height=height)

        self.text_edit = QLineEdit()
        self.text_edit.setFixedHeight(height)

        layout.addWidget(self.label)
        layout.addWidget(self.text_edit)

    def set_label_text(self, text):
        self.label.setText(text)

    def set_text(self, text):
        self.text_edit.setText(text)

    def get_text(self):
        return self.text_edit.text()

    def clear(self):
        self.text_edit.clear()


class MultiLineInputBox(QWidget):
    def __init__(self, parent=None, *, label_text="", width=None, height=100):
        super().__init__(parent)
        if width:
            self.setFixedWidth(width)
        if height:
            self.setFixedHeight(height)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.label = Label(text=label_text, height=25)

        self.text_edit = QPlainTextEdit()
        self.text_edit.setFixedHeight(height - self.label.height())

        layout.addWidget(self.label)
        layout.addWidget(self.text_edit)

    def set_label_text(self, text):
        self.label.setText(text)

    def set_text(self, text):
        self.text_edit.setPlainText(text)

    def get_text(self):
        return self.text_edit.toPlainText()

    def clear(self):
        self.text_edit.clear()


class PathSelectionBox(QWidget):
    def __init__(self, label_text="path", select_type="dir", *, parent=None, width=None, height=30, tag_width=70, btn_width=50, direction="H"):
        super().__init__(parent)
        if width:
            self.setFixedWidth(width)
        if height:
            self.setFixedHeight(height)
        if direction == "V":
            layout = QVBoxLayout(self)
            self.input_box = MultiLineInputBox(label_text=label_text)
        else:
            layout = QHBoxLayout(self)
            self.input_box = InputBox(label_text=label_text, tag_width=tag_width)

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        self.btn_select_path = PushButton("选择")
        if select_type == "file":
            self.btn_select_path.clicked.connect(self.get_file_path)
        else:
            self.btn_select_path.clicked.connect(self.get_dir_path)
        if direction == "V":
            self.btn_select_path.setFixedHeight(25)
        else:
            self.btn_select_path.setFixedSize(btn_width, height)

        layout.addWidget(self.input_box)
        layout.addWidget(self.btn_select_path)

    def get_dir_path(self):
        dir_path = QFileDialog.getExistingDirectory(
            parent=self,
            caption="选择目录",
            dir="."
        )
        if dir_path:
            self.set_text(dir_path)
            return dir_path
        else:
            return None

    def get_file_path(self):
        file_path = QFileDialog.getOpenFileName(
            parent=self,
            caption="选择文件",
            dir=".",
            filter="所有文件 (*.*)"
        )
        if file_path:
            self.set_text(file_path)
            return file_path
        else:
            return None

    def set_text(self, text):
        return self.input_box.set_text(text)

    def get_text(self):
        return self.input_box.get_text()

    def clear(self):
        self.input_box.clear()


class ApiKeyInputBox(QWidget):
    def __init__(self, label_text="", url="", *, parent=None, tag_width=100, width=None, height=80):
        super().__init__(parent)
        if width:
            self.setFixedWidth(width)
        if height:
            self.setFixedHeight(height)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.input_box = InputBox(label_text=label_text, tag_width=tag_width)

        self.url_Label = Label(url=url)

        layout.addWidget(self.input_box)
        layout.addWidget(self.url_Label)
        layout.addStretch()

    def set_text(self, text):
        self.input_box.set_text(text)

    def get_text(self):
        return self.input_box.get_text()

    def set_url(self, url):
        self.url_Label.set_url(url)

    def clear(self):
        self.input_box.clear()


class ImagePreviewerWidget(QWidget):
    def __init__(self, parent=None, *, image_path="", width=None, height=None):
        super().__init__(parent)
        if width:
            self.setFixedWidth(width)
        if height:
            self.setFixedHeight(height)
        self.pixmap = QPixmap()
        self.scale_factor = 1.0
        self.last_mouse_pos = QPointF()
        self.offset = QPointF(0, 0)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        if image_path:
            self.set_image(image_path)

    def set_image(self, image_path):
        self.pixmap = QPixmap(image_path)
        self.reset_view()
        self.update()

    def reset_view(self):
        if not self.pixmap.isNull():
            w_ration = self.width() / self.pixmap.width()
            h_ration = self.height() / self.pixmap.height()
            self.scale_factor = min(w_ration, h_ration, 1.0)
            self.offset = QPointF(0, 0)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        bg_color = QColor("#1e1e1e")
        painter.fillRect(self.rect(), bg_color)

        if self.pixmap.isNull():
            self._draw_border(painter)
            return

        painter.save()

        painter.translate(self.width() / 2 + self.offset.x(), self.height() / 2 + self.offset.y())
        painter.scale(self.scale_factor, self.scale_factor)

        draw_rect = QRect(
            -self.pixmap.width() // 2,
            -self.pixmap.height() // 2,
            self.pixmap.width(),
            self.pixmap.height()
        )
        painter.drawPixmap(draw_rect, self.pixmap)

        painter.restore()

        self._draw_border(painter)

    def _draw_border(self, painter):
        border_color = QColor("#ffffff")
        pen = painter.pen()
        pen.setColor(border_color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        painter.drawRect(self.rect().adjusted(1, 1, -1, -1))

    def wheelEvent(self, event):
        old_scale = self.scale_factor
        mouse_pos = event.position()

        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            self.scale_factor *= zoom_in_factor
        else:
            self.scale_factor *= zoom_out_factor

        self.scale_factor = max(0.1, min(self.scale_factor, 10.0))

        k = self.scale_factor / old_scale
        center = QPointF(self.width() / 2, self.height() / 2)

        relative_mouse_pos = mouse_pos - center

        self.offset = relative_mouse_pos - k * (relative_mouse_pos - self.offset)

        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.last_mouse_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.position() - self.last_mouse_pos
            self.offset += delta
            self.last_mouse_pos = event.position()
            self.update()

    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.CursorShape.OpenHandCursor)


class SubWindow(QWidget):
    def __init__(self, width=500, height=500, direction="H"):
        super().__init__()
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        screen_width, screen_height = screen_geometry.width(), screen_geometry.height()
        self._width, self._height = width, height
        self.setGeometry(int(screen_width // 2 - self._width / 2), int(screen_height // 2 - self._height / 2), self._width, self._height)

        self.layout = QVBoxLayout(self) if direction == "V" else QHBoxLayout(self)

    def add_widget(self, widget):
        self.layout.addWidget(widget)
