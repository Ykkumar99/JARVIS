"""
Generate a startup sound effect for JARVIS.
Run this once to create the startup.wav file.
"""

import os
import struct
import math
import wave


def generate_startup_sound(output_path: str):
    """Generate a sci-fi bootup sound effect."""
    sample_rate = 44100
    duration = 2.5
    num_samples = int(sample_rate * duration)

    samples = []
    for i in range(num_samples):
        t = i / sample_rate

        # Rising frequency sweep (200 Hz -> 800 Hz)
        freq = 200 + 600 * (t / duration) ** 2
        sweep = 0.3 * math.sin(2 * math.pi * freq * t)

        # Sub bass hum
        bass = 0.15 * math.sin(2 * math.pi * 80 * t)

        # High sparkle
        sparkle_freq = 2000 + 1000 * math.sin(2 * math.pi * 0.5 * t)
        sparkle = 0.05 * math.sin(2 * math.pi * sparkle_freq * t)

        # Envelope: fade in, sustain, fade out
        if t < 0.3:
            envelope = t / 0.3
        elif t > duration - 0.5:
            envelope = (duration - t) / 0.5
        else:
            envelope = 1.0

        # Combine
        sample = (sweep + bass + sparkle) * envelope * 0.7

        # Clamp
        sample = max(-1.0, min(1.0, sample))
        samples.append(int(sample * 32767))

    # Write WAV
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with wave.open(output_path, "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        for s in samples:
            wav.writeframes(struct.pack("<h", s))

    print(f"[JARVIS] Startup sound saved to: {output_path}")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output = os.path.join(base_dir, "assets", "sounds", "startup.wav")
    generate_startup_sound(output)
    print("Done!")
