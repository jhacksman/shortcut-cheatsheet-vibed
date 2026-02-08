"""
Module for managing shortcut data.

This module handles loading, saving, and managing keyboard shortcuts
for different applications. Shortcuts are stored in TOML files.
"""

import os
import toml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Shortcut:
    """A single keyboard shortcut."""
    action: str
    keys: str


@dataclass
class ShortcutSection:
    """A section of shortcuts (e.g., 'Navigation', 'Editing')."""
    name: str
    shortcuts: list[Shortcut] = field(default_factory=list)


@dataclass
class AppShortcuts:
    """Shortcuts for a specific application."""
    app_name: str
    wm_class: str
    sections: list[ShortcutSection] = field(default_factory=list)


class ShortcutManager:
    """Manages loading and saving shortcuts for applications."""

    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize the shortcut manager."""
        if data_dir is None:
            config_home = os.environ.get(
                "XDG_CONFIG_HOME",
                os.path.expanduser("~/.config")
            )
            data_dir = Path(config_home) / "shortcut-cheatsheet" / "shortcuts"

        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, AppShortcuts] = {}

    def _get_shortcut_file(self, wm_class: str) -> Path:
        """Get the path to the shortcut file for an application."""
        safe_name = wm_class.lower().replace(" ", "_").replace("/", "_")
        return self.data_dir / f"{safe_name}.toml"

    def load_shortcuts(self, wm_class: str) -> Optional[AppShortcuts]:
        """Load shortcuts for an application by its wm_class."""
        if wm_class in self._cache:
            return self._cache[wm_class]

        shortcut_file = self._get_shortcut_file(wm_class)
        if not shortcut_file.exists():
            return None

        try:
            data = toml.load(shortcut_file)
            app_shortcuts = AppShortcuts(
                app_name=data.get("app_name", wm_class),
                wm_class=data.get("wm_class", wm_class),
                sections=[]
            )

            for section_name, shortcuts_data in data.get("sections", {}).items():
                section = ShortcutSection(name=section_name)
                for action, keys in shortcuts_data.items():
                    section.shortcuts.append(Shortcut(action=action, keys=keys))
                app_shortcuts.sections.append(section)

            self._cache[wm_class] = app_shortcuts
            return app_shortcuts

        except (toml.TomlDecodeError, KeyError):
            return None

    def save_shortcuts(self, app_shortcuts: AppShortcuts) -> bool:
        """Save shortcuts for an application."""
        shortcut_file = self._get_shortcut_file(app_shortcuts.wm_class)

        data = {
            "app_name": app_shortcuts.app_name,
            "wm_class": app_shortcuts.wm_class,
            "sections": {}
        }

        for section in app_shortcuts.sections:
            section_data = {}
            for shortcut in section.shortcuts:
                section_data[shortcut.action] = shortcut.keys
            data["sections"][section.name] = section_data

        try:
            with open(shortcut_file, "w") as f:
                toml.dump(data, f)
            self._cache[app_shortcuts.wm_class] = app_shortcuts
            return True
        except OSError:
            return False

    def delete_shortcuts(self, wm_class: str) -> bool:
        """Delete shortcuts for an application."""
        shortcut_file = self._get_shortcut_file(wm_class)
        if wm_class in self._cache:
            del self._cache[wm_class]

        try:
            if shortcut_file.exists():
                shortcut_file.unlink()
            return True
        except OSError:
            return False

    def list_applications(self) -> list[str]:
        """List all applications with saved shortcuts."""
        apps = []
        for file in self.data_dir.glob("*.toml"):
            try:
                data = toml.load(file)
                apps.append(data.get("wm_class", file.stem))
            except toml.TomlDecodeError:
                continue
        return apps

    def create_empty_shortcuts(self, wm_class: str, app_name: str) -> AppShortcuts:
        """Create an empty shortcuts profile for an application."""
        app_shortcuts = AppShortcuts(
            app_name=app_name,
            wm_class=wm_class,
            sections=[ShortcutSection(name="General")]
        )
        self.save_shortcuts(app_shortcuts)
        return app_shortcuts

    def clear_cache(self) -> None:
        """Clear the shortcuts cache."""
        self._cache.clear()
