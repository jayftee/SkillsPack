"""Text helpers."""


def collapse_whitespace(text: str) -> str:
    """Trim the text and replace every run of whitespace inside it with a single space.

    Args:
        text: Any text.

    Returns:
        The text with normalised spacing; empty if it contained only whitespace.
    """
    return " ".join(text.split())
