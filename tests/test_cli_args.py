import os
import subprocess
import sys


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


def test_monochrome_and_color_scheme_are_compatible_and_emit_no_ansi():
    env = dict(os.environ)
    env["TRADE_HEADLESS"] = "1"
    env["LC_ALL"] = "en_US.UTF-8"
    env["LANG"] = "en_US.UTF-8"

    result = subprocess.run(
        [
            sys.executable,
            "trade_main.py",
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
