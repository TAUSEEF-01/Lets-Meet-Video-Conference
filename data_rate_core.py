import time
import threading
from collections import deque, defaultdict
from dataclasses import dataclass
from typing import Dict


@dataclass
class DataRateEntry:
    timestamp: float
    bytes_sent: int
    bytes_received: int
    data_type: str  # VIDEO, AUDIO, TEXT, FILE


class DataRateTracker:
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.data_entries = deque(maxlen=window_size)
        self.total_sent = 0
        self.total_received = 0
        self.lock = threading.Lock()

    def add_sent_data(self, bytes_count: int, data_type: str):
        with self.lock:
            self.total_sent += bytes_count
            self.data_entries.append(
                DataRateEntry(
                    timestamp=time.time(),
                    bytes_sent=bytes_count,
                    bytes_received=0,
                    data_type=data_type,
                )
            )

    def add_received_data(self, bytes_count: int, data_type: str):
        with self.lock:
            self.total_received += bytes_count
            self.data_entries.append(
                DataRateEntry(
                    timestamp=time.time(),
                    bytes_sent=0,
                    bytes_received=bytes_count,
                    data_type=data_type,
                )
            )

    def get_rate_data(self, time_window: float = 5.0) -> Dict:
        """Get data rates for the last time_window seconds"""
        with self.lock:
            current_time = time.time()
            cutoff_time = current_time - time_window

            # Filter entries within time window
            recent_entries = [
                e for e in self.data_entries if e.timestamp >= cutoff_time
            ]

            # Calculate rates by data type
            rates = defaultdict(lambda: {"sent": 0, "received": 0})

            for entry in recent_entries:
                rates[entry.data_type]["sent"] += entry.bytes_sent
                rates[entry.data_type]["received"] += entry.bytes_received

            # Convert to rates (bytes per second)
            for data_type in rates:
                rates[data_type]["sent"] /= time_window
                rates[data_type]["received"] /= time_window

            # Calculate total rates
            total_sent_rate = sum(rates[dt]["sent"] for dt in rates)
            total_received_rate = sum(rates[dt]["received"] for dt in rates)

            return {
                "total_sent": total_sent_rate,
                "total_received": total_received_rate,
                "by_type": dict(rates),
                "timestamps": [e.timestamp for e in recent_entries],
                "total_bytes_sent": self.total_sent,
                "total_bytes_received": self.total_received,
            }

    def format_bytes(self, bytes_val):
        """Convert bytes to human readable format"""
        for unit in ["B", "KB", "MB", "GB"]:
            if bytes_val < 1024.0:
                return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.2f} TB"

    def get_stats_summary(self, time_window: float = 30.0) -> str:
        """Get a formatted string summary of current stats"""
        rate_data = self.get_rate_data(time_window)
        return (
            f"Sent: {rate_data['total_sent']:.2f} B/s, "
            f"Received: {rate_data['total_received']:.2f} B/s, "
            f"Total Sent: {self.format_bytes(rate_data['total_bytes_sent'])}, "
            f"Total Received: {self.format_bytes(rate_data['total_bytes_received'])}"
        )
