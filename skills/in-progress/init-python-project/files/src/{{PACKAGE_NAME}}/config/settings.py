"""Greeting settings, read from environment variables."""

from collections.abc import Mapping
from dataclasses import dataclass

from {{PACKAGE_NAME}}.enums.greeting_style import GreetingStyle
from {{PACKAGE_NAME}}.exceptions.errors import ConfigurationError

NAME_VARIABLE = "GREETING_NAME"
STYLE_VARIABLE = "GREETING_STYLE"
DEFAULT_NAME = "World"


@dataclass(frozen=True)
class Settings:
    """Validated greeting settings."""

    name: str
    style: GreetingStyle


def load_settings(environment_variables: Mapping[str, str]) -> Settings:
    """Read the settings, applying defaults for anything not set.

    Args:
        environment_variables: Usually ``os.environ``; tests pass a plain dict.

    Returns:
        The validated settings.

    Raises:
        ConfigurationError: If GREETING_STYLE is not a known style.
    """
    style_value = environment_variables.get(STYLE_VARIABLE, GreetingStyle.FRIENDLY.value)
    try:
        style = GreetingStyle(style_value)
    except ValueError as error:
        allowed_values = ", ".join(GreetingStyle)
        message = f"{STYLE_VARIABLE}={style_value!r} is not one of: {allowed_values}"
        raise ConfigurationError(message) from error
    return Settings(name=environment_variables.get(NAME_VARIABLE, DEFAULT_NAME), style=style)
