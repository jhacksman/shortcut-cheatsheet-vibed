"""
Main cheatsheet window for displaying keyboard shortcuts.

This window shows shortcuts for the currently focused application
in a table format with actions and key combinations.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QLabel, QHeaderView, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeyEvent, QFont, QPalette, QColor

from ..platform.window_focus import get_window_focus_provider
from ..platform.window_position import get_window_position_provider, ScreenCorner
from ..platform.window_pin import get_window_pin_provider
from ..shortcuts import ShortcutManager
from ..settings import Settings

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .settings_window import SettingsWindow


class CheatsheetWindow(QMainWindow):
    """Main window displaying keyboard shortcuts for the focused application."""

    APP_WM_CLASS = "shortcut-cheatsheet"

    def __init__(self):
        super().__init__()

        self.settings = Settings()
        self.shortcut_manager = ShortcutManager()
        self.focus_provider = get_window_focus_provider()
        self.position_provider = get_window_position_provider()
        self.pin_provider = get_window_pin_provider()

        self.current_app: Optional[str] = None
        self.last_external_app: Optional[str] = None
        self.current_corner = ScreenCorner.TOP_RIGHT
        self.settings_window: Optional["SettingsWindow"] = None
        self._own_window_id: Optional[int] = None

        self._setup_ui()
        self._setup_dark_theme()
        self._apply_font_size()
        self._setup_focus_timer()

        self.pin_provider.set_always_on_top(self, True)

        saved_corner = self.settings.get_window_corner()
        if saved_corner:
            try:
                self.current_corner = ScreenCorner(saved_corner)
            except ValueError:
                pass

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        self.setWindowTitle("Shortcut Cheatsheet")
        self.setMinimumSize(400, 300)
        self.resize(500, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.app_label = QLabel("No application focused")
        self.app_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.app_label)

        self.shortcuts_table = QTableWidget()
        self.shortcuts_table.setColumnCount(2)
        self.shortcuts_table.setHorizontalHeaderLabels(["Action", "Shortcut"])
        self.shortcuts_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.shortcuts_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.shortcuts_table.verticalHeader().setVisible(False)
        self.shortcuts_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.shortcuts_table.setSelectionMode(
            QTableWidget.SelectionMode.NoSelection
        )
        self.shortcuts_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout.addWidget(self.shortcuts_table)

        self.hint_label = QLabel(
            "Arrow keys: move | Ctrl+/Ctrl-: font size | S: settings | Q: quit"
        )
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self.hint_label.font()
        font.setPointSize(9)
        self.hint_label.setFont(font)
        layout.addWidget(self.hint_label)

    def _setup_dark_theme(self) -> None:
        """Apply dark theme to the window."""
        palette = QPalette()

        palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 220))
        palette.setColor(QPalette.ColorRole.Base, QColor(40, 40, 40))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(50, 50, 50))
        palette.setColor(QPalette.ColorRole.Text, QColor(220, 220, 220))
        palette.setColor(QPalette.ColorRole.Button, QColor(50, 50, 50))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(220, 220, 220))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(70, 130, 180))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

        self.setPalette(palette)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #dcdcdc;
            }
            QTableWidget {
                background-color: #282828;
                color: #dcdcdc;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #383838;
                color: #dcdcdc;
                padding: 5px;
                border: 1px solid #404040;
            }
        """)

    def _apply_font_size(self) -> None:
        """Apply the current font size to all elements."""
        font_size = self.settings.get_font_size()

        font = QFont()
        font.setPointSize(font_size)

        self.app_label.setFont(font)
        self.shortcuts_table.setFont(font)

        header_font = QFont()
        header_font.setPointSize(font_size)
        header_font.setBold(True)
        self.shortcuts_table.horizontalHeader().setFont(header_font)

        hint_font = QFont()
        hint_font.setPointSize(max(9, font_size - 3))
        self.hint_label.setFont(hint_font)

    def _setup_focus_timer(self) -> None:
        """Set up timer to periodically check focused window."""
        self.focus_timer = QTimer(self)
        self.focus_timer.timeout.connect(self._check_focused_window)
        self.focus_timer.start(500)

    def _check_focused_window(self) -> None:
        """Check the currently focused window and update display."""
        focused = self.focus_provider.get_focused_window()

        if focused is None:
            return

        if focused.wm_class.lower() == self.APP_WM_CLASS.lower():
            return

        if focused.wm_class == self.current_app:
            return

        self.current_app = focused.wm_class
        self.last_external_app = focused.wm_class
        self.settings.set_last_app(focused.wm_class)
        self._update_shortcuts_display(focused.wm_class)

    def _update_shortcuts_display(self, wm_class: str) -> None:
        """Update the shortcuts table for the given application."""
        self.app_label.setText(wm_class)
        self.setWindowTitle(f"Shortcuts - {wm_class}")

        shortcuts = self.shortcut_manager.load_shortcuts(wm_class)

        self.shortcuts_table.setRowCount(0)

        if shortcuts is None:
            self.shortcuts_table.setRowCount(1)
            no_shortcuts_item = QTableWidgetItem(
                f"No shortcuts defined for {wm_class}"
            )
            no_shortcuts_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.shortcuts_table.setItem(0, 0, no_shortcuts_item)
            self.shortcuts_table.setSpan(0, 0, 1, 2)
            return

        row = 0
        for section in shortcuts.sections:
            self.shortcuts_table.insertRow(row)
            section_item = QTableWidgetItem(section.name)
            section_item.setBackground(QColor(60, 60, 60))
            font = section_item.font()
            font.setBold(True)
            section_item.setFont(font)
            self.shortcuts_table.setItem(row, 0, section_item)
            self.shortcuts_table.setSpan(row, 0, 1, 2)
            row += 1

            for shortcut in section.shortcuts:
                self.shortcuts_table.insertRow(row)
                action_item = QTableWidgetItem(shortcut.action)
                keys_item = QTableWidgetItem(shortcut.keys)
                keys_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.shortcuts_table.setItem(row, 0, action_item)
                self.shortcuts_table.setItem(row, 1, keys_item)
                row += 1

    def _get_own_window_id(self) -> int:
        """Get this window's ID from window-calls extension."""
        if self._own_window_id is not None:
            return self._own_window_id

        windows = self.focus_provider.get_window_list()
        for w in windows:
            if w.wm_class.lower() == self.APP_WM_CLASS.lower():
                self._own_window_id = w.window_id
                return w.window_id

            if "shortcut" in w.wm_class.lower() or "cheatsheet" in w.wm_class.lower():
                self._own_window_id = w.window_id
                return w.window_id

        return 0

    def _move_to_corner(self, corner: ScreenCorner) -> None:
        """Move the window to the specified corner."""
        self.current_corner = corner
        self.settings.set_window_corner(corner.value)

        screen = QApplication.primaryScreen()
        if screen is None:
            return

        screen_geometry = screen.availableGeometry()
        window_size = self.size()
        margin = 10

        if corner == ScreenCorner.TOP_LEFT:
            x = screen_geometry.x() + margin
            y = screen_geometry.y() + margin
        elif corner == ScreenCorner.TOP_RIGHT:
            x = screen_geometry.x() + screen_geometry.width() - window_size.width() - margin
            y = screen_geometry.y() + margin
        elif corner == ScreenCorner.BOTTOM_LEFT:
            x = screen_geometry.x() + margin
            y = screen_geometry.y() + screen_geometry.height() - window_size.height() - margin
        elif corner == ScreenCorner.BOTTOM_RIGHT:
            x = screen_geometry.x() + screen_geometry.width() - window_size.width() - margin
            y = screen_geometry.y() + screen_geometry.height() - window_size.height() - margin
        else:
            return

        window_id = self._get_own_window_id()
        if window_id > 0:
            self.position_provider.move_window(window_id, x, y)
        else:
            self.move(x, y)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events."""
        key = event.key()
        modifiers = event.modifiers()

        if key == Qt.Key.Key_Left:
            if self.current_corner in (ScreenCorner.TOP_RIGHT, ScreenCorner.BOTTOM_RIGHT):
                new_corner = (
                    ScreenCorner.TOP_LEFT
                    if self.current_corner == ScreenCorner.TOP_RIGHT
                    else ScreenCorner.BOTTOM_LEFT
                )
                self._move_to_corner(new_corner)

        elif key == Qt.Key.Key_Right:
            if self.current_corner in (ScreenCorner.TOP_LEFT, ScreenCorner.BOTTOM_LEFT):
                new_corner = (
                    ScreenCorner.TOP_RIGHT
                    if self.current_corner == ScreenCorner.TOP_LEFT
                    else ScreenCorner.BOTTOM_RIGHT
                )
                self._move_to_corner(new_corner)

        elif key == Qt.Key.Key_Up:
            if self.current_corner in (ScreenCorner.BOTTOM_LEFT, ScreenCorner.BOTTOM_RIGHT):
                new_corner = (
                    ScreenCorner.TOP_LEFT
                    if self.current_corner == ScreenCorner.BOTTOM_LEFT
                    else ScreenCorner.TOP_RIGHT
                )
                self._move_to_corner(new_corner)

        elif key == Qt.Key.Key_Down:
            if self.current_corner in (ScreenCorner.TOP_LEFT, ScreenCorner.TOP_RIGHT):
                new_corner = (
                    ScreenCorner.BOTTOM_LEFT
                    if self.current_corner == ScreenCorner.TOP_LEFT
                    else ScreenCorner.BOTTOM_RIGHT
                )
                self._move_to_corner(new_corner)

        elif key == Qt.Key.Key_Plus and modifiers & Qt.KeyboardModifier.ControlModifier:
            self.settings.increase_font_size()
            self._apply_font_size()

        elif key == Qt.Key.Key_Minus and modifiers & Qt.KeyboardModifier.ControlModifier:
            self.settings.decrease_font_size()
            self._apply_font_size()

        elif key == Qt.Key.Key_Equal and modifiers & Qt.KeyboardModifier.ControlModifier:
            self.settings.increase_font_size()
            self._apply_font_size()

        elif key == Qt.Key.Key_S:
            self._open_settings()

        elif key == Qt.Key.Key_Q:
            self.close()

        elif key == Qt.Key.Key_Escape:
            self.close()

        else:
            super().keyPressEvent(event)

    def _open_settings(self) -> None:
        """Open the settings window."""
        from .settings_window import SettingsWindow

        if self.settings_window is not None and self.settings_window.isVisible():
            self.settings_window.activateWindow()
            return

        last_app = self.last_external_app or self.settings.get_last_app()
        self.settings_window = SettingsWindow(
            self.shortcut_manager,
            self.focus_provider,
            last_app,
            parent=self
        )
        self.settings_window.shortcuts_saved.connect(self._on_shortcuts_saved)
        self.settings_window.show()

    def _on_shortcuts_saved(self) -> None:
        """Handle shortcuts being saved in settings window."""
        self.shortcut_manager.clear_cache()
        if self.current_app:
            self._update_shortcuts_display(self.current_app)

    def showEvent(self, event) -> None:
        """Handle window show event."""
        super().showEvent(event)
        self._move_to_corner(self.current_corner)

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        if self.settings_window is not None:
            self.settings_window.close()
        super().closeEvent(event)
