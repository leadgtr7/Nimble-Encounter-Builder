"""
Bulk Marker Assignment Dialog: allows setting markers for multiple monsters at once.
"""

from __future__ import annotations

from typing import Optional, List, Tuple
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QComboBox,
    QSpinBox,
    QPushButton,
    QDialogButtonBox,
    QGroupBox,
)

from modules.config import CONFIG


class BulkMarkerDialog(QDialog):
    """Dialog for setting markers for multiple monsters."""

    def __init__(self, parent=None, monsters: List = None, manager=None):
        super().__init__(parent)
        self.monsters = monsters or []
        self.manager = manager
        self.marker_assignments = {}  # Map monster to (color, number)

        self.setWindowTitle("Set Markers for Selected Monsters")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        # Main layout
        layout = QVBoxLayout(self)

        # Info label
        info_label = QLabel(f"Setting markers for {len(self.monsters)} monster(s)")
        info_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(info_label)

        # Monster list
        list_group = QGroupBox("Selected Monsters")
        list_layout = QVBoxLayout(list_group)
        self.monster_list = QListWidget()
        list_layout.addWidget(self.monster_list)
        layout.addWidget(list_group)

        # Populate monster list
        for monster in self.monsters:
            name = getattr(monster, "name", "Unknown")
            current_color = getattr(monster, "marker_color", "")
            current_number = getattr(monster, "marker_number", 0)

            display_text = f"{name}"
            if current_color and current_number:
                display_text += f" (Currently: {current_number})"

            item = QListWidgetItem(display_text)
            if current_color:
                item.setBackground(QColor(current_color))
                # Calculate contrasting text color
                color = QColor(current_color)
                r, g, b = color.red(), color.green(), color.blue()
                luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
                text_color = QColor("black") if luminance > 0.5 else QColor("white")
                item.setForeground(text_color)

            self.monster_list.addItem(item)

        # Color and number selection
        controls_group = QGroupBox("Marker Settings")
        controls_layout = QVBoxLayout(controls_group)

        # Color selector
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Color:"))
        self.color_combo = QComboBox()
        for color in CONFIG.marker_palette:
            # Create colored icon
            self.color_combo.addItem("", color)
            idx = self.color_combo.count() - 1
            self.color_combo.setItemData(idx, QColor(color), Qt.ItemDataRole.BackgroundRole)
            self.color_combo.setItemData(idx, QColor("white"), Qt.ItemDataRole.ForegroundRole)
            self.color_combo.setItemText(idx, f"  {color}")

        color_layout.addWidget(self.color_combo)
        controls_layout.addLayout(color_layout)

        # Starting number selector
        number_layout = QHBoxLayout()
        number_layout.addWidget(QLabel("Starting Number:"))
        self.number_spin = QSpinBox()
        self.number_spin.setMinimum(CONFIG.marker_start_number)
        self.number_spin.setMaximum(99)
        self.number_spin.setValue(CONFIG.marker_start_number)
        number_layout.addWidget(self.number_spin)
        number_layout.addStretch()
        controls_layout.addLayout(number_layout)

        # Auto-suggest next number button
        suggest_btn = QPushButton("Auto-Suggest Next Number")
        suggest_btn.clicked.connect(self._on_auto_suggest)
        controls_layout.addWidget(suggest_btn)

        layout.addWidget(controls_group)

        # Sequential numbering info
        info = QLabel("Monsters will be assigned sequential numbers starting from the number above.")
        info.setWordWrap(True)
        info.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(info)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Auto-suggest on startup
        self._on_auto_suggest()

    def _on_auto_suggest(self):
        """Auto-suggest the next available number for the selected color."""
        if not self.manager:
            return
        # Marker numbers are per-color; ask manager for the next free number.

        selected_color = self.color_combo.currentData()
        if selected_color:
            next_number = self.manager._next_marker_number_for_color(selected_color)
            self.number_spin.setValue(next_number)

    def get_assignments(self) -> List[Tuple[str, int]]:
        """Return list of (color, number) tuples for each monster."""
        color = self.color_combo.currentData()
        start_number = self.number_spin.value()

        assignments = []
        for i in range(len(self.monsters)):
            assignments.append((color, start_number + i))

        return assignments


def show_bulk_marker_dialog(parent=None, monsters: List = None, manager=None) -> Optional[List[Tuple[str, int]]]:
    """
    Show the bulk marker dialog and return assignments if accepted, None if canceled.
    Returns: List of (color, number) tuples, one for each monster.
    """
    dialog = BulkMarkerDialog(parent, monsters, manager)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.get_assignments()
    return None
