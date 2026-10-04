import pytest

from {{PACKAGE_NAME}}.utils.text import collapse_whitespace


@pytest.mark.parametrize(
    ("text", "expected_text"),
    [
        ("plain", "plain"),
        ("  padded  ", "padded"),
        ("tabs\tand\nnewlines", "tabs and newlines"),
        ("   ", ""),
    ],
)
def test_collapse_whitespace(text: str, expected_text: str) -> None:
    assert collapse_whitespace(text) == expected_text
