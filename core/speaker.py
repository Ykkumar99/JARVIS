"""
J.A.R.V.I.S. — Speaker Module
Handles Text-to-Speech using Coqui TTS (primary, offline) with edge-tts fallback.
"""

import os
import sys
import threading
import tempfile
import time

import pygame

_tts_engine = None
_tts_type = None  # "coqui" or "edge"
_tts_lock = threading.Lock()
_pygame_initialized = False


def _log(msg):
    """Print with flush for Windows."""
    print(msg, flush=True)


def _init_pygame():
    """Initialize pygame mixer for audio playback."""
    global _pygame_initialized
    if not _pygame_initialized:
        try:
            pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=4096)
            _pygame_initialized = True
            _log("[JARVIS] Pygame mixer initialized")
        except Exception as e:
            _log(f"[JARVIS] Pygame mixer init failed: {e}")
            # Try with default settings
            try:
                pygame.mixer.init()
                _pygame_initialized = True
                _log("[JARVIS] Pygame mixer initialized (default settings)")
            except Exception as e2:
                _log(f"[JARVIS] Pygame mixer completely failed: {e2}")


def _init_tts():
    """Try Coqui TTS first, fall back to edge-tts."""
    global _tts_engine, _tts_type

    if _tts_engine is not None:
        return

    with _tts_lock:
        if _tts_engine is not None:
            return

        # Try Coqui TTS
        try:
            from TTS.api import TTS as CoquiTTS
            _log("[JARVIS] Loading Coqui TTS model...")
            from config import COQUI_MODEL, COQUI_SPEAKER
            engine = CoquiTTS(model_name=COQUI_MODEL, progress_bar=True)
            _tts_engine = engine
            _tts_type = "coqui"
            _log(f"[JARVIS] Coqui TTS loaded: {COQUI_MODEL} (speaker: {COQUI_SPEAKER})")
            return
        except Exception as e:
            _log(f"[JARVIS] Coqui TTS failed: {e}")
            _log("[JARVIS] Falling back to edge-tts...")

        # Fallback: edge-tts
        try:
            import edge_tts
            _tts_engine = "edge"
            _tts_type = "edge"
            _log("[JARVIS] edge-tts ready (en-GB-RyanNeural)")
        except ImportError as e:
            _log(f"[JARVIS] ERROR: No TTS engine available! {e}")
            _tts_engine = None
            _tts_type = None


def speak(text: str, on_start=None, on_done=None):
    """
    Speak the given text using the available TTS engine.
    Blocks until speech is complete.
    """
    _init_tts()
    _init_pygame()

    if _tts_engine is None:
        _log(f"[JARVIS] (no TTS) Would say: {text}")
        if on_done:
            on_done()
        return

    try:
        # Create temp file for audio — edge-tts outputs mp3
        if _tts_type == "edge":
            tmp_file = os.path.join(tempfile.gettempdir(), "jarvis_speech.mp3")
        else:
            tmp_file = os.path.join(tempfile.gettempdir(), "jarvis_speech.wav")

        if on_start:
            on_start()

        if _tts_type == "coqui":
            from config import COQUI_SPEAKER
            _tts_engine.tts_to_file(
                text=text,
                file_path=tmp_file,
                speaker=COQUI_SPEAKER,
            )
        elif _tts_type == "edge":
            import asyncio
            import edge_tts
            from config import EDGE_TTS_VOICE

            async def _generate():
                communicate = edge_tts.Communicate(text, EDGE_TTS_VOICE)
                await communicate.save(tmp_file)

            # Run async edge-tts — need a fresh event loop in threads
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(_generate())
                loop.close()
            except Exception as e:
                _log(f"[JARVIS] edge-tts generation error: {e}")
                if on_done:
                    on_done()
                return

        # Play the audio
        if os.path.exists(tmp_file) and os.path.getsize(tmp_file) > 0:
            _log(f"[JARVIS] Playing speech ({os.path.getsize(tmp_file)} bytes)...")
            try:
                pygame.mixer.music.load(tmp_file)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.05)
                pygame.mixer.music.unload()
            except Exception as e:
                _log(f"[JARVIS] Audio playback error: {e}")

            # Clean up
            try:
                os.remove(tmp_file)
            except OSError:
                pass
        else:
            _log("[JARVIS] TTS generated empty or missing audio file")

    except Exception as e:
        _log(f"[JARVIS] TTS error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if on_done:
            on_done()


class Speaker(threading.Thread):
    """Background thread for non-blocking speech."""

    def __init__(self):
        super().__init__(daemon=True)
        self._queue = []
        self._lock = threading.Lock()
        self._event = threading.Event()
        self._stop = threading.Event()
        self.is_speaking = False
        self.on_start = None
        self.on_done = None

    def run(self):
        _init_tts()
        _init_pygame()

        while not self._stop.is_set():
            self._event.wait(timeout=0.1)
            self._event.clear()

            while True:
                with self._lock:
                    if not self._queue:
                        break
                    text = self._queue.pop(0)

                self.is_speaking = True
                speak(text, on_start=self.on_start, on_done=self.on_done)
                self.is_speaking = False

    def say(self, text: str):
        """Queue text to be spoken."""
        with self._lock:
            self._queue.append(text)
        self._event.set()

    def stop(self):
        self._stop.set()
        self._event.set()
