import os
import cv2
import pyaudio
from PyQt6.QtCore import Qt, QThread, QTimer, QSize, QRunnable, pyqtSlot
from PyQt6.QtGui import QImage, QPixmap, QActionGroup, QIcon, QFont, QPalette, QColor
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
    QFrame,
)

from constants import *

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
    # '1080p': (1920, 1080)
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
        # self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        # self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

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
        self.init_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_video)

        self.init_video()

    def init_ui(self):
        # Enhanced styling for video widget
        self.setStyleSheet(
            """
            VideoWidget {
                background-color: #2b2b2b;
                border: 2px solid #4a4a4a;
                border-radius: 12px;
                margin: 5px;
            }
            VideoWidget:hover {
                border: 2px solid #6366f1;
            }
        """
        )

        self.video_viewer = QLabel()
        if self.client.current_device:
            self.name_label = QLabel(f"You - {self.client.name}")
        else:
            self.name_label = QLabel(self.client.name)

        # Style the video viewer
        self.video_viewer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_viewer.setStyleSheet(
            """
            QLabel {
                background-color: #1a1a1a;
                border-radius: 8px;
                border: 1px solid #4a4a4a;
            }
        """
        )

        # Style the name label
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet(
            """
            QLabel {
                background-color: rgba(99, 102, 241, 0.8);
                color: white;
                font-weight: bold;
                font-size: 12px;
                border-radius: 6px;
                padding: 4px 8px;
                margin: 2px;
            }
        """
        )

        self.layout = QVBoxLayout()
        self.layout.setSpacing(8)
        self.layout.setContentsMargins(8, 8, 8, 8)
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

        # Enhanced styling for video list
        self.setStyleSheet(
            """
            QListWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2d2d2d, stop:1 #1a1a1a);
                border: none;
                padding: 10px;
            }
            QListWidget::item {
                border: none;
                margin: 3px;
                border-radius: 8px;
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
        # item.setSizeHint(video_widget.sizeHint())
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
        self.init_ui()

    def init_ui(self):
        # Enhanced styling for chat widget
        self.setStyleSheet(
            """
            ChatWidget {
                background-color: #f8fafc;
                border-radius: 12px;
                padding: 10px;
            }
        """
        )

        self.layout = QVBoxLayout()
        self.layout.setSpacing(12)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.setLayout(self.layout)

        # Chat title
        self.title_label = QLabel("💬 Chat")
        self.title_label.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #6366f1;
                padding: 8px;
                border-bottom: 2px solid #e0e7ff;
                margin-bottom: 10px;
            }
        """
        )
        self.layout.addWidget(self.title_label)

        self.central_widget = QTextEdit(self)
        self.central_widget.setReadOnly(True)
        self.central_widget.setStyleSheet(
            """
            QTextEdit {
                background-color: white;
                border: 2px solid #e0e7ff;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
                line-height: 1.4;
            }
        """
        )
        self.layout.addWidget(self.central_widget)

        self.clients_menu = QMenu("Clients", self)
        self.clients_menu.aboutToShow.connect(self.resize_clients_menu)
        self.clients_menu.setStyleSheet(
            """
            QMenu {
                background-color: white;
                border: 2px solid #e0e7ff;
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #e0e7ff;
            }
        """
        )
        self.clients_checkboxes = {}
        self.clients_menu_actions = {}

        self.select_all_checkbox, _ = self.add_client("")  # Select All Checkbox
        self.clients_menu.addSeparator()

        self.clients_button = QPushButton("👥 Select Recipients", self)
        self.clients_button.setMenu(self.clients_menu)
        self.clients_button.setStyleSheet(
            """
            QPushButton {
                background-color: #e0e7ff;
                border: 2px solid #c7d2fe;
                border-radius: 8px;
                padding: 10px 15px;
                font-size: 14px;
                font-weight: 500;
                color: #374151;
            }
            QPushButton:hover {
                background-color: #c7d2fe;
                border-color: #6366f1;
            }
            QPushButton:pressed {
                background-color: #a5b4fc;
            }
        """
        )
        self.layout.addWidget(self.clients_button)

        self.file_button = QPushButton("📎 Send File", self)
        self.file_button.setStyleSheet(
            """
            QPushButton {
                background-color: #fef3c7;
                border: 2px solid #fbbf24;
                border-radius: 8px;
                padding: 10px 15px;
                font-size: 14px;
                font-weight: 500;
                color: #92400e;
            }
            QPushButton:hover {
                background-color: #fde68a;
                border-color: #f59e0b;
            }
            QPushButton:pressed {
                background-color: #fbbf24;
            }
        """
        )
        self.layout.addWidget(self.file_button)

        self.send_layout = QHBoxLayout()
        self.send_layout.setSpacing(8)
        self.layout.addLayout(self.send_layout)

        self.line_edit = QLineEdit(self)
        self.line_edit.setPlaceholderText("Type your message here...")
        self.line_edit.setStyleSheet(
            """
            QLineEdit {
                border: 2px solid #e0e7ff;
                border-radius: 10px;
                padding: 12px 15px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #6366f1;
                outline: none;
            }
        """
        )
        self.send_layout.addWidget(self.line_edit)

        self.send_button = QPushButton("📤 Send", self)
        self.send_button.setStyleSheet(
            """
            QPushButton {
                background-color: #6366f1;
                border: none;
                border-radius: 10px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: 600;
                color: white;
            }
            QPushButton:hover {
                background-color: #5b21b6;
            }
            QPushButton:pressed {
                background-color: #4c1d95;
            }
        """
        )
        self.send_layout.addWidget(self.send_button)

        # Add some spacing
        self.layout.addSpacing(20)

        self.end_button = QPushButton("📞 End Call", self)
        self.end_button.setStyleSheet(
            """
            QPushButton {
                background-color: #ef4444;
                border: none;
                border-radius: 10px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: 600;
                color: white;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
            QPushButton:pressed {
                background-color: #b91c1c;
            }
        """
        )
        self.layout.addWidget(self.end_button)

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
        self.central_widget.append(f"[{from_name} 🠖 {to_name}] {msg}")


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("🎥 Video Conference - Login")
        self.setFixedSize(400, 200)

        # Enhanced styling for login dialog
        self.setStyleSheet(
            """
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6366f1, stop:1 #3b82f6);
                border-radius: 15px;
            }
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: 600;
            }
            QLineEdit {
                border: 2px solid #e0e7ff;
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #6366f1;
                outline: none;
            }
            QPushButton {
                background-color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
                color: #6366f1;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
            }
            QPushButton:pressed {
                background-color: #e2e8f0;
            }
        """
        )

        self.layout = QGridLayout()
        self.layout.setSpacing(15)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.setLayout(self.layout)

        # Add logo/title
        self.title_label = QLabel("🎥 Join Video Conference")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(
            """
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: white;
                margin-bottom: 10px;
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
        self.setWindowTitle("🎥 Video Conference - Premium Experience")
        self.setGeometry(100, 100, 1400, 900)

        # Enhanced main window styling
        self.setStyleSheet(
            """
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8fafc, stop:1 #e2e8f0);
            }
            QMenuBar {
                background-color: #6366f1;
                color: white;
                font-size: 14px;
                font-weight: 500;
                padding: 5px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background-color: rgba(255, 255, 255, 0.2);
            }
            QMenu {
                background-color: white;
                border: 2px solid #e0e7ff;
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #e0e7ff;
            }
        """
        )

        self.video_list_widget = VideoListWidget()
        self.setCentralWidget(self.video_list_widget)

        self.sidebar = QDockWidget("💬 Chat & Controls", self)
        self.sidebar.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.sidebar.setStyleSheet(
            """
            QDockWidget {
                background-color: #f8fafc;
                border: 2px solid #e0e7ff;
                border-radius: 12px;
                font-size: 16px;
                font-weight: 600;
                color: #6366f1;
            }
            QDockWidget::title {
                background-color: #6366f1;
                color: white;
                padding: 10px;
                border-radius: 8px 8px 0 0;
            }
        """
        )
        self.chat_widget = ChatWidget()
        self.sidebar.setWidget(self.chat_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.sidebar)
        self.chat_widget.send_button.clicked.connect(lambda: self.send_msg(TEXT))
        self.chat_widget.line_edit.returnPressed.connect(lambda: self.send_msg(TEXT))
        self.chat_widget.file_button.clicked.connect(lambda: self.send_msg(FILE))
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
