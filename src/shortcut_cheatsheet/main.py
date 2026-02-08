"""
Main entry point for Shortcut Cheatsheet application.
"""

import sys
from PyQt6.QtWidgets import QApplication

from .ui.cheatsheet_window import CheatsheetWindow
from .data_loader import initialize_user_data


def main() -> int:
    """Main entry point."""
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
