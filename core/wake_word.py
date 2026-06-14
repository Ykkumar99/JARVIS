"""
J.A.R.V.I.S. — Wake Word Detector
Checks if incoming text contains a wake word or sleep command.
Uses fuzzy matching because Whisper may transcribe wake words imperfectly.
"""

import re
from config import WAKE_WORDS, SLEEP_COMMANDS


def _normalize(text: str) -> str:
    """Normalize text for matching: lowercase, strip punctuation, collapse spaces."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", "", text)  # remove all non-alphanumeric
    text = re.sub(r"\s+", " ", text).strip()   # collapse whitespace
    return text


def check_wake_word(text: str) -> tuple[bool, str]:
    """
    Check if the text contains a wake word.
    Uses fuzzy matching to handle Whisper transcription variations.
    
    Returns:
        (is_wake_word, response_text)
    """
    normalized = _normalize(text)

    # Direct matching against config wake words
    for wake_phrase, response in WAKE_WORDS.items():
        wake_norm = _normalize(wake_phrase)
        if wake_norm in normalized:
            return True, response

    # ── Fuzzy matching for common Whisper mis-transcriptions ──

    # "Hey JARVIS" variations
    # Whisper might hear: "hey jarvis", "a jarvis", "hey travis", "hey jarvas",
    # "hey jervis", "hey service", "hey jar vis", "hey jarvus", "hey gervis"
    hey_patterns = [
        r"\b(?:hey|a|hay|he)\s*(?:jarvis|jarvas|jervis|jarvus|gervis|travis|jarves|javis|jarvi)\b",
        r"\bjarvis\b",  # Just "Jarvis" alone should also work
    ]
    for pattern in hey_patterns:
        if re.search(pattern, normalized):
            return True, "Yes sir, I'm listening."

    # "JARVIS are you there" variations
    there_patterns = [
        r"(?:jarvis|jarvas|jervis|jarvus)\s*(?:are you|you)\s*(?:there|here|their)",
        r"(?:jarvis|jarvas|jervis|jarvus)\s*(?:are you|you)\s*(?:listening|awake|online)",
    ]
    for pattern in there_patterns:
        if re.search(pattern, normalized):
            return True, "Online and ready, sir. How can I assist?"

    # "Daddy's home" variations
    daddy_patterns = [
        r"daddy(?:s|z|is)?\s*(?:home|hom|here)",
        r"daddys?\s*(?:home|hom|here)",
    ]
    for pattern in daddy_patterns:
        if re.search(pattern, normalized):
            return True, "Welcome back, sir. I've been keeping things warm. All systems nominal."

    return False, ""


def check_sleep_command(text: str) -> bool:
    """Check if the text is a sleep/standby command."""
    normalized = _normalize(text)

    # Direct matching
    for sleep_phrase in SLEEP_COMMANDS:
        sleep_norm = _normalize(sleep_phrase)
        if sleep_norm in normalized:
            return True

    # Fuzzy patterns
    sleep_patterns = [
        r"(?:jarvis|jarvas|jervis)\s*(?:stand\s*by|standby)",
        r"that(?:ll| will|s)\s*be\s*all",
        r"go\s*to\s*sleep",
        r"stand\s*by",
        r"good\s*night\s*(?:jarvis|jarvas|jervis)?",
        r"shut\s*(?:down|up)",
    ]
    for pattern in sleep_patterns:
        if re.search(pattern, normalized):
            return True

    return False


def is_daddy_home(text: str) -> bool:
    """Check if this is the 'Daddy's home' wake word for dramatic bootup."""
    normalized = _normalize(text)
    return bool(re.search(r"daddy", normalized))
