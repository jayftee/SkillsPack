"""How formal a greeting is."""

from enum import StrEnum


class GreetingStyle(StrEnum):
    """Tone of a greeting."""

    FRIENDLY = "friendly"
    FORMAL = "formal"
