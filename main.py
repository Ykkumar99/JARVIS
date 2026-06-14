"""
J.A.R.V.I.S. — Just A Rather Very Intelligent System
Main entry point. Orchestrates all subsystems.

Usage:
    python -u main.py
"""

import sys
import os
import queue
import time
import threading

# Force unbuffered output on Windows
os.environ["PYTHONUNBUFFERED"] = "1"

# Add project root to path
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _PROJECT_ROOT)

# Load .env file BEFORE any config imports
from dotenv import load_dotenv
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))


def log(msg):
    """Print with flush for Windows console."""
    print(msg, flush=True)


from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal, QObject

from config import WHISPER_MODEL, INACTIVITY_TIMEOUT_SECONDS, AUTO_COMPACT_SECONDS
from core.listener import Listener
from core.speaker import Speaker, speak
from core.wake_word import check_wake_word, check_sleep_command, is_daddy_home
from core.command_router import route_command
from skills.time_date import get_time, get_date
from skills.app_control import open_app, close_app
from skills.system_info import get_system_info
from skills.web_search import web_search
from skills.media import play_music
from skills.reminders import ReminderManager
from skills.small_talk import handle_small_talk
from skills.gemini_ai import ask_gemini, is_gemini_available
from ui.hud_widget import HudWidget
from ui.system_tray import JarvisTray


class JarvisBridge(QObject):
    """
    Bridge between background threads and the Qt UI.
    Emits signals to safely update the UI from worker threads.
    """
    # Signals for UI updates
    wake_up_signal = pyqtSignal(str, bool)  # response_text, is_daddy_home
    sleep_signal = pyqtSignal()
    command_signal = pyqtSignal(str)        # user command text
    response_signal = pyqtSignal(str)       # JARVIS response text
    state_signal = pyqtSignal(str)          # "standby", "listening", "processing", "speaking"
    online_signal = pyqtSignal(bool)        # Gemini API availability


class JarvisAssistant:
    """Main JARVIS orchestrator."""

    def __init__(self):
        self.is_awake = False
        self.last_activity_time = 0

        # Communication queue from listener
        self.text_queue = queue.Queue()

        # Bridge for thread-safe UI updates
        self.bridge = JarvisBridge()

        # Listener (STT)
        self.listener = Listener(
            whisper_model_name=WHISPER_MODEL,
            result_queue=self.text_queue,
        )

        # Speaker (TTS)
        self.speaker = Speaker()
        self.speaker.on_start = lambda: self.bridge.state_signal.emit("speaking")
        self.speaker.on_done = lambda: self.bridge.state_signal.emit(
            "listening" if self.is_awake else "standby"
        )

        # Reminder manager
        self.reminder_manager = ReminderManager(speak_callback=self._reminder_speak)

        # UI
        self.app = None
        self.hud = None
        self.tray = None

        # Auto-compact timer (separate from inactivity standby)
        self._auto_compact_timer = None

    def _reminder_speak(self, text: str):
        """Called when a reminder fires."""
        self.bridge.response_signal.emit(text)
        self.speaker.say(text)
        self.last_activity_time = time.time()

    def start(self):
        """Start all JARVIS subsystems."""
        log("[JARVIS] Initializing Qt application...")

        # Start Qt app
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # Global exception hook for Qt threads
        def _exception_hook(exc_type, exc_value, exc_tb):
            import traceback
            log("[JARVIS] UNCAUGHT EXCEPTION:")
            traceback.print_exception(exc_type, exc_value, exc_tb)
        sys.excepthook = _exception_hook

        log("[JARVIS] Creating HUD widget...")

        # Create HUD
        self.hud = HudWidget()
        self.hud.close_requested.connect(self._quit)
        self.hud.minimize_requested.connect(self._on_minimize_clicked)
        self.hud.compact_clicked.connect(self._on_compact_clicked)

        # Connect bridge signals to UI
        self.bridge.wake_up_signal.connect(self._on_wake_up)
        self.bridge.sleep_signal.connect(self._on_sleep)
        self.bridge.command_signal.connect(self._on_command)
        self.bridge.response_signal.connect(self._on_response)
        self.bridge.state_signal.connect(self._on_state_change)
        self.bridge.online_signal.connect(self._on_online_status)

        log("[JARVIS] Setting up system tray...")

        # System tray
        self.tray = JarvisTray(
            self.hud,
            on_show=self._on_compact_clicked,
            on_quit=self._quit,
        )
        self.tray.show()

        # Show HUD in compact standby mode
        self.hud.set_state_standby()
        self.hud.animate_in()

        log("[JARVIS] Starting listener thread...")

        # Start background threads
        self.listener.start()
        self.speaker.start()

        log("[JARVIS] Starting speaker thread...")

        # Poll for transcribed text
        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self._poll_text_queue)
        self._poll_timer.start(100)  # Check every 100ms

        # Inactivity check (full standby after 30s)
        self._inactivity_timer = QTimer()
        self._inactivity_timer.timeout.connect(self._check_inactivity)
        self._inactivity_timer.start(1000)  # Check every second

        # Auto-compact timer (shrink UI after 10s, keep listening)
        self._auto_compact_timer = QTimer()
        self._auto_compact_timer.setSingleShot(True)
        self._auto_compact_timer.timeout.connect(self._auto_compact)

        # Gemini API status check
        self._api_check_timer = QTimer()
        self._api_check_timer.timeout.connect(self._check_api_status)
        self._api_check_timer.start(30000)  # Check every 30 seconds
        # Initial check
        self._check_api_status()

        log("[JARVIS] ========================================")
        log("[JARVIS] All systems online!")
        log("[JARVIS] Waiting for wake word...")
        log("[JARVIS] Say 'Hey JARVIS' to activate")
        log("[JARVIS] ========================================")

        # Run event loop
        sys.exit(self.app.exec())

    def _poll_text_queue(self):
        """Check for new transcribed text from the listener."""
        while not self.text_queue.empty():
            try:
                text = self.text_queue.get_nowait()
                self._process_text(text)
            except queue.Empty:
                break

    def _process_text(self, text: str):
        """Process a piece of transcribed text."""
        log(f"[JARVIS] Heard: '{text}'")

        if not self.is_awake:
            # Check for wake word
            is_wake, response = check_wake_word(text)
            if is_wake:
                log(f"[JARVIS] Wake word detected! Response: {response}")
                daddy = is_daddy_home(text)
                self.bridge.wake_up_signal.emit(response, daddy)
            else:
                log(f"[JARVIS] (sleeping - not a wake word)")
            return

        # Check for sleep command
        if check_sleep_command(text):
            self.speaker.say("Going to standby, sir. Call me if you need anything.")
            self.bridge.response_signal.emit("Going to standby, sir.")
            self.bridge.sleep_signal.emit()
            return

        # Update activity
        self.last_activity_time = time.time()

        # Cancel auto-compact timer — user is active
        self._auto_compact_timer.stop()

        # If HUD is compact, expand it (user gave a command while listening)
        if self.hud.is_compact():
            self.hud.expand_to_full()

        # Show the command
        self.bridge.command_signal.emit(text)
        self.bridge.state_signal.emit("processing")

        # Pause listener while processing to avoid feedback
        self.listener.pause()

        # Route command in a background thread
        threading.Thread(
            target=self._execute_command,
            args=(text,),
            daemon=True,
        ).start()

    def _execute_command(self, text: str):
        """Execute a routed command (runs in background thread)."""
        try:
            skill, params = route_command(text)
            log(f"[JARVIS] Routing to: {skill} with {params}")

            response = ""

            if skill == "time":
                response = get_time()
            elif skill == "date":
                response = get_date()
            elif skill == "open_app":
                response = open_app(params["app"])
            elif skill == "close_app":
                response = close_app(params["app"])
            elif skill == "system_info":
                response = get_system_info(params.get("type", "all"))
            elif skill == "search":
                response = web_search(params["query"])
            elif skill == "play_music":
                response = play_music()
            elif skill == "reminder":
                response = self.reminder_manager.set_reminder(
                    params["seconds"], params["message"],
                    params["amount"], params["unit"],
                )
            elif skill == "small_talk":
                response = handle_small_talk(params["text"])
            elif skill == "gemini":
                self.bridge.response_signal.emit("Thinking...")
                response = ask_gemini(params["text"])
            else:
                response = "I'm not sure how to handle that, sir."

            log(f"[JARVIS] Response: {response}")
            self.bridge.response_signal.emit(response)
            self.speaker.say(response)

        except Exception as e:
            error_msg = f"I encountered an error, sir: {str(e)}"
            log(f"[JARVIS] Error: {e}")
            import traceback
            traceback.print_exc()
            self.bridge.response_signal.emit(error_msg)
            self.speaker.say("I encountered an error processing that request, sir.")
        finally:
            # Wait for speaker to finish before resuming listener
            # This prevents the mic from picking up JARVIS's own voice
            while self.speaker.is_speaking:
                time.sleep(0.1)
            # Small extra delay for audio to fully stop
            time.sleep(0.3)
            # Resume listener
            self.listener.resume()
            # Start auto-compact countdown
            self._start_auto_compact()

    def _start_auto_compact(self):
        """Start the auto-compact countdown (runs from background thread, needs signal)."""
        # Use QTimer from the main thread via a singleShot
        QTimer.singleShot(0, lambda: self._auto_compact_timer.start(AUTO_COMPACT_SECONDS * 1000))

    def _auto_compact(self):
        """Shrink HUD to compact pill after inactivity, but keep listening."""
        if not self.is_awake:
            return
        if self.speaker.is_speaking:
            # Restart timer — speaker still going
            self._auto_compact_timer.start(AUTO_COMPACT_SECONDS * 1000)
            return
        if not self.hud.is_compact():
            log("[JARVIS] Auto-compacting HUD (still listening)...")
            self.hud.shrink_to_compact()

    def _check_inactivity(self):
        """Put JARVIS to sleep after inactivity timeout (full standby)."""
        if not self.is_awake:
            return

        if self.speaker.is_speaking:
            self.last_activity_time = time.time()
            return

        elapsed = time.time() - self.last_activity_time
        if elapsed >= INACTIVITY_TIMEOUT_SECONDS:
            self.bridge.response_signal.emit("Going to standby due to inactivity.")
            self.speaker.say("Going to standby, sir.")
            self.bridge.sleep_signal.emit()

    # ── UI Callbacks ─────────────────────────────────

    def _on_wake_up(self, response_text: str, daddy: bool):
        """Handle wake up event."""
        self.is_awake = True
        self.last_activity_time = time.time()
        self._auto_compact_timer.stop()

        if daddy:
            # Dramatic bootup
            self.listener.pause()
            self.hud.play_bootup(callback=lambda: self._finish_wakeup(response_text))
        else:
            # Cinematic expand from compact to full
            self.hud.expand_to_full(callback=lambda: self._finish_wakeup(response_text))

    def _finish_wakeup(self, response_text: str):
        """Complete the wakeup sequence."""
        self.hud.set_state_listening()
        self.hud.set_response(response_text)
        self.listener.pause()
        self.speaker.say(response_text)
        log(f"[JARVIS] Awake: {response_text}")

        # Resume listener after TTS finishes (in background to not block Qt)
        def _wait_and_resume():
            while self.speaker.is_speaking:
                time.sleep(0.1)
            time.sleep(0.3)
            self.listener.resume()
            # Start auto-compact countdown
            self._start_auto_compact()
        threading.Thread(target=_wait_and_resume, daemon=True).start()

    def _on_sleep(self):
        """Handle sleep event -- shrink to compact + enter standby."""
        self.is_awake = False
        self._auto_compact_timer.stop()
        self.hud.set_state_standby()
        self.hud.set_command("")
        self.hud.set_response('Say "Hey JARVIS" to activate...')
        self.hud.shrink_to_compact()
        log("[JARVIS] Going to standby...")

    def _on_minimize_clicked(self):
        """Minimize button -- enter standby + shrink to compact."""
        log("[JARVIS] Minimize clicked -- entering standby...")
        self.speaker.say("Going to standby, sir.")
        self.bridge.response_signal.emit("Going to standby, sir.")
        self.bridge.sleep_signal.emit()

    def _on_compact_clicked(self):
        """Compact pill clicked -- wake up JARVIS."""
        if not self.is_awake:
            log("[JARVIS] Compact pill clicked -- waking up...")
            self.is_awake = True
            self.last_activity_time = time.time()
            self.hud.expand_to_full(callback=lambda: self._finish_wakeup("Yes sir, I'm listening."))
        elif self.hud.is_compact():
            # Already awake but HUD is compact — just expand
            log("[JARVIS] Expanding HUD (already awake)...")
            self.hud.expand_to_full()
            self._auto_compact_timer.stop()
            self._start_auto_compact()

    def _on_command(self, text: str):
        """Display user command on HUD."""
        self.hud.set_command(text)

    def _on_response(self, text: str):
        """Display JARVIS response on HUD."""
        self.hud.set_response(text)

    def _on_state_change(self, state: str):
        """Update HUD state indicator."""
        if state == "standby":
            self.hud.set_state_standby()
        elif state == "listening":
            self.hud.set_state_listening()
        elif state == "processing":
            self.hud.set_state_processing()
        elif state == "speaking":
            self.hud.set_state_speaking()

    def _on_online_status(self, is_online: bool):
        """Update HUD online/offline indicator."""
        self.hud.set_online_status(is_online)

    def _check_api_status(self):
        """Check Gemini API availability and update HUD."""
        online = is_gemini_available()
        self.bridge.online_signal.emit(online)

    def _show_hud(self):
        """Show the HUD from tray."""
        self._on_compact_clicked()

    def _quit(self):
        """Shut down JARVIS."""
        log("[JARVIS] Shutting down...")
        self._auto_compact_timer.stop()
        self.listener.stop()
        self.speaker.stop()
        self.reminder_manager.cancel_all()
        self.tray.hide()
        self.app.quit()


def main():
    """Entry point."""
    log("=" * 50)
    log("  J.A.R.V.I.S.")
    log("  Just A Rather Very Intelligent System")
    log("  v1.0 -- Windows Desktop Assistant")
    log("=" * 50)
    log("")

    try:
        jarvis = JarvisAssistant()
        jarvis.start()
    except Exception as e:
        log(f"[JARVIS] FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()
