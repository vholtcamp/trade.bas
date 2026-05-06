"""
Terminal abstraction layer.

Defines the minimal interface required by the Display layer.
Concrete implementations provide platform-specific behavior.
"""

class TerminalBase:
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