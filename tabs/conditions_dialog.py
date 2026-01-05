"""
Conditions dialog: allows selecting active conditions for a monster.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QVBoxLayout,
    QLabel,
)

# Make sure we can import config from the project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if PROJECT_ROOT.exists() and str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules import config  # noqa: E402


class ConditionsDialog(QDialog):
    """Dialog for selecting active conditions from checkboxes."""

    def __init__(self, parent=None, current_conditions: List[str] = None):
        super().__init__(parent)

        if current_conditions is None:
            current_conditions = []

        self.setWindowTitle("Set Conditions")
        self.setMinimumWidth(400)

        # Main layout
        layout = QVBoxLayout()

        # Title label
        title = QLabel("Select active conditions:")
        title.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title)

        # Grid layout for checkboxes (2 columns)
        grid = QGridLayout()
        grid.setSpacing(8)

        self.checkboxes = {}
        available = config.CONFIG.available_conditions

        # Create checkboxes in a 2-column grid
        for idx, condition in enumerate(available):
            # Reflect current selection by default for quick edits.
            checkbox = QCheckBox(condition)
            checkbox.setChecked(condition in current_conditions)
            self.checkboxes[condition] = checkbox

            row = idx // 2
            col = idx % 2
            grid.addWidget(checkbox, row, col)

        layout.addLayout(grid)

        # Button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def get_selected_conditions(self) -> List[str]:
        """Return a list of selected condition names."""
        selected = []
        for condition, checkbox in self.checkboxes.items():
            if checkbox.isChecked():
                selected.append(condition)
        return selected


def show_conditions_dialog(
    parent=None, current_conditions: List[str] = None
) -> Optional[List[str]]:
    """
    Show the conditions dialog and return selected conditions if accepted, None if canceled.
    """
    dialog = ConditionsDialog(parent, current_conditions)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.get_selected_conditions()
    return None
