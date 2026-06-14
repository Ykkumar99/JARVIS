"""
J.A.R.V.I.S. — Reminders Skill
Set timed reminders that fire after a delay.
"""

import threading


class ReminderManager:
    """Manages timed reminders."""

    def __init__(self, speak_callback=None):
        self.speak_callback = speak_callback
        self.active_reminders = []

    def set_reminder(self, seconds: int, message: str, amount: int, unit: str) -> str:
        """Set a reminder that fires after the given number of seconds."""
        timer = threading.Timer(seconds, self._fire_reminder, args=[message])
        timer.daemon = True
        timer.start()
        self.active_reminders.append(timer)

        unit_label = unit.rstrip("s")
        if amount > 1:
            unit_label += "s"

        return f"Reminder set, sir. I'll remind you in {amount} {unit_label}."

    def _fire_reminder(self, message: str):
        """Called when a reminder fires."""
        reminder_text = f"Sir, reminder: {message}"
        if self.speak_callback:
            self.speak_callback(reminder_text)
        else:
            print(f"[JARVIS REMINDER] {reminder_text}")

    def cancel_all(self):
        """Cancel all active reminders."""
        for timer in self.active_reminders:
            timer.cancel()
        self.active_reminders.clear()
