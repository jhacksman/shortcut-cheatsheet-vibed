"""
Module for loading bundled shortcut data.

This module handles copying bundled shortcut files to the user's
config directory on first run.
"""

import os
import shutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def get_bundled_data_dir() -> Path:
    """Get the path to the bundled data directory."""
    module_dir = Path(__file__).parent.parent.parent
    bundled_dir = module_dir / "data" / "shortcuts"

    if not bundled_dir.exists():
        alt_dir = module_dir.parent / "data" / "shortcuts"
        if alt_dir.exists():
            return alt_dir

    return bundled_dir


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

    logger.debug(f"Bundled data dir: {bundled_dir}")
    logger.debug(f"User data dir: {user_dir}")
    logger.debug(f"Bundled dir exists: {bundled_dir.exists()}")

    if not bundled_dir.exists():
        logger.warning(f"Bundled data directory not found: {bundled_dir}")
        return

    user_dir.mkdir(parents=True, exist_ok=True)

    copied_count = 0
    for bundled_file in bundled_dir.glob("*.toml"):
        user_file = user_dir / bundled_file.name
        if not user_file.exists():
            shutil.copy2(bundled_file, user_file)
            copied_count += 1
            logger.debug(f"Copied {bundled_file.name} to user config")

    logger.info(f"Initialized user data: copied {copied_count} shortcut files")
