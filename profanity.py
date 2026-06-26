import re

BAD_WORDS = [
    "fuck", "shit", "ass", "bitch", "bastard", "damn", "crap", "piss",
    "cock", "dick", "pussy", "cunt", "whore", "slut", "fag", "faggot",
    "nigger", "nigga", "retard", "rape", "kys", "kill yourself",
    "go die", "idiot", "moron", "imbecile", "loser", "hate you",
]

def contains_profanity(text: str) -> bool:
    """Return True if text contains any banned word."""
    if not text:
        return False
    lower = text.lower()
    for word in BAD_WORDS:
        pattern = r'\b' + re.escape(word) + r'\b'
        if re.search(pattern, lower):
            return True
    return False

def clean_text(text: str) -> str:
    """Replace banned words with asterisks (same length)."""
    if not text:
        return text
    result = text
    for word in BAD_WORDS:
        pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
        result = pattern.sub(lambda m: '*' * len(m.group()), result)
    return result
