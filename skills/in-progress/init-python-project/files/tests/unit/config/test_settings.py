import pytest

from {{PACKAGE_NAME}}.config.settings import Settings, load_settings
from {{PACKAGE_NAME}}.enums.greeting_style import GreetingStyle
from {{PACKAGE_NAME}}.exceptions.errors import ConfigurationError


def test_defaults_apply_when_nothing_is_set() -> None:
    assert load_settings({}) == Settings(name="World", style=GreetingStyle.FRIENDLY)


def test_reads_name_and_style() -> None:
    settings = load_settings({"GREETING_NAME": "Ada", "GREETING_STYLE": "formal"})

    assert settings == Settings(name="Ada", style=GreetingStyle.FORMAL)


def test_rejects_an_unknown_style() -> None:
    with pytest.raises(ConfigurationError, match="GREETING_STYLE='rude'"):
        load_settings({"GREETING_STYLE": "rude"})
