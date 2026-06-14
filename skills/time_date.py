"""
J.A.R.V.I.S. — Time & Date Skill
"""

from datetime import datetime


def get_time() -> str:
    """Get the current time in a human-friendly format."""
    now = datetime.now()
    hour = now.strftime("%I").lstrip("0")
    minute = now.strftime("%M")
    period = now.strftime("%p")

    if minute == "00":
        return f"It's {hour} {period}, sir."
    else:
        return f"It's {hour}:{minute} {period}, sir."


def get_date() -> str:
    """Get today's date in a human-friendly format."""
    now = datetime.now()
    day = now.strftime("%A")
    date_str = now.strftime("%B %d, %Y")
    return f"Today is {day}, {date_str}, sir."
