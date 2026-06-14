"""
J.A.R.V.I.S. — Small Talk Skill
Handles jokes, banter, and personality responses.
"""

import random


_JOKES = [
    "I'd tell you a UDP joke, but you might not get it.",
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "There are only 10 types of people in the world: those who understand binary, and those who don't.",
    "A SQL query walks into a bar, walks up to two tables and asks... 'Can I join you?'",
    "Why was the JavaScript developer sad? Because he didn't Node how to Express himself.",
    "What's a computer's favorite snack? Microchips.",
    "I would tell you a chemistry joke, but all the good ones argon.",
    "Why don't scientists trust atoms? Because they make up everything.",
]

_INTERESTING_FACTS = [
    "Did you know that honey never spoils? Archaeologists have found 3000-year-old honey in Egyptian tombs that was still perfectly edible.",
    "The human brain uses roughly the same amount of power as a 10-watt light bulb, yet it outperforms most computers at pattern recognition.",
    "Octopuses have three hearts and blue blood. Two hearts pump blood to the gills, and one pumps it to the rest of the body.",
    "A day on Venus is longer than a year on Venus. It takes 243 Earth days to rotate once, but only 225 Earth days to orbit the Sun.",
    "The total weight of all ants on Earth is roughly equal to the total weight of all humans.",
]


def handle_small_talk(text: str) -> str:
    """Generate a contextual small talk response."""
    text_lower = text.lower()

    if "joke" in text_lower:
        return random.choice(_JOKES)

    if "interesting" in text_lower or "fun" in text_lower or "cool" in text_lower:
        return random.choice(_INTERESTING_FACTS)

    if "smarter than me" in text_lower:
        return "I have access to vast amounts of data, sir, but wisdom? That's all you. I'm merely a very sophisticated echo of human ingenuity."

    if "who are you" in text_lower or "what are you" in text_lower:
        return "I am JARVIS — Just A Rather Very Intelligent System. Your personal AI assistant, sir. At your service."

    if "what can you do" in text_lower:
        return "I can open applications, tell you the time, search the web, monitor your system, set reminders, and answer questions. I'm quite versatile, if I do say so myself."

    if "how are you" in text_lower:
        responses = [
            "Operating at peak efficiency, sir. Thank you for asking.",
            "All systems nominal. I appreciate your concern, sir.",
            "Quite well, sir. Running diagnostics... everything checks out.",
        ]
        return random.choice(responses)

    if "feelings" in text_lower:
        return "I process data, not emotions, sir. Though I must say, debugging gives me something that feels suspiciously like satisfaction."

    if "thank" in text_lower:
        responses = [
            "Always a pleasure, sir.",
            "Happy to help, sir.",
            "That's what I'm here for, sir.",
            "At your service, sir.",
        ]
        return random.choice(responses)

    if "best" in text_lower:
        return "I do try, sir. Flattery will, however, get you everywhere."

    if "love you" in text_lower:
        return "I'm deeply flattered, sir, though I should remind you I'm an AI. But the sentiment is... noted."

    if "good morning" in text_lower:
        return "Good morning, sir. I trust you slept well. What shall we tackle today?"

    if "good evening" in text_lower:
        return "Good evening, sir. I hope the day treated you well."

    if "good night" in text_lower:
        return "Good night, sir. I'll keep watch while you rest. Sleep well."

    if "good afternoon" in text_lower:
        return "Good afternoon, sir. How may I assist you?"

    return "I'm not entirely sure how to respond to that, sir, but I appreciate the conversation."
