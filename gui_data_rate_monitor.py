import time
import threading
import random
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import numpy as np
from collections import deque
from data_rate_core import DataRateTracker
from dataclasses import dataclass
from typing import Dict, Optional
import socket
import json


@dataclass
class NetworkSession:
    session_id: str
    client_ip: str
    server_ip: str
    is_server: bool
    connected_at: float


class VideoAudioTracker:
    def __init__(self):
        self.video_codec = "H.264"  # or VP8, VP9
        self.audio_codec = "Opus"  # or AAC, G.722
        self.video_resolution = "720p"  # 480p, 720p, 1080p
        self.video_fps = 30
        self.audio_sample_rate = 48000

    def get_video_baseline_rate(self) -> int:
        """Get baseline video bitrate based on settings"""
        rates = {
            "480p": {"30fps": 1000000, "15fps": 600000},  # 1Mbps, 600kbps
            "720p": {"30fps": 2500000, "15fps": 1500000},  # 2.5Mbps, 1.5Mbps
            "1080p": {"30fps": 5000000, "15fps": 3000000},  # 5Mbps, 3Mbps
        }
        fps_key = f"{self.video_fps}fps"
        return rates.get(self.video_resolution, rates["720p"]).get(fps_key, 2500000)

    def get_audio_baseline_rate(self) -> int:
        """Get baseline audio bitrate"""
        return 64000  # 64 kbps for Opus codec


class GUIDataRateMonitor:
    def __init__(self):
        self.tracker = DataRateTracker()
        self.video_audio_tracker = VideoAudioTracker()
        self.running = False
        self.simulation_thread = None

        # Network session info
        self.current_session: Optional[NetworkSession] = None
        self.is_server_mode = False
        self.connected_clients = {}

        # Realistic data patterns
        self.network_quality = 1.0  # 1.0 = perfect, 0.5 = poor
        self.packet_loss = 0.0  # percentage
        self.latency = 50  # milliseconds

        # Data for plotting
        self.time_data = deque(maxlen=100)
        self.video_upload_client = deque(maxlen=100)
        self.video_download_client = deque(maxlen=100)
        self.video_upload_server = deque(maxlen=100)
        self.video_download_server = deque(maxlen=100)
        self.audio_upload_client = deque(maxlen=100)
        self.audio_download_client = deque(maxlen=100)
        self.audio_upload_server = deque(maxlen=100)
        self.audio_download_server = deque(maxlen=100)

        self.setup_gui()

    def setup_gui(self):
        """Setup the main GUI window"""
        self.root = tk.Tk()
        self.root.title("Video Conference Data Rate Monitor - Client/Server Tracking")
        self.root.geometry("1400x900")
        self.root.configure(bg="#f0f0f0")

        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="📊 Video Conference Data Rate Monitor - Client/Server",
            font=("Arial", 16, "bold"),
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        # Control panel
        self.setup_control_panel(main_frame)

        # Network settings panel
        self.setup_network_panel(main_frame)

        # Stats panel
        self.setup_stats_panel(main_frame)

        # Chart panel
        self.setup_chart_panel(main_frame)

    def setup_control_panel(self, parent):
        """Setup control buttons"""
        control_frame = ttk.LabelFrame(parent, text="Controls", padding="10")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N), padx=(0, 5))

        # Mode selection
        mode_frame = ttk.Frame(control_frame)
        mode_frame.grid(row=0, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))

        ttk.Label(mode_frame, text="Mode:").pack(side=tk.LEFT)
        self.mode_var = tk.StringVar(value="client")
        ttk.Radiobutton(
            mode_frame,
            text="Client",
            variable=self.mode_var,
            value="client",
            command=self.on_mode_change,
        ).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(
            mode_frame,
            text="Server",
            variable=self.mode_var,
            value="server",
            command=self.on_mode_change,
        ).pack(side=tk.LEFT, padx=5)

        self.start_button = ttk.Button(
            control_frame, text="Start Conference", command=self.start_monitoring
        )
        self.start_button.grid(row=1, column=0, pady=5, sticky=(tk.W, tk.E))

        self.stop_button = ttk.Button(
            control_frame,
            text="End Conference",
            command=self.stop_monitoring,
            state="disabled",
        )
        self.stop_button.grid(row=1, column=1, pady=5, sticky=(tk.W, tk.E))

        self.reset_button = ttk.Button(
            control_frame, text="Reset Stats", command=self.reset_stats
        )
        self.reset_button.grid(
            row=2, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E)
        )

        # Status indicators
        self.status_label = ttk.Label(
            control_frame, text="Status: Disconnected", font=("Arial", 10, "bold")
        )
        self.status_label.grid(row=3, column=0, columnspan=2, pady=5)

        self.connection_label = ttk.Label(
            control_frame, text="Connection: None", font=("Arial", 9)
        )
        self.connection_label.grid(row=4, column=0, columnspan=2, pady=2)

        control_frame.columnconfigure(0, weight=1)
        control_frame.columnconfigure(1, weight=1)

    def setup_network_panel(self, parent):
        """Setup network quality controls"""
        network_frame = ttk.LabelFrame(parent, text="Network Conditions", padding="10")
        network_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N), padx=(5, 0))

        # Network quality slider
        ttk.Label(network_frame, text="Network Quality:").grid(
            row=0, column=0, sticky=tk.W
        )
        self.quality_var = tk.DoubleVar(value=1.0)
        quality_scale = ttk.Scale(
            network_frame,
            from_=0.1,
            to=1.0,
            variable=self.quality_var,
            orient=tk.HORIZONTAL,
        )
        quality_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        self.quality_label = ttk.Label(network_frame, text="Excellent")
        self.quality_label.grid(row=0, column=2)

        # Packet loss slider
        ttk.Label(network_frame, text="Packet Loss %:").grid(
            row=1, column=0, sticky=tk.W
        )
        self.loss_var = tk.DoubleVar(value=0.0)
        loss_scale = ttk.Scale(
            network_frame,
            from_=0.0,
            to=10.0,
            variable=self.loss_var,
            orient=tk.HORIZONTAL,
        )
        loss_scale.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        self.loss_label = ttk.Label(network_frame, text="0.0%")
        self.loss_label.grid(row=1, column=2)

        # Video settings
        ttk.Label(network_frame, text="Video Quality:").grid(
            row=2, column=0, sticky=tk.W
        )
        self.video_quality_var = tk.StringVar(value="720p")
        quality_combo = ttk.Combobox(
            network_frame,
            textvariable=self.video_quality_var,
            values=["480p", "720p", "1080p"],
            state="readonly",
        )
        quality_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)

        # Bind events
        quality_scale.bind("<Motion>", self.update_network_labels)
        loss_scale.bind("<Motion>", self.update_network_labels)

        network_frame.columnconfigure(1, weight=1)

    def setup_stats_panel(self, parent):
        """Setup statistics display panel"""
        stats_frame = ttk.LabelFrame(parent, text="Current Statistics", padding="10")
        stats_frame.grid(
            row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10), pady=(10, 0)
        )

        # Create text widget for stats
        self.stats_text = tk.Text(stats_frame, height=15, width=40, font=("Courier", 9))
        stats_scrollbar = ttk.Scrollbar(
            stats_frame, orient="vertical", command=self.stats_text.yview
        )
        self.stats_text.configure(yscrollcommand=stats_scrollbar.set)

        self.stats_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        stats_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        stats_frame.columnconfigure(0, weight=1)
        stats_frame.rowconfigure(0, weight=1)

    def setup_chart_panel(self, parent):
        """Setup matplotlib chart panel"""
        chart_frame = ttk.LabelFrame(
            parent, text="Real-time Client/Server Data Rates", padding="10"
        )
        chart_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Create matplotlib figure with 3 subplots
        self.fig, (self.ax1, self.ax2, self.ax3) = plt.subplots(3, 1, figsize=(12, 10))
        self.fig.patch.set_facecolor("#f0f0f0")

        # Setup plots
        self.ax1.set_title(
            "Video Data Rates (Client ↔ Server)", fontsize=12, fontweight="bold"
        )
        self.ax1.set_ylabel("Rate (KB/s)")
        self.ax1.grid(True, alpha=0.3)

        self.ax2.set_title(
            "Audio Data Rates (Client ↔ Server)", fontsize=12, fontweight="bold"
        )
        self.ax2.set_ylabel("Rate (KB/s)")
        self.ax2.grid(True, alpha=0.3)

        self.ax3.set_title("Total Bandwidth Usage", fontsize=12, fontweight="bold")
        self.ax3.set_xlabel("Time (seconds)")
        self.ax3.set_ylabel("Rate (KB/s)")
        self.ax3.grid(True, alpha=0.3)

        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(
            row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S)
        )

        chart_frame.columnconfigure(0, weight=1)
        chart_frame.rowconfigure(0, weight=1)

        # Setup animation
        self.animation = FuncAnimation(
            self.fig, self.update_charts, interval=1000, blit=False
        )

    def on_mode_change(self):
        """Handle mode change between client and server"""
        self.is_server_mode = self.mode_var.get() == "server"
        mode_text = "Server" if self.is_server_mode else "Client"
        self.root.title(f"Video Conference Data Rate Monitor - {mode_text}")

    def update_network_labels(self, event=None):
        """Update network condition labels"""
        quality = self.quality_var.get()
        loss = self.loss_var.get()

        quality_text = (
            "Excellent" if quality > 0.8 else "Good" if quality > 0.6 else "Poor"
        )
        self.quality_label.config(text=quality_text)
        self.loss_label.config(text=f"{loss:.1f}%")

        # Update internal values
        self.network_quality = quality
        self.packet_loss = loss / 100.0

    def simulate_video_conference_data(self):
        """Simulate realistic video conference data between client and server"""
        while self.running:
            # Get baseline rates
            video_baseline = self.video_audio_tracker.get_video_baseline_rate()
            audio_baseline = self.video_audio_tracker.get_audio_baseline_rate()

            # Apply network conditions
            quality_factor = self.network_quality
            loss_factor = 1.0 - self.packet_loss

            # Video data simulation
            video_variation = random.uniform(0.7, 1.3)  # Natural bitrate variation
            video_rate = int(
                video_baseline * quality_factor * loss_factor * video_variation
            )

            # Audio data simulation (more stable than video)
            audio_variation = random.uniform(0.9, 1.1)
            audio_rate = int(
                audio_baseline * quality_factor * loss_factor * audio_variation
            )

            # Simulate bidirectional communication
            if self.is_server_mode:
                # Server receives from multiple clients, sends to multiple clients
                num_clients = random.randint(1, 4)  # Simulate 1-4 connected clients

                # Incoming data from clients
                for _ in range(num_clients):
                    self.tracker.add_received_data(
                        video_rate // 8, "VIDEO"
                    )  # Convert to bytes
                    self.tracker.add_received_data(audio_rate // 8, "AUDIO")

                # Outgoing data to clients (server distributes video/audio)
                for _ in range(num_clients):
                    self.tracker.add_sent_data(video_rate // 8, "VIDEO")
                    self.tracker.add_sent_data(audio_rate // 8, "AUDIO")

            else:
                # Client mode - sends own video/audio, receives from server
                self.tracker.add_sent_data(video_rate // 8, "VIDEO")
                self.tracker.add_sent_data(audio_rate // 8, "AUDIO")

                # Receive video/audio from other participants via server
                num_participants = random.randint(1, 3)
                for _ in range(num_participants):
                    self.tracker.add_received_data(video_rate // 8, "VIDEO")
                    self.tracker.add_received_data(audio_rate // 8, "AUDIO")

            # Simulate control messages and file transfers occasionally
            if random.random() < 0.1:  # 10% chance
                control_size = random.randint(100, 500)
                self.tracker.add_sent_data(control_size, "TEXT")

            if random.random() < 0.02:  # 2% chance for file transfer
                file_chunk = random.randint(5000, 50000)
                if random.choice([True, False]):
                    self.tracker.add_sent_data(file_chunk, "FILE")
                else:
                    self.tracker.add_received_data(file_chunk, "FILE")

            # Sleep based on network quality (poor network = longer intervals)
            sleep_time = 0.5 + (1.0 - quality_factor) * 0.5
            time.sleep(sleep_time)

    def update_charts(self, frame):
        """Update the matplotlib charts with client/server specific data"""
        if not self.running:
            return

        # Get current rates
        rate_data = self.tracker.get_rate_data(time_window=5.0)
        current_time = time.time()

        # Add data to deques
        self.time_data.append(current_time)

        # Get rates by type
        video_rates = rate_data["by_type"].get("VIDEO", {"sent": 0, "received": 0})
        audio_rates = rate_data["by_type"].get("AUDIO", {"sent": 0, "received": 0})

        if self.is_server_mode:
            self.video_upload_server.append(video_rates["sent"] / 1024)
            self.video_download_server.append(video_rates["received"] / 1024)
            self.audio_upload_server.append(audio_rates["sent"] / 1024)
            self.audio_download_server.append(audio_rates["received"] / 1024)
            # Clear client data for server mode
            self.video_upload_client.append(0)
            self.video_download_client.append(0)
            self.audio_upload_client.append(0)
            self.audio_download_client.append(0)
        else:
            self.video_upload_client.append(video_rates["sent"] / 1024)
            self.video_download_client.append(video_rates["received"] / 1024)
            self.audio_upload_client.append(audio_rates["sent"] / 1024)
            self.audio_download_client.append(audio_rates["received"] / 1024)
            # Clear server data for client mode
            self.video_upload_server.append(0)
            self.video_download_server.append(0)
            self.audio_upload_server.append(0)
            self.audio_download_server.append(0)

        # Convert time to relative seconds
        if len(self.time_data) > 1:
            time_relative = [t - self.time_data[0] for t in self.time_data]
        else:
            time_relative = [0]

        # Clear and plot
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()

        # Plot video rates
        if self.is_server_mode:
            self.ax1.plot(
                time_relative,
                list(self.video_upload_server),
                "b-",
                label="Server → Clients",
                linewidth=2,
            )
            self.ax1.plot(
                time_relative,
                list(self.video_download_server),
                "r-",
                label="Clients → Server",
                linewidth=2,
            )
        else:
            self.ax1.plot(
                time_relative,
                list(self.video_upload_client),
                "g-",
                label="Client → Server",
                linewidth=2,
            )
            self.ax1.plot(
                time_relative,
                list(self.video_download_client),
                "orange",
                label="Server → Client",
                linewidth=2,
            )

        self.ax1.set_title(
            "Video Data Rates (Client ↔ Server)", fontsize=12, fontweight="bold"
        )
        self.ax1.set_ylabel("Rate (KB/s)")
        self.ax1.legend()
        self.ax1.grid(True, alpha=0.3)

        # Plot audio rates
        if self.is_server_mode:
            self.ax2.plot(
                time_relative,
                list(self.audio_upload_server),
                "b--",
                label="Server → Clients",
                linewidth=2,
            )
            self.ax2.plot(
                time_relative,
                list(self.audio_download_server),
                "r--",
                label="Clients → Server",
                linewidth=2,
            )
        else:
            self.ax2.plot(
                time_relative,
                list(self.audio_upload_client),
                "g--",
                label="Client → Server",
                linewidth=2,
            )
            self.ax2.plot(
                time_relative,
                list(self.audio_download_client),
                "orange",
                linestyle="--",
                label="Server → Client",
                linewidth=2,
            )

        self.ax2.set_title(
            "Audio Data Rates (Client ↔ Server)", fontsize=12, fontweight="bold"
        )
        self.ax2.set_ylabel("Rate (KB/s)")
        self.ax2.legend()
        self.ax2.grid(True, alpha=0.3)

        # Plot total bandwidth
        total_upload = [
            v + a
            for v, a in zip(
                (
                    self.video_upload_client
                    if not self.is_server_mode
                    else self.video_upload_server
                ),
                (
                    self.audio_upload_client
                    if not self.is_server_mode
                    else self.audio_upload_server
                ),
            )
        ]
        total_download = [
            v + a
            for v, a in zip(
                (
                    self.video_download_client
                    if not self.is_server_mode
                    else self.video_download_server
                ),
                (
                    self.audio_download_client
                    if not self.is_server_mode
                    else self.audio_download_server
                ),
            )
        ]

        self.ax3.plot(
            time_relative, total_upload, "purple", label="Total Upload", linewidth=2
        )
        self.ax3.plot(
            time_relative, total_download, "brown", label="Total Download", linewidth=2
        )
        self.ax3.set_title("Total Bandwidth Usage", fontsize=12, fontweight="bold")
        self.ax3.set_xlabel("Time (seconds)")
        self.ax3.set_ylabel("Rate (KB/s)")
        self.ax3.legend()
        self.ax3.grid(True, alpha=0.3)

        self.fig.tight_layout()

        # Update stats display
        self.update_stats_display()

    def update_stats_display(self):
        """Update the statistics text display with client/server info"""
        rate_data = self.tracker.get_rate_data(time_window=5.0)
        mode = "SERVER" if self.is_server_mode else "CLIENT"

        stats_text = f"📊 {mode} STATISTICS\n"
        stats_text += "=" * 35 + "\n\n"

        stats_text += f"📡 Network Quality: {self.quality_label.cget('text')}\n"
        stats_text += f"📉 Packet Loss: {self.loss_label.cget('text')}\n"
        stats_text += f"📹 Video Quality: {self.video_quality_var.get()}\n\n"

        stats_text += "📈 TOTAL RATES (Last 5 sec):\n"
        stats_text += (
            f"   Upload:   {self.tracker.format_bytes(rate_data['total_sent'])}/s\n"
        )
        stats_text += f"   Download: {self.tracker.format_bytes(rate_data['total_received'])}/s\n\n"

        stats_text += "📋 BY DATA TYPE:\n"
        for data_type, rates in rate_data["by_type"].items():
            sent_rate = self.tracker.format_bytes(rates["sent"])
            recv_rate = self.tracker.format_bytes(rates["received"])

            if data_type in ["VIDEO", "AUDIO"]:
                direction_up = "→ Server" if not self.is_server_mode else "→ Clients"
                direction_down = "← Server" if not self.is_server_mode else "← Clients"
                stats_text += f"   {data_type:6}:\n"
                stats_text += f"     {direction_up}: {sent_rate:>10}/s\n"
                stats_text += f"     {direction_down}: {recv_rate:>10}/s\n"
            else:
                stats_text += f"   {data_type:6}:\n"
                stats_text += f"     Up: {sent_rate:>10}/s\n"
                stats_text += f"     Down: {recv_rate:>10}/s\n"

        stats_text += "\n📊 SESSION TOTALS:\n"
        stats_text += f"   Total Sent: {self.tracker.format_bytes(rate_data['total_bytes_sent'])}\n"
        stats_text += f"   Total Received: {self.tracker.format_bytes(rate_data['total_bytes_received'])}\n\n"

        # Activity level
        recent_entries = len(
            [e for e in self.tracker.data_entries if time.time() - e.timestamp < 1.0]
        )
        activity = (
            "🟢 High"
            if recent_entries > 10
            else "🟡 Medium" if recent_entries > 5 else "🔴 Low"
        )
        stats_text += f"🎯 Activity: {activity}\n"
        stats_text += f"   ({recent_entries} packets/sec)\n"

        # Update text widget
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)

    def start_monitoring(self):
        """Start the video conference monitoring"""
        if not self.running:
            self.running = True

            # Update video settings
            self.video_audio_tracker.video_resolution = self.video_quality_var.get()

            # Start simulation thread
            self.simulation_thread = threading.Thread(
                target=self.simulate_video_conference_data
            )
            self.simulation_thread.daemon = True
            self.simulation_thread.start()

            # Update UI
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            mode = "Server" if self.is_server_mode else "Client"
            self.status_label.config(
                text=f"Status: Connected as {mode}", foreground="green"
            )

            # Simulate connection info
            if self.is_server_mode:
                self.connection_label.config(text="Listening on: 192.168.1.100:8080")
            else:
                self.connection_label.config(text="Connected to: 192.168.1.100:8080")

    def stop_monitoring(self):
        """Stop the monitoring"""
        self.running = False

        if self.simulation_thread:
            self.simulation_thread.join(timeout=1.0)

        # Update UI
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.status_label.config(text="Status: Disconnected", foreground="red")
        self.connection_label.config(text="Connection: None")

    def reset_stats(self):
        """Reset all statistics"""
        if messagebox.askyesno(
            "Reset Statistics", "Are you sure you want to reset all statistics?"
        ):
            self.tracker = DataRateTracker()

            # Clear plot data
            self.time_data.clear()
            self.video_upload_client.clear()
            self.video_download_client.clear()
            self.video_upload_server.clear()
            self.video_download_server.clear()
            self.audio_upload_client.clear()
            self.audio_download_client.clear()
            self.audio_upload_server.clear()
            self.audio_download_server.clear()

            # Clear charts
            self.ax1.clear()
            self.ax2.clear()
            self.ax3.clear()
            self.canvas.draw()

            # Clear stats
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(
                1.0, "Statistics reset. Start monitoring to see new data."
            )

    def run(self):
        """Run the GUI application"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def on_closing(self):
        """Handle window closing"""
        if self.running:
            self.stop_monitoring()
        self.root.destroy()


def main():
    try:
        monitor = GUIDataRateMonitor()
        monitor.run()
    except ImportError as e:
        print(f"Error: {e}")
        print("Please install required packages: pip install matplotlib")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
