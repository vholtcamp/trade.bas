"""
Terminal abstraction layer.

Defines the minimal interface required by the Display layer.
Concrete implementations provide platform-specific behavior.
"""

class TerminalBase:

    @property
    def supports_color(self) -> bool:
        return False

    def clear(self) -> str:
        """
        Return a string that clears the terminal screen.
        """
        raise NotImplementedError

    def bold(self, text: str) -> str:
        """
        Return text rendered in bold, if supported.
        """
        raise NotImplementedError

    def reset(self) -> str:
        """
        Return terminal reset / normal formatting sequence.
        """
        raise NotImplementedError

    def get_size(self) -> tuple[int, int]:
        """
        Return (columns, rows) of the terminal.
        """
        raise NotImplementedError

    def input(self, prompt: str = "") -> str:
        """
        Read input from the user.
        """
        return input(prompt)
    
    def fullscreen(self):
        """
        Context manager for fullscreen terminal mode.
        Default implementation is a no-op.
        """
        return nullcontext()

    

    def color(
        self,
        text: str,
        fg: str | None = None,
        bold: bool = False
        ) -> str:
        """
        Return text rendered with optional foreground color and bold styling.
        fg may be None or a color name (e.g. 'red', 'green').
        """
        raise NotImplementedError
