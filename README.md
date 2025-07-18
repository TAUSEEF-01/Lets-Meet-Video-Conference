# 🎥 Lets Meet - Modern Video Conference Application

A feature-rich, real-time server-client video conferencing application built with **Python**. Lets Meet leverages **PyQt6** for a modern GUI, **OpenCV** for video processing, **PyAudio** for audio streaming, and **socket programming** for robust network communication. The application supports live video/audio, chat, file sharing, and more, all with a responsive and intuitive interface.

---

## 🛠️ Technologies Used

- **Python 3.8+**  
- **PyQt6** – Modern cross-platform GUI  
- **OpenCV** – Real-time video capture and processing  
- **PyAudio** – Audio input/output streaming  
- **Socket Programming** – TCP/UDP networking for real-time communication  
- **Matplotlib** – Live server data rate monitoring  
- **Threading** – For concurrent media and message handling  

---

## ✨ Features

- Real-time video and audio conferencing
- Modern, responsive GUI (PyQt6)
- Live chat messaging between participants
- File sharing during conference
- Live server data rate monitoring (matplotlib)
- Multi-client support
- Device toggling (camera/microphone on/off)
- User join/leave notifications
- Robust error handling and connection management

---

## 📁 File Structure

```
Lets-Meet-Video-Conference/
│
├── client.py              # Client-side logic and GUI launch
├── server.py              # Server-side logic and data rate monitoring
├── constants.py           # Shared constants and message definitions
├── qt_gui.py              # PyQt6 GUI components and widgets
├── data_rate_core.py      # Data rate tracking and plotting utilities
├── requirements.txt       # Python dependencies
├── img/
│   ├── nocam.jpeg         # Placeholder image for no camera
│   └── nomic.jpeg         # Placeholder image for no microphone
└── README.md              # Project documentation
```

---

## 🌐 Network Configuration

- **Server IP:**  
  Set the `IP` variable in `server.py` to your server's local network IP address (e.g., `IP = "192.168.1.10"`).

- **Client IP:**  
  Set the `IP` variable in `client.py` to the same local network IP as the server, or use automatic detection if available.

- **Ports Used:**  
  - `MAIN_PORT` (default: 8080) – Main server communication  
  - `VIDEO_PORT` (default: 53531) – Video streaming  
  - `AUDIO_PORT` (default: 53532) – Audio streaming  

- **Firewall:**  
  Ensure these ports are open on your network and not blocked by firewalls.

---

## 🚀 How to Run

1. **Clone the Repository**
   ```bash
   git clone https://github.com/TAUSEEF-01/Lets-Meet-Video-Conference.git
   cd Lets-Meet-Video-Conference
   ```

2. **Create and Activate a Virtual Environment**
   ```bash
   # Windows
   python -m venv env
   env\Scripts\activate

   # macOS/Linux
   python3 -m venv env
   source env/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **(Optional) Fix PyAudio Installation Issues**
   - **Windows:**  
     ```bash
     pip install pipwin
     pipwin install pyaudio
     ```
   - **macOS:**  
     ```bash
     brew install portaudio
     pip install pyaudio
     ```
   - **Linux:**  
     ```bash
     sudo apt update
     sudo apt install python3-pyaudio portaudio19-dev python3-dev
     pip install pyaudio
     ```

5. **Configure Server and Client IPs**
   - In `server.py` and `client.py`, set the `IP` variable to your local network IP address.

6. **Start the Server**
   ```bash
   python server.py
   ```
   You should see server listening messages in the terminal.

7. **Start the Client(s)**
   ```bash
   python client.py
   ```
   Enter your username and join the conference!

---

## 👥 Contributors

- **Md. Tauseef-Ur-Rahman**
- **Tamzid Bin Tariq**

---

_Bringing people together through technology_