"""
Main entry point for Shortcut Cheatsheet application.
"""

import sys
import logging
from PyQt6.QtWidgets import QApplication

from .ui.cheatsheet_window import CheatsheetWindow
from .data_loader import initialize_user_data


def setup_logging() -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main() -> int:
    """Main entry point."""
    setup_logging()
    initialize_user_data()

    app = QApplication(sys.argv)
    app.setApplicationName("Shortcut Cheatsheet")
    app.setOrganizationName("ShortcutCheatsheet")

    app.setStyle("Fusion")

    window = CheatsheetWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
