import time
import threading
from collections import deque, defaultdict
from dataclasses import dataclass
from typing import Dict, List, Tuple

# Import core functionality
from data_rate_core import DataRateTracker, DataRateEntry

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
from PyQt6.QtCore import QTimer, QThread, pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QCheckBox,
    QGridLayout,
    QFrame,
    QSizePolicy,
)


class DataRateGraphWidget(QWidget):
    def __init__(self, data_tracker: DataRateTracker, parent=None):
        super().__init__(parent)
        self.data_tracker = data_tracker
        self.init_ui()
        self.setup_plot()

    def init_ui(self):
        self.setStyleSheet(
            """
            DataRateGraphWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8fafc);
                border-radius: 12px;
                border: 2px solid #e2e8f0;
            }
        """
        )

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        self.setLayout(layout)

        # Title
        title_label = QLabel("📊 Network Data Rate Monitor")
        title_label.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: 700;
                color: #1f2937;
                padding: 10px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #a5b4fc);
                color: white;
                border-radius: 8px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """
        )
        layout.addWidget(title_label)

        # Create matplotlib figure
        self.figure = Figure(figsize=(12, 8), facecolor="white")
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.canvas)

        # Controls
        controls_layout = QHBoxLayout()

        self.time_window_combo = QComboBox()
        self.time_window_combo.addItems(["5s", "10s", "30s", "60s"])
        self.time_window_combo.setCurrentText("10s")
        self.time_window_combo.currentTextChanged.connect(self.update_time_window)
        controls_layout.addWidget(QLabel("Time Window:"))
        controls_layout.addWidget(self.time_window_combo)

        self.show_video_cb = QCheckBox("Video")
        self.show_audio_cb = QCheckBox("Audio")
        self.show_text_cb = QCheckBox("Text/File")
        self.show_video_cb.setChecked(True)
        self.show_audio_cb.setChecked(True)
        self.show_text_cb.setChecked(True)

        controls_layout.addWidget(QLabel("Show:"))
        controls_layout.addWidget(self.show_video_cb)
        controls_layout.addWidget(self.show_audio_cb)
        controls_layout.addWidget(self.show_text_cb)
        controls_layout.addStretch()

        layout.addLayout(controls_layout)

    def setup_plot(self):
        # Clear figure
        self.figure.clear()

        # Create subplots
        self.ax1 = self.figure.add_subplot(221)  # Total rates
        self.ax2 = self.figure.add_subplot(222)  # By data type
        self.ax3 = self.figure.add_subplot(223)  # Cumulative data
        self.ax4 = self.figure.add_subplot(224)  # Rate over time

        self.figure.suptitle(
            "Network Data Rate Monitor", fontsize=16, fontweight="bold"
        )

        # Initialize data storage for plotting
        self.time_data = deque(maxlen=200)
        self.sent_data = deque(maxlen=200)
        self.received_data = deque(maxlen=200)

        # Setup timer for updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plots)
        self.timer.start(1000)  # Update every second

    def update_time_window(self, text):
        pass  # Will be used to change time window for calculations

    def format_bytes(self, bytes_val):
        """Convert bytes to human readable format"""
        return self.data_tracker.format_bytes(bytes_val)

    def update_plots(self):
        time_window_map = {"5s": 5, "10s": 10, "30s": 30, "60s": 60}
        time_window = time_window_map.get(self.time_window_combo.currentText(), 10)

        # Get current data
        rate_data = self.data_tracker.get_rate_data(time_window)
        current_time = time.time()

        # Update time series data
        self.time_data.append(current_time)
        self.sent_data.append(rate_data["total_sent"])
        self.received_data.append(rate_data["total_received"])

        # Clear all subplots
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
            ax.clear()

        # Plot 1: Total current rates (bar chart)
        self.ax1.bar(
            ["Sent", "Received"],
            [rate_data["total_sent"], rate_data["total_received"]],
            color=["#ef4444", "#10b981"],
        )
        self.ax1.set_title("Current Data Rate")
        self.ax1.set_ylabel("Bytes/sec")
        for i, v in enumerate([rate_data["total_sent"], rate_data["total_received"]]):
            self.ax1.text(
                i,
                v + max(rate_data["total_sent"], rate_data["total_received"]) * 0.01,
                self.format_bytes(v),
                ha="center",
                va="bottom",
            )

        # Plot 2: By data type (pie chart if data exists)
        by_type = rate_data["by_type"]
        if by_type:
            labels = []
            sizes = []
            colors = {
                "VIDEO": "#6366f1",
                "AUDIO": "#f59e0b",
                "TEXT": "#10b981",
                "FILE": "#8b5cf6",
            }

            for data_type, rates in by_type.items():
                total_rate = rates["sent"] + rates["received"]
                if total_rate > 0:
                    labels.append(f"{data_type}\n({self.format_bytes(total_rate)}/s)")
                    sizes.append(total_rate)

            if sizes:
                pie_colors = [
                    colors.get(label.split("\n")[0], "#6b7280") for label in labels
                ]
                self.ax2.pie(sizes, labels=labels, autopct="%1.1f%%", colors=pie_colors)
            self.ax2.set_title("Data Rate by Type")

        # Plot 3: Cumulative data transferred
        self.ax3.bar(
            ["Total Sent", "Total Received"],
            [rate_data["total_bytes_sent"], rate_data["total_bytes_received"]],
            color=["#ef4444", "#10b981"],
        )
        self.ax3.set_title("Total Data Transferred")
        self.ax3.set_ylabel("Bytes")
        for i, v in enumerate(
            [rate_data["total_bytes_sent"], rate_data["total_bytes_received"]]
        ):
            self.ax3.text(
                i,
                v
                + max(rate_data["total_bytes_sent"], rate_data["total_bytes_received"])
                * 0.01,
                self.format_bytes(v),
                ha="center",
                va="bottom",
            )

        # Plot 4: Rate over time
        if len(self.time_data) > 1:
            time_offset = min(self.time_data)
            x_data = [(t - time_offset) for t in self.time_data]
            self.ax4.plot(x_data, list(self.sent_data), "r-", label="Sent", linewidth=2)
            self.ax4.plot(
                x_data, list(self.received_data), "g-", label="Received", linewidth=2
            )
            self.ax4.set_title("Data Rate Over Time")
            self.ax4.set_xlabel("Time (seconds)")
            self.ax4.set_ylabel("Bytes/sec")
            self.ax4.legend()
            self.ax4.grid(True, alpha=0.3)

        # Adjust layout and refresh
        self.figure.tight_layout()
        self.canvas.draw()


class DataRateMonitorWindow(QWidget):
    def __init__(self, data_tracker: DataRateTracker, parent=None):
        super().__init__(parent)
        self.data_tracker = data_tracker
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("📊 Data Rate Monitor - Lets Meet")
        self.setGeometry(200, 200, 1000, 700)

        # Modern window styling
        self.setStyleSheet(
            """
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8fafc, stop:1 #e2e8f0);
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """
        )

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        self.setLayout(layout)

        # Header with stats
        header_frame = QFrame()
        header_frame.setStyleSheet(
            """
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #a5b4fc);
                border-radius: 12px;
                padding: 15px;
            }
        """
        )
        header_layout = QHBoxLayout(header_frame)

        self.stats_label = QLabel("📊 Monitoring Active...")
        self.stats_label.setStyleSheet(
            """
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: 700;
            }
        """
        )
        header_layout.addWidget(self.stats_label)
        header_layout.addStretch()

        layout.addWidget(header_frame)

        # Graph widget
        self.graph_widget = DataRateGraphWidget(self.data_tracker)
        layout.addWidget(self.graph_widget)

        # Controls
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        refresh_btn.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #10b981, stop:1 #34d399);
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                color: white;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #059669, stop:1 #10b981);
            }
        """
        )

        controls_layout.addWidget(refresh_btn)
        controls_layout.addStretch()

        layout.addWidget(controls_frame)

        # Update stats timer
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_stats)
        self.stats_timer.start(2000)  # Update every 2 seconds

    def update_stats(self):
        rate_data = self.data_tracker.get_rate_data(10)
        total_sent = self.data_tracker.format_bytes(rate_data["total_bytes_sent"])
        total_received = self.data_tracker.format_bytes(rate_data["total_bytes_received"])
        current_rate = self.data_tracker.format_bytes(
            rate_data["total_sent"] + rate_data["total_received"]
        )

        self.stats_label.setText(
            f"📊 Total Sent: {total_sent} | Total Received: {total_received} | Current Rate: {current_rate}/s"
        )

    def refresh_data(self):
        self.graph_widget.update_plots()

    def update_stats(self):
        rate_data = self.data_tracker.get_rate_data(10)
        total_sent = self.data_tracker.format_bytes(rate_data["total_bytes_sent"])
        total_received = self.data_tracker.format_bytes(rate_data["total_bytes_received"])
        current_rate = self.data_tracker.format_bytes(
            rate_data["total_sent"] + rate_data["total_received"]
        )

        self.stats_label.setText(
            f"📊 Total Sent: {total_sent} | Total Received: {total_received} | Current Rate: {current_rate}/s"
        )

    def refresh_data(self):
        self.graph_widget.update_plots()

    def closeEvent(self, event):
        self.stats_timer.stop()
        self.graph_widget.timer.stop()
        super().closeEvent(event)
