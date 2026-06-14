# 🔵 J.A.R.V.I.S.

### Just A Rather Very Intelligent System
*A local Windows desktop AI assistant inspired by Tony Stark's AI*

---

## ⚡ Quick Start

### 1. Run Setup (installs everything)
```bash
python setup.py
```

### 2. (Optional) Set Gemini API Key
```bash
set GEMINI_API_KEY=your-api-key-here
```

### 3. Launch JARVIS
```bash
python main.py
```

---

## 🔘 Wake Words

| Say This | JARVIS Responds |
|---|---|
| **"JARVIS, are you there?"** | "Online and ready, sir. How can I assist?" |
| **"Hey JARVIS"** | "Yes sir, I'm listening." |
| **"Daddy's home"** | *Dramatic HUD bootup animation* + "Welcome back, sir. I've been keeping things warm. All systems nominal." |

### Sleep Commands
- "JARVIS, standby"
- "That'll be all, JARVIS"
- Auto-sleeps after 30 seconds of inactivity

---

## 🤖 What JARVIS Can Do

| Command | Example |
|---|---|
| 🕐 **Time & Date** | "What time is it?", "What's today's date?" |
| 📂 **Open Apps** | "Open Chrome", "Launch Spotify", "Open VS Code" |
| ❌ **Close Apps** | "Close Notepad", "Kill Chrome" |
| 🔍 **Web Search** | "Search for the weather in Noida" |
| 📊 **System Info** | "How much RAM is being used?", "CPU load?" |
| 🎵 **Play Music** | "Play some music" |
| ⏰ **Reminders** | "Remind me in 10 minutes to drink water" |
| 💬 **Small Talk** | "Tell me a joke", "Are you smarter than me?" |
| 🧠 **AI Q&A** | Any question → routes to Gemini API |

---

## 🎨 UI Features

- **Floating HUD** — Always-on-top dark glass widget in the corner
- **Arc Reactor** — Pulsing animation that glows brighter when listening
- **Status Indicators** — Standby (dim) / Listening (cyan) / Processing (amber) / Speaking (green)
- **Draggable** — Click and drag to reposition
- **System Tray** — Minimize to tray, double-click to restore

---

## ⚙️ Tech Stack

| Component | Technology |
|---|---|
| UI | PyQt6 (floating glassmorphism HUD) |
| STT | OpenAI Whisper (offline) |
| TTS Primary | Coqui TTS — `tts_models/en/vctk/vits` speaker `p267` |
| TTS Fallback | edge-tts — `en-GB-RyanNeural` |
| System Stats | psutil |
| AI Q&A | Google Gemini API |
| Audio | pygame |

---

## 📁 Project Structure

```
JARVIS/
├── main.py              # Entry point & orchestrator
├── config.py            # All configuration
├── setup.py             # One-click installer
├── requirements.txt     # Dependencies
├── generate_sounds.py   # Startup sound generator
├── core/
│   ├── listener.py      # Whisper STT
│   ├── speaker.py       # Coqui/edge-tts
│   ├── wake_word.py     # Wake word detection
│   └── command_router.py # Intent routing
├── skills/
│   ├── time_date.py     # Time & date
│   ├── app_control.py   # Open/close apps
│   ├── system_info.py   # CPU, RAM, battery
│   ├── web_search.py    # Google search
│   ├── media.py         # Music playback
│   ├── reminders.py     # Timed reminders
│   ├── small_talk.py    # Jokes & banter
│   └── gemini_ai.py     # Gemini AI fallback
├── ui/
│   ├── hud_widget.py    # Main floating HUD
│   ├── animations.py    # Arc reactor + bootup
│   ├── styles.py        # QSS dark theme
│   └── system_tray.py   # Tray icon
└── assets/
    ├── sounds/
    ├── icons/
    └── fonts/
```

---

## 🔒 Privacy

- **Offline by default** — Voice recognition (Whisper) and TTS (Coqui) run entirely locally
- **Only Gemini API needs internet** — and that's optional
- **No data sent anywhere** — everything stays on your machine
