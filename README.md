# 🎥 Lets Meet - Modern Video Conference Application

A feature-rich, server-client based video conferencing application built with PyQt6 and socket programming in Python. Experience modern UI design with real-time video/audio streaming, text messaging, and file sharing capabilities.

## ✨ Features

### 🎬 Video & Audio

- **Real-time Video Streaming** with multiple resolution support (240p to 900p)
- **High-Quality Audio** streaming with noise management
- **Camera Controls** - Enable/disable camera with visual indicators
- **Microphone Controls** - Mute/unmute with visual feedback
- **Dynamic Layout** - Automatic video layout adjustment based on participant count

### 💬 Communication

- **Real-time Text Chat** with modern bubble-style messages
- **File Sharing** - Send and receive files seamlessly
- **Private Messaging** - Send messages to specific participants
- **Group Messaging** - Broadcast to all or selected participants

### 🎨 Modern UI/UX

- **Responsive Design** - Scales beautifully on different screen sizes
- **Gradient Themes** - Professional purple/blue color scheme
- **Dynamic Resizing** - All elements adapt to window size changes
- **Intuitive Controls** - User-friendly interface with emoji icons
- **Hover Effects** - Interactive feedback for better user experience

### 🔧 Advanced Features

- **Leave Meeting** - Disconnect without closing the application
- **Multiple Layout Options** - Choose from various video grid layouts
- **Connection Management** - Robust error handling and reconnection
- **Resource Cleanup** - Proper cleanup of camera and audio resources

## 📋 Requirements

### System Requirements

- **Operating System**: Windows 10/11, macOS 10.15+, or Linux Ubuntu 18.04+
- **Python**: 3.8 or higher
- **RAM**: Minimum 4GB (8GB recommended)
- **Camera**: USB webcam or built-in camera
- **Microphone**: Built-in or external microphone
- **Network**: Stable internet connection for remote meetings

### Python Dependencies

```bash
PyQt6>=6.4.0
opencv-python>=4.6.0
PyAudio>=0.2.11
numpy>=1.21.0
```

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/Lets-Meet-Video-Conference.git
cd Lets-Meet-Video-Conference
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv env
env\Scripts\activate

# macOS/Linux
python3 -m venv env
source env/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Additional Setup

#### For Windows:

```bash
# If you encounter PyAudio installation issues
pip install pipwin
pipwin install pyaudio
```

#### For macOS:

```bash
# Install portaudio first
brew install portaudio
pip install pyaudio
```

#### For Linux:

```bash
# Install system dependencies
sudo apt update
sudo apt install python3-pyaudio portaudio19-dev python3-dev
pip install pyaudio
```

## 🎯 Quick Start

### Starting the Server

1. **Configure Server IP** in `server.py`:

   ```python
   IP = 'YOUR_SERVER_IP'  # Replace with your actual IP
   ```

2. **Run the Server**:
   ```bash
   python server.py
   ```
   You should see:
   ```
   [LISTENING] Main Server is listening on YOUR_IP:53530
   [LISTENING] Video Server is listening on YOUR_IP:53531
   [LISTENING] Audio Server is listening on YOUR_IP:53532
   ```

### Connecting Clients

1. **Configure Client IP** in `client.py`:

   ```python
   IP = 'SERVER_IP'  # Use the same IP as server
   ```

2. **Run the Client**:

   ```bash
   python client.py
   ```

3. **Join Conference**:
   - Enter your username (no spaces allowed)
   - Click "🚀 Join Conference"
   - Start communicating!

## 📖 Usage Guide

### Video Controls

- **📹 Camera Menu**: Toggle camera on/off
- **🎤 Microphone Menu**: Toggle microphone on/off
- **📐 Layout Menu**: Choose video layout (240p to 900p)

### Chat Features

- **👥 Select Recipients**: Choose who receives your messages
- **💭 Text Input**: Type and send messages
- **📎 Send File**: Share files with participants
- **🚪 Leave Meeting**: Disconnect gracefully
- **📞 End Call**: Close the application

### Keyboard Shortcuts

- **Enter**: Send message
- **Escape**: Close dialogs

## 🏗️ Architecture

### Server Components

- **Main Server** (TCP): Handles client connections and text messages
- **Video Server** (UDP): Manages video streaming
- **Audio Server** (UDP): Handles audio streaming

### Client Components

- **GUI Layer**: PyQt6-based modern interface
- **Network Layer**: Socket-based communication
- **Media Layer**: OpenCV for video, PyAudio for audio
- **Threading**: Separate threads for video, audio, and messaging

### File Structure

```
Lets-Meet-Video-Conference/
├── client.py              # Main client application
├── server.py              # Server implementation
├── qt_gui.py              # GUI components and styling
├── constants.py           # Shared constants and utilities
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── img/                  # Image assets
    ├── nocam.jpeg        # No camera placeholder
    └── nomic.jpeg        # No microphone indicator
```

## 🛠️ Configuration

### Network Settings

Modify these in both `client.py` and `server.py`:

```python
MAIN_PORT = 53530    # Main communication port
VIDEO_PORT = 53531   # Video streaming port
AUDIO_PORT = 53532   # Audio streaming port
```

### Video Quality

Adjust in `qt_gui.py`:

```python
CAMERA_RES = "480p"    # Default camera resolution
LAYOUT_RES = "900p"    # Default layout resolution
```

### Audio Settings

Modify in `constants.py`:

```python
SAMPLE_RATE = 48000    # Audio sample rate
BLOCK_SIZE = 2048      # Audio buffer size
```

## 🐛 Troubleshooting

### Common Issues

**Camera not detected:**

```bash
# Check camera permissions and try different indices
# In qt_gui.py, modify Camera class:
self.cap = cv2.VideoCapture(0)  # Try 0, 1, 2
```

**Audio issues:**

```bash
# List audio devices
python -c "import pyaudio; pa = pyaudio.PyAudio(); [print(f'{i}: {pa.get_device_info_by_index(i)[\"name\"]}') for i in range(pa.get_device_count())]"
```

**Connection errors:**

- Ensure firewall allows the application
- Check if ports 53530-53532 are available
- Verify IP addresses are correct

**PyAudio installation fails:**

- On Windows: Use `pipwin install pyaudio`
- On macOS: Install portaudio with Homebrew first
- On Linux: Install python3-pyaudio package

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **PyQt6** for the modern GUI framework
- **OpenCV** for video processing capabilities
- **PyAudio** for audio streaming functionality
- **Socket Programming** for network communication

## 📞 Support

For support, email your-email@example.com or create an issue on GitHub.

---

**Made with ❤️ by [Your Name]**

_Bringing people together through technology_
