# 🎧 audio-combine

**audio-combine** is a simple terminal application (TUI) written in Go. It helps you combine multiple audio outputs (like laptop speakers, HDMI, and Bluetooth) into a single output on **Linux**.

It works with both **PulseAudio** and **PipeWire**.

---

## ✨ Features

*   **Simple Interface**: Clean and easy-to-use terminal screen.
*   **Auto-Detect**: Automatically finds your speakers, HDMI, and Bluetooth devices.
*   **Instant Combine**: Merges your selected outputs in one click.
*   **Auto-Route**: Automatically moves all playing music/videos to the new combined output.
*   **Easy Reset**: Remove combined outputs anytime with a single keypress.

---

## 🛠️ Requirements

Your Linux system needs:
1.  `pactl` (standard tool on PulseAudio and PipeWire systems).
2.  Go 1.18+ (only if you want to build it yourself).

---

## 🚀 How to Run & Install

Use the following commands in your terminal:

```bash
# Run the app without building
make run

# Build the app executable
make build

# Install the app to your system (so you can run 'audio-combine' anywhere)
sudo make install
```

### 🎮 Keyboard Controls
*   `Up / Down` (or `k / j`): Move up and down the list.
*   `SPACE`: Select or deselect an output.
*   `ENTER`: Combine the selected outputs.
*   `R`: Refresh the list of audio devices.
*   `DELETE`: Remove the combined output and reset.
*   `Q` (or `Ctrl+C`): Exit the app.

---

## 💡 Tip: Use `pavucontrol` for Easy Audio Control

We highly recommend using **pavucontrol** (PulseAudio Volume Control) alongside this tool. It makes managing your volume much easier.

### Why use `pavucontrol`?
1.  **Individual Volume**: Adjust the volume of your Bluetooth speaker and laptop speaker separately inside the combined output.
2.  **Move Apps Visually**: Easily choose which app plays through the combined output using a graphical interface.
3.  **Visual Audio Bars**: See real-time volume meters to check if everything is balanced.

### How to Install `pavucontrol`:
*   **Ubuntu / Debian**: `sudo apt install pavucontrol`
*   **Fedora**: `sudo dnf install pavucontrol`
*   **Arch Linux**: `sudo pacman -S pavucontrol`

Once installed, just open your app launcher and search for **Volume Control**, or run `pavucontrol` in your terminal.
