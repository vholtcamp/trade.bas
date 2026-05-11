import shutil
import subprocess
from contextlib import nullcontext
from terminal.base import TerminalBase
from terminal.colors import ColorScheme


try:
    from colorama import Fore, Style, init
    init()
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False


class WindowsTerminal(TerminalBase):
    def __init__(self, use_color=True, color_scheme=ColorScheme.DEFAULT):
        self._supports_color = COLORAMA_AVAILABLE and use_color
        self.color_scheme = color_scheme

    @property
    def supports_color(self) -> bool:
        return self._supports_color

    def clear(self):
        subprocess.run('cls', shell=True)
        return ""

    def bold(self, text: str) -> str:
        if not self.supports_color:
            return text
        return f"{Style.BRIGHT}{text}{Style.RESET_ALL}"

    def reset(self) -> str:
        if not self.supports_color:
            return ""
        return Style.RESET_ALL

    def get_size(self) -> tuple[int, int]:
        size = shutil.get_terminal_size(fallback=(80, 24))
        return size.columns, size.lines

    def color(self, text: str, fg: str | None = None, bold: bool = False) -> str:
        if not self.supports_color or not fg:
            return self.bold(text) if bold else text

        color = getattr(Fore, fg.upper(), "")
        rendered = f"{color}{text}{Style.RESET_ALL}"
        if bold:
            rendered = f"{Style.BRIGHT}{rendered}{Style.RESET_ALL}"
        return rendered
    

    def fullscreen(self):
        # Windows has no curses-style fullscreen; no-op context manager
        return nullcontext()

