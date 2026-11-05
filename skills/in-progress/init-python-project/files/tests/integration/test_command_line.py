"""Runs the whole program in-process: environment variables in, text and exit code out."""

import pytest

from {{PACKAGE_NAME}}.__main__ import main


def test_prints_a_configured_greeting(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("GREETING_NAME", "Ada")
    monkeypatch.setenv("GREETING_STYLE", "formal")

    exit_code = main()

    assert exit_code == 0
    assert capsys.readouterr().out == "Good day, Ada.\n"


def test_reports_bad_settings_on_stderr(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("GREETING_STYLE", "rude")

    exit_code = main()

    assert exit_code == 2
    assert "GREETING_STYLE" in capsys.readouterr().err
