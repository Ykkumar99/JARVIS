"""
J.A.R.V.I.S. — Gemini AI Skill
Routes unrecognized queries to Google's Gemini API.
Uses the new google-genai SDK with retry, quota handling,
response caching, and call cooldown to stay within free-tier limits.
"""

import re
import time
from collections import OrderedDict
from config import GEMINI_API_KEY, GEMINI_MODEL

_client = None
_last_error_time = 0
_error_cooldown = 60  # Don't retry for 60 seconds after a quota error
_last_call_time = 0
_call_cooldown = 5    # Minimum 5 seconds between API calls

# ── Response Cache ────────────────────────────────────
_cache = OrderedDict()
_CACHE_MAX_SIZE = 50


def _normalize_for_cache(text: str) -> str:
    """Normalize text for cache key comparison."""
    return re.sub(r'[^\w\s]', '', text.lower()).strip()


def _cache_get(text: str) -> str | None:
    """Look up a cached response."""
    key = _normalize_for_cache(text)
    if key in _cache:
        # Move to end (most recently used)
        _cache.move_to_end(key)
        return _cache[key]
    return None


def _cache_put(text: str, response: str):
    """Store a response in the cache."""
    key = _normalize_for_cache(text)
    _cache[key] = response
    # Evict oldest if over limit
    while len(_cache) > _CACHE_MAX_SIZE:
        _cache.popitem(last=False)


# ── Junk Input Filter ────────────────────────────────
# Short, meaningless fragments that Whisper hallucinates or the user
# says as filler — these should NOT be sent to Gemini.
_JUNK_PATTERNS = {
    "jarvis", "hey", "yeah", "yes", "no", "nope", "okay", "ok",
    "um", "uh", "hmm", "huh", "ah", "oh", "ooh", "wow",
    "i'm not", "i'm here", "i'm not sure", "i'm sorry",
    "sorry", "what", "hm", "right", "sure", "fine", "cool",
}


def _is_junk_input(text: str) -> bool:
    """Check if the input is too short or meaningless to send to Gemini."""
    cleaned = re.sub(r'[^\w\s]', '', text.lower()).strip()

    # Too short (under 3 words and under 10 chars)
    words = cleaned.split()
    if len(words) <= 2 and len(cleaned) < 10:
        return True

    # Known junk phrases
    if cleaned in _JUNK_PATTERNS:
        return True

    return False


def _init_gemini():
    """Initialize Gemini client using the new google-genai SDK."""
    global _client
    if _client is not None:
        return True

    if not GEMINI_API_KEY:
        return False

    try:
        from google import genai
        _client = genai.Client(api_key=GEMINI_API_KEY)
        return True
    except ImportError:
        # Fall back to old SDK if new one not available
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            _client = "legacy"
            return True
        except Exception as e:
            print(f"[JARVIS] Gemini init error: {e}", flush=True)
            return False
    except Exception as e:
        print(f"[JARVIS] Gemini init error: {e}", flush=True)
        return False


def _query_new_sdk(text: str) -> str:
    """Query using the new google-genai SDK."""
    from google import genai

    system_instruction = (
        "You are JARVIS, a sophisticated AI assistant inspired by Tony Stark's AI. "
        "You address the user as 'sir'. You are calm, professional, slightly witty, "
        "and speak with a refined British demeanor. Keep responses concise — under 3 sentences "
        "unless the topic truly requires more detail. Never use markdown formatting. "
        "Speak naturally as if you are a voice assistant."
    )

    response = _client.models.generate_content(
        model=GEMINI_MODEL,
        contents=text,
        config=genai.types.GenerateContentConfig(
            system_instruction=system_instruction,
        ),
    )
    return response.text.strip()


def _query_legacy_sdk(text: str) -> str:
    """Query using the legacy google.generativeai SDK."""
    import google.generativeai as genai

    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=(
            "You are JARVIS, a sophisticated AI assistant inspired by Tony Stark's AI. "
            "You address the user as 'sir'. You are calm, professional, slightly witty, "
            "and speak with a refined British demeanor. Keep responses concise — under 3 sentences "
            "unless the topic truly requires more detail. Never use markdown formatting. "
            "Speak naturally as if you are a voice assistant."
        ),
    )
    response = model.generate_content(text)
    return response.text.strip()


def is_gemini_available() -> bool:
    """Check if Gemini API is configured and not rate-limited."""
    if not GEMINI_API_KEY:
        return False
    if not _init_gemini():
        return False
    # If we're in cooldown, still report as available (just throttled)
    return True


def ask_gemini(text: str) -> str:
    """Send a query to Gemini and return the response.

    Includes protections against rate-limiting:
    - Rejects junk/fragment inputs
    - Enforces minimum cooldown between calls
    - Checks response cache before calling API
    - Caches successful responses
    """
    global _last_error_time, _last_call_time

    # ── Step 1: Reject junk inputs ───────────────────
    if _is_junk_input(text):
        print(f"[JARVIS] Gemini skipped (junk input): '{text}'", flush=True)
        return "I didn't quite catch a full command, sir. Could you say that again?"

    # ── Step 2: Check cache ──────────────────────────
    cached = _cache_get(text)
    if cached:
        print(f"[JARVIS] Gemini cache hit: '{text}'", flush=True)
        return cached

    # ── Step 3: Check API availability ───────────────
    if not _init_gemini():
        return (
            "I'm sorry sir, but my advanced reasoning module isn't configured yet. "
            "Please set the GEMINI_API_KEY environment variable to enable AI-powered responses."
        )

    # ── Step 4: Check error cooldown ─────────────────
    if _last_error_time > 0:
        elapsed = time.time() - _last_error_time
        if elapsed < _error_cooldown:
            remaining = int(_error_cooldown - elapsed)
            return (
                f"My neural network is temporarily rate-limited, sir. "
                f"I'll be able to answer complex questions again in about {remaining} seconds. "
                f"In the meantime, try asking me the time, to open an app, or for system info."
            )
        else:
            _last_error_time = 0  # Reset cooldown

    # ── Step 5: Enforce call cooldown ────────────────
    now = time.time()
    since_last = now - _last_call_time
    if since_last < _call_cooldown:
        wait_time = _call_cooldown - since_last
        print(f"[JARVIS] Gemini cooldown: waiting {wait_time:.1f}s", flush=True)
        time.sleep(wait_time)

    # ── Step 6: Call API ─────────────────────────────
    _last_call_time = time.time()

    max_retries = 2
    for attempt in range(max_retries):
        try:
            if _client == "legacy":
                response = _query_legacy_sdk(text)
            else:
                response = _query_new_sdk(text)

            # Cache the successful response
            _cache_put(text, response)
            return response

        except Exception as e:
            error_str = str(e)
            print(f"[JARVIS] Gemini error (attempt {attempt+1}): {error_str}", flush=True)

            if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                _last_error_time = time.time()
                return (
                    "I've hit my API rate limit, sir. My neural network needs a moment to cool down. "
                    "Try again in about a minute, or ask me something I can handle offline — "
                    "like the time, opening apps, or system info."
                )

            if attempt < max_retries - 1:
                time.sleep(1)
                continue

            return (
                "I'm having trouble reaching my neural network at the moment, sir. "
                "Please check your internet connection."
            )
