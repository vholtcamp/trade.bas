"""
Blessings-based terminal backend for Unix-like systems.
"""

from blessings import Terminal
from .base import TerminalBase


class BlessingsTerminal(TerminalBase):
    supports_color = True

    def __init__(self):
        self.term = Terminal()

    def clear(self) -> str:
        return self.term.clear()

    def bold(self, text: str) -> str:
        return self.term.bold(text)

    def reset(self) -> str:
        return self.term.normal

    def get_size(self) -> tuple[int, int]:
        return self.term.width, self.term.height

    def color(self, text: str, fg: str | None = None, bold: bool = False) -> str:
        """
        Render text with optional foreground color and bold styling.
        """
        result = text

        if fg:
            # blessings exposes colors as attributes (e.g., term.red)
            try:
                color_fn = getattr(self.term, fg)
                result = color_fn(result)
            except AttributeError:
                # Unknown color name; fall back to plain text
                pass

        if bold:
            result = self.term.bold(result)

        return result