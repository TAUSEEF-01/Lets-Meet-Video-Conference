import socket
import threading
import time
import os
import traceback
import pickle
from dataclasses import dataclass, field
import sys
import os
import matplotlib

matplotlib.use("TkAgg")
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from constants import *
from data_rate_core import DataRateTracker

IP = "10.42.0.73"

clients = {}  
video_conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
audio_conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
media_conns = {VIDEO: video_conn, AUDIO: audio_conn}

server_data_tracker = DataRateTracker()

shutdown_event = threading.Event()


@dataclass
class Client:
    name: str
    main_conn: socket.socket
    connected: bool
    media_addrs: dict = field(default_factory=lambda: {VIDEO: None, AUDIO: None})

    def send_msg( # client data sending msg
        self, from_name: str, request: str, data_type: str = None, data: any = None
    ):
        msg = Message(from_name, request, data_type, data)
        msg_bytes = pickle.dumps(msg) # msg Serialize kortese

        server_data_tracker.add_sent_data(len(msg_bytes), data_type or "CONTROL")

        try:
            if data_type in [VIDEO, AUDIO]:
                addr = self.media_addrs.get(data_type, None)
                if addr is None:
                    return
                media_conns[data_type].sendto(msg_bytes, addr)
            else:
                self.main_conn.send_bytes(msg_bytes)
        except (BrokenPipeError, ConnectionResetError, OSError):
            print(
                f"[{self.name}] [ERROR] BrokenPipeError or ConnectionResetError or OSError"
            )
            self.connected = False


def broadcast_msg( # msg broadcast kortese
    from_name: str, request: str, data_type: str = None, data: any = None
):
    all_clients = tuple(clients.values())
    for client in all_clients:
        if client.name == from_name:
            continue
        client.send_msg(from_name, request, data_type, data)


def multicast_msg(
    from_name: str,
    request: str,
    to_names: tuple[str],
    data_type: str = None,
    data: any = None,
):
    if not to_names:
        broadcast_msg(
            from_name, request, data_type, data
        )  
        return
    for name in to_names:
        if name not in clients:
            continue
        clients[name].send_msg(from_name, request, data_type, data)


def media_server(media: str, port: int):
    conn = media_conns[media]
    conn.bind((IP, port))
    print(f"[LISTENING] {media} Server is listening on {IP}:{port}")

    while True:
        msg_bytes, addr = conn.recvfrom(MEDIA_SIZE[media])

        server_data_tracker.add_received_data(len(msg_bytes), media)

        try:
            msg: Message = pickle.loads(msg_bytes)
        except pickle.UnpicklingError:
            print(f"[{addr}] [{media}] [ERROR] UnpicklingError")
            continue

        if msg.request == ADD:
            client = clients[msg.from_name]
            client.media_addrs[media] = addr
            print(f"[{addr}] [{media}] {msg.from_name} added")
        else:
            broadcast_msg(msg.from_name, msg.request, msg.data_type, msg.data)


def disconnect_client(client: Client):
    global clients

    print(f"[DISCONNECT] {client.name} disconnected from Main Server")
    client.media_addrs.update({VIDEO: None, AUDIO: None})
    client.connected = False

    broadcast_msg(client.name, RM)
    client.main_conn.disconnect()
    try:
        clients.pop(client.name)
    except KeyError:
        print(f"[ERROR] {client.name} not in clients")
        print(clients)
        pass


def handle_main_conn(name: str):
    client: Client = clients[name]
    conn = client.main_conn

    for client_name in clients:
        if client_name == name:
            continue
        client.send_msg(client_name, ADD)

    broadcast_msg(name, ADD)

    while client.connected:
        msg_bytes = conn.recv_bytes()
        if not msg_bytes:
            break

        server_data_tracker.add_received_data(len(msg_bytes), "CONTROL")

        try:
            msg = pickle.loads(msg_bytes)
        except pickle.UnpicklingError:
            print(f"[{name}] [ERROR] UnpicklingError")
            continue

        print(msg)
        if msg.request == DISCONNECT:
            break
        multicast_msg(name, msg.request, msg.to_names, msg.data_type, msg.data)

    disconnect_client(client)


class ServerDataRateGraphWindow:
    def __init__(self, tracker):
        self.tracker = tracker
        self.root = tk.Tk()
        self.root.title("Server Data Transmission Rate")
        self.fig = Figure(figsize=(10, 6))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._running = True

        self.sent_rates = []
        self.recv_rates = []
        self.timestamps = []

        self.update_plot()

    def update_plot(self):
        if not self._running or shutdown_event.is_set():
            self.on_close()
            return

        rate_data = self.tracker.get_rate_data(5.0) 
        current_time = time.time()

        self.sent_rates.append(rate_data["total_sent"])
        self.recv_rates.append(rate_data["total_received"])
        self.timestamps.append(current_time)

        if len(self.timestamps) > 100:
            self.sent_rates.pop(0)
            self.recv_rates.pop(0)
            self.timestamps.pop(0)

        self.ax.clear()
        if self.timestamps:
            t0 = self.timestamps[0]
            times = [t - t0 for t in self.timestamps]

            self.ax.plot(times, self.sent_rates, label="Sent (B/s)", color="blue")
            self.ax.plot(times, self.recv_rates, label="Received (B/s)", color="red")

        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Bytes per second")
        self.ax.set_title("Server Data Transmission Rate")
        self.ax.legend()
        self.ax.grid(True)
        self.canvas.draw()

        self.root.after(1000, self.update_plot)  # Update every 1 second

    def on_close(self):
        self._running = False
        try:
            self.root.quit()
            self.root.destroy()
        except:
            pass

    def run(self):
        self.root.mainloop()


def print_server_stats():
    """Print server data rate statistics periodically"""

    def stats_loop():
        while not shutdown_event.is_set():
            time.sleep(1)
            if int(time.time()) % 30 == 0:
                stats_summary = server_data_tracker.get_stats_summary(30)
                print(f"[SERVER STATS] {stats_summary}")

    stats_thread = threading.Thread(target=stats_loop, daemon=True)
    stats_thread.start()

    def graph_loop():
        graph_window = ServerDataRateGraphWindow(server_data_tracker)
        graph_window.run()

    graph_thread = threading.Thread(target=graph_loop, daemon=True)
    graph_thread.start()


def main_server():
    main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP socket
    main_socket.bind((IP, MAIN_PORT))
    main_socket.listen()
    print(f"[LISTENING] Main Server is listening on {IP}:{MAIN_PORT}")
    print(f"[INFO] Server data rate monitoring enabled")

    print_server_stats()

    video_server_thread = threading.Thread(
        target=media_server, args=(VIDEO, VIDEO_PORT)
    )
    video_server_thread.start()
    audio_server_thread = threading.Thread(
        target=media_server, args=(AUDIO, AUDIO_PORT)
    )
    audio_server_thread.start()

    while True:
        conn, addr = main_socket.accept()
        name = conn.recv_bytes().decode()
        if name in clients:
            conn.send_bytes("Username already taken".encode())
            continue
        conn.send_bytes(OK.encode())
        clients[name] = Client(name, conn, True)
        print(f"[NEW CONNECTION] {name} connected to Main Server")

        main_conn_thread = threading.Thread(target=handle_main_conn, args=(name,))
        main_conn_thread.start()


if __name__ == "__main__":
    try:
        main_server()
    except KeyboardInterrupt:
        print("[EXITING] Keyboard Interrupt")
        shutdown_event.set()
        time.sleep(1)
        for client in clients.values():
            disconnect_client(client)
    except Exception as e:
        print(f"[ERROR] {e}")
        print(traceback.format_exc())
        shutdown_event.set()
        time.sleep(1)
        for client in clients.values():
            disconnect_client(client)
