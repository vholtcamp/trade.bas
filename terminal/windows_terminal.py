import os
import subprocess
from contextlib import nullcontext
from terminal.colors import ColorScheme


try:
    from colorama import Fore, Style, init
    init()
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False


class WindowsTerminal:
    def __init__(self, use_color=True, color_scheme=ColorScheme.DEFAULT):
        self.supports_color = COLORAMA_AVAILABLE and use_color
        self.color_scheme = color_scheme

    def clear(self):
        subprocess.run('cls', shell=True)
        return ""

    def color(self, text, fg=None):
        if not self.supports_color or not fg:
            return text

        color = getattr(Fore, fg.upper(), "")
        return f"{color}{text}{Style.RESET_ALL}"
    

    def fullscreen(self):
        # Windows has no curses-style fullscreen; no-op context manager
        return nullcontext()

