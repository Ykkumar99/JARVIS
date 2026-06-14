"""
J.A.R.V.I.S. Configuration
Just A Rather Very Intelligent System
"""

import os
from dotenv import load_dotenv

# ─── Load .env file ──────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")
ICONS_DIR = os.path.join(ASSETS_DIR, "icons")

# ─── Wake Words ──────────────────────────────────────
WAKE_WORDS = {
    "jarvis are you there": "Online and ready, sir. How can I assist?",
    "hey jarvis": "Yes sir, I'm listening.",
    "daddy's home": "Welcome back, sir. I've been keeping things warm. All systems nominal.",
    "daddys home": "Welcome back, sir. I've been keeping things warm. All systems nominal.",
    "daddy is home": "Welcome back, sir. I've been keeping things warm. All systems nominal.",
}

# ─── Sleep Commands ──────────────────────────────────
SLEEP_COMMANDS = [
    "jarvis standby",
    "jarvis stand by",
    "that'll be all jarvis",
    "that will be all jarvis",
    "that'll be all",
    "go to sleep",
    "standby",
]

# ─── Inactivity Timeout ─────────────────────────────
INACTIVITY_TIMEOUT_SECONDS = 30

# ─── TTS Configuration ──────────────────────────────
# Coqui TTS - Primary (offline)
COQUI_MODEL = "tts_models/en/vctk/vits"
COQUI_SPEAKER = "p267"  # British male speaker

# Edge TTS - Fallback
EDGE_TTS_VOICE = "en-GB-RyanNeural"

# ─── Whisper Configuration ───────────────────────────
WHISPER_MODEL = "small"  # Options: tiny, base, small, medium, large

# ─── Gemini API ──────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.0-flash"

# ─── App Aliases (for opening apps) ─────────────────
APP_ALIASES = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "browser": "chrome",
    "notepad": "notepad",
    "calculator": "calc",
    "calc": "calc",
    "file explorer": "explorer",
    "explorer": "explorer",
    "spotify": "spotify",
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "task manager": "taskmgr",
    "command prompt": "cmd",
    "cmd": "cmd",
    "terminal": "wt",
    "settings": "ms-settings:",
    "paint": "mspaint",
    "vs code": "code",
    "vscode": "code",
    "visual studio code": "code",
    "discord": "discord",
    "telegram": "telegram",
    "whatsapp": r"explorer shell:AppsFolder\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App",
    "youtube": "https://youtube.com",
    "youtube music": "https://music.youtube.com",
    "gmail": "https://mail.google.com",
    "github": "https://github.com",
}

# ─── UI Configuration ───────────────────────────────
HUD_WIDTH = 420
HUD_HEIGHT = 320
HUD_OPACITY = 0.92

# ─── Compact / Standby Mode ─────────────────────
COMPACT_WIDTH = 140
COMPACT_HEIGHT = 140
AUTO_COMPACT_SECONDS = 10  # Shrink UI after 10s inactivity (stays listening)
