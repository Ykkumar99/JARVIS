"""
J.A.R.V.I.S. — Command Router
Parses user commands and routes them to the appropriate skill.
"""

import re


def route_command(text: str) -> tuple[str, dict]:
    """
    Parse a command and return (skill_name, params).
    
    Returns:
        (skill_name, params_dict)
        skill_name is one of: "time", "date", "open_app", "close_app", 
        "system_info", "search", "play_music", "reminder", "small_talk", "gemini"
    """
    text_lower = text.lower().strip()

    # ── Time ─────────────────────────────────────────
    time_patterns = [
        r"what(?:'s| is) the time",
        r"what time is it",
        r"tell me the time",
        r"current time",
        r"time right now",
        r"time please",
    ]
    for pattern in time_patterns:
        if re.search(pattern, text_lower):
            return "time", {}

    # ── Date ─────────────────────────────────────────
    date_patterns = [
        r"what(?:'s| is) (?:today(?:'s)?|the) date",
        r"what day is it",
        r"today(?:'s)? date",
        r"current date",
        r"what date is it",
    ]
    for pattern in date_patterns:
        if re.search(pattern, text_lower):
            return "date", {}

    # ── Open App ─────────────────────────────────────
    open_patterns = [
        r"open\s+(.+)",
        r"launch\s+(.+)",
        r"start\s+(.+)",
        r"run\s+(.+)",
    ]
    for pattern in open_patterns:
        match = re.search(pattern, text_lower)
        if match:
            app_name = match.group(1).strip()
            # Clean trailing words
            app_name = re.sub(r"\s*(please|for me|now|jarvis)$", "", app_name).strip()
            return "open_app", {"app": app_name}

    # ── Close App ────────────────────────────────────
    close_patterns = [
        r"close\s+(.+)",
        r"quit\s+(.+)",
        r"exit\s+(.+)",
        r"kill\s+(.+)",
        r"shut down\s+(.+)",
    ]
    for pattern in close_patterns:
        match = re.search(pattern, text_lower)
        if match:
            app_name = match.group(1).strip()
            app_name = re.sub(r"\s*(please|for me|now|jarvis)$", "", app_name).strip()
            return "close_app", {"app": app_name}

    # ── System Info ──────────────────────────────────
    sysinfo_patterns = [
        (r"(?:cpu|processor)\s*(?:load|usage|utilization)", "cpu"),
        (r"how(?:'s| is) (?:the )?cpu", "cpu"),
        (r"(?:ram|memory)\s*(?:usage|used|available|free)", "ram"),
        (r"how much (?:ram|memory)", "ram"),
        (r"(?:battery|power)\s*(?:level|status|percentage)?", "battery"),
        (r"(?:disk|storage)\s*(?:space|usage)", "disk"),
        (r"system (?:info|status|stats|health)", "all"),
    ]
    for pattern, info_type in sysinfo_patterns:
        if re.search(pattern, text_lower):
            return "system_info", {"type": info_type}

    # ── Web Search ───────────────────────────────────
    search_patterns = [
        r"search\s+(?:for\s+)?(.+)",
        r"google\s+(.+)",
        r"look up\s+(.+)",
        r"find\s+(?:me\s+)?(?:information\s+)?(?:about\s+)?(.+)",
    ]
    for pattern in search_patterns:
        match = re.search(pattern, text_lower)
        if match:
            query = match.group(1).strip()
            query = re.sub(r"\s*(please|jarvis)$", "", query).strip()
            return "search", {"query": query}

    # ── Play Music ───────────────────────────────────
    music_patterns = [
        r"play\s+(?:some\s+)?music",
        r"play\s+(?:some\s+)?songs?",
        r"put on (?:some )?music",
        r"i want (?:to hear|to listen to) music",
    ]
    for pattern in music_patterns:
        if re.search(pattern, text_lower):
            return "play_music", {}

    # ── Reminders ────────────────────────────────────
    reminder_patterns = [
        r"remind me (?:in |after )?(\d+)\s*(minutes?|mins?|hours?|hrs?|seconds?|secs?)\s+(?:to\s+)?(.+)",
        r"set (?:a |an )?(?:reminder|alarm|timer)\s+(?:for\s+)?(\d+)\s*(minutes?|mins?|hours?|hrs?|seconds?|secs?)(?:\s+(?:to\s+)(.+))?",
    ]
    for pattern in reminder_patterns:
        match = re.search(pattern, text_lower)
        if match:
            groups = match.groups()
            amount = int(groups[0])
            unit = groups[1].lower()
            message = groups[2] if len(groups) > 2 and groups[2] else "Time's up, sir."

            # Normalize to seconds
            if unit.startswith("min"):
                seconds = amount * 60
            elif unit.startswith("hour") or unit.startswith("hr"):
                seconds = amount * 3600
            else:
                seconds = amount

            return "reminder", {"seconds": seconds, "message": message, "amount": amount, "unit": unit}

    # ── Small Talk / Fun ─────────────────────────────
    small_talk_triggers = [
        r"tell me (?:a )?joke",
        r"tell me something (?:interesting|fun|cool)",
        r"are you smarter than me",
        r"who are you",
        r"what are you",
        r"what can you do",
        r"how are you",
        r"do you have feelings",
        r"thank you|thanks",
        r"you(?:'re| are) (?:the )?best",
        r"i love you",
        r"good (?:morning|evening|night|afternoon)",
    ]
    for pattern in small_talk_triggers:
        if re.search(pattern, text_lower):
            return "small_talk", {"text": text}

    # ── Default: Gemini AI ───────────────────────────
    return "gemini", {"text": text}
