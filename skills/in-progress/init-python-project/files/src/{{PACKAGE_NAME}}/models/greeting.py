"""A greeting addressed to someone."""

from dataclasses import dataclass

from {{PACKAGE_NAME}}.enums.greeting_style import GreetingStyle


@dataclass(frozen=True)
class Greeting:
    """A greeting for one recipient, in one style."""

    recipient: str
    style: GreetingStyle
