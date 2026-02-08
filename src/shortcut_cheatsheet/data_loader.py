"""
Module for loading bundled shortcut data.

This module handles copying bundled shortcut files to the user's
config directory on first run.
"""

import os
import shutil
from pathlib import Path


def get_bundled_data_dir() -> Path:
    """Get the path to the bundled data directory."""
    module_dir = Path(__file__).parent.parent.parent
    return module_dir / "data" / "shortcuts"


def get_user_data_dir() -> Path:
    """Get the path to the user's shortcut data directory."""
    config_home = os.environ.get(
        "XDG_CONFIG_HOME",
        os.path.expanduser("~/.config")
    )
    return Path(config_home) / "shortcut-cheatsheet" / "shortcuts"


def initialize_user_data() -> None:
    """
    Initialize the user's data directory with bundled shortcuts.
    
    Only copies files that don't already exist in the user's directory.
    """
    bundled_dir = get_bundled_data_dir()
    user_dir = get_user_data_dir()

    if not bundled_dir.exists():
        return

    user_dir.mkdir(parents=True, exist_ok=True)

    for bundled_file in bundled_dir.glob("*.toml"):
        user_file = user_dir / bundled_file.name
        if not user_file.exists():
            shutil.copy2(bundled_file, user_file)
