"""
Module for positioning windows on screen.

This module provides a platform-agnostic interface for moving windows
to specific positions. On Gnome/Wayland, it uses the window-calls
extension via D-Bus.
"""

import subprocess
from abc import ABC, abstractmethod
from enum import Enum
from typing import Tuple


class ScreenCorner(Enum):
    """Screen corners for window positioning."""
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"


class WindowPositionProvider(ABC):
    """Abstract base class for window positioning."""

    @abstractmethod
    def move_window(self, window_id: int, x: int, y: int) -> bool:
        """Move a window to the specified position."""
        pass

    @abstractmethod
    def get_screen_size(self) -> Tuple[int, int]:
        """Get the screen dimensions (width, height)."""
        pass

    def move_to_corner(
        self,
        window_id: int,
        corner: ScreenCorner,
        window_width: int,
        window_height: int,
        margin: int = 10
    ) -> bool:
        """Move a window to a screen corner."""
        screen_width, screen_height = self.get_screen_size()

        if corner == ScreenCorner.TOP_LEFT:
            x, y = margin, margin
        elif corner == ScreenCorner.TOP_RIGHT:
            x = screen_width - window_width - margin
            y = margin
        elif corner == ScreenCorner.BOTTOM_LEFT:
            x = margin
            y = screen_height - window_height - margin
        elif corner == ScreenCorner.BOTTOM_RIGHT:
            x = screen_width - window_width - margin
            y = screen_height - window_height - margin
        else:
            return False

        return self.move_window(window_id, x, y)


class GnomeWindowCallsPositionProvider(WindowPositionProvider):
    """
    Window position provider using the window-calls Gnome extension.
    
    This provider communicates with the window-calls extension via D-Bus
    to move windows on Wayland.
    """

    DBUS_DEST = "org.gnome.Shell"
    DBUS_PATH = "/org/gnome/Shell/Extensions/Windows"
    DBUS_INTERFACE = "org.gnome.Shell.Extensions.Windows"

    def _call_dbus_method(self, method: str, *args: str) -> bool:
        """Call a D-Bus method on the window-calls extension."""
        cmd = [
            "gdbus", "call", "--session",
            "--dest", self.DBUS_DEST,
            "--object-path", self.DBUS_PATH,
            "--method", f"{self.DBUS_INTERFACE}.{method}"
        ]
        cmd.extend(args)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

    def move_window(self, window_id: int, x: int, y: int) -> bool:
        """Move a window to the specified position using window-calls."""
        return self._call_dbus_method("Move", str(window_id), str(x), str(y))

    def get_screen_size(self) -> Tuple[int, int]:
        """Get the screen dimensions using xrandr or default values."""
        try:
            result = subprocess.run(
                ["xrandr", "--current"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if " connected" in line and "primary" in line:
                        parts = line.split()
                        for part in parts:
                            if "x" in part and "+" in part:
                                resolution = part.split("+")[0]
                                width, height = resolution.split("x")
                                return int(width), int(height)
                    elif " connected" in line:
                        parts = line.split()
                        for part in parts:
                            if "x" in part and "+" in part:
                                resolution = part.split("+")[0]
                                width, height = resolution.split("x")
                                return int(width), int(height)
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, ValueError):
            pass

        return 1920, 1080


def get_window_position_provider() -> WindowPositionProvider:
    """Get the appropriate window position provider for the current platform."""
    return GnomeWindowCallsPositionProvider()
