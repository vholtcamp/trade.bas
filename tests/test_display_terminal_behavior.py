from os import terminal_size

import trade_objects
from trade_objects import (
    BlankLine,
    ContentLine,
    Display,
    RuleLine,
    SPECIAL_ANNOUNCEMENT_TEXT_WIDTH,
    visible_len,
)
from terminal.colors import ColorScheme


def test_visible_len_strips_csi_and_non_csi_escapes():
    assert visible_len("\x1b[31mRed\x1b[0m") == 3
    assert visible_len("\x1b(B\x1b[31mA\x1b[m") == 1
    assert visible_len("plain") == 5


def test_apply_display_alignment_respects_visible_width(game):
    display = Display(game)

    centered = display._apply_display_alignment("\x1b[31mRed\x1b[0m", alignment="c", col_width=9)
    left = display._apply_display_alignment("X", alignment="l", col_width=4)
    right = display._apply_display_alignment("X", alignment="r", col_width=4)

    assert visible_len(centered) == 9
    assert visible_len(left) == 4
    assert visible_len(right) == 4
    assert left.startswith("X")
    assert right.endswith("X")


def test_create_columns_line_fills_announcement_width(game):
    display = Display(game)

    line = display._create_columns_line(["A", "B", "C"], ["l", "c", "r"])

    assert visible_len(line) == SPECIAL_ANNOUNCEMENT_TEXT_WIDTH
    assert "A" in line
    assert "B" in line
    assert "C" in line


def test_display_map_no_color_emits_structural_output(game, capsys):
    player = game.players[0]
    game.active_player = player
    game.map["A1"] = "A"

    Display.display_map(game.display, player)

    out = capsys.readouterr().out
    assert "Turn " in out
    assert "Portfolio" in out
    assert "A" in out
    assert "\x1b" not in out


def test_display_map_color_mode_includes_ansi_when_terminal_colors(game, capsys):
    player = game.players[0]
    game.active_player = player
    game.map["A1"] = "A"

    game.terminal.supports_color = True
    game.terminal.color = lambda text, **kwargs: f"\x1b[31m{text}\x1b[0m"

    Display.display_map(game.display, player)

    out = capsys.readouterr().out
    assert "\x1b[" in out


def test_display_map_monochrome_suppresses_ansi_even_when_terminal_supports_color(game_factory, capsys):
    game = game_factory(monochrome=True)
    player = game.players[0]
    game.active_player = player
    game.map["A1"] = "A"

    game.terminal.supports_color = True
    game.terminal.color = lambda text, **kwargs: f"\x1b[31m{text}\x1b[0m"

    Display.display_map(game.display, player)

    out = capsys.readouterr().out
    assert trade_objects.ANSI_ESCAPE_RE.search(out) is None


def test_display_map_monochrome_overrides_selected_color_scheme(game_factory, capsys):
    game = game_factory(monochrome=True, color_scheme=ColorScheme.AMBER)
    player = game.players[0]
    game.active_player = player
    game.map["A1"] = "A"

    game.terminal.supports_color = True
    game.terminal.color = lambda text, **kwargs: f"\x1b[33m{text}\x1b[0m"

    Display.display_map(game.display, player)

    out = capsys.readouterr().out
    assert trade_objects.ANSI_ESCAPE_RE.search(out) is None


def test_display_map_green_scheme_uses_green_foreground(game_factory):
    game = game_factory(color_scheme=ColorScheme.GREEN)
    player = game.players[0]
    game.active_player = player
    game.map["A1"] = "A"

    game.terminal.supports_color = True
    captured_fgs = []

    def fake_color(text, **kwargs):
        captured_fgs.append(kwargs.get("fg"))
        return text

    game.terminal.color = fake_color

    Display.display_map(game.display, player)

    assert "green" in captured_fgs
    assert set(captured_fgs) == {"green"}


def test_display_map_wraps_long_last_action_to_two_lines(game, capsys):
    player = game.players[0]
    game.active_player = player
    game.last_action = "WRAPTOKEN " * 8

    Display.display_map(game.display, player)

    out = capsys.readouterr().out
    wrapped_lines = [line for line in out.splitlines() if "WRAPTOKEN" in line]

    assert len(wrapped_lines) == 2
    header = (
        trade_objects.MAP_HEADER
        + trade_objects.PORTFOLIO_SPACER
        + f"*** {game.active_player.name}'s Portfolio ***"
    )
    max_width = visible_len(header)
    assert all(visible_len(line.strip()) <= max_width for line in wrapped_lines)
    assert all(line.startswith("WRAPTOKEN") for line in wrapped_lines)


def test_display_announcement_renders_content_rule_and_blank(game, capsys):
    lines = [
        ContentLine("Header"),
        RuleLine(),
        BlankLine(),
        "Footer",
    ]

    game.display.display_announcement(lines)

    out = capsys.readouterr().out
    assert "Header" in out
    assert "Footer" in out
    assert "---" in out


def test_display_paged_paragraphs_breaks_by_terminal_height(game, monkeypatch, capsys):
    prompts = []

    game.interactive = True
    game.terminal.clear = lambda: ""

    monkeypatch.setattr(
        trade_objects.shutil,
        "get_terminal_size",
        lambda fallback=(80, 24): terminal_size((80, 8)),
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": prompts.append(prompt) or "",
    )

    paragraphs = [
        ["p1-l1", "p1-l2", "p1-l3"],
        ["p2-l1", "p2-l2", "p2-l3"],
    ]

    game.display.display_paged_paragraphs(paragraphs, margin=3)

    out = capsys.readouterr().out
    assert "p1-l1" in out
    assert "p2-l1" in out
    assert prompts == ["\n(Press Enter to continue)"]
