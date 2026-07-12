from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QLineEdit, QPlainTextEdit,
                               QDoubleSpinBox, QComboBox, QColorDialog, QStyle, QStyleOptionComboBox, QStylePainter, QStyleOptionFrame)
from PySide6.QtCore import Qt, QPoint, Signal, QRect, QPointF, QEvent
from PySide6.QtGui import QPainter, QColor, QFont, QColor, QPolygon, QFontMetrics, QPen, QPixmap
from nodes.helpers import color_to_hex, hex_to_color
from nodes.helpers import pil_to_pixmap


class Widget(QWidget):
    def __init__(self, parent=None, direction="H"):
        super().__init__(parent)
        if direction == "H":
            self.layout = QHBoxLayout(self)
        elif direction == "V":
            self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

    def add_widgets(self, widgets):
        for widget, scalability in widgets:
            self.layout.addWidget(widget, scalability)


class Label(QLabel):
    setCompleted = Signal(object)

    def __init__(self, text="", *, parent=None, fixed_width=None, fixed_height=None):
        super().__init__(parent)
        self.setText(text)
        if fixed_width:
            self.setFixedWidth(fixed_width)
        if fixed_height:
            self.setFixedHeight(fixed_height)
        self.setMinimumHeight(20)


class ColorLabel(QLabel):
    setCompleted = Signal(object)

    def __init__(self, name, required=False, *, parent=None, fixed_width=None, fixed_height=25):
        super().__init__(parent)
        self.name = name
        self.required = required
        if fixed_width:
            self.setFixedWidth(fixed_width)
        if fixed_height:
            self.setFixedHeight(fixed_height)
        self.setMinimumHeight(25)
        self.color = QColor("#ffffff")
        self.set_color(color_to_hex(self.color))

    def mousePressEvent(self, event):
        col = QColorDialog.getColor(self.color, None, "选择颜色")
        if col.isValid():
            if self.color == col:
                return
            else:
                self.color = col
            self.set_color(color_to_hex(self.color))

        super().mousePressEvent(event)

    def set_color(self, color: str):
        self.setStyleSheet(f"background: {color}; border: 1px solid #555555;")
        self.setCompleted.emit()

    def get_color(self):
        return color_to_hex(self.color)


class PushButton(QPushButton):
    clickCompleted = Signal()

    def __init__(self, text="", event=None, *, parent=None, fixed_width=None, fixed_height=25):
        super().__init__(parent)
        self.setText(text)
        if fixed_width:
            self.setFixedWidth(fixed_width)
        if fixed_height:
            self.setFixedHeight(fixed_height)
        self.setMinimumHeight(25)
        self.setStyleSheet("""
            QPushButton {
                color: #e5e5e5;
                background: #545454;
                border: 1px solid #434343;;
            }
            QPushButton::hover {
                background: #656565;
            }
            QPushButton::pressed {
                background: #797979;
            }
            QPushButton:disabled {
                color: rgba(255, 255, 255, 32);
                background: rgba(128, 128, 128, 32);
            }
        """)
        self.clicked.connect(event)


class LineEdit(QLineEdit):
    def __init__(self, name, required=False, *, parent=None, fixed_width=None, fixed_height=25, background="#222222", is_elide=False):
        super().__init__(parent)
        self.name = name
        self.setToolTip(self.name)
        self.required = required
        if fixed_width:
            self.setFixedWidth(fixed_width)
        if fixed_height:
            self.setFixedHeight(fixed_height)
        self.setMinimumHeight(25)
        self.setAlignment(Qt.AlignCenter)

        self.setStyleSheet(f"""
            QLineEdit {{
                color: #e5e5e5;
                background: {background};
                border: 1px solid #434343;
                border-radius: 4px;
            }}
            QLineEdit:disabled {{
                color: rgba(255, 255, 255, 32);
                background: rgba(128, 128, 128, 64);
            }}
        """)

        self.is_elide = is_elide
        self.original_text = ""

        self.textChanged.connect(self.on_text_changed)

    def paintEvent(self, event):
        if self.is_elide:
            painter = QStylePainter(self)
            if self.isEnabled():
                painter.setPen(QColor("#e5e5e5"))
            else:
                painter.setPen(QColor(255, 255, 255, 32))

            opt = QStyleOptionFrame()
            self.initStyleOption(opt)

            text_rect = self.style().subElementRect(QStyle.SE_LineEditContents, opt, self)
            if self.isRightToLeft():
                text_rect.moveRight(self.rect().right())

            elided_text = self.fontMetrics().elidedText(self.original_text, Qt.TextElideMode.ElideMiddle, text_rect.width())
            painter.drawItemText(text_rect, Qt.AlignCenter | Qt.AlignVCenter, self.palette(), self.isEnabled(), elided_text)

        else:
            super().paintEvent(event)

        painter = QPainter(self)
        if self.isEnabled():
            painter.setPen(QColor("#e5e5e5"))
        else:
            painter.setPen(QColor(255, 255, 255, 32))

        rect = self.rect()

        font = QFont("Arial", 9)
        painter.setFont(font)
        fm = QFontMetrics(font)
        w = fm.horizontalAdvance(self.name + ":")

        padding = 5

        if not w + padding + self.get_text_width()/2 >= self.width()/2:
            rect.setLeft(padding)
            painter.drawText(rect, Qt.AlignLeft | Qt.AlignVCenter, self.name + ":")

    def get_text_width(self):
        text = self.text()
        font = self.font()
        fm = QFontMetrics(font)
        w = fm.horizontalAdvance(text)
        return w

    def on_text_changed(self, text):
        self.original_text = text

    def setText(self, text):
        self.original_text = text
        super().setText(text)

    def set_value(self, text):
        self.setText(text)

    def value(self):
        return self.original_text


class PlainTextEdit(QPlainTextEdit):
    editingFinished = Signal()

    def __init__(self, name, text="", required=False, *, parent=None, fixed_width=None, fixed_height=None, use_style=True):
        super().__init__(parent)
        self.name = name
        self.setToolTip(self.name)
        self.required = required
        if fixed_width:
            self.setFixedWidth(fixed_width)
        if fixed_height:
            self.setFixedHeight(fixed_height)
        self.setMinimumHeight(25)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setPlainText(text)
        if use_style:
            self.setStyleSheet("""
                QPlainTextEdit {color: #e5e5e5; background-color: #545454;}
                QPlainTextEdit:disabled {color: rgba(255, 255, 255, 32); background: rgba(128, 128, 128, 32);}
            """)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.editingFinished.emit()

    def setPlainText(self, text):
        super().setPlainText(text)
        self.editingFinished.emit()

    def value(self):
        return self.toPlainText()


class MultiLineTextEdit(QWidget):
    def __init__(self, name, text="", required=False, *, parent=None, fixed_width=None, fixed_height=None):
        super().__init__(parent)
        self.name = name
        self.setToolTip(self.name)
        self.required = required
        if fixed_width:
            self.setFixedWidth(fixed_width)
        if fixed_height:
            self.setFixedHeight(fixed_height)
        self.setMinimumHeight(50)
        self.setStyleSheet("""
            QWidget {
                background-color: #545454;
            }
            QLabel {
                color: "#e5e5e5"; 
                background-color: #545454; 
                border: 1px solid #434343; 
                border-top-left-radius: 4px; 
                border-top-right-radius: 4px;
            }
            QLabel:disabled{
                color: rgba(255, 255, 255, 32);
                background: rgba(128, 128, 128, 32);
            }
            QPlainTextEdit {
                color: "#e5e5e5"; 
                background-color: #545454; 
                border: 1px solid #434343; 
                border-bottom-left-radius: 4px;
                border-bottom-right-radius: 4px;
            }
            QPlaintextEdit:disabled {
                color: rgba(255, 255, 255, 32);
                background: rgba(128, 128, 128, 32);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.label = QLabel(self.name)
        self.label.setFixedHeight(20)
        self.text_edit = PlainTextEdit(name, text)

        layout.addWidget(self.label)
        layout.addWidget(self.text_edit)

    def set_text(self, text):
        self.text_edit.setPlainText(text)

    def value(self):
        return self.text_edit.value()


class DoubleSpinBox(QDoubleSpinBox):
    def __init__(self, name, value=0.0, parent=None):
        super().__init__(parent)
        self.name = name
        self.setRange(-100000000.0, 10000000000000000.0)
        self.setValue(value)
        self.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.setAlignment(Qt.AlignCenter)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.text:
            painter = QPainter(self)
            if self.isEnabled():
                painter.setPen(QColor("#e5e5e5"))
            else:
                painter.setPen(QColor(255, 255, 255, 32))
            rect = self.rect()
            rect.setLeft(5)
            font = QFont("Arial", 9)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignLeft | Qt.AlignVCenter, self.name + ":")


class DoubleArrowSpinBox(QWidget):
    def __init__(self, name, value=0.0, required=False, *, parent=None, fixed_width=None, fixed_height=25, decimals=2, data_type="float"):
        super().__init__(parent)
        self.name = name
        self.setToolTip(self.name)
        self.required = required
        self.data_type = data_type
        self.setStyleSheet("""
            QWidget {background: #545454;}
            QDoubleSpinBox {color: #e5e5e5; background: #545454; border: none; border: 1px solid #434343;}
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {width: 0;}
            QDoubleSpinBox:disabled {color: rgba(255, 255, 255, 32); background: rgba(128, 128, 128, 32);}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.btn_left = PushButton("<", self.decrease_value, fixed_width=20)
        self.spinbox = DoubleSpinBox(name, value)
        if data_type == "int":
            self.spinbox.setDecimals(0)
            self.step = 1
        else:
            self.spinbox.setDecimals(decimals)
            self.step = 0.1
        self.btn_right = PushButton(">", self.increase_value, fixed_width=20)

        if fixed_width:
            self.setFixedWidth(fixed_width)
        if fixed_height:
            self.setFixedHeight(fixed_height)
            self.btn_left.setFixedHeight(fixed_height)
            self.spinbox.setFixedHeight(fixed_height)
            self.btn_right.setFixedHeight(fixed_height)
        self.setMinimumHeight(25)

        layout.addWidget(self.btn_left)
        layout.addWidget(self.spinbox, 1)
        layout.addWidget(self.btn_right)

    def set_enable(self):
        all_children = self.findChildren(QWidget)
        for widget in all_children:
            widget.setEnabled(False)

    def decrease_value(self):
        self.spinbox.setValue(self.spinbox.value() - self.step)
        self.btn_left.clickCompleted.emit()

    def increase_value(self):
        self.spinbox.setValue(self.spinbox.value() + self.step)
        self.btn_right.clickCompleted.emit()

    def set_value(self, value):
        self.spinbox.setValue(value)

    def value(self):
        if self.data_type == "int":
            return int(self.spinbox.value())
        else:
            return self.spinbox.value()


class ComboBox(QComboBox):
    def __init__(self, name, required=False, *, parent=None, fixed_width=None, fixed_height=25, background="#333333", use_style=True, hide_button=False):
        super().__init__(parent)
        self.name = name
        self.setToolTip(self.name)
        self.required = required
        if fixed_width:
            self.setFixedWidth(fixed_width)
        if fixed_height:
            self.setFixedHeight(fixed_height)
        self.setMinimumHeight(25)

        if use_style:
            self.setStyleSheet(f"""
                QComboBox {{
                    color: #e5e5e5;
                    background: {background};
                    border: 1px solid #434343;
                    border-radius: 4px;
                    padding-left: 2px;
                }}
                QComboBox::drop-down {{
                    border: none;
                    background: transparent;
                }}
                QComboBox QAbstractItemView {{
                    color: #eeeeee;
                    background: {background};
                    border: 1px solid #ffffff;
                    border-radius: 4px;
                    selection-background-color: #555555;
                }}
                QComboBox:disabled {{
                    color: rgba(255, 255, 255, 32);
                    background: rgba(128, 128, 128, 32);
                }}
            """)

        self.hide_button = hide_button

        self.line_edit = LineEdit(self.name, is_elide=True)
        self.line_edit.setAlignment(Qt.AlignCenter)
        self.line_edit.mousePressEvent = self.mousePressEvent
        self.line_edit.setReadOnly(True)
        self.setLineEdit(self.line_edit)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)

        if not self.view().isVisible():
            self.showPopup()

    def paintEvent(self, event):
        super().paintEvent(event)

        if self.hide_button:
            return

        opt = QStyleOptionComboBox()
        self.initStyleOption(opt)
        arrow_rect = self.style().subControlRect(QStyle.ComplexControl.CC_ComboBox, opt, QStyle.SubControl.SC_ComboBoxArrow, self)

        painter = QPainter(self)
        if self.isEnabled():
            painter.setPen(QColor("#e5e5e5"))
        else:
            painter.setPen(QColor(255, 255, 255, 32))

        points = QPolygon([QPoint(arrow_rect.x(), arrow_rect.y() + 8), QPoint(arrow_rect.x() + 10, arrow_rect.y() + 8),
                           QPoint(arrow_rect.x() + 5, arrow_rect.y() + 18)])

        painter.drawPolygon(points)

    def set_value(self, text):
        self.setCurrentText(text)

    def value(self):
        return self.currentText()


class DoubleArrowComBoBox(QWidget):
    def __init__(self, name, required=False, *, parent=None, fixed_width=None, fixed_height=25, background="#545454"):
        super().__init__(parent)
        self.name = name
        self.setToolTip(self.name)
        self.required = required
        self.setStyleSheet(f"""
            QComboBox {{
                color: #e5e5e5;
                background: {background};
                border: 1px solid #555555;
                border-radius: 0px;
                padding-left: 2px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 0px;
            }}
            QComboBox::down-arrow {{
                image: none;
                width: 0px;
                height: 0px;
            }}
            QComboBox QAbstractItemView {{
                color: #eeeeee;
                background: {background};
                border: 1px solid #555555;
                selection-background-color: #555555;
            }}
            QComboBox:disabled {{
            color: rgba(255, 255, 255, 32);
            background: rgba(128, 128, 128, 32);
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.btn_left = PushButton("<", self.decrease_value, fixed_width=20)
        self.combo = ComboBox(name, use_style=False, hide_button=True)
        self.btn_right = PushButton(">", self.increase_value, fixed_width=20)

        if fixed_width:
            self.setFixedWidth(fixed_width)
        if fixed_height:
            self.setFixedHeight(fixed_height)
            self.btn_left.setFixedHeight(fixed_height)
            self.combo.setFixedHeight(fixed_height)
            self.btn_right.setFixedHeight(fixed_height)
        self.setMinimumHeight(25)

        layout.addWidget(self.btn_left)
        layout.addWidget(self.combo, 1)
        layout.addWidget(self.btn_right)

    def decrease_value(self):
        items_text = [self.combo.itemText(i) for i in range(self.combo.count())]
        current_index = items_text.index(self.combo.currentText())
        new_index = current_index - 1
        if new_index >= 0:
            self.combo.setCurrentIndex(new_index)
        else:
            self.combo.setCurrentIndex(self.combo.count() - 1)
        self.btn_left.clickCompleted.emit()

    def increase_value(self):
        items_text = [self.combo.itemText(i) for i in range(self.combo.count())]
        current_index = items_text.index(self.combo.currentText())
        new_index = current_index + 1
        if new_index <= self.combo.count() - 1:
            self.combo.setCurrentIndex(new_index)
        else:
            self.combo.setCurrentIndex(0)
        self.btn_right.clickCompleted.emit()

    def add_items(self, item_list):
        self.combo.addItems(item_list)

    def set_current_text(self, text):
        self.combo.setCurrentText(text)

    def get_current_text(self):
        return self.combo.currentText()

    def set_current_index(self, index):
        self.combo.setCurrentIndex(index)

    def get_current_index(self):
        return self.combo.currentIndex()

    def value(self):
        return self.combo.currentText()


class ImageShowBox(QWidget):
    setCompleted = Signal()

    def __init__(self, name, required=False, *, parent=None, fixed_width=None, fixed_height=None):
        super().__init__(parent)
        self.name = name
        self.setToolTip(self.name)
        self.required = required
        if fixed_width:
            self.setFixedWidth(fixed_width)
        if fixed_height:
            self.setFixedHeight(fixed_height)
        self.setMinimumHeight(125)
        self.pixmap = QPixmap()
        self.scale_factor = 1.0
        self.last_mouse_pos = QPointF()

    def set_image(self, image):
        if image:
            pixmap = pil_to_pixmap(image)
            self.pixmap = QPixmap(pixmap)
            self.reset_view()
            self.update()
            self.setCompleted.emit()

    def reset_view(self):
        if not self.pixmap.isNull():
            w_ration = self.width() / self.pixmap.width()
            h_ration = self.height() / self.pixmap.height()
            self.scale_factor = min(w_ration, h_ration, 1.0)
        else:
            self.scale_factor = 1.0

    def resizeEvent(self, event):
        self.reset_view()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        bg_color = QColor("#303030")
        painter.fillRect(self.rect(), bg_color)

        if self.pixmap.isNull():
            self._draw_border(painter)
            return

        scaled_w = self.pixmap.width() * self.scale_factor
        scaled_h = self.pixmap.height() * self.scale_factor

        draw_rect = QRect(
            int((self.width() - scaled_w) / 2),
            int((self.height() - scaled_h) / 2),
            int(scaled_w),
            int(scaled_h)
        )
        painter.drawPixmap(draw_rect, self.pixmap)

        self._draw_border(painter)

    def _draw_border(self, painter):
        border_color = QColor("#555555")
        pen = painter.pen()
        pen.setColor(border_color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        painter.drawRect(self.rect().adjusted(1, 1, -1, -1))
