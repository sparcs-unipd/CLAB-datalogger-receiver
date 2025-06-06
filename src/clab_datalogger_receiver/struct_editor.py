import yaml
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QComboBox, QLineEdit, QLabel, QMessageBox, QWidget, QHeaderView
)
from PySide6.QtCore import Qt, Signal

DATATYPES = ['float','char','int8','uint8','int16','uint16','int32','uint32','int64','uint64','double']
    
class StructConfigEditor(QDialog):
    yaml_saved = Signal()

    def __init__(self, yaml_path, parent=None):
        super().__init__(parent)
        self.yaml_path = yaml_path
        self.setWindowTitle("Edit struct_cfg.yaml")
        self.resize(700, 400)
        self.layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Subplot Name", "Trace Name", "Datatype"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.add_trace_btn = QPushButton("Add Trace")
        self.remove_row_btn = QPushButton("Remove Selected Row")
        self.save_btn = QPushButton("Save")
        btn_layout.addWidget(self.add_trace_btn)
        btn_layout.addWidget(self.remove_row_btn)
        btn_layout.addWidget(self.save_btn)
        self.layout.addLayout(btn_layout)

        self.add_trace_btn.clicked.connect(self.add_trace)
        self.remove_row_btn.clicked.connect(self.remove_row)
        self.save_btn.clicked.connect(self.save_yaml)

        self.load_yaml()

    def load_yaml(self):
        self.table.setRowCount(0)
        try:
            with open(self.yaml_path, "r") as f:
                data = yaml.safe_load(f)
            if not data:
                return
            for subplot in data:
                subplot_name = list(subplot.keys())[0]
                fields = subplot[subplot_name]
                for trace_name, dtype in fields.items():
                    self.add_row(subplot_name, trace_name, dtype)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load YAML: {e}")

    def add_row(self, subplot_name="", trace_name="", dtype="float"):
        row = self.table.rowCount()
        self.table.insertRow(row)
        # Subplot name
        subplot_item = QTableWidgetItem(subplot_name)
        self.table.setItem(row, 0, subplot_item)
        # Trace name
        trace_item = QTableWidgetItem(trace_name)
        self.table.setItem(row, 1, trace_item)
        # Datatype dropdown
        dtype_combo = QComboBox()
        dtype_combo.addItems(DATATYPES)
        if dtype in DATATYPES:
            dtype_combo.setCurrentText(dtype)
        self.table.setCellWidget(row, 2, dtype_combo)

    def add_trace(self):
        # Adds a trace to the same subplot as the currently selected row, or a new one if none selected
        row = self.table.currentRow()
        if row >= 0:
            subplot_name = self.table.item(row, 0).text()
            self.add_row(subplot_name, "trace", "float")
        else:
            self.add_row("subplot", "trace", "float")

    def remove_row(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)

    def save_yaml(self):
        # Build YAML structure
        subplots = {}
        for row in range(self.table.rowCount()):
            subplot = self.table.item(row, 0).text().strip()
            trace = self.table.item(row, 1).text().strip()
            dtype = self.table.cellWidget(row, 2).currentText()
            if not subplot or not trace:
                continue
            if subplot not in subplots:
                subplots[subplot] = {}
            subplots[subplot][trace] = dtype
        yaml_list = [{k: v} for k, v in subplots.items()]
        try:
            with open(self.yaml_path, "w") as f:
                yaml.dump(yaml_list, f, sort_keys=False)
            QMessageBox.information(self, "Saved", "YAML saved successfully.")
            self.yaml_saved.emit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save YAML: {e}")
