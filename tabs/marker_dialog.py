"""
Marker dialog: allows setting color and number for monster map markers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple
import sys

from PySide6.QtCore import QFile, QIODevice, QSize
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QDialog, QComboBox, QSpinBox, QDialogButtonBox, QStyledItemDelegate
from PySide6.QtUiTools import QUiLoader

# Make sure we can import config from the project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if PROJECT_ROOT.exists() and str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules import config  # noqa: E402


def create_color_icon(color_hex: str, size: int = 16) -> QPixmap:
    """Create a colored square pixmap for the combo box."""
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(color_hex))
    return pixmap


class MarkerDialog(QDialog):
    """Dialog for setting monster marker color and number."""

    def __init__(self, parent=None, current_color: str = "", current_number: int = 1, manager=None):
        super().__init__(parent)

        self.manager = manager

        # Load UI
        ui_path = PROJECT_ROOT / "uiDesign" / "setMapMarkers.ui"
        loader = QUiLoader()
        ui_file = QFile(str(ui_path))
        if not ui_file.open(QIODevice.OpenModeFlag.ReadOnly):
            raise RuntimeError(f"Cannot open UI file: {ui_path}")

        # Load UI as a widget and set it as the dialog's layout
        ui_widget = loader.load(ui_file)
        ui_file.close()

        if ui_widget is None:
            raise RuntimeError(f"Failed to load UI from: {ui_path}")

        # Transfer the layout from the loaded widget to this dialog
        self.setLayout(ui_widget.layout())
        self.setWindowTitle("Set Map Marker")

        # Get widgets
        self.color_combo: QComboBox = self.findChild(QComboBox, "colorCombo")
        self.value_spin: QSpinBox = self.findChild(QSpinBox, "valueSpin")
        self.button_box: QDialogButtonBox = self.findChild(QDialogButtonBox, "buttonBox")

        if self.color_combo is None or self.value_spin is None or self.button_box is None:
            raise RuntimeError("Could not find required widgets in setMapMarkers.ui")

        # Populate color dropdown from config with colored icons
        self.color_combo.clear()
        for color in config.CONFIG.marker_palette:
            icon = create_color_icon(color, 24)
            self.color_combo.addItem(icon, "", color)  # icon, empty text, data

        # Connect color change to auto-update number
        self.color_combo.currentIndexChanged.connect(self._on_color_changed)

        # Set current values
        if current_color:
            idx = self.color_combo.findData(current_color)
            if idx >= 0:
                self.color_combo.setCurrentIndex(idx)

        # If no current number was provided, auto-select for the current color
        if current_number <= 0 and self.manager:
            # Auto-suggest the next per-color marker number.
            selected_color = self.color_combo.currentData()
            if selected_color:
                current_number = self.manager._next_marker_number_for_color(selected_color)

        self.value_spin.setValue(current_number)
        self.value_spin.setMinimum(config.CONFIG.marker_start_number)
        self.value_spin.setMaximum(99)

        # Connect buttons
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def _on_color_changed(self, index: int) -> None:
        """Auto-select the next available number when color changes."""
        if self.manager is None:
            return

        selected_color = self.color_combo.currentData()
        if selected_color:
            next_number = self.manager._next_marker_number_for_color(selected_color)
            self.value_spin.setValue(next_number)

    def get_values(self) -> Tuple[str, int]:
        """Return the selected color and number."""
        color = self.color_combo.currentData()
        number = self.value_spin.value()
        return (color, number)


def show_marker_dialog(
    parent=None, current_color: str = "", current_number: int = 1, manager=None
) -> Optional[Tuple[str, int]]:
    """
    Show the marker dialog and return (color, number) if accepted, None if canceled.
    """
    dialog = MarkerDialog(parent, current_color, current_number, manager)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.get_values()
    return None
