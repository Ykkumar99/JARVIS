"""
J.A.R.V.I.S. — App Control Skill
Open and close applications on Windows.
"""

import subprocess
import os
import webbrowser

from config import APP_ALIASES


def open_app(app_name: str) -> str:
    """Open an application by name."""
    app_lower = app_name.lower().strip()

    # Check if it's a known alias
    target = APP_ALIASES.get(app_lower, app_lower)

    # If it's a URL, open in browser
    if target.startswith("http://") or target.startswith("https://"):
        webbrowser.open(target)
        return f"Opening {app_name} in your browser, sir."

    # If it's a ms-settings: URI
    if target.startswith("ms-settings:"):
        os.startfile(target)
        return f"Opening Settings, sir."

    # If it's a shell command (like WhatsApp)
    if "shell:" in target:
        subprocess.Popen(target, shell=True)
        return f"Opening {app_name}, sir."

    # Try to launch as executable
    try:
        subprocess.Popen(
            target,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return f"Opening {app_name}, sir."
    except FileNotFoundError:
        # Try with 'start' command
        try:
            subprocess.Popen(
                f'start "" "{target}"',
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return f"Opening {app_name}, sir."
        except Exception:
            return f"I'm sorry sir, I couldn't find {app_name} on your system."


def close_app(app_name: str) -> str:
    """Close an application by name."""
    app_lower = app_name.lower().strip()

    # Map common names to process names
    process_map = {
        "chrome": "chrome.exe",
        "google chrome": "chrome.exe",
        "firefox": "firefox.exe",
        "notepad": "notepad.exe",
        "spotify": "Spotify.exe",
        "word": "WINWORD.EXE",
        "excel": "EXCEL.EXE",
        "powerpoint": "POWERPNT.EXE",
        "discord": "Discord.exe",
        "telegram": "Telegram.exe",
        "vs code": "Code.exe",
        "vscode": "Code.exe",
        "visual studio code": "Code.exe",
        "calculator": "Calculator.exe",
        "paint": "mspaint.exe",
        "file explorer": "explorer.exe",
        "task manager": "Taskmgr.exe",
    }

    process_name = process_map.get(app_lower, f"{app_lower}.exe")

    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", process_name],
            capture_output=True,
            text=True,
        )
        return f"Closing {app_name}, sir."
    except Exception:
        return f"I couldn't close {app_name}, sir. It may not be running."
