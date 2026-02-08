"""
Module for managing application settings.

This module handles persistent settings like font size, window position,
and other user preferences using QSettings.
"""

from PyQt6.QtCore import QSettings
from typing import Optional


class Settings:
    """Manages persistent application settings."""

    ORGANIZATION = "ShortcutCheatsheet"
    APPLICATION = "ShortcutCheatsheet"

    DEFAULT_FONT_SIZE = 12
    MIN_FONT_SIZE = 8
    MAX_FONT_SIZE = 32

    def __init__(self):
        """Initialize settings."""
        self._settings = QSettings(self.ORGANIZATION, self.APPLICATION)

    def get_font_size(self) -> int:
        """Get the current font size."""
        size = self._settings.value("font_size", self.DEFAULT_FONT_SIZE, type=int)
        return max(self.MIN_FONT_SIZE, min(self.MAX_FONT_SIZE, size))

    def set_font_size(self, size: int) -> None:
        """Set the font size."""
        size = max(self.MIN_FONT_SIZE, min(self.MAX_FONT_SIZE, size))
        self._settings.setValue("font_size", size)

    def increase_font_size(self) -> int:
        """Increase font size by 1 and return the new size."""
        new_size = min(self.get_font_size() + 1, self.MAX_FONT_SIZE)
        self.set_font_size(new_size)
        return new_size

    def decrease_font_size(self) -> int:
        """Decrease font size by 1 and return the new size."""
        new_size = max(self.get_font_size() - 1, self.MIN_FONT_SIZE)
        self.set_font_size(new_size)
        return new_size

    def get_window_corner(self) -> Optional[str]:
        """Get the last window corner position."""
        return self._settings.value("window_corner", None, type=str)

    def set_window_corner(self, corner: str) -> None:
        """Set the window corner position."""
        self._settings.setValue("window_corner", corner)

    def get_last_app(self) -> Optional[str]:
        """Get the last focused application wm_class."""
        return self._settings.value("last_app", None, type=str)

    def set_last_app(self, wm_class: str) -> None:
        """Set the last focused application wm_class."""
        self._settings.setValue("last_app", wm_class)
