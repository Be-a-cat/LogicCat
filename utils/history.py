from PySide6.QtGui import QColor, QBrush
from PySide6.QtCore import QObject, Signal, QTimer


class HistoryManager(QObject):
    history_changed = Signal()

    def __init__(self, serializer, list_widget=None):
        super().__init__()
        self.serializer = serializer
        self.history_ui_list = list_widget

        self.snapshots = []
        self.actions = []
        self.current_step = -1
        self.max_steps = 10
        self.is_suspended = False

    def record(self, action_name):
        if self.is_suspended:
            return

        snapshot = self.serializer.serialize_to_dict()

        if len(self.snapshots) != 0:
            last_snapshot = self.snapshots[self.current_step][1]
            if snapshot == last_snapshot:
                return

        if self.current_step < len(self.snapshots) - 1:
            self.snapshots = self.snapshots[:self.current_step + 1]
            self.actions = self.actions[:self.current_step + 1]

            if self.history_ui_list:
                while self.history_ui_list.count() > self.current_step + 1:
                    self.history_ui_list.takeItem(self.history_ui_list.count() - 1)

        self.snapshots.append((action_name, snapshot))
        self.actions.append(action_name)

        if len(self.snapshots) > self.max_steps:
            self.snapshots.pop(0)
            self.actions.pop(0)

            if self.history_ui_list:
                self.history_ui_list.takeItem(0)
        else:
            self.current_step += 1

        if self.history_ui_list:
            self.history_ui_list.addItem(f"{action_name}")
            self.history_ui_list.setCurrentRow(self.current_step)

        self.history_changed.emit()
        self.record_completed()

        print(self.actions)

    def undo(self):
        if self.current_step > 0:
            self.current_step -= 1
            snapshot = self.snapshots[self.current_step][1]

            nodes = self.serializer.load_from_dict(snapshot)
            for node in nodes.values():
                node.adjusted.connect(self.record)

            if self.history_ui_list:
                item = self.history_ui_list.item(self.current_step + 1)
                item.setForeground(QBrush(QColor(255, 128, 128)))
                font = item.font()
                font.setStrikeOut(True)
                item.setFont(font)
                self.history_ui_list.setCurrentRow(self.current_step)

            self.history_changed.emit()

            print("撤销")
            print(self.actions)
        print(self.current_step, len(self.snapshots))

    def redo(self):
        if self.current_step < len(self.snapshots) - 1:
            self.current_step += 1
            snapshot = self.snapshots[self.current_step][1]

            nodes = self.serializer.load_from_dict(snapshot)
            for node in nodes.values():
                node.adjusted.connect(self.record)

            if self.history_ui_list:
                item = self.history_ui_list.item(self.current_step)
                item.setForeground(QBrush(QColor(255, 255, 255)))
                font = item.font()
                font.setStrikeOut(False)
                item.setFont(font)
                self.history_ui_list.setCurrentRow(self.current_step)

            self.history_changed.emit()

            print("重做")
            print(self.actions)
        print(self.current_step, len(self.snapshots))

    def suspend(self):
        self.is_suspended = True

    def resume(self):
        self.is_suspended = False

    def record_completed(self):
        pass

    def undo_completed(self):
        pass

    def redo_completed(self):
        pass
