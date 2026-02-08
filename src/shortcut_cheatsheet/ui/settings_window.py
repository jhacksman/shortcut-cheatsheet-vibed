"""
Settings window for editing keyboard shortcuts.

This window allows users to edit shortcuts for applications,
add new applications, and manage shortcut profiles.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QComboBox, QLabel, QLineEdit,
    QDialog, QListWidget, QListWidgetItem, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent

from ..platform.window_focus import WindowFocusProvider
from ..shortcuts import ShortcutManager, AppShortcuts, ShortcutSection, Shortcut

from typing import Optional


class AddAppDialog(QDialog):
    """Dialog for selecting an application to add shortcuts for."""

    def __init__(
        self,
        focus_provider: WindowFocusProvider,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.focus_provider = focus_provider
        self.selected_app: Optional[str] = None

        self._setup_ui()
        self._setup_dark_theme()
        self._load_running_apps()

    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        self.setWindowTitle("Add Application")
        self.setMinimumSize(300, 400)

        layout = QVBoxLayout(self)

        label = QLabel("Select a running application:")
        layout.addWidget(label)

        self.app_list = QListWidget()
        self.app_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.app_list)

        manual_label = QLabel("Or enter wm_class manually:")
        layout.addWidget(manual_label)

        self.manual_input = QLineEdit()
        self.manual_input.setPlaceholderText("e.g., firefox, code, gnome-terminal")
        layout.addWidget(self.manual_input)

        button_layout = QHBoxLayout()

        self.add_button = QPushButton("&Add")
        self.add_button.clicked.connect(self._on_add_clicked)
        button_layout.addWidget(self.add_button)

        self.cancel_button = QPushButton("&Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

    def _setup_dark_theme(self) -> None:
        """Apply dark theme to the dialog."""
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #dcdcdc;
            }
            QListWidget {
                background-color: #282828;
                color: #dcdcdc;
                border: 1px solid #404040;
            }
            QListWidget::item:selected {
                background-color: #4682b4;
            }
            QListWidget::item:focus {
                background-color: #5a5a5a;
            }
            QLineEdit {
                background-color: #282828;
                color: #dcdcdc;
                border: 1px solid #404040;
                padding: 5px;
            }
            QLineEdit:focus {
                border: 1px solid #4682b4;
            }
            QPushButton {
                background-color: #383838;
                color: #dcdcdc;
                border: 1px solid #404040;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #484848;
            }
            QPushButton:focus {
                border: 1px solid #4682b4;
                background-color: #4a4a4a;
            }
        """)

    def _load_running_apps(self) -> None:
        """Load the list of running applications."""
        windows = self.focus_provider.get_window_list()
        seen_classes = set()

        for window in windows:
            if window.wm_class and window.wm_class not in seen_classes:
                seen_classes.add(window.wm_class)
                item = QListWidgetItem(window.wm_class)
                self.app_list.addItem(item)

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle double-click on an application item."""
        self.selected_app = item.text()
        self.accept()

    def _on_add_clicked(self) -> None:
        """Handle add button click."""
        if self.manual_input.text().strip():
            self.selected_app = self.manual_input.text().strip()
        elif self.app_list.currentItem():
            self.selected_app = self.app_list.currentItem().text()
        else:
            return

        self.accept()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)


class SettingsWindow(QMainWindow):
    """Window for editing application shortcuts."""

    shortcuts_saved = pyqtSignal()

    def __init__(
        self,
        shortcut_manager: ShortcutManager,
        focus_provider: WindowFocusProvider,
        initial_app: Optional[str] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)

        self.shortcut_manager = shortcut_manager
        self.focus_provider = focus_provider
        self.current_app: Optional[str] = initial_app
        self.current_shortcuts: Optional[AppShortcuts] = None
        self.has_unsaved_changes = False

        self._setup_ui()
        self._setup_dark_theme()
        self._load_applications()

        if initial_app:
            index = self.app_combo.findText(initial_app)
            if index >= 0:
                self.app_combo.setCurrentIndex(index)
            else:
                self._create_new_app(initial_app)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        self.setWindowTitle("Shortcut Settings")
        self.setMinimumSize(600, 500)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        app_layout = QHBoxLayout()

        app_label = QLabel("&Application:")
        self.app_combo = QComboBox()
        self.app_combo.currentTextChanged.connect(self._on_app_changed)
        app_label.setBuddy(self.app_combo)
        app_layout.addWidget(app_label)
        app_layout.addWidget(self.app_combo, 1)

        self.add_app_button = QPushButton("Add &New")
        self.add_app_button.clicked.connect(self._on_add_app_clicked)
        app_layout.addWidget(self.add_app_button)

        self.delete_app_button = QPushButton("&Delete Profile")
        self.delete_app_button.clicked.connect(self._on_delete_app_clicked)
        app_layout.addWidget(self.delete_app_button)

        layout.addLayout(app_layout)

        self.shortcuts_table = QTableWidget()
        self.shortcuts_table.setColumnCount(3)
        self.shortcuts_table.setHorizontalHeaderLabels(["Action", "Shortcut", ""])
        self.shortcuts_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.shortcuts_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.shortcuts_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Fixed
        )
        self.shortcuts_table.setColumnWidth(2, 40)
        self.shortcuts_table.verticalHeader().setVisible(False)
        self.shortcuts_table.cellChanged.connect(self._on_cell_changed)
        layout.addWidget(self.shortcuts_table)

        add_row_layout = QHBoxLayout()
        self.add_row_button = QPushButton("Add &Row")
        self.add_row_button.clicked.connect(self._on_add_row_clicked)
        add_row_layout.addWidget(self.add_row_button)
        add_row_layout.addStretch()
        layout.addLayout(add_row_layout)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.save_button = QPushButton("&Save")
        self.save_button.clicked.connect(self._on_save_clicked)
        button_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("&Cancel")
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

    def _setup_dark_theme(self) -> None:
        """Apply dark theme to the window."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #dcdcdc;
            }
            QComboBox {
                background-color: #282828;
                color: #dcdcdc;
                border: 1px solid #404040;
                padding: 5px;
            }
            QComboBox:focus {
                border: 1px solid #4682b4;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #282828;
                color: #dcdcdc;
                selection-background-color: #4682b4;
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
            QTableWidget::item:focus {
                background-color: #4a4a4a;
            }
            QHeaderView::section {
                background-color: #383838;
                color: #dcdcdc;
                padding: 5px;
                border: 1px solid #404040;
            }
            QPushButton {
                background-color: #383838;
                color: #dcdcdc;
                border: 1px solid #404040;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #484848;
            }
            QPushButton:focus {
                border: 1px solid #4682b4;
                background-color: #4a4a4a;
            }
            QLineEdit {
                background-color: #282828;
                color: #dcdcdc;
                border: 1px solid #404040;
                padding: 5px;
            }
            QLineEdit:focus {
                border: 1px solid #4682b4;
            }
        """)

    def _load_applications(self) -> None:
        """Load the list of applications with shortcuts."""
        self.app_combo.clear()
        apps = self.shortcut_manager.list_applications()
        for app in sorted(apps):
            self.app_combo.addItem(app)

    def _on_app_changed(self, app_name: str) -> None:
        """Handle application selection change."""
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Discard them?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                index = self.app_combo.findText(self.current_app or "")
                if index >= 0:
                    self.app_combo.blockSignals(True)
                    self.app_combo.setCurrentIndex(index)
                    self.app_combo.blockSignals(False)
                return

        self.current_app = app_name
        self.has_unsaved_changes = False
        self._load_shortcuts(app_name)

    def _load_shortcuts(self, wm_class: str) -> None:
        """Load shortcuts for the given application."""
        self.current_shortcuts = self.shortcut_manager.load_shortcuts(wm_class)

        self.shortcuts_table.blockSignals(True)
        self.shortcuts_table.setRowCount(0)

        if self.current_shortcuts is None:
            self.shortcuts_table.blockSignals(False)
            return

        row = 0
        for section in self.current_shortcuts.sections:
            for shortcut in section.shortcuts:
                self.shortcuts_table.insertRow(row)

                action_item = QTableWidgetItem(shortcut.action)
                self.shortcuts_table.setItem(row, 0, action_item)

                keys_item = QTableWidgetItem(shortcut.keys)
                self.shortcuts_table.setItem(row, 1, keys_item)

                delete_button = QPushButton("X")
                delete_button.setStyleSheet("""
                    QPushButton {
                        background-color: #8b0000;
                        color: white;
                        border: none;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #a00000;
                    }
                """)
                delete_button.clicked.connect(
                    lambda checked, r=row: self._on_delete_row_clicked(r)
                )
                self.shortcuts_table.setCellWidget(row, 2, delete_button)

                row += 1

        self.shortcuts_table.blockSignals(False)

    def _on_cell_changed(self, row: int, column: int) -> None:
        """Handle cell content change."""
        self.has_unsaved_changes = True

    def _on_add_row_clicked(self) -> None:
        """Add a new shortcut row."""
        row = self.shortcuts_table.rowCount()
        self.shortcuts_table.insertRow(row)

        action_item = QTableWidgetItem("")
        self.shortcuts_table.setItem(row, 0, action_item)

        keys_item = QTableWidgetItem("")
        self.shortcuts_table.setItem(row, 1, keys_item)

        delete_button = QPushButton("X")
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #8b0000;
                color: white;
                border: none;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #a00000;
            }
        """)
        delete_button.clicked.connect(
            lambda checked, r=row: self._on_delete_row_clicked(r)
        )
        self.shortcuts_table.setCellWidget(row, 2, delete_button)

        self.has_unsaved_changes = True
        self.shortcuts_table.setCurrentCell(row, 0)
        self.shortcuts_table.editItem(self.shortcuts_table.item(row, 0))

    def _on_delete_row_clicked(self, row: int) -> None:
        """Delete a shortcut row."""
        if row < self.shortcuts_table.rowCount():
            self.shortcuts_table.removeRow(row)
            self.has_unsaved_changes = True
            self._refresh_delete_buttons()

    def _refresh_delete_buttons(self) -> None:
        """Refresh delete button connections after row deletion."""
        for row in range(self.shortcuts_table.rowCount()):
            delete_button = QPushButton("X")
            delete_button.setStyleSheet("""
                QPushButton {
                    background-color: #8b0000;
                    color: white;
                    border: none;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #a00000;
                }
            """)
            delete_button.clicked.connect(
                lambda checked, r=row: self._on_delete_row_clicked(r)
            )
            self.shortcuts_table.setCellWidget(row, 2, delete_button)

    def _on_add_app_clicked(self) -> None:
        """Open dialog to add a new application."""
        dialog = AddAppDialog(self.focus_provider, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_app:
            self._create_new_app(dialog.selected_app)

    def _create_new_app(self, wm_class: str) -> None:
        """Create a new application shortcut profile."""
        self.shortcut_manager.create_empty_shortcuts(wm_class, wm_class)
        self._load_applications()

        index = self.app_combo.findText(wm_class)
        if index >= 0:
            self.app_combo.setCurrentIndex(index)

    def _on_delete_app_clicked(self) -> None:
        """Delete the current application's shortcut profile."""
        if not self.current_app:
            return

        reply = QMessageBox.question(
            self,
            "Delete Profile",
            f"Delete all shortcuts for {self.current_app}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.shortcut_manager.delete_shortcuts(self.current_app)
            self.has_unsaved_changes = False
            self._load_applications()
            self.shortcuts_saved.emit()

    def _on_save_clicked(self) -> None:
        """Save the current shortcuts."""
        if not self.current_app:
            return

        shortcuts = []
        for row in range(self.shortcuts_table.rowCount()):
            action_item = self.shortcuts_table.item(row, 0)
            keys_item = self.shortcuts_table.item(row, 1)

            if action_item and keys_item:
                action = action_item.text().strip()
                keys = keys_item.text().strip()
                if action and keys:
                    shortcuts.append(Shortcut(action=action, keys=keys))

        app_shortcuts = AppShortcuts(
            app_name=self.current_app,
            wm_class=self.current_app,
            sections=[ShortcutSection(name="General", shortcuts=shortcuts)]
        )

        if self.shortcut_manager.save_shortcuts(app_shortcuts):
            self.has_unsaved_changes = False
            self.shortcuts_saved.emit()
            self.close()
        else:
            QMessageBox.warning(
                self,
                "Save Failed",
                "Failed to save shortcuts."
            )

    def _on_cancel_clicked(self) -> None:
        """Cancel and close the settings window."""
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Discard them?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        self.close()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Escape:
            self._on_cancel_clicked()
        else:
            super().keyPressEvent(event)
