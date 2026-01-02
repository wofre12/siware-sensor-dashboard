import sys
from datetime import datetime
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTableWidget, QTableWidgetItem, QLabel, QHeaderView,
                             QScrollArea, QFrame, QTabWidget, QPushButton, QLineEdit,
                             QInputDialog, QMessageBox, QTextEdit, QCheckBox, QGridLayout)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont

from .config import SENSORS_CONFIG, PLOT_HISTORY_SECONDS, UPDATE_INTERVAL_MS, MAINTENANCE_PASSWORD
from .data_models import SensorReading, AlarmEvent
from .logger import logger

class MplCanvas(FigureCanvas):
    def __init__(self, title, unit, parent=None, width=5, height=3, dpi=100):
        # We use a dark theme for a professional "industrial" look
        plt.style.use('dark_background')
        self.fig, self.ax = plt.subplots(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)
        self.ax.set_title(title, fontsize=10)
        self.ax.set_ylabel(unit, fontsize=8)
        self.ax.tick_params(axis='both', which='major', labelsize=8)
        self.xdata = []
        self.ydata = []
        self.line, = self.ax.plot([], [], '#00ff00', linewidth=1)
        self.fig.tight_layout()

    def update_plot(self, new_x, new_y):
        self.xdata = new_x
        self.ydata = new_y
        self.line.set_data(self.xdata, self.ydata)
        if self.xdata:
            self.ax.set_xlim(min(self.xdata), max(self.xdata))
            # Dynamic Y-axis with some padding
            if self.ydata:
                ymin, ymax = min(self.ydata), max(self.ydata)
                padding = max(0.1, (ymax - ymin) * 0.1)
                self.ax.set_ylim(ymin - padding, ymax + padding)
        self.draw()

class DashboardWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Industrial Sensor Monitor - Si-Ware Systems")
        self.resize(1200, 800)
        
        # Data storage
        self.readings = {name: deque(maxlen=int(PLOT_HISTORY_SECONDS * 5)) for name in SENSORS_CONFIG}
        self.latest_readings = {}
        
        self.setup_ui()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)

        # Tabs
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        # Tab 1: Dashboard
        self.dashboard_tab = QWidget()
        self.setup_dashboard_tab()
        self.tabs.addTab(self.dashboard_tab, "Dashboard")

        # Tab 2: Maintenance
        self.maintenance_tab = QWidget()
        self.setup_maintenance_tab()
        self.tabs.addTab(self.maintenance_tab, "Maintenance")

        # Header (Moved out of setup_dashboard_tab to be persistent if desired, 
        # or kept inside - the requirements suggest it's part of the monitor)
        # Let's keep it global above the tabs if possible or inside dashboard.
        # Requirements say "Global system status indicator at top".
        
    def setup_dashboard_tab(self):
        tab_layout = QVBoxLayout(self.dashboard_tab)
        
        # Header: Global Status
        header_layout = QHBoxLayout()
        self.status_label = QLabel("SYSTEM STATUS: STARTING...")
        self.status_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.status_label.setContentsMargins(10, 5, 10, 5)
        self.set_global_status("OK")
        header_layout.addWidget(self.status_label)
        header_layout.addStretch()
        tab_layout.addLayout(header_layout)

        # Middle: Table and Plots
        content_layout = QHBoxLayout()
        
        # Left side: Table
        self.table = QTableWidget(len(SENSORS_CONFIG), 4)
        self.table.setHorizontalHeaderLabels(["Sensor", "Value", "Timestamp", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        
        for i, name in enumerate(SENSORS_CONFIG):
            self.table.setItem(i, 0, QTableWidgetItem(name))
            self.table.setItem(i, 1, QTableWidgetItem("---"))
            self.table.setItem(i, 2, QTableWidgetItem("---"))
            self.table.setItem(i, 3, QTableWidgetItem("DISCONNECTED"))
            
        table_container = QVBoxLayout()
        table_container.addWidget(QLabel("Live Sensor Data"))
        table_container.addWidget(self.table)
        content_layout.addLayout(table_container, 2)

        # Right side: Plots (Scrollable list of plots)
        plots_scroll = QScrollArea()
        plots_widget = QWidget()
        self.plots_grid = QGridLayout(plots_widget)
        self.canvases = {}
        
        for i, (name, cfg) in enumerate(SENSORS_CONFIG.items()):
            canvas = MplCanvas(name, cfg['unit'], width=3, height=2)
            self.canvases[name] = canvas
            # 2 columns grid
            row, col = divmod(i, 2)
            self.plots_grid.addWidget(canvas, row, col)
            
        plots_scroll.setWidget(plots_widget)
        plots_scroll.setWidgetResizable(True)
        content_layout.addWidget(plots_scroll, 3)
        
        tab_layout.addLayout(content_layout, 3)

        # Bottom: Alarm Log
        self.alarm_log = QTableWidget(0, 5)
        self.alarm_log.setHorizontalHeaderLabels(["Time", "Sensor", "Value", "Type", "Message"])
        self.alarm_log.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        log_container = QVBoxLayout()
        log_container.addWidget(QLabel("Alarm History"))
        log_container.addWidget(self.alarm_log)
        tab_layout.addLayout(log_container, 1)

    def setup_maintenance_tab(self):
        self.maint_layout = QVBoxLayout(self.maintenance_tab)
        
        self.login_frame = QFrame()
        login_layout = QVBoxLayout(self.login_frame)
        login_layout.setAlignment(Qt.AlignCenter)
        
        login_layout.addWidget(QLabel("Maintenance Access Required"))
        self.pwd_input = QLineEdit()
        self.pwd_input.setEchoMode(QLineEdit.Password)
        self.pwd_input.setPlaceholderText("Enter Password")
        self.pwd_input.setFixedWidth(200)
        login_layout.addWidget(self.pwd_input)
        
        self.login_btn = QPushButton("Unlock")
        self.login_btn.setFixedWidth(100)
        self.login_btn.clicked.connect(self.check_password)
        login_layout.addWidget(self.login_btn)
        
        self.maint_layout.addWidget(self.login_frame)
        
        # Hidden Maintenance Controls
        self.control_frame = QFrame()
        self.control_frame.setVisible(False)
        ctrl_layout = QVBoxLayout(self.control_frame)
        
        self.clear_btn = QPushButton("Clear Alarm History")
        self.clear_btn.setFixedHeight(40)
        ctrl_layout.addWidget(self.clear_btn)
        
        self.refresh_btn = QPushButton("Force System Refresh (Restart Workers)")
        self.refresh_btn.setFixedHeight(40)
        ctrl_layout.addWidget(self.refresh_btn)

        # New Commands (A4)
        h_cmd_layout = QHBoxLayout()
        self.selftest_btn = QPushButton("Run System Self-Test")
        self.selftest_btn.setFixedHeight(40)
        h_cmd_layout.addWidget(self.selftest_btn)

        self.clearlog_btn = QPushButton("Clear app.log File")
        self.clearlog_btn.setFixedHeight(40)
        h_cmd_layout.addWidget(self.clearlog_btn)
        ctrl_layout.addLayout(h_cmd_layout)

        # Log Viewer (A3)
        ctrl_layout.addWidget(QLabel("Live System Logs"))
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; font-family: 'Consolas', monospace;")
        ctrl_layout.addWidget(self.log_display)

        log_ctrl_layout = QHBoxLayout()
        self.log_pause_cb = QCheckBox("Pause Log Stream")
        log_ctrl_layout.addWidget(self.log_pause_cb)
        
        self.log_autoscroll_cb = QCheckBox("Auto-scroll")
        self.log_autoscroll_cb.setChecked(True)
        log_ctrl_layout.addWidget(self.log_autoscroll_cb)

        self.clear_view_btn = QPushButton("Clear View")
        self.clear_view_btn.clicked.connect(lambda: self.log_display.clear())
        log_ctrl_layout.addWidget(self.clear_view_btn)
        
        ctrl_layout.addLayout(log_ctrl_layout)
        
        self.lock_btn = QPushButton("Lock Maintenance")
        self.lock_btn.clicked.connect(self.lock_maintenance)
        ctrl_layout.addWidget(self.lock_btn)
        
        self.maint_layout.addWidget(self.control_frame)

    def check_password(self):
        if self.pwd_input.text() == MAINTENANCE_PASSWORD:
            self.login_frame.setVisible(False)
            self.control_frame.setVisible(True)
            self.pwd_input.clear()
        else:
            QMessageBox.warning(self, "Access Denied", "Invalid Password")
            self.pwd_input.clear()

    def lock_maintenance(self):
        self.control_frame.setVisible(False)
        self.login_frame.setVisible(True)

    def append_log(self, text):
        if self.log_pause_cb.isChecked():
            return
        
        self.log_display.append(text)
        if self.log_autoscroll_cb.isChecked():
            self.log_display.verticalScrollBar().setValue(
                self.log_display.verticalScrollBar().maximum()
            )

    def set_global_status(self, status):
        # Priority: ALARM (Red) > DEGRADED/FAULTY (Yellow) > ALL OK (Green)
        if status == "OK":
            self.status_label.setText("🟢 SYSTEM STATUS: ALL OK")
            self.status_label.setStyleSheet("background-color: #2e7d32; color: white; border-radius: 5px; padding: 10px;")
        elif status == "DEGRADED":
            self.status_label.setText("🟡 SYSTEM STATUS: FAULTY SENSORS")
            self.status_label.setStyleSheet("background-color: #f9a825; color: black; border-radius: 5px; padding: 10px;")
        else: # ALARM
            self.status_label.setText("🔴 SYSTEM STATUS: ACTIVE ALARMS")
            self.status_label.setStyleSheet("background-color: #c62828; color: white; border-radius: 5px; padding: 10px;")

    def update_sensor_row(self, reading: SensorReading, is_alarm: bool):
        # find row
        row = list(SENSORS_CONFIG.keys()).index(reading.sensor_name)
        
        self.table.item(row, 1).setText(f"{reading.value:.2f} {SENSORS_CONFIG[reading.sensor_name]['unit']}")
        self.table.item(row, 2).setText(reading.timestamp.strftime("%H:%M:%S.%f")[:-3])
        
        # Strict Priority: Faulty (Yellow) > Alarm (Red) > OK (Green)
        bg_color = QColor(Qt.transparent)
        text_color = QColor(Qt.white)
        status_text = "OK"
        
        if reading.status != "OK":
            bg_color = QColor("#f9a825") # Yellow
            text_color = QColor(Qt.black)
            status_text = "FAULTY"
        elif is_alarm:
            bg_color = QColor("#c62828") # Red
            status_text = "ALARM"
        else:
            bg_color = QColor("#2e7d32") # Green
            status_text = "OK"

        self.table.item(row, 3).setText(status_text)
        
        for col in range(4):
            item = self.table.item(row, col)
            item.setBackground(bg_color)
            item.setForeground(text_color)

    def add_alarm_to_log(self, alarm: AlarmEvent):
        row_position = 0 # Insert at top
        self.alarm_log.insertRow(row_position)
        self.alarm_log.setItem(row_position, 0, QTableWidgetItem(alarm.timestamp.strftime("%H:%M:%S")))
        self.alarm_log.setItem(row_position, 1, QTableWidgetItem(alarm.sensor_name))
        self.alarm_log.setItem(row_position, 2, QTableWidgetItem(str(alarm.value)))
        self.alarm_log.setItem(row_position, 3, QTableWidgetItem(alarm.alarm_type))
        self.alarm_log.setItem(row_position, 4, QTableWidgetItem(alarm.message))
        
        # Cleanup old logs if too many
        if self.alarm_log.rowCount() > 50:
            self.alarm_log.removeRow(50)

    def update_plots(self):
        for name, data_deque in self.readings.items():
            if not data_deque:
                continue
            
            # Use relative time for X-axis
            start_time = data_deque[0].timestamp.timestamp()
            x = [r.timestamp.timestamp() - start_time for r in data_deque]
            y = [r.value for r in data_deque]
            self.canvases[name].update_plot(x, y)
