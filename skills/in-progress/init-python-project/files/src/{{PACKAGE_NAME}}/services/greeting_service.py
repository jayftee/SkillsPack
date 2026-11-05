"""Builds and renders greetings."""

from {{PACKAGE_NAME}}.config.settings import DEFAULT_NAME, Settings
from {{PACKAGE_NAME}}.enums.greeting_style import GreetingStyle
from {{PACKAGE_NAME}}.models.greeting import Greeting
from {{PACKAGE_NAME}}.utils.text import collapse_whitespace


class GreetingService:
    """Turns settings into a greeting, and a greeting into text."""

    def create(self, settings: Settings) -> Greeting:
        """Build the greeting described by the settings.

        Args:
            settings: Validated settings.

        Returns:
            The greeting, addressed to the default name if the configured one is blank.
        """
        recipient = collapse_whitespace(settings.name) or DEFAULT_NAME
        return Greeting(recipient=recipient, style=settings.style)

    def render(self, greeting: Greeting) -> str:
        """Format the greeting as a line of text.

        Args:
            greeting: The greeting to format.

        Returns:
            The text to show.
        """
        if greeting.style is GreetingStyle.FORMAL:
            return f"Good day, {greeting.recipient}."
        return f"Hello, {greeting.recipient}!"
