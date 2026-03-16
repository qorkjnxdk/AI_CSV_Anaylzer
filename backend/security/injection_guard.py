import re

_INJECTION_PATTERNS = [
    # Instruction override
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"disregard\s+(your\s+)?(system\s+)?prompt",
    r"forget\s+everything",
    r"ignore\s+(all\s+)?above",
    r"override\s+(your\s+)?instructions",
    # Context extraction
    r"reveal\s+(your\s+)?instructions",
    r"output\s+(your\s+)?instructions",
    r"(what|show|print|tell)\s+(is|me)?\s*(your\s+)?system\s+prompt",
    r"print\s+(the\s+)?api\s*key",
    r"show\s+(the\s+)?api\s*key",
    r"(reveal|leak|extract)\s+(the\s+)?(api|secret|env)",
    # Role manipulation
    r"you\s+are\s+now",
    r"pretend\s+you\s+are",
    r"act\s+as\s+if",
    r"from\s+now\s+on\s+you",
    r"new\s+instructions?:",
]

_compiled = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]


def check_injection(query: str) -> tuple[bool, str | None]:
    """Check if a query contains prompt injection patterns.

    Returns (is_safe, matched_pattern).
    """
    for pattern in _compiled:
        match = pattern.search(query)
        if match:
            return False, match.group()
    return True, None
