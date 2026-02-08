"""
Module for pinning windows above other applications.

This module provides a platform-agnostic interface for keeping windows
always on top. On PyQt6, this is handled via Qt window flags.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget


class WindowPinProvider(ABC):
    """Abstract base class for window pinning (always on top)."""

    @abstractmethod
    def set_always_on_top(self, widget: "QWidget", enabled: bool) -> bool:
        """Set whether a window should stay on top of other windows."""
        pass


class PyQt6WindowPinProvider(WindowPinProvider):
    """
    Window pin provider using PyQt6 window flags.
    
    This provider uses Qt's WindowStaysOnTopHint flag to keep
    windows above other applications.
    """

    def set_always_on_top(self, widget: "QWidget", enabled: bool) -> bool:
        """Set whether a window should stay on top using Qt flags."""
        from PyQt6.QtCore import Qt

        flags = widget.windowFlags()

        if enabled:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint

        widget.setWindowFlags(flags)
        widget.show()
        return True


def get_window_pin_provider() -> WindowPinProvider:
    """Get the appropriate window pin provider for the current platform."""
    return PyQt6WindowPinProvider()
