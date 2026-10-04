import pytest

from {{PACKAGE_NAME}}.config.settings import Settings
from {{PACKAGE_NAME}}.enums.greeting_style import GreetingStyle
from {{PACKAGE_NAME}}.models.greeting import Greeting
from {{PACKAGE_NAME}}.services.greeting_service import GreetingService


@pytest.mark.parametrize(
    ("name", "expected_recipient"),
    [
        ("Ada", "Ada"),
        ("  Ada   Lovelace ", "Ada Lovelace"),
        ("   ", "World"),
    ],
)
def test_create_normalises_the_recipient(name: str, expected_recipient: str) -> None:
    greeting = GreetingService().create(Settings(name=name, style=GreetingStyle.FRIENDLY))

    assert greeting == Greeting(recipient=expected_recipient, style=GreetingStyle.FRIENDLY)


@pytest.mark.parametrize(
    ("style", "expected_text"),
    [
        (GreetingStyle.FRIENDLY, "Hello, Ada!"),
        (GreetingStyle.FORMAL, "Good day, Ada."),
    ],
)
def test_render_follows_the_style(style: GreetingStyle, expected_text: str) -> None:
    assert GreetingService().render(Greeting(recipient="Ada", style=style)) == expected_text
