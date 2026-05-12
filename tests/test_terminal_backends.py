from terminal.windows_terminal import WindowsTerminal
import sys
import pytest

try:
    from terminal.blessings_term import BlessingsTerminal
    BLESSINGS_AVAILABLE = True
except (ImportError, Exception):
    BlessingsTerminal = None
    BLESSINGS_AVAILABLE = False


def test_windows_terminal_implements_base_contract_surface():
    term = WindowsTerminal(use_color=False)

    # Contract methods exist and are callable.
    assert callable(term.clear)
    assert callable(term.bold)
    assert callable(term.reset)
    assert callable(term.get_size)
    assert callable(term.color)
    assert callable(term.fullscreen)


def test_windows_terminal_no_color_fallbacks_are_safe():
    term = WindowsTerminal(use_color=False)

    assert term.bold("X") == "X"
    assert term.reset() == ""
    assert term.color("X", fg="red") == "X"
    assert term.color("X", fg="red", bold=True) == "X"

    cols, rows = term.get_size()
    assert isinstance(cols, int)
    assert isinstance(rows, int)
    assert cols > 0
    assert rows > 0


def test_windows_terminal_unknown_color_name_does_not_crash():
    term = WindowsTerminal(use_color=True)

    rendered = term.color("X", fg="not_a_real_color")

    assert "X" in rendered


@pytest.mark.skipif(not BLESSINGS_AVAILABLE, reason="blessings library not available")
def test_blessings_terminal_contract_surface_and_basic_rendering():
    term = BlessingsTerminal()

    assert term.supports_color is True
    assert isinstance(term.clear(), str)
    assert isinstance(term.reset(), str)

    bold_text = term.bold("X")
    color_text = term.color("X", fg="red")
    unknown_color_text = term.color("X", fg="not_a_real_color")

    assert "X" in bold_text
    assert "X" in color_text
    assert "X" in unknown_color_text


@pytest.mark.skipif(not BLESSINGS_AVAILABLE, reason="blessings library not available")
def test_blessings_terminal_get_size_reports_positive_dimensions():
    term = BlessingsTerminal()

    cols, rows = term.get_size()
    assert cols is None or (isinstance(cols, int) and cols > 0)
    assert rows is None or (isinstance(rows, int) and rows > 0)


def test_windows_terminal_fullscreen_returns_context_manager():
    term = WindowsTerminal(use_color=False)

    ctx = term.fullscreen()
    assert hasattr(ctx, "__enter__")
    assert hasattr(ctx, "__exit__")

    with ctx:
        pass


@pytest.mark.skipif(not BLESSINGS_AVAILABLE, reason="blessings library not available")
def test_blessings_terminal_fullscreen_returns_context_manager():
    term = BlessingsTerminal()

    ctx = term.fullscreen()
    assert hasattr(ctx, "__enter__")
    assert hasattr(ctx, "__exit__")


def test_windows_terminal_input_wraps_builtin(monkeypatch):
    term = WindowsTerminal(use_color=False)

    def fake_input(prompt=""):
        return "test_response"

    monkeypatch.setattr("builtins.input", fake_input)

    result = term.input("Enter text: ")
    assert result == "test_response"


@pytest.mark.skipif(not BLESSINGS_AVAILABLE, reason="blessings library not available")
def test_blessings_terminal_input_wraps_builtin(monkeypatch):
    term = BlessingsTerminal()

    def fake_input(prompt=""):
        return "blessings_input"

    monkeypatch.setattr("builtins.input", fake_input)

    result = term.input("Prompt: ")
    assert result == "blessings_input"


def test_windows_terminal_color_and_bold_stack_safely():
    term = WindowsTerminal(use_color=True)

    result = term.color("X", fg="red", bold=True)

    assert "X" in result
    assert isinstance(result, str)


@pytest.mark.skipif(not BLESSINGS_AVAILABLE, reason="blessings library not available")
def test_blessings_terminal_color_and_bold_stack_safely():
    term = BlessingsTerminal()

    result = term.color("X", fg="red", bold=True)

    assert "X" in result
    assert isinstance(result, str)


def test_windows_terminal_bold_with_color_none_graceful():
    term = WindowsTerminal(use_color=True)

    result = term.color("X", fg=None, bold=True)

    assert "X" in result


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")
def test_windows_terminal_colorama_unavailable_fallback_safe():
    """Regression: if colorama is missing, Windows backend should gracefully degrade."""
    term = WindowsTerminal(use_color=True)

    # If colorama is unavailable, supports_color should be False
    # and all styling methods should safely return plain text.
    if not term.supports_color:
        assert term.bold("X") == "X"
        assert term.reset() == ""
        assert term.color("X", fg="red") == "X"


@pytest.mark.skipif(not BLESSINGS_AVAILABLE, reason="blessings library not available")
def test_blessings_terminal_clear_returns_string():
    term = BlessingsTerminal()

    result = term.clear()
    assert isinstance(result, str)


def test_windows_terminal_clear_returns_string():
    term = WindowsTerminal(use_color=False)

    result = term.clear()
    assert isinstance(result, str)


def test_windows_terminal_supports_color_property_is_boolean():
    windows_term = WindowsTerminal(use_color=False)

    assert isinstance(windows_term.supports_color, bool)


@pytest.mark.skipif(not BLESSINGS_AVAILABLE, reason="blessings library not available")
def test_blessings_terminal_supports_color_property_is_boolean():
    blessings_term = BlessingsTerminal()

    assert isinstance(blessings_term.supports_color, bool)
