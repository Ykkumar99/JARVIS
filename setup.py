"""
J.A.R.V.I.S. — Setup & Installation Helper
Run this script to set up JARVIS for the first time.
"""

import os
import sys
import subprocess


def main():
    print("=" * 50)
    print("  J.A.R.V.I.S. Setup")
    print("  Just A Rather Very Intelligent System")
    print("=" * 50)
    print()

    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Step 1: Create directories
    print("[1/5] Creating directories...")
    dirs = [
        os.path.join(base_dir, "assets", "sounds"),
        os.path.join(base_dir, "assets", "icons"),
        os.path.join(base_dir, "assets", "fonts"),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"  [OK] {d}")

    # Step 2: Install core dependencies first
    print("\n[2/5] Installing core dependencies...")
    core_deps = [
        "PyQt6",
        "psutil",
        "SpeechRecognition",
        "PyAudio",
        "pygame",
        "numpy",
        "edge-tts",
        "google-generativeai",
    ]
    for dep in core_deps:
        print(f"  Installing {dep}...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", dep],
            capture_output=True,
        )
        print(f"  [OK] {dep}")

    # Step 3: Install Whisper
    print("\n[3/5] Installing OpenAI Whisper...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "openai-whisper"],
        capture_output=True,
    )
    print("  [OK] Whisper installed")

    # Step 4: Try Coqui TTS (optional, may fail on some systems)
    print("\n[4/5] Attempting Coqui TTS installation (optional)...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "TTS"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print("  [OK] Coqui TTS installed successfully!")
        print("  --> Will use offline British voice model")
    else:
        print("  [WARN] Coqui TTS installation failed (this is okay)")
        print("  --> Will use edge-tts (en-GB-RyanNeural) as fallback")
        print(f"  --> Error: {result.stderr[-200:] if result.stderr else 'unknown'}")

    # Step 5: Generate startup sound
    print("\n[5/5] Generating startup sound effect...")
    try:
        from generate_sounds import generate_startup_sound
        sound_path = os.path.join(base_dir, "assets", "sounds", "startup.wav")
        generate_startup_sound(sound_path)
        print("  [OK] Startup sound generated")
    except Exception as e:
        print(f"  [WARN] Could not generate sound: {e}")

    print("\n" + "=" * 50)
    print("  Setup Complete!")
    print("=" * 50)
    print()
    print("To set up Gemini AI (optional):")
    print('  set GEMINI_API_KEY=your-api-key-here')
    print()
    print("To start JARVIS:")
    print(f"  python {os.path.join(base_dir, 'main.py')}")
    print()
    print("Wake words:")
    print('  "Hey JARVIS"')
    print('  "JARVIS, are you there?"')
    print('  "Daddy\'s home" (dramatic bootup)')
    print()


if __name__ == "__main__":
    main()
