import os
import subprocess
import sys

import pytest


def test_help_includes_monochrome_flag():
    result = subprocess.run(
        [sys.executable, "trade_main.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "--monochrome" in result.stdout


def test_help_includes_color_scheme_flag_and_values():
    result = subprocess.run(
        [sys.executable, "trade_main.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "--color-scheme" in result.stdout
    assert "default" in result.stdout
    assert "green" in result.stdout
    assert "amber" in result.stdout
    assert "white" in result.stdout


def test_help_includes_execution_mode_flags():
    result = subprocess.run(
        [sys.executable, "trade_main.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "--headless" in result.stdout
    assert "--autopilot" in result.stdout
    assert "--interactive" in result.stdout
    assert "--pause-at-end" in result.stdout
    assert "{true,false}" in result.stdout


def test_monochrome_and_color_scheme_are_compatible_and_emit_no_ansi():
    env = dict(os.environ)
    env["LC_ALL"] = "en_US.UTF-8"
    env["LANG"] = "en_US.UTF-8"

    result = subprocess.run(
        [
            sys.executable,
            "trade_main.py",
            "--headless",
            "--monochrome",
            "--color-scheme",
            "amber",
        ],
        capture_output=True,
        text=True,
        check=False,
        env=env,
        timeout=20,
    )

    assert result.returncode == 0
    assert "\x1b" not in result.stdout
    assert "\x1b" not in result.stderr


def test_explicit_boolean_values_are_parsed_for_execution_mode_flags():
    result = subprocess.run(
        [
            sys.executable,
            "trade_main.py",
            "--headless",
            "--autopilot",
            "true",
            "--interactive",
            "false",
            "--pause-at-end",
            "false",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )

    assert result.returncode != 0
    assert (
        "--headless cannot be combined with explicit mode flags: "
        "--autopilot, --interactive, --pause-at-end"
    ) in result.stderr


def test_invalid_boolean_value_returns_cli_error():
    result = subprocess.run(
        [sys.executable, "trade_main.py", "--autopilot", "maybe"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "Expected a boolean value: true/false" in result.stderr


def test_headless_conflicts_with_interactive_true():
    result = subprocess.run(
        [sys.executable, "trade_main.py", "--headless", "--interactive", "true"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--headless cannot be combined with explicit mode flags: --interactive" in result.stderr


def test_headless_conflicts_with_autopilot_false():
    result = subprocess.run(
        [sys.executable, "trade_main.py", "--headless", "--autopilot", "false"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--headless cannot be combined with explicit mode flags: --autopilot" in result.stderr


def test_headless_conflicts_with_pause_at_end_true():
    result = subprocess.run(
        [sys.executable, "trade_main.py", "--headless", "--pause-at-end", "true"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--headless cannot be combined with explicit mode flags: --pause-at-end" in result.stderr


def test_headless_conflicts_with_multiple_explicit_mode_flags():
    result = subprocess.run(
        [
            sys.executable,
            "trade_main.py",
            "--headless",
            "--autopilot",
            "true",
            "--interactive",
            "false",
            "--pause-at-end",
            "false",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert (
        "--headless cannot be combined with explicit mode flags: "
        "--autopilot, --interactive, --pause-at-end"
    ) in result.stderr


@pytest.mark.parametrize(
    "token",
    [
        "1",
        "0",
        "yes",
        "no",
        "on",
        "off",
    ],
)
def test_boolean_aliases_are_accepted_for_autopilot(token):
    args = [
        sys.executable,
        "trade_main.py",
        "--headless",
        "--autopilot",
        token,
    ]

    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )

    assert result.returncode != 0
    assert "--headless cannot be combined with explicit mode flags: --autopilot" in result.stderr
