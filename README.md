# Let's Meet - Video Conference Application

A modern, aesthetic video conferencing application built with Python and PyQt6, featuring real-time video streaming, audio communication, and chat functionality.

## 🎥 Features

- **Real-time Video Streaming**: High-quality video communication with multiple participants
- **Audio Communication**: Crystal clear audio transmission with microphone controls
- **Group Chat**: Modern chat interface with message bubbles and timestamps
- **File Sharing**: Send files to selected participants
- **Device Controls**: Toggle camera and microphone on/off
- **Responsive Layout**: Automatic video grid resizing based on participant count
- **Modern UI**: Beautiful gradient designs with smooth animations
- **Cross-platform**: Works on Windows, macOS, and Linux

## 🚀 Prerequisites

- Python 3.8 or higher
- Webcam and microphone
- Network connection

## 📦 Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/Lets-Meet-Video-Conference.git
cd Lets-Meet-Video-Conference
```

2. Create a virtual environment:

```bash
python -m venv env
```

3. Activate the virtual environment:

- Windows: `env\Scripts\activate`
- macOS/Linux: `source env/bin/activate`

4. Install required dependencies:

```bash
pip install -r requirements.txt
```

## 🔧 Dependencies

```
PyQt6>=6.4.0
opencv-python>=4.7.0
pyaudio>=0.2.11
numpy>=1.21.0
```

## 🏃‍♂️ Quick Start

1. **Start the Server** (First Terminal):

```bash
python server.py
```

2. **Launch Client** (Second Terminal):

```bash
python client.py
```

3. **Join the Meeting**:
   - Enter your username in the login dialog
   - Click "🚀 Join Conference"
   - Start communicating!

## 🎮 Usage

### Video Controls

- **📹 Camera Menu**: Enable/disable your camera
- **🎤 Microphone Menu**: Mute/unmute your microphone
- **📐 Layout Menu**: Choose video grid resolution (240p to 900p)

### Chat Features

- **👥 Select Recipients**: Choose who to send messages to
- **💭 Text Messages**: Type and send instant messages
- **📎 File Sharing**: Share files with selected participants
- **📞 End Call**: Leave the conference

### Window Management

- **Resizable Interface**: Adjust window size as needed
- **Top-positioned**: Window appears at the top-center of screen
- **Responsive Chat**: Chat section adjusts height automatically

## 🏗️ Architecture

```
├── server.py          # WebSocket signaling server
├── client.py          # Main client application
├── qt_gui.py          # PyQt6 GUI implementation
├── constants.py       # Application constants
├── qt_gui.html        # Alternative web-based GUI
└── img/              # UI assets
    ├── nocam.jpeg    # No camera placeholder
    └── nomic.jpeg    # Muted microphone indicator
```

## 🌐 Network Configuration

- **Default Server Port**: 8765 (WebSocket) + 8766 (HTTP)
- **Local Network**: Clients can connect via LAN IP
- **Firewall**: Ensure ports are open for network access

## 🎨 UI Customization

The application features a modern design with:

- **Gradient backgrounds** for visual appeal
- **Rounded corners** and smooth borders
- **Hover effects** on interactive elements
- **Professional color scheme** (Purple/Blue theme)
- **Emoji icons** for intuitive navigation

## 🔧 Troubleshooting

### Camera Issues

- Error: "Camera index out of range"
  - Solution: Check camera connections, adjust camera index in `Camera` class

### Audio Problems

- Microphone not detected
  - Solution: Verify PyAudio installation and microphone permissions

### Connection Issues

- Server connection failed
  - Solution: Ensure server is running and firewall allows connections

### Performance

- Lag or choppy video
  - Solution: Reduce video resolution via Layout menu

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- PyQt6 for the beautiful GUI framework
- OpenCV for video processing capabilities
- PyAudio for real-time audio streaming
- The open-source community for inspiration

## 🔮 Future Enhancements

- [ ] Screen sharing functionality
- [ ] Recording capabilities
- [ ] Virtual backgrounds
- [ ] Breakout rooms
- [ ] Mobile app support
- [ ] End-to-end encryption
- [ ] Cloud deployment options

---

**Made with ❤️ for seamless video communication**
