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
