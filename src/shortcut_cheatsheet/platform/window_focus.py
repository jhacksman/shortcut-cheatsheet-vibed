"""
Module for detecting the currently focused window.

This module provides a platform-agnostic interface for getting information
about the currently focused window. On Gnome/Wayland, it uses the window-calls
extension via D-Bus.
"""

import subprocess
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class WindowInfo:
    """Information about a window."""
    wm_class: str
    title: str
    pid: int
    window_id: int
    x: int
    y: int
    width: int
    height: int


class WindowFocusProvider(ABC):
    """Abstract base class for window focus detection."""

    @abstractmethod
    def get_focused_window(self) -> Optional[WindowInfo]:
        """Get information about the currently focused window."""
        pass

    @abstractmethod
    def get_window_list(self) -> list[WindowInfo]:
        """Get a list of all windows."""
        pass


class GnomeWindowCallsProvider(WindowFocusProvider):
    """
    Window focus provider using the window-calls Gnome extension.
    
    This provider communicates with the window-calls extension via D-Bus
    to get information about windows on Wayland.
    """

    DBUS_DEST = "org.gnome.Shell"
    DBUS_PATH = "/org/gnome/Shell/Extensions/Windows"
    DBUS_INTERFACE = "org.gnome.Shell.Extensions.Windows"

    def _call_dbus_method(self, method: str, *args: str) -> Optional[str]:
        """Call a D-Bus method on the window-calls extension."""
        cmd = [
            "gdbus", "call", "--session",
            "--dest", self.DBUS_DEST,
            "--object-path", self.DBUS_PATH,
            "--print-reply=literal",
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
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return None

    def _parse_window_list(self, raw_output: str) -> list[dict]:
        """Parse the JSON output from the List method."""
        if not raw_output:
            return []
        try:
            return json.loads(raw_output)
        except json.JSONDecodeError:
            return []

    def get_window_list(self) -> list[WindowInfo]:
        """Get a list of all windows."""
        raw = self._call_dbus_method("List")
        windows_data = self._parse_window_list(raw)

        windows = []
        for w in windows_data:
            if w.get("frame_type") == 0 and w.get("window_type") == 0:
                windows.append(WindowInfo(
                    wm_class=w.get("wm_class", ""),
                    title="",
                    pid=w.get("pid", 0),
                    window_id=w.get("id", 0),
                    x=w.get("x", 0),
                    y=w.get("y", 0),
                    width=w.get("width", 0),
                    height=w.get("height", 0)
                ))
        return windows

    def get_focused_window(self) -> Optional[WindowInfo]:
        """Get information about the currently focused window."""
        raw = self._call_dbus_method("List")
        windows_data = self._parse_window_list(raw)

        for w in windows_data:
            if w.get("frame_type") == 0 and w.get("window_type") == 0:
                window_id = w.get("id", 0)
                details_raw = self._call_dbus_method("Details", str(window_id))
                if details_raw:
                    try:
                        details = json.loads(details_raw)
                        if details.get("focus", False):
                            title_raw = self._call_dbus_method("GetTitle", str(window_id))
                            title = ""
                            if title_raw:
                                title = title_raw.strip()
                                if title.startswith("'") and title.endswith("'"):
                                    title = title[1:-1]
                                elif title.startswith('"') and title.endswith('"'):
                                    title = title[1:-1]

                            return WindowInfo(
                                wm_class=details.get("wm_class", w.get("wm_class", "")),
                                title=title,
                                pid=details.get("pid", w.get("pid", 0)),
                                window_id=window_id,
                                x=details.get("x", w.get("x", 0)),
                                y=details.get("y", w.get("y", 0)),
                                width=details.get("width", w.get("width", 0)),
                                height=details.get("height", w.get("height", 0))
                            )
                    except json.JSONDecodeError:
                        if w.get("wm_class"):
                            return WindowInfo(
                                wm_class=w.get("wm_class", ""),
                                title="",
                                pid=w.get("pid", 0),
                                window_id=window_id,
                                x=w.get("x", 0),
                                y=w.get("y", 0),
                                width=w.get("width", 0),
                                height=w.get("height", 0)
                            )
        return None

    def get_window_by_id(self, window_id: int) -> Optional[WindowInfo]:
        """Get information about a specific window by ID."""
        details_raw = self._call_dbus_method("Details", str(window_id))
        if not details_raw:
            return None

        try:
            details = json.loads(details_raw)
            title_raw = self._call_dbus_method("GetTitle", str(window_id))
            title = title_raw.strip("'\"") if title_raw else ""

            return WindowInfo(
                wm_class=details.get("wm_class", ""),
                title=title,
                pid=details.get("pid", 0),
                window_id=window_id,
                x=details.get("x", 0),
                y=details.get("y", 0),
                width=details.get("width", 0),
                height=details.get("height", 0)
            )
        except json.JSONDecodeError:
            return None


def get_window_focus_provider() -> WindowFocusProvider:
    """Get the appropriate window focus provider for the current platform."""
    return GnomeWindowCallsProvider()
