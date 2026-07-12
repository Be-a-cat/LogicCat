from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QMenu,
                               QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QAction, QCursor, QKeySequence

from utils.config_manager import global_config
from utils.integrity_checker import check_project_integrity
from utils.serializer import SessionSerializer
from utils.history import HistoryManager
from utils.custom_loader import load_custom_nodes, LOADER_LOGS

from app.ui import LogicCatUI, MenuBar, StatusBar, SettingsDialog, ToolBar, SearchBox, LogPanel, DrawerPanel
from app.n_panel import NPanel

from nodes.scene import NodeScene, NodeGraphView
from nodes.runner import GraphRunner
from nodes.node_base import BaseNode
from nodes.node_input import ValueNode
from nodes.node_math import MathNode
from nodes.node_output import OutputNode

import os
import sys
from datetime import datetime
from collections import deque

load_custom_nodes()


class LogicCat(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.ui = LogicCatUI(self, self.app)
        self.scene = self.ui.scene
        self.view = self.ui.view
        self.menubar = self.ui.menubar
        self.statusbar = self.ui.statusbar
        self.toolbar = self.ui.toolbar
        self.drawer_panel = self.ui.drawer_panel
        self.bottom_panel = self.ui.bottom_panel
        self.outliner_panel = self.ui.outliner_panel
        self.log_panel = self.bottom_panel.log_panel
        self.asset_panel = self.bottom_panel.asset_panel

        self.runner = GraphRunner()

        self.init_menubar()
        self.init_toolbar()

        self.serializer = SessionSerializer(self.view)
        self.history = HistoryManager(self.serializer, self.log_panel.history_list)
        self.history.history_changed.connect(self.history_changed)

        self.runner.node_status_changed.connect(self.sync_node_status)
        self.runner.node_log_message.connect(self.append_log)
        self.runner.queue_completed.connect(self.run_completed)
        self.runner.data_delivery.connect(self.data_reception)

        self.n_panel = NPanel(self.view)

        self.scene.selectionChanged.connect(self.on_selection_changed)
        self.view.node_adjusted.connect(self.history.record)

        for log_msg in LOADER_LOGS:
            self.append_log(log_msg)

        nodes = self.serializer.load_from_file(global_config.get("paths", "files", "default_workflow"))
        if nodes:
            for node in nodes.values():
                node.adjusted.connect(self.history.record)

        self.history.record("初始化")

        self.run_queue = deque()

        self.set_shortcut()

    def set_shortcut(self):
        action_undo = QAction("撤销", self)
        action_undo.setShortcut(QKeySequence.Undo)
        action_undo.triggered.connect(self.history.undo)
        self.addAction(action_undo)

        action_redo = QAction("重做", self)
        action_redo.setShortcut(QKeySequence.Redo)
        action_redo.triggered.connect(self.history.redo)
        self.addAction(action_redo)

        action_search = QAction("搜索节点", self)
        action_search.setShortcut(QKeySequence("Shift+A"))
        action_search.triggered.connect(self.open_search)
        self.addAction(action_search)

    def init_menubar(self):
        self.menubar.action_save.triggered.connect(self.on_save)
        self.menubar.action_save_as.triggered.connect(self.on_save_as)
        self.menubar.action_open.triggered.connect(self.on_open)
        self.menubar.action_open_last.triggered.connect(self.on_open_last)

        self.menubar.action_setting.triggered.connect(self.on_setting)

    def on_save(self):
        """保存工作流"""
        file_name = datetime.now().strftime("%Y%m%d%H%M%S")
        save_path = global_config.get("paths", "dirs", "workflow_save")
        ext = ".json"
        file_path = os.path.join(save_path, file_name + ext)
        self.serializer.save_to_file(file_path)

    def on_save_as(self):
        """另存工作流"""
        file_path, _ = QFileDialog.getSaveFileName(self, "保存工作流", "workflow.json", "JSON Files (*.json)")
        if file_path:
            self.serializer.save_to_file(file_path)

    def on_open(self):
        """打开工作流"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择工作流", ".", "JSON Files (*.json)")
        if file_path:
            reply = QMessageBox.question(self, "确认", "是否清空当前工作流并打开新工作流？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                nodes = self.serializer.load_from_file(file_path)
                for node in nodes.values():
                    node.adjusted.connect(self.history.record)
                self.history.record("打开工作流")

    def on_open_last(self):
        """打开最后一次会话"""
        file_path = global_config.get("paths", "files", "autosave_workflow")
        if file_path:
            reply = QMessageBox.question(self, "确认", "是否清空当前工作流并打开新工作流？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                nodes = self.serializer.load_from_file(file_path)
                for node in nodes.values():
                    node.adjusted.connect(self.history.record)
                self.history.record("打开最后一次会话")

    def on_setting(self):
        """打开设置"""
        dialog = SettingsDialog(self)
        dialog.show()

    def init_toolbar(self):
        """初始化工具栏"""
        self.toolbar.btn_run.clicked.connect(self.add_workflow)
        self.toolbar.btn_stop.clicked.connect(self.runner.interrupt)
        self.toolbar.btn_properties.clicked.connect(lambda: self.drawer_panel.toggle_side_panel(0))
        self.toolbar.btn_workflow.clicked.connect(lambda: self.drawer_panel.toggle_side_panel(1))
        self.toolbar.btn_versatile.clicked.connect(self.bottom_panel.visibility)

    def on_selection_changed(self):
        """选择项改变时触发"""
        if not self.scene.selectedItems():
            return
        select_items = self.scene.selectedItems()
        item = select_items[0]
        if isinstance(item, BaseNode):
            self.statusbar.set_text(f"{item.title}")
            print(f"{item.title}")

    def append_log(self, msg):
        """添加消息"""
        time_str = datetime.now().strftime("%H:%M:%S")
        self.log_panel.append_msg(f"[{time_str}]{msg}")

    def open_search(self):
        """打开搜索框"""
        mouse_pos = self.view.mapFromGlobal(QCursor.pos())
        scene_pos = self.view.mapToScene(mouse_pos)

        def on_selected(node_cls):
            self.view.add_node(node_cls, scene_pos)

        search_box = SearchBox(self, on_selected)
        search_box.move(QCursor.pos())
        search_box.show()
        search_box.input.setFocus()

    def history_changed(self):
        """历史记录改变时触发"""
        node = None
        nodes = []
        if self.view.focus_node:
            for item in self.scene.items():
                if hasattr(item, "idx") and item.idx == self.view.focus_node.idx:
                    node = item
                    nodes.append(node)
            if node:
                self.view.focus_node = node
                self.view.focus_node.setSelected(True)
                self.drawer_panel.update_properties_panel(self.view.focus_node)
                self.window().outliner_panel.update_properties(self.view.focus_node)

            else:
                self.view.focus_node = None
                self.drawer_panel.update_properties_panel()
                self.outliner_panel.update_properties()

        self.outliner_panel.refresh()

    def get_active_nodes(self):
        """获取运行节点"""
        active_nodes = set()
        stack = [item for item in self.scene.items() if hasattr(item, "is_terminator") and item.is_terminator]

        while stack:
            current_node = stack.pop()

            active_nodes.add(current_node)

            if current_node.input_socket or list(current_node.widget_socket.values()):
                for socket in current_node.input_socket + list(current_node.widget_socket.values()):
                    if socket:
                        for edge in socket.edges:
                            upstream_node = edge.start_socket.parentItem()
                            if upstream_node not in stack:
                                stack.append(upstream_node)
        return active_nodes

    def add_workflow(self):
        """添加工作流"""
        active_nodes = self.get_active_nodes()

        for node in active_nodes:
            if not node.validate():
                return

        snapshot = self.serializer.serialize_to_dict(active_nodes)

        self.run_queue.append(snapshot)

        self.run_workflow()

        self.toolbar.label_queue_number.setText(str(len(self.run_queue) + 1))

        print("成功添加执行队列···")

    def run_workflow(self):
        """运行工作流"""
        if self.run_queue and not self.runner.is_running:
            self.runner.is_running = True

            for item in self.scene.items():
                if isinstance(item, BaseNode):
                    item.reset_state()

            workflow = self.run_queue.popleft()
            self.runner.run(workflow)
            print("开始运行工作流···")

    def run_completed(self):
        """运行完成后触发"""
        self.toolbar.label_queue_number.setText(str(len(self.run_queue)))
        self.history.record("工作流执行完成")
        self.run_workflow()

    def data_reception(self, node_idx, data):
        """将虚拟节点的数据映射到真实节点"""
        for item in self.scene.items():
            if isinstance(item, BaseNode) and item.idx == node_idx and not isinstance(item, OutputNode):
                item.set_widget_input(data["inputs"])
                return

    def sync_node_status(self, idx, status, data, duration):
        """将虚拟节点的状态映射到真实节点，虚拟节点设置状态时触发"""
        target_node = None
        for item in self.scene.items():
            if hasattr(item, "idx") and item.idx == idx:
                target_node = item
                break

        if target_node:
            target_node.set_state(status)

            if status == "IDLE" and data is not None:
                target_node.results = data["results"]
                target_node.post_execute(data)
                if duration > 0:
                    target_node.last_run_time = duration

            if status == "ERROR":
                target_node.running_prompt = "error"

            target_node.update()

            if self.view.focus_node:
                self.drawer_panel.update_properties_panel(self.view.focus_node)
                self.outliner_panel.update_properties(self.view.focus_node)

    def closeEvent(self, event):
        self.serializer.save_to_file(global_config.get("paths", "files", "autosave_workflow"))
        event.accept()


if __name__ == '__main__':
    check_project_integrity()

    app = QApplication(sys.argv)
    window = LogicCat(app)
    window.show()
    app.processEvents()
    app.exec()   # sys.exit(app.exec())
