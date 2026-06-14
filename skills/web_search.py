"""
J.A.R.V.I.S. — Web Search Skill
Opens web searches in the default browser.
"""

import webbrowser
import urllib.parse


def web_search(query: str) -> str:
    """Search the web using the default browser."""
    encoded_query = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={encoded_query}"
    webbrowser.open(url)
    return f"Searching for {query}, sir. I've opened the results in your browser."
