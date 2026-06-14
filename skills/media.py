"""
J.A.R.V.I.S. — Media Skill
Play music via Spotify or YouTube Music.
"""

import subprocess
import webbrowser


def play_music() -> str:
    """Try to open Spotify, fall back to YouTube Music."""
    try:
        subprocess.Popen(
            "spotify",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return "Launching Spotify for you, sir. Enjoy the music."
    except Exception:
        webbrowser.open("https://music.youtube.com")
        return "Spotify doesn't seem to be installed. I've opened YouTube Music instead, sir."
