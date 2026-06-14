"""
J.A.R.V.I.S. — Listener Module
Handles microphone input and Whisper-based speech-to-text.

Uses direct PyAudio recording instead of speech_recognition's listen() method,
which has unreliable energy threshold detection for quiet laptop mics.
Records in fixed chunks, uses simple RMS-based VAD, normalizes audio,
and sends to Whisper for transcription.
"""

import threading
import queue
import time
import numpy as np

# Whisper loaded lazily
_whisper_model = None
_whisper_lock = threading.Lock()


def _log(msg):
    print(msg, flush=True)


def _load_whisper(model_name: str):
    """Load Whisper model once and cache it."""
    global _whisper_model
    if _whisper_model is None:
        with _whisper_lock:
            if _whisper_model is None:
                import whisper
                _log(f"[JARVIS] Loading Whisper model: {model_name}...")
                _log("[JARVIS] (First run will download the model, please wait...)")
                _whisper_model = whisper.load_model(model_name)
                _log("[JARVIS] Whisper model loaded successfully!")
    return _whisper_model


# ── Audio recording parameters ──
RATE = 16000          # Whisper expects 16kHz
CHANNELS = 1
CHUNK = 1024          # Frames per buffer
FORMAT_WIDTH = 2      # 16-bit audio = 2 bytes per sample

# ── VAD parameters ──
# These are tuned for quiet laptop mics
SILENCE_THRESHOLD_RMS = 0.003   # Very low - laptop mics are quiet
SPEECH_START_CHUNKS = 2         # Need 2 consecutive "loud" chunks to start recording
SILENCE_AFTER_SPEECH_SEC = 1.5  # Seconds of silence after speech to stop
MAX_RECORDING_SEC = 10          # Max recording length
MIN_RECORDING_SEC = 0.5         # Min recording length to bother transcribing


class Listener(threading.Thread):
    """
    Background thread that continuously listens to the microphone.
    Uses direct PyAudio recording with simple RMS-based VAD.
    Produces transcribed text into a queue.
    """

    def __init__(self, whisper_model_name: str = "base", result_queue: queue.Queue = None):
        super().__init__(daemon=True)
        self.whisper_model_name = whisper_model_name
        self.result_queue = result_queue or queue.Queue()
        self._stop_event = threading.Event()
        self._listening = threading.Event()
        self._listening.set()  # Start in listening mode
        self._pyaudio = None
        self._stream = None

    def _init_audio(self):
        """Initialize PyAudio and open microphone stream."""
        import pyaudio
        self._pyaudio = pyaudio.PyAudio()

        # Find best input device
        default_info = self._pyaudio.get_default_input_device_info()
        device_index = default_info['index']
        _log(f"[JARVIS] Using microphone: [{device_index}] {default_info['name']}")

        # List all input devices for debugging
        _log(f"[JARVIS] Available input devices:")
        for i in range(self._pyaudio.get_device_count()):
            info = self._pyaudio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                _log(f"[JARVIS]   [{i}] {info['name']} (inputs={info['maxInputChannels']})")

        self._stream = self._pyaudio.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=CHUNK,
        )
        _log("[JARVIS] Audio stream opened successfully")

    def _close_audio(self):
        """Close audio stream and PyAudio."""
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
        if self._pyaudio:
            try:
                self._pyaudio.terminate()
            except Exception:
                pass

    def _measure_ambient(self, duration_sec=2):
        """Measure ambient noise level to auto-tune VAD threshold."""
        _log(f"[JARVIS] Measuring ambient noise ({duration_sec}s, stay quiet)...")
        chunks_needed = int(RATE * duration_sec / CHUNK)
        rms_values = []

        for _ in range(chunks_needed):
            try:
                data = self._stream.read(CHUNK, exception_on_overflow=False)
                audio = np.frombuffer(data, np.int16).astype(np.float32) / 32768.0
                rms = np.sqrt(np.mean(audio ** 2))
                rms_values.append(rms)
            except Exception:
                continue

        if rms_values:
            ambient_rms = np.mean(rms_values)
            ambient_peak = np.max(rms_values)
            # Set threshold to 2x the peak ambient noise, minimum of 0.003
            threshold = max(ambient_peak * 2.0, SILENCE_THRESHOLD_RMS)
            _log(f"[JARVIS] Ambient noise: mean_RMS={ambient_rms:.5f}, peak_RMS={ambient_peak:.5f}")
            _log(f"[JARVIS] VAD threshold set to: {threshold:.5f}")
            return threshold
        return SILENCE_THRESHOLD_RMS

    def run(self):
        """Main listening loop."""
        try:
            self._init_audio()
        except Exception as e:
            _log(f"[JARVIS] FATAL: Could not initialize microphone: {e}")
            import traceback
            traceback.print_exc()
            return

        # Load Whisper
        _load_whisper(self.whisper_model_name)

        # Measure ambient noise
        vad_threshold = self._measure_ambient()

        _log("[JARVIS] Listener thread started -- actively listening for speech...")

        listen_cycles = 0
        while not self._stop_event.is_set():
            if not self._listening.is_set():
                time.sleep(0.1)
                continue

            try:
                # Phase 1: Wait for speech to start
                speech_start_count = 0
                while not self._stop_event.is_set() and self._listening.is_set():
                    try:
                        data = self._stream.read(CHUNK, exception_on_overflow=False)
                    except Exception:
                        time.sleep(0.01)
                        continue

                    audio = np.frombuffer(data, np.int16).astype(np.float32) / 32768.0
                    rms = np.sqrt(np.mean(audio ** 2))

                    if rms > vad_threshold:
                        speech_start_count += 1
                        if speech_start_count >= SPEECH_START_CHUNKS:
                            break
                    else:
                        speech_start_count = 0

                    listen_cycles += 1
                    if listen_cycles % 500 == 0:
                        _log(f"[JARVIS] Still listening... (cycles={listen_cycles})")

                if self._stop_event.is_set() or not self._listening.is_set():
                    continue

                # Phase 2: Record speech until silence
                _log("[JARVIS] Speech started! Recording...")
                frames = []
                silence_chunks = 0
                silence_chunks_needed = int(SILENCE_AFTER_SPEECH_SEC * RATE / CHUNK)
                max_chunks = int(MAX_RECORDING_SEC * RATE / CHUNK)

                for chunk_num in range(max_chunks):
                    if self._stop_event.is_set() or not self._listening.is_set():
                        break

                    try:
                        data = self._stream.read(CHUNK, exception_on_overflow=False)
                    except Exception:
                        continue

                    frames.append(data)
                    audio = np.frombuffer(data, np.int16).astype(np.float32) / 32768.0
                    rms = np.sqrt(np.mean(audio ** 2))

                    if rms < vad_threshold:
                        silence_chunks += 1
                        if silence_chunks >= silence_chunks_needed:
                            break
                    else:
                        silence_chunks = 0

                if not frames:
                    continue

                # Convert recorded frames to numpy array
                raw_data = b''.join(frames)
                audio_data = np.frombuffer(raw_data, np.int16).astype(np.float32) / 32768.0
                duration_sec = len(audio_data) / RATE
                rms = np.sqrt(np.mean(audio_data ** 2))
                peak = np.max(np.abs(audio_data)) if len(audio_data) > 0 else 0

                _log(f"[JARVIS] Recorded {duration_sec:.1f}s, RMS={rms:.4f}, Peak={peak:.4f}")

                # Skip too-short recordings
                if duration_sec < MIN_RECORDING_SEC:
                    _log("[JARVIS] Too short, skipping")
                    continue

                # ── Normalize audio amplitude ──
                # Laptop mics produce very quiet audio. Normalize to target peak.
                TARGET_PEAK = 0.7
                if peak > 0.001:
                    gain = min(TARGET_PEAK / peak, 50.0)
                    audio_data = np.clip(audio_data * gain, -1.0, 1.0)
                    new_rms = np.sqrt(np.mean(audio_data ** 2))
                    _log(f"[JARVIS] Normalized: gain={gain:.1f}x, RMS={new_rms:.4f}")

                # Transcribe with Whisper
                model = _load_whisper(self.whisper_model_name)
                result = model.transcribe(
                    audio_data,
                    language="en",
                    fp16=False,
                    no_speech_threshold=0.3,
                    logprob_threshold=-1.5,
                    condition_on_previous_text=False,
                    initial_prompt="Hey Jarvis, open Chrome. Jarvis, what time is it? Jarvis, are you there?",
                )
                text = result["text"].strip()

                # Filter out common Whisper hallucinations on silence/noise
                hallucinations = {
                    "", ".", "you", "thank you", "thanks for watching",
                    "thank you for watching", "the end", "bye",
                    "thanks for watching!", "subscribe",
                }
                text_check = text.lower().strip(".!?, ")
                if text_check in hallucinations:
                    _log(f"[JARVIS] Filtered noise: '{text}'")
                    continue

                if text and len(text) > 1:
                    _log(f"[JARVIS] >> Transcribed: '{text}'")
                    self.result_queue.put(text)

            except OSError as e:
                _log(f"[JARVIS] Mic OS error: {e}")
                time.sleep(2)
                # Try to reinitialize audio
                try:
                    self._close_audio()
                    self._init_audio()
                except Exception:
                    pass
            except Exception as e:
                _log(f"[JARVIS] Listener error: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(1)

        self._close_audio()

    def pause(self):
        """Pause listening."""
        _log("[JARVIS] Listener paused")
        self._listening.clear()

    def resume(self):
        """Resume listening."""
        _log("[JARVIS] Listener resumed")
        self._listening.set()

    def stop(self):
        """Stop the listener thread."""
        _log("[JARVIS] Listener stopping...")
        self._stop_event.set()
