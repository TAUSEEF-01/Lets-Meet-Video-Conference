import os
import cv2
import pyaudio
from PyQt6.QtCore import Qt, QThread, QTimer, QSize, QRunnable, pyqtSlot
from PyQt6.QtGui import QImage, QPixmap, QActionGroup, QIcon
from PyQt6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QDockWidget,
    QLabel,
    QWidget,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QComboBox,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QDialog,
    QMenu,
    QWidgetAction,
    QCheckBox,
    QSizePolicy,
)

from constants import *
from data_rate_core import DataRateTracker
from data_rate_monitor import DataRateMonitorWindow

# Camera
CAMERA_RES = "240p"
LAYOUT_RES = "900p"
frame_size = {
    "240p": (352, 240),
    "360p": (480, 360),
    "480p": (640, 480),
    "560p": (800, 560),
    "720p": (1080, 720),
    "900p": (1400, 900),
}
FRAME_WIDTH = frame_size[CAMERA_RES][0]
FRAME_HEIGHT = frame_size[CAMERA_RES][1]

# Image Encoding
ENABLE_ENCODE = True
ENCODE_PARAM = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

# frame for no camera
NOCAM_FRAME = cv2.imread("img/nocam.jpeg")
# crop center part of the nocam frame
nocam_h, nocam_w = NOCAM_FRAME.shape[:2]
x, y = (nocam_w - FRAME_WIDTH) // 2, (nocam_h - FRAME_HEIGHT) // 2
NOCAM_FRAME = NOCAM_FRAME[y : y + FRAME_HEIGHT, x : x + FRAME_WIDTH]
# frame for no microphone
NOMIC_FRAME = cv2.imread("img/nomic.jpeg")

# Audio
ENABLE_AUDIO = True
SAMPLE_RATE = 48000
BLOCK_SIZE = 2048
pa = pyaudio.PyAudio()


class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self):
        self.fn(*self.args, **self.kwargs)


class Microphone:
    def __init__(self):
        self.stream = pa.open(
            rate=SAMPLE_RATE,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=BLOCK_SIZE,
        )

    def get_data(self):
        return self.stream.read(BLOCK_SIZE)


class AudioThread(QThread):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.stream = pa.open(
            rate=SAMPLE_RATE,
            channels=1,
            format=pyaudio.paInt16,
            output=True,
            frames_per_buffer=BLOCK_SIZE,
        )
        self.connected = True

    def run(self):
        # if this is the current client, then don't play audio
        if self.client.microphone is not None:
            return
        while self.connected:
            self.update_audio()

    def update_audio(self):
        data = self.client.get_audio()
        if data is not None:
            self.stream.write(data)


class Camera:
    def __init__(self):
        self.cap = cv2.VideoCapture(2)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)

    def get_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(
                frame, frame_size[CAMERA_RES], interpolation=cv2.INTER_AREA
            )
            if ENABLE_ENCODE:
                _, frame = cv2.imencode(".jpg", frame, ENCODE_PARAM)
            return frame


class VideoWidget(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.parent_window = parent
        self.init_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_video)
        self.init_video()

    def init_ui(self):
        # Modern styling without unsupported properties
        self.setStyleSheet(
            """
            VideoWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a5568, stop:1 #2d3748);
                border: 2px solid #6366f1;
                border-radius: 22px;
                margin: 10px;
            }
            VideoWidget:hover {
                border: 2.5px solid #a5b4fc;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a67d8, stop:1 #4c51bf);
            }
        """
        )

        self.video_viewer = QLabel()
        if self.client.current_device:
            self.name_label = QLabel(f"🎥 You - {self.client.name}")
        else:
            self.name_label = QLabel(f"👤 {self.client.name}")

        self.video_viewer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_viewer.setStyleSheet(
            """
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a202c, stop:1 #2d3748);
                border-radius: 16px;
                border: 2px solid #21262d;
                min-height: 80px;
            }
        """
        )

        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet(
            """
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #a5b4fc);
                color: #fff;
                font-weight: 700;
                font-size: 13px;
                font-family: 'Segoe UI', Arial, sans-serif;
                border-radius: 8px;
                padding: 6px 12px;
                margin: 4px;
                border: 1px solid #4c63d2;
            }
        """
        )

        self.layout = QVBoxLayout()
        self.layout.setSpacing(8)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.addWidget(self.video_viewer)
        self.layout.addWidget(self.name_label)
        self.setLayout(self.layout)

    def init_video(self):
        self.timer.start(30)

    def update_video(self):
        frame = self.client.get_video()
        if frame is None:
            frame = NOCAM_FRAME.copy()
        elif ENABLE_ENCODE:
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

        frame = cv2.resize(
            frame, (FRAME_WIDTH, FRAME_HEIGHT), interpolation=cv2.INTER_AREA
        )

        if self.client.audio_data is None:
            # replace bottom center part of the frame with nomic frame
            nomic_h, nomic_w, _ = NOMIC_FRAME.shape
            x, y = FRAME_WIDTH // 2 - nomic_w // 2, FRAME_HEIGHT - 50
            frame[y : y + nomic_h, x : x + nomic_w] = NOMIC_FRAME.copy()

        h, w, ch = frame.shape
        bytes_per_line = ch * w
        q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        self.video_viewer.setPixmap(QPixmap.fromImage(q_img))

    def resizeEvent(self, event):
        """Handle dynamic resizing of video widget elements"""
        super().resizeEvent(event)
        size = event.size()

        # Adjust font size based on widget size
        base_font_size = max(10, min(16, size.width() // 25))
        self.name_label.setStyleSheet(
            f"""
            QLabel {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #a5b4fc);
                color: #fff;
                font-weight: 700;
                font-size: {base_font_size}px;
                font-family: 'Segoe UI', Arial, sans-serif;
                border-radius: 8px;
                padding: {max(4, base_font_size//3)}px {max(8, base_font_size//2)}px;
                margin: 4px;
                border: 1px solid #4c63d2;
            }}
        """
        )


class VideoListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_items = {}
        self.init_ui()

    def init_ui(self):
        self.setFlow(QListWidget.Flow.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setMovement(QListWidget.Movement.Static)

        # Clean gradient background
        self.setStyleSheet(
            """
            QListWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e293b, stop:1 #0f172a);
                border: 2px solid #374151;
                padding: 18px;
                border-radius: 18px;
            }
            QListWidget::item {
                border: none;
                margin: 7px;
                border-radius: 16px;
                background: transparent;
            }
            QListWidget::item:selected {
                background: none;
            }
        """
        )

    def add_client(self, client):
        video_widget = VideoWidget(client)

        item = QListWidgetItem()
        item.setFlags(
            item.flags() & ~(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        )
        if client.current_device:
            self.insertItem(0, item)
        else:
            self.addItem(item)
        item.setSizeHint(QSize(FRAME_WIDTH, FRAME_HEIGHT))
        self.setItemWidget(item, video_widget)
        self.all_items[client.name] = item
        self.resize_widgets()

    def resize_widgets(self, res: str = None):
        global FRAME_WIDTH, FRAME_HEIGHT, LAYOUT_RES
        n = self.count()
        if res is None:
            if n <= 1:
                res = "900p"
            elif n <= 4:
                res = "480p"
            elif n <= 6:
                res = "360p"
            else:
                res = "240p"
        new_size = frame_size[res]

        if new_size == (FRAME_WIDTH, FRAME_HEIGHT):
            return
        else:
            FRAME_WIDTH, FRAME_HEIGHT = new_size
            LAYOUT_RES = res

        for i in range(n):
            self.item(i).setSizeHint(QSize(FRAME_WIDTH, FRAME_HEIGHT))

    def remove_client(self, name: str):
        self.takeItem(self.row(self.all_items[name]))
        self.all_items.pop(name)
        self.resize_widgets()


class ChatWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.init_ui()

    def init_ui(self):
        # Clean modern styling without unsupported properties
        self.setStyleSheet(
            """
            ChatWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8fafc, stop:1 #e2e8f0);
                border-radius: 28px;
                padding: 18px;
                border: 2px solid #c7d2fe;
            }
        """
        )

        self.layout = QVBoxLayout()
        self.layout.setSpacing(20)
        self.layout.setContentsMargins(25, 25, 25, 25)
        self.setLayout(self.layout)

        self.title_label = QLabel("💬 Chat Hub")
        self.title_label.setStyleSheet(
            """
            QLabel {
                font-size: 22px;
                font-weight: 900;
                color: #fff;
                padding: 18px 24px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #a5b4fc);
                border-radius: 16px;
                margin-bottom: 10px;
                border: 2px solid #6366f1;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """
        )
        self.layout.addWidget(self.title_label)

        self.central_widget = QTextEdit(self)
        self.central_widget.setReadOnly(True)
        self.central_widget.setStyleSheet(
            """
            QTextEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8fafc);
                border: 2px solid #e0e7ff;
                border-radius: 18px;
                padding: 18px;
                font-size: 15px;
                color: #334155;
                font-family: 'Segoe UI', Arial, sans-serif;
                selection-background-color: #a5b4fc;
                min-height: 180px;
            }
            QTextEdit:focus {
                border: 2px solid #6366f1;
                background: #fff;
            }
        """
        )
        self.central_widget.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
        )
        self.layout.addWidget(self.central_widget)

        self.clients_menu = QMenu("Clients", self)
        self.clients_menu.aboutToShow.connect(self.resize_clients_menu)
        self.clients_menu.setStyleSheet(
            """
            QMenu {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8fafc);
                border: 2px solid #a5b4fc;
                border-radius: 14px;
                padding: 8px;
            }
            QMenu::item {
                padding: 12px 18px;
                border-radius: 10px;
                margin: 2px;
                font-size: 14px;
            }
            QMenu::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #a5b4fc);
                color: #fff;
            }
        """
        )
        self.clients_checkboxes = {}
        self.clients_menu_actions = {}

        self.select_all_checkbox, _ = self.add_client("")
        self.clients_menu.addSeparator()

        # Modern styled buttons with dynamic sizing
        self.clients_button = QPushButton("👥 Select Recipients", self)
        self.clients_button.setMenu(self.clients_menu)
        self.clients_button.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #a5b4fc);
                border: none;
                border-radius: 16px;
                padding: 14px 26px;
                font-size: 15px;
                font-weight: 700;
                color: #fff;
                font-family: 'Segoe UI', Arial, sans-serif;
                min-height: 40px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a67d8, stop:1 #818cf8);
            }
            QPushButton:pressed {
                background: #4c51bf;
            }
        """
        )
        self.layout.addWidget(self.clients_button)

        self.file_button = QPushButton("📎 Send File", self)
        self.file_button.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f59e0b, stop:1 #fbbf24);
                border: none;
                border-radius: 16px;
                padding: 14px 26px;
                font-size: 15px;
                font-weight: 700;
                color: #fff;
                font-family: 'Segoe UI', Arial, sans-serif;
                min-height: 40px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #d97706, stop:1 #f59e0b);
            }
            QPushButton:pressed {
                background: #b45309;
            }
        """
        )
        self.layout.addWidget(self.file_button)

        self.send_layout = QHBoxLayout()
        self.send_layout.setSpacing(15)
        self.layout.addLayout(self.send_layout)

        self.line_edit = QLineEdit(self)
        self.line_edit.setPlaceholderText("💭 Type your message here...")
        self.line_edit.setStyleSheet(
            """
            QLineEdit {
                border: 2px solid #a5b4fc;
                border-radius: 14px;
                padding: 14px 20px;
                font-size: 15px;
                background: #ffffff;
                color: #334155;
                font-family: 'Segoe UI', Arial, sans-serif;
                min-height: 20px;
            }
            QLineEdit:focus {
                border: 2px solid #6366f1;
                outline: none;
            }
            QLineEdit:hover {
                border: 2px solid #818cf8;
            }
        """
        )
        self.send_layout.addWidget(self.line_edit)

        self.send_button = QPushButton("📤 Send", self)
        self.send_button.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6366f1, stop:1 #818cf8);
                border: none;
                border-radius: 14px;
                padding: 14px 28px;
                font-size: 15px;
                font-weight: 800;
                color: #fff;
                min-width: 90px;
                min-height: 20px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a67d8, stop:1 #6366f1);
            }
            QPushButton:pressed {
                background: #4c51bf;
            }
        """
        )
        self.send_layout.addWidget(self.send_button)

        self.layout.addSpacing(20)

        # Button container for Leave and End call buttons
        self.button_container = QHBoxLayout()
        self.button_container.setSpacing(12)
        self.layout.addLayout(self.button_container)

        # Leave meeting button
        self.leave_button = QPushButton("🚪 Leave Meeting", self)
        self.leave_button.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f59e0b, stop:1 #fbbf24);
                border: none;
                border-radius: 16px;
                padding: 14px 24px;
                font-size: 15px;
                font-weight: 800;
                color: #fff;
                font-family: 'Segoe UI', Arial, sans-serif;
                min-height: 40px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #d97706, stop:1 #f59e0b);
            }
            QPushButton:pressed {
                background: #b45309;
            }
        """
        )
        self.button_container.addWidget(self.leave_button)

        # End call button with modern danger styling
        self.end_button = QPushButton("📞 End Call", self)
        self.end_button.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ef4444, stop:1 #f87171);
                border: none;
                border-radius: 16px;
                padding: 14px 24px;
                font-size: 15px;
                font-weight: 800;
                color: #fff;
                font-family: 'Segoe UI', Arial, sans-serif;
                min-height: 40px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #dc2626, stop:1 #ef4444);
            }
            QPushButton:pressed {
                background: #b91c1c;
            }
        """
        )
        self.button_container.addWidget(self.end_button)

    def add_client(self, name: str):
        checkbox = QCheckBox(name, self)
        checkbox.setChecked(True)
        action_widget = QWidgetAction(self)
        action_widget.setDefaultWidget(checkbox)
        self.clients_menu.addAction(action_widget)

        if name == "":  # Select All Checkbox
            checkbox.setText("Select All")
            checkbox.stateChanged.connect(
                lambda state: self.on_checkbox_click(state, is_select_all=True)
            )
            return checkbox, action_widget

        checkbox.stateChanged.connect(lambda state: self.on_checkbox_click(state))
        self.clients_checkboxes[name] = checkbox
        self.clients_menu_actions[name] = action_widget
        return checkbox, action_widget

    def remove_client(self, name: str):
        self.clients_menu.removeAction(self.clients_menu_actions[name])
        self.clients_menu_actions.pop(name)
        self.clients_checkboxes.pop(name)

    def resize_clients_menu(self):
        self.clients_menu.setMinimumWidth(self.clients_button.width())

    def on_checkbox_click(self, is_checked: bool, is_select_all: bool = False):
        if is_select_all:
            for client_checkbox in self.clients_checkboxes.values():
                client_checkbox.blockSignals(True)
                client_checkbox.setChecked(is_checked)
                client_checkbox.blockSignals(False)
        else:
            if not is_checked:
                self.select_all_checkbox.blockSignals(True)
                self.select_all_checkbox.setChecked(False)
                self.select_all_checkbox.blockSignals(False)

    def selected_clients(self):
        selected = []
        for name, checkbox in self.clients_checkboxes.items():
            if checkbox.isChecked():
                selected.append(name)
        return tuple(selected)

    def get_file(self):
        file_path = QFileDialog.getOpenFileName(
            None, "Select File", options=QFileDialog.Option.DontUseNativeDialog
        )[0]
        return file_path

    def get_text(self):
        text = self.line_edit.text()
        self.line_edit.clear()
        return text

    def add_msg(self, from_name: str, to_name: str, msg: str):
        # Clean chat bubbles without unsupported properties
        timestamp = __import__("datetime").datetime.now().strftime("%H:%M")

        if from_name == "You":
            bubble_style = """
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #a5b4fc);
                color: white;
                margin-left: 60px;
                text-align: right;
            """
            sender_style = "color: #6366f1; text-align: right; margin-left: 60px;"
        else:
            bubble_style = """
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f8fafc, stop:1 #e2e8f0);
                color: #334155;
                margin-right: 60px;
                border: 2px solid #a5b4fc;
            """
            sender_style = "color: #334155; margin-right: 60px;"

        html = f"""
        <div style="margin-bottom: 22px; font-family: 'Segoe UI', Arial, sans-serif;">
            <div style="{sender_style} font-weight: 700; font-size: 15px; margin-bottom: 7px;">
                {from_name} <span style="color: #64748b; font-weight: 400;">to {to_name}</span>
                <span style="color: #6366f1; font-size: 12px; margin-left: 12px;">{timestamp}</span>
            </div>
            <div style="{bubble_style} padding: 18px 24px; border-radius: 22px; 
                        display: inline-block; max-width: 80%; word-wrap: break-word;
                        font-size: 16px; line-height: 1.5;">
                {msg}
            </div>
        </div>
        """
        self.central_widget.append(html)
        scrollbar = self.central_widget.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("🎥 Video Conference - Join Now")
        self.setFixedSize(420, 240)

        # Clean modern styling
        self.setStyleSheet(
            """
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6366f1, stop:1 #a5b4fc);
                border-radius: 20px;
            }
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: 700;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit {
                border: 2px solid rgba(255, 255, 255, 0.5);
                border-radius: 12px;
                padding: 14px 18px;
                font-size: 16px;
                background-color: #fff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit:focus {
                border: 2px solid #ffffff;
                outline: none;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ffffff, stop:1 #f8fafc);
                border: none;
                border-radius: 12px;
                padding: 14px 28px;
                font-size: 16px;
                font-weight: 700;
                color: #6366f1;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f1f5f9, stop:1 #e2e8f0);
            }
            QPushButton:pressed {
                background: #e2e8f0;
            }
        """
        )

        self.layout = QGridLayout()
        self.layout.setSpacing(20)
        self.layout.setContentsMargins(35, 35, 35, 35)
        self.setLayout(self.layout)

        self.title_label = QLabel("🎥 Join Video Conference")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(
            """
            QLabel {
                font-size: 20px;
                font-weight: 800;
                color: white;
                margin-bottom: 15px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """
        )
        self.layout.addWidget(self.title_label, 0, 0, 1, 2)

        self.name_label = QLabel("👤 Username:")
        self.layout.addWidget(self.name_label, 1, 0)

        self.name_edit = QLineEdit(self)
        self.name_edit.setPlaceholderText("Enter your username...")
        self.layout.addWidget(self.name_edit, 1, 1)

        self.button = QPushButton("🚀 Join Conference", self)
        self.layout.addWidget(self.button, 2, 0, 1, 2)

        self.button.clicked.connect(self.login)

    def get_name(self):
        return self.name_edit.text()

    def login(self):
        if self.get_name() == "":
            QMessageBox.critical(self, "Error", "Username cannot be empty")
            return
        if " " in self.get_name():
            QMessageBox.critical(self, "Error", "Username cannot contain spaces")
            return
        self.accept()

    def close(self):
        self.reject()


class MainWindow(QMainWindow):
    def __init__(self, client, server_conn):
        super().__init__()
        self.client = client
        self.server_conn = server_conn
        self.audio_threads = {}

        # Initialize data rate tracker
        self.data_rate_tracker = DataRateTracker()
        self.data_rate_window = None

        # Pass tracker to server connection
        self.server_conn.data_rate_tracker = self.data_rate_tracker

        self.server_conn.add_client_signal.connect(self.add_client)
        self.server_conn.remove_client_signal.connect(self.remove_client)
        self.server_conn.add_msg_signal.connect(self.add_msg)

        self.login_dialog = LoginDialog(self)
        if not self.login_dialog.exec():
            exit()

        self.server_conn.name = self.login_dialog.get_name()
        self.server_conn.start()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("🎥 Lets Meet - Modern Video Conference")
        self.resize(1100, 600)

        # Center the window
        screen_geometry = self.screen().availableGeometry()
        x = (screen_geometry.width() - 1100) // 2
        y = (screen_geometry.height() - 600) // 2
        self.move(x, y)
        self.setMinimumSize(700, 400)

        # Clean modern main window styling
        self.setStyleSheet(
            """
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6366f1, stop:1 #a5b4fc);
            }
            QMenuBar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4c63d2, stop:1 #6366f1);
                color: white;
                font-size: 14px;
                font-weight: 700;
                padding: 8px;
                border-radius: 6px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 10px 18px;
                border-radius: 6px;
                margin: 2px;
            }
            QMenuBar::item:selected {
                background-color: rgba(255, 255, 255, 0.2);
            }
            QMenu {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8fafc);
                border: 2px solid #a5b4fc;
                border-radius: 12px;
                padding: 8px;
                font-size: 13px;
            }
            QMenu::item {
                padding: 10px 18px;
                border-radius: 8px;
                margin: 2px;
            }
            QMenu::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #a5b4fc);
                color: #fff;
            }
        """
        )

        self.video_list_widget = VideoListWidget()
        self.setCentralWidget(self.video_list_widget)

        # Enhanced sidebar styling with dynamic sizing
        self.sidebar = QDockWidget("💬 Chat", self)
        self.sidebar.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.sidebar.setMinimumWidth(300)
        self.sidebar.setMaximumWidth(500)

        self.chat_widget = ChatWidget(self)
        self.sidebar.setWidget(self.chat_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.sidebar)

        # Connect buttons
        self.chat_widget.send_button.clicked.connect(lambda: self.send_msg(TEXT))
        self.chat_widget.line_edit.returnPressed.connect(lambda: self.send_msg(TEXT))
        self.chat_widget.file_button.clicked.connect(lambda: self.send_msg(FILE))
        self.chat_widget.leave_button.clicked.connect(self.leave_meeting)
        self.chat_widget.end_button.clicked.connect(self.close)

        # menus for camera and microphone toggle
        self.camera_menu = self.menuBar().addMenu("📹 Camera")
        self.microphone_menu = self.menuBar().addMenu("🎤 Microphone")
        self.layout_menu = self.menuBar().addMenu("📐 Layout")
        self.monitor_menu = self.menuBar().addMenu("📊 Monitor")

        self.camera_menu.addAction("📹 Disable Camera", self.toggle_camera)
        self.microphone_menu.addAction("🎤 Disable Microphone", self.toggle_microphone)

        # Add data rate monitoring menu
        self.monitor_menu.addAction(
            "📊 Show Data Rate Monitor", self.show_data_rate_monitor
        )
        self.monitor_menu.addSeparator()
        self.monitor_menu.addAction("📈 Reset Statistics", self.reset_data_rate_stats)

        self.layout_actions = {}
        layout_action_group = QActionGroup(self)
        for res in frame_size.keys():
            layout_action = layout_action_group.addAction(f"📐 {res}")
            layout_action.setCheckable(True)
            layout_action.triggered.connect(
                lambda checked, res=res: self.video_list_widget.resize_widgets(res)
            )
            if res == LAYOUT_RES:
                layout_action.setChecked(True)
            self.layout_menu.addAction(layout_action)
            self.layout_actions[res] = layout_action

    def add_client(self, client):
        self.video_list_widget.add_client(client)
        self.layout_actions[LAYOUT_RES].setChecked(True)
        if ENABLE_AUDIO:
            self.audio_threads[client.name] = AudioThread(client, self)
            self.audio_threads[client.name].start()
        if not client.current_device:
            self.chat_widget.add_client(client.name)

    def remove_client(self, name: str):
        self.video_list_widget.remove_client(name)
        self.layout_actions[LAYOUT_RES].setChecked(True)
        if ENABLE_AUDIO:
            self.audio_threads[name].connected = False
            self.audio_threads[name].wait()
            self.audio_threads.pop(name)
            print(f"Audio Thread for {name} terminated")
        print(f"removing {name} chat...")
        self.chat_widget.remove_client(name)
        print(f"{name} removed")

    def send_msg(self, data_type: str = TEXT):
        selected = self.chat_widget.selected_clients()
        if len(selected) == 0:
            QMessageBox.critical(self, "Error", "Select at least one client")
            return

        if data_type == TEXT:
            msg_text = self.chat_widget.get_text()
        elif data_type == FILE:
            filepath = self.chat_widget.get_file()
            if not filepath:
                return
            msg_text = os.path.basename(filepath)
        else:
            print(f"{data_type} data_type not supported")
            return

        if msg_text == "":
            QMessageBox.critical(self, "Error", f"{data_type} cannot be empty")
            return

        msg = Message(
            self.client.name, POST, data_type, data=msg_text, to_names=selected
        )
        self.server_conn.send_msg(self.server_conn.main_socket, msg)

        if data_type == FILE:
            send_file_thread = Worker(self.server_conn.send_file, filepath, selected)
            self.server_conn.threadpool.start(send_file_thread)
            msg_text = f"Sending {msg_text}..."

        self.chat_widget.add_msg("You", ", ".join(selected), msg_text)

    def add_msg(self, from_name: str, msg: str):
        self.chat_widget.add_msg(from_name, "You", msg)

    def toggle_camera(self):
        if self.client.camera_enabled:
            self.camera_menu.actions()[0].setText("📹 Enable Camera")
        else:
            self.camera_menu.actions()[0].setText("📹 Disable Camera")
        self.client.camera_enabled = not self.client.camera_enabled

    def toggle_microphone(self):
        if self.client.microphone_enabled:
            self.microphone_menu.actions()[0].setText("🎤 Enable Microphone")
        else:
            self.microphone_menu.actions()[0].setText("🎤 Disable Microphone")
        self.client.microphone_enabled = not self.client.microphone_enabled

    def leave_meeting(self):
        """Handle leaving the meeting without closing the application"""
        reply = QMessageBox.question(
            self,
            "Leave Meeting",
            "Are you sure you want to leave the meeting?\nYou can rejoin by restarting the application.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Disconnect from server but keep the window open
            self.server_conn.connected = False
            self.server_conn.disconnect_server()

            # Show a message that user has left
            self.chat_widget.add_msg(
                "System", "You", "You have left the meeting. Please restart to rejoin."
            )

            # Disable controls
            self.chat_widget.send_button.setEnabled(False)
            self.chat_widget.line_edit.setEnabled(False)
            self.chat_widget.file_button.setEnabled(False)
            self.chat_widget.clients_button.setEnabled(False)
            self.chat_widget.leave_button.setEnabled(False)

    def closeEvent(self, event):
        """Handle window close event to properly cleanup resources."""
        if self.client.camera:
            self.client.camera.release()
        super().closeEvent(event)

    def resizeEvent(self, event):
        """Handle dynamic resizing of main window elements"""
        super().resizeEvent(event)
        size = event.size()

        # Adjust sidebar width based on window size
        sidebar_width = max(250, min(400, size.width() // 3))
        self.sidebar.setMinimumWidth(sidebar_width)
        self.sidebar.setMaximumWidth(sidebar_width + 50)

        # Adjust menu bar font size
        menu_font_size = max(12, min(16, size.width() // 80))
        self.setStyleSheet(
            f"""
            QMainWindow {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6366f1, stop:1 #a5b4fc);
            }}
            QMenuBar {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4c63d2, stop:1 #6366f1);
                color: white;
                font-size: {menu_font_size}px;
                font-weight: 700;
                padding: {max(6, menu_font_size//2)}px;
                border-radius: 6px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QMenuBar::item {{
                background-color: transparent;
                padding: {max(8, menu_font_size//1.5)}px {max(14, menu_font_size)}px;
                border-radius: 6px;
                margin: 2px;
            }}
            QMenuBar::item:selected {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
            QMenu {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8fafc);
                border: 2px solid #a5b4fc;
                border-radius: 12px;
                padding: 8px;
                font-size: {max(11, menu_font_size-2)}px;
            }}
            QMenu::item {{
                padding: {max(8, menu_font_size//1.5)}px {max(14, menu_font_size)}px;
                border-radius: 8px;
                margin: 2px;
            }}
            QMenu::item:selected {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #a5b4fc);
                color: #fff;
            }}
        """
        )

    def show_data_rate_monitor(self):
        """Show the data rate monitoring window"""
        if self.data_rate_window is None:
            self.data_rate_window = DataRateMonitorWindow(self.data_rate_tracker, self)

        self.data_rate_window.show()
        self.data_rate_window.raise_()
        self.data_rate_window.activateWindow()

    def reset_data_rate_stats(self):
        """Reset data rate statistics"""
        reply = QMessageBox.question(
            self,
            "Reset Statistics",
            "Are you sure you want to reset all data rate statistics?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.data_rate_tracker = DataRateTracker()
            self.server_conn.data_rate_tracker = self.data_rate_tracker
            if self.data_rate_window:
                self.data_rate_window.close()
                self.data_rate_window = None
            QMessageBox.information(
                self, "Reset Complete", "Data rate statistics have been reset."
            )
            QMessageBox.information(
                self, "Reset Complete", "Data rate statistics have been reset."
            )

    def run(self):
        # if this is the current client, then don't play audio
        if self.client.microphone is not None:
            return
        while self.connected:
            self.update_audio()

    def update_audio(self):
        data = self.client.get_audio()
        if data is not None:
            self.stream.write(data)


class Camera:
    def __init__(self):
        self.cap = cv2.VideoCapture(2)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)

    def get_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(
                frame, frame_size[CAMERA_RES], interpolation=cv2.INTER_AREA
            )
            if ENABLE_ENCODE:
                _, frame = cv2.imencode(".jpg", frame, ENCODE_PARAM)
            return frame


class VideoWidget(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.parent_window = parent
        self.init_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_video)
        self.init_video()

    def init_ui(self):
        # Modern styling without unsupported properties
        self.setStyleSheet(
            """
            VideoWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a5568, stop:1 #2d3748);
                border: 2px solid #6366f1;
                border-radius: 22px;
                margin: 10px;
            }
            VideoWidget:hover {
                border: 2.5px solid #a5b4fc;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a67d8, stop:1 #4c51bf);
            }
        """
        )

        self.video_viewer = QLabel()
        if self.client.current_device:
            self.name_label = QLabel(f"🎥 You - {self.client.name}")
        else:
            self.name_label = QLabel(f"👤 {self.client.name}")

        self.video_viewer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_viewer.setStyleSheet(
            """
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a202c, stop:1 #2d3748);
                border-radius: 16px;
                border: 2px solid #21262d;
                min-height: 80px;
            }
        """
        )

        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet(
            """
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #a5b4fc);
                color: #fff;
                font-weight: 700;
                font-size: 13px;
                font-family: 'Segoe UI', Arial, sans-serif;
                border-radius: 8px;
                padding: 6px 12px;
                margin: 4px;
                border: 1px solid #4c63d2;
            }
        """
        )

        self.layout = QVBoxLayout()
        self.layout.setSpacing(8)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.addWidget(self.video_viewer)
        self.layout.addWidget(self.name_label)
        self.setLayout(self.layout)

    def init_video(self):
        self.timer.start(30)

    def update_video(self):
        frame = self.client.get_video()
        if frame is None:
            frame = NOCAM_FRAME.copy()
        elif ENABLE_ENCODE:
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

        frame = cv2.resize(
            frame, (FRAME_WIDTH, FRAME_HEIGHT), interpolation=cv2.INTER_AREA
        )

        if self.client.audio_data is None:
            # replace bottom center part of the frame with nomic frame
            nomic_h, nomic_w, _ = NOMIC_FRAME.shape
            x, y = FRAME_WIDTH // 2 - nomic_w // 2, FRAME_HEIGHT - 50
            frame[y : y + nomic_h, x : x + nomic_w] = NOMIC_FRAME.copy()

        h, w, ch = frame.shape
        bytes_per_line = ch * w
        q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        self.video_viewer.setPixmap(QPixmap.fromImage(q_img))

    def resizeEvent(self, event):
        """Handle dynamic resizing of video widget elements"""
        super().resizeEvent(event)
        size = event.size()

        # Adjust font size based on widget size
        base_font_size = max(10, min(16, size.width() // 25))
        self.name_label.setStyleSheet(
            f"""
            QLabel {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #a5b4fc);
                color: #fff;
                font-weight: 700;
                font-size: {base_font_size}px;
                font-family: 'Segoe UI', Arial, sans-serif;
                border-radius: 8px;
                padding: {max(4, base_font_size//3)}px {max(8, base_font_size//2)}px;
                margin: 4px;
                border: 1px solid #4c63d2;
            }}
        """
        )


class VideoListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_items = {}
        self.init_ui()

    def init_ui(self):
        self.setFlow(QListWidget.Flow.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setMovement(QListWidget.Movement.Static)

        # Clean gradient background
        self.setStyleSheet(
            """
            QListWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e293b, stop:1 #0f172a);
                border: 2px solid #374151;
                padding: 18px;
                border-radius: 18px;
            }
            QListWidget::item {
                border: none;
                margin: 7px;
                border-radius: 16px;
                background: transparent;
            }
            QListWidget::item:selected {
                background: none;
            }
        """
        )

    def add_client(self, client):
        video_widget = VideoWidget(client)

        item = QListWidgetItem()
        item.setFlags(
            item.flags() & ~(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        )
        if client.current_device:
            self.insertItem(0, item)
        else:
            self.addItem(item)
        item.setSizeHint(QSize(FRAME_WIDTH, FRAME_HEIGHT))
        self.setItemWidget(item, video_widget)
        self.all_items[client.name] = item
        self.resize_widgets()

    def resize_widgets(self, res: str = None):
        global FRAME_WIDTH, FRAME_HEIGHT, LAYOUT_RES
        n = self.count()
        if res is None:
            if n <= 1:
                res = "900p"
            elif n <= 4:
                res = "480p"
            elif n <= 6:
                res = "360p"
            else:
                res = "240p"
        new_size = frame_size[res]

        if new_size == (FRAME_WIDTH, FRAME_HEIGHT):
            return
        else:
            FRAME_WIDTH, FRAME_HEIGHT = new_size
            LAYOUT_RES = res

        for i in range(n):
            self.item(i).setSizeHint(QSize(FRAME_WIDTH, FRAME_HEIGHT))

    def remove_client(self, name: str):
        self.takeItem(self.row(self.all_items[name]))
        self.all_items.pop(name)
        self.resize_widgets()


class ChatWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.init_ui()

    def init_ui(self):
        # Clean modern styling without unsupported properties
        self.setStyleSheet(
            """
            ChatWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8fafc, stop:1 #e2e8f0);
                border-radius: 28px;
                padding: 18px;
                border: 2px solid #c7d2fe;
            }
        """
        )

        self.layout = QVBoxLayout()
        self.layout.setSpacing(20)
        self.layout.setContentsMargins(25, 25, 25, 25)
        self.setLayout(self.layout)

        self.title_label = QLabel("💬 Chat Hub")
        self.title_label.setStyleSheet(
            """
            QLabel {
                font-size: 22px;
                font-weight: 900;
                color: #fff;
                padding: 18px 24px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #a5b4fc);
                border-radius: 16px;
                margin-bottom: 10px;
                border: 2px solid #6366f1;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """
        )
        self.layout.addWidget(self.title_label)

        self.central_widget = QTextEdit(self)
        self.central_widget.setReadOnly(True)
        self.central_widget.setStyleSheet(
            """
            QTextEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8fafc);
                border: 2px solid #e0e7ff;
                border-radius: 18px;
                padding: 18px;
                font-size: 15px;
                color: #334155;
                font-family: 'Segoe UI', Arial, sans-serif;
                selection-background-color: #a5b4fc;
                min-height: 180px;
            }
            QTextEdit:focus {
                border: 2px solid #6366f1;
                background: #fff;
            }
        """
        )
        self.central_widget.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
        )
        self.layout.addWidget(self.central_widget)

        self.clients_menu = QMenu("Clients", self)
        self.clients_menu.aboutToShow.connect(self.resize_clients_menu)
        self.clients_menu.setStyleSheet(
            """
            QMenu {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8fafc);
                border: 2px solid #a5b4fc;
                border-radius: 14px;
                padding: 8px;
            }
            QMenu::item {
                padding: 12px 18px;
                border-radius: 10px;
                margin: 2px;
                font-size: 14px;
            }
            QMenu::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #a5b4fc);
                color: #fff;
            }
        """
        )
        self.clients_checkboxes = {}
        self.clients_menu_actions = {}

        self.select_all_checkbox, _ = self.add_client("")
        self.clients_menu.addSeparator()

        # Modern styled buttons with dynamic sizing
        self.clients_button = QPushButton("👥 Select Recipients", self)
        self.clients_button.setMenu(self.clients_menu)
        self.clients_button.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #a5b4fc);
                border: none;
                border-radius: 16px;
                padding: 14px 26px;
                font-size: 15px;
                font-weight: 700;
                color: #fff;
                font-family: 'Segoe UI', Arial, sans-serif;
                min-height: 40px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a67d8, stop:1 #818cf8);
            }
            QPushButton:pressed {
                background: #4c51bf;
            }
        """
        )
        self.layout.addWidget(self.clients_button)

        self.file_button = QPushButton("📎 Send File", self)
        self.file_button.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f59e0b, stop:1 #fbbf24);
                border: none;
                border-radius: 16px;
                padding: 14px 26px;
                font-size: 15px;
                font-weight: 700;
                color: #fff;
                font-family: 'Segoe UI', Arial, sans-serif;
                min-height: 40px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #d97706, stop:1 #f59e0b);
            }
            QPushButton:pressed {
                background: #b45309;
            }
        """
        )
        self.layout.addWidget(self.file_button)

        self.send_layout = QHBoxLayout()
        self.send_layout.setSpacing(15)
        self.layout.addLayout(self.send_layout)

        self.line_edit = QLineEdit(self)
        self.line_edit.setPlaceholderText("💭 Type your message here...")
        self.line_edit.setStyleSheet(
            """
            QLineEdit {
                border: 2px solid #a5b4fc;
                border-radius: 14px;
                padding: 14px 20px;
                font-size: 15px;
                background: #ffffff;
                color: #334155;
                font-family: 'Segoe UI', Arial, sans-serif;
                min-height: 20px;
            }
            QLineEdit:focus {
                border: 2px solid #6366f1;
                outline: none;
            }
            QLineEdit:hover {
                border: 2px solid #818cf8;
            }
        """
        )
        self.send_layout.addWidget(self.line_edit)

        self.send_button = QPushButton("📤 Send", self)
        self.send_button.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6366f1, stop:1 #818cf8);
                border: none;
                border-radius: 14px;
                padding: 14px 28px;
                font-size: 15px;
                font-weight: 800;
                color: #fff;
                min-width: 90px;
                min-height: 20px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a67d8, stop:1 #6366f1);
            }
            QPushButton:pressed {
                background: #4c51bf;
            }
        """
        )
        self.send_layout.addWidget(self.send_button)

        self.layout.addSpacing(20)

        # Button container for Leave and End call buttons
        self.button_container = QHBoxLayout()
        self.button_container.setSpacing(12)
        self.layout.addLayout(self.button_container)

        # Leave meeting button
        self.leave_button = QPushButton("🚪 Leave Meeting", self)
        self.leave_button.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f59e0b, stop:1 #fbbf24);
                border: none;
                border-radius: 16px;
                padding: 14px 24px;
                font-size: 15px;
                font-weight: 800;
                color: #fff;
                font-family: 'Segoe UI', Arial, sans-serif;
                min-height: 40px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #d97706, stop:1 #f59e0b);
            }
            QPushButton:pressed {
                background: #b45309;
            }
        """
        )
        self.button_container.addWidget(self.leave_button)

        # End call button with modern danger styling
        self.end_button = QPushButton("📞 End Call", self)
        self.end_button.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ef4444, stop:1 #f87171);
                border: none;
                border-radius: 16px;
                padding: 14px 24px;
                font-size: 15px;
                font-weight: 800;
                color: #fff;
                font-family: 'Segoe UI', Arial, sans-serif;
                min-height: 40px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #dc2626, stop:1 #ef4444);
            }
            QPushButton:pressed {
                background: #b91c1c;
            }
        """
        )
        self.button_container.addWidget(self.end_button)

    def add_client(self, name: str):
        checkbox = QCheckBox(name, self)
        checkbox.setChecked(True)
        action_widget = QWidgetAction(self)
        action_widget.setDefaultWidget(checkbox)
        self.clients_menu.addAction(action_widget)

        if name == "":  # Select All Checkbox
            checkbox.setText("Select All")
            checkbox.stateChanged.connect(
                lambda state: self.on_checkbox_click(state, is_select_all=True)
            )
            return checkbox, action_widget

        checkbox.stateChanged.connect(lambda state: self.on_checkbox_click(state))
        self.clients_checkboxes[name] = checkbox
        self.clients_menu_actions[name] = action_widget
        return checkbox, action_widget

    def remove_client(self, name: str):
        self.clients_menu.removeAction(self.clients_menu_actions[name])
        self.clients_menu_actions.pop(name)
        self.clients_checkboxes.pop(name)

    def resize_clients_menu(self):
        self.clients_menu.setMinimumWidth(self.clients_button.width())

    def on_checkbox_click(self, is_checked: bool, is_select_all: bool = False):
        if is_select_all:
            for client_checkbox in self.clients_checkboxes.values():
                client_checkbox.blockSignals(True)
                client_checkbox.setChecked(is_checked)
                client_checkbox.blockSignals(False)
        else:
            if not is_checked:
                self.select_all_checkbox.blockSignals(True)
                self.select_all_checkbox.setChecked(False)
                self.select_all_checkbox.blockSignals(False)

    def selected_clients(self):
        selected = []
        for name, checkbox in self.clients_checkboxes.items():
            if checkbox.isChecked():
                selected.append(name)
        return tuple(selected)

    def get_file(self):
        file_path = QFileDialog.getOpenFileName(
            None, "Select File", options=QFileDialog.Option.DontUseNativeDialog
        )[0]
        return file_path

    def get_text(self):
        text = self.line_edit.text()
        self.line_edit.clear()
        return text

    def add_msg(self, from_name: str, to_name: str, msg: str):
        # Clean chat bubbles without unsupported properties
        timestamp = __import__("datetime").datetime.now().strftime("%H:%M")

        if from_name == "You":
            bubble_style = """
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #a5b4fc);
                color: white;
                margin-left: 60px;
                text-align: right;
            """
            sender_style = "color: #6366f1; text-align: right; margin-left: 60px;"
        else:
            bubble_style = """
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f8fafc, stop:1 #e2e8f0);
                color: #334155;
                margin-right: 60px;
                border: 2px solid #a5b4fc;
            """
            sender_style = "color: #334155; margin-right: 60px;"

        html = f"""
        <div style="margin-bottom: 22px; font-family: 'Segoe UI', Arial, sans-serif;">
            <div style="{sender_style} font-weight: 700; font-size: 15px; margin-bottom: 7px;">
                {from_name} <span style="color: #64748b; font-weight: 400;">to {to_name}</span>
                <span style="color: #6366f1; font-size: 12px; margin-left: 12px;">{timestamp}</span>
            </div>
            <div style="{bubble_style} padding: 18px 24px; border-radius: 22px; 
                        display: inline-block; max-width: 80%; word-wrap: break-word;
                        font-size: 16px; line-height: 1.5;">
                {msg}
            </div>
        </div>
        """
        self.central_widget.append(html)
        scrollbar = self.central_widget.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("🎥 Video Conference - Join Now")
        self.setFixedSize(420, 240)

        # Clean modern styling
        self.setStyleSheet(
            """
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6366f1, stop:1 #a5b4fc);
                border-radius: 20px;
            }
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: 700;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit {
                border: 2px solid rgba(255, 255, 255, 0.5);
                border-radius: 12px;
                padding: 14px 18px;
                font-size: 16px;
                background-color: #fff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit:focus {
                border: 2px solid #ffffff;
                outline: none;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ffffff, stop:1 #f8fafc);
                border: none;
                border-radius: 12px;
                padding: 14px 28px;
                font-size: 16px;
                font-weight: 700;
                color: #6366f1;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f1f5f9, stop:1 #e2e8f0);
            }
            QPushButton:pressed {
                background: #e2e8f0;
            }
        """
        )

        self.layout = QGridLayout()
        self.layout.setSpacing(20)
        self.layout.setContentsMargins(35, 35, 35, 35)
        self.setLayout(self.layout)

        self.title_label = QLabel("🎥 Join Video Conference")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(
            """
            QLabel {
                font-size: 20px;
                font-weight: 800;
                color: white;
                margin-bottom: 15px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """
        )
        self.layout.addWidget(self.title_label, 0, 0, 1, 2)

        self.name_label = QLabel("👤 Username:")
        self.layout.addWidget(self.name_label, 1, 0)

        self.name_edit = QLineEdit(self)
        self.name_edit.setPlaceholderText("Enter your username...")
        self.layout.addWidget(self.name_edit, 1, 1)

        self.button = QPushButton("🚀 Join Conference", self)
        self.layout.addWidget(self.button, 2, 0, 1, 2)

        self.button.clicked.connect(self.login)

    def get_name(self):
        return self.name_edit.text()

    def login(self):
        if self.get_name() == "":
            QMessageBox.critical(self, "Error", "Username cannot be empty")
            return
        if " " in self.get_name():
            QMessageBox.critical(self, "Error", "Username cannot contain spaces")
            return
        self.accept()

    def close(self):
        self.reject()


class MainWindow(QMainWindow):
    def __init__(self, client, server_conn):
        super().__init__()
        self.client = client
        self.server_conn = server_conn
        self.audio_threads = {}

        self.server_conn.add_client_signal.connect(self.add_client)
        self.server_conn.remove_client_signal.connect(self.remove_client)
        self.server_conn.add_msg_signal.connect(self.add_msg)

        self.login_dialog = LoginDialog(self)
        if not self.login_dialog.exec():
            exit()

        self.server_conn.name = self.login_dialog.get_name()
        self.server_conn.start()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("🎥 Lets Meet - Modern Video Conference")
        self.resize(1100, 600)

        # Center the window
        screen_geometry = self.screen().availableGeometry()
        x = (screen_geometry.width() - 1100) // 2
        y = (screen_geometry.height() - 600) // 2
        self.move(x, y)
        self.setMinimumSize(700, 400)

        # Clean modern main window styling
        self.setStyleSheet(
            """
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6366f1, stop:1 #a5b4fc);
            }
            QMenuBar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4c63d2, stop:1 #6366f1);
                color: white;
                font-size: 14px;
                font-weight: 700;
                padding: 8px;
                border-radius: 6px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 10px 18px;
                border-radius: 6px;
                margin: 2px;
            }
            QMenuBar::item:selected {
                background-color: rgba(255, 255, 255, 0.2);
            }
            QMenu {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8fafc);
                border: 2px solid #a5b4fc;
                border-radius: 12px;
                padding: 8px;
                font-size: 13px;
            }
            QMenu::item {
                padding: 10px 18px;
                border-radius: 8px;
                margin: 2px;
            }
            QMenu::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #a5b4fc);
                color: #fff;
            }
        """
        )

        self.video_list_widget = VideoListWidget()
        self.setCentralWidget(self.video_list_widget)

        # Enhanced sidebar styling with dynamic sizing
        self.sidebar = QDockWidget("💬 Chat", self)
        self.sidebar.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.sidebar.setMinimumWidth(300)
        self.sidebar.setMaximumWidth(500)

        self.chat_widget = ChatWidget(self)
        self.sidebar.setWidget(self.chat_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.sidebar)

        # Connect buttons
        self.chat_widget.send_button.clicked.connect(lambda: self.send_msg(TEXT))
        self.chat_widget.line_edit.returnPressed.connect(lambda: self.send_msg(TEXT))
        self.chat_widget.file_button.clicked.connect(lambda: self.send_msg(FILE))
        self.chat_widget.leave_button.clicked.connect(self.leave_meeting)
        self.chat_widget.end_button.clicked.connect(self.close)

        # menus for camera and microphone toggle
        self.camera_menu = self.menuBar().addMenu("📹 Camera")
        self.microphone_menu = self.menuBar().addMenu("🎤 Microphone")
        self.layout_menu = self.menuBar().addMenu("📐 Layout")

        self.camera_menu.addAction("📹 Disable Camera", self.toggle_camera)
        self.microphone_menu.addAction("🎤 Disable Microphone", self.toggle_microphone)

        self.layout_actions = {}
        layout_action_group = QActionGroup(self)
        for res in frame_size.keys():
            layout_action = layout_action_group.addAction(f"📐 {res}")
            layout_action.setCheckable(True)
            layout_action.triggered.connect(
                lambda checked, res=res: self.video_list_widget.resize_widgets(res)
            )
            if res == LAYOUT_RES:
                layout_action.setChecked(True)
            self.layout_menu.addAction(layout_action)
            self.layout_actions[res] = layout_action

    def add_client(self, client):
        self.video_list_widget.add_client(client)
        self.layout_actions[LAYOUT_RES].setChecked(True)
        if ENABLE_AUDIO:
            self.audio_threads[client.name] = AudioThread(client, self)
            self.audio_threads[client.name].start()
        if not client.current_device:
            self.chat_widget.add_client(client.name)

    def remove_client(self, name: str):
        self.video_list_widget.remove_client(name)
        self.layout_actions[LAYOUT_RES].setChecked(True)
        if ENABLE_AUDIO:
            self.audio_threads[name].connected = False
            self.audio_threads[name].wait()
            self.audio_threads.pop(name)
            print(f"Audio Thread for {name} terminated")
        print(f"removing {name} chat...")
        self.chat_widget.remove_client(name)
        print(f"{name} removed")

    def send_msg(self, data_type: str = TEXT):
        selected = self.chat_widget.selected_clients()
        if len(selected) == 0:
            QMessageBox.critical(self, "Error", "Select at least one client")
            return

        if data_type == TEXT:
            msg_text = self.chat_widget.get_text()
        elif data_type == FILE:
            filepath = self.chat_widget.get_file()
            if not filepath:
                return
            msg_text = os.path.basename(filepath)
        else:
            print(f"{data_type} data_type not supported")
            return

        if msg_text == "":
            QMessageBox.critical(self, "Error", f"{data_type} cannot be empty")
            return

        msg = Message(
            self.client.name, POST, data_type, data=msg_text, to_names=selected
        )
        self.server_conn.send_msg(self.server_conn.main_socket, msg)

        if data_type == FILE:
            send_file_thread = Worker(self.server_conn.send_file, filepath, selected)
            self.server_conn.threadpool.start(send_file_thread)
            msg_text = f"Sending {msg_text}..."

        self.chat_widget.add_msg("You", ", ".join(selected), msg_text)

    def add_msg(self, from_name: str, msg: str):
        self.chat_widget.add_msg(from_name, "You", msg)

    def toggle_camera(self):
        if self.client.camera_enabled:
            self.camera_menu.actions()[0].setText("📹 Enable Camera")
        else:
            self.camera_menu.actions()[0].setText("📹 Disable Camera")
        self.client.camera_enabled = not self.client.camera_enabled

    def toggle_microphone(self):
        if self.client.microphone_enabled:
            self.microphone_menu.actions()[0].setText("🎤 Enable Microphone")
        else:
            self.microphone_menu.actions()[0].setText("🎤 Disable Microphone")
        self.client.microphone_enabled = not self.client.microphone_enabled

    def leave_meeting(self):
        """Handle leaving the meeting without closing the application"""
        reply = QMessageBox.question(
            self,
            "Leave Meeting",
            "Are you sure you want to leave the meeting?\nYou can rejoin by restarting the application.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Disconnect from server but keep the window open
            self.server_conn.connected = False
            self.server_conn.disconnect_server()

            # Show a message that user has left
            self.chat_widget.add_msg(
                "System", "You", "You have left the meeting. Please restart to rejoin."
            )

            # Disable controls
            self.chat_widget.send_button.setEnabled(False)
            self.chat_widget.line_edit.setEnabled(False)
            self.chat_widget.file_button.setEnabled(False)
            self.chat_widget.clients_button.setEnabled(False)
            self.chat_widget.leave_button.setEnabled(False)

    def closeEvent(self, event):
        """Handle window close event to properly cleanup resources."""
        if self.client.camera:
            self.client.camera.release()
        super().closeEvent(event)

    def resizeEvent(self, event):
        """Handle dynamic resizing of main window elements"""
        super().resizeEvent(event)
        size = event.size()

        # Adjust sidebar width based on window size
        sidebar_width = max(250, min(400, size.width() // 3))
        self.sidebar.setMinimumWidth(sidebar_width)
        self.sidebar.setMaximumWidth(sidebar_width + 50)

        # Adjust menu bar font size
        menu_font_size = max(12, min(16, size.width() // 80))
        self.setStyleSheet(
            f"""
            QMainWindow {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6366f1, stop:1 #a5b4fc);
            }}
            QMenuBar {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4c63d2, stop:1 #6366f1);
                color: white;
                font-size: {menu_font_size}px;
                font-weight: 700;
                padding: {max(6, menu_font_size//2)}px;
                border-radius: 6px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QMenuBar::item {{
                background-color: transparent;
                padding: {max(8, menu_font_size//1.5)}px {max(14, menu_font_size)}px;
                border-radius: 6px;
                margin: 2px;
            }}
            QMenuBar::item:selected {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
            QMenu {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8fafc);
                border: 2px solid #a5b4fc;
                border-radius: 12px;
                padding: 8px;
                font-size: {max(11, menu_font_size-2)}px;
            }}
            QMenu::item {{
                padding: {max(8, menu_font_size//1.5)}px {max(14, menu_font_size)}px;
                border-radius: 8px;
                margin: 2px;
            }}
            QMenu::item:selected {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #a5b4fc);
                color: #fff;
            }}
        """
        )
