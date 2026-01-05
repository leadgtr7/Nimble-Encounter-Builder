"""
Damage/Heal dialog: uses numberInput.ui with customizable colors for damage vs healing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import sys

from PySide6.QtCore import QFile, QIODevice, Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QPushButton, QLineEdit

from modules import config

from PySide6.QtUiTools import QUiLoader

# Make sure we can import from the project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if PROJECT_ROOT.exists() and str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class DamageHealDialog(QDialog):
    """Dialog for entering damage or heal amounts using numberInput.ui."""

    def __init__(self, parent=None, mode: str = "damage"):
        """
        Initialize the dialog.

        Args:
            parent: Parent widget
            mode: Either "damage" or "heal" - controls title and button colors
        """
        super().__init__(parent)

        self.mode = mode
        self.selected_value = 0

        # Load UI
        ui_path = PROJECT_ROOT / "uiDesign" / "numberInput.ui"
        loader = QUiLoader()
        ui_file = QFile(str(ui_path))
        if not ui_file.open(QIODevice.OpenModeFlag.ReadOnly):
            raise RuntimeError(f"Cannot open UI file: {ui_path}")

        # Load UI as a widget
        ui_widget = loader.load(ui_file)
        ui_file.close()

        if ui_widget is None:
            raise RuntimeError(f"Failed to load UI from: {ui_path}")

        # Transfer the layout from the loaded widget to this dialog
        self.setLayout(ui_widget.layout())

        # Set title based on mode
        if mode == "heal":
            self.setWindowTitle("Heal")
            button_color = self._rgb_to_hex(config.CONFIG.hp_healthy_color)
        else:
            self.setWindowTitle("Damage")
            button_color = self._rgb_to_hex(config.CONFIG.hp_critical_color)

        # Get the freeform input widget
        self.freeform_input: QLineEdit = self.findChild(QLineEdit, "freeformInput")
        if self.freeform_input is None:
            raise RuntimeError("Could not find freeformInput widget in numberInput.ui")

        # Connect Enter key in freeform input
        self.freeform_input.returnPressed.connect(self._on_freeform_enter)

        # Find and connect all number buttons (1-30)
        for i in range(1, 31):
            btn: QPushButton = self.findChild(QPushButton, f"btn_{i}")
            if btn is not None:
                # Set button color
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {button_color};
                        color: white;
                        font-size: 12px;
                        font-weight: bold;
                        border: 1px solid #555;
                        border-radius: 4px;
                        padding: 4px;
                        min-height: 28px;
                        max-height: 28px;
                        min-width: 40px;
                        max-width: 40px;
                    }}
                    QPushButton:hover {{
                        background-color: {self._lighten_color(button_color)};
                    }}
                    QPushButton:pressed {{
                        background-color: {self._darken_color(button_color)};
                    }}
                """)
                # Connect button click; bind current loop value with default arg.
                btn.clicked.connect(lambda checked=False, value=i: self._on_button_clicked(value))

    def _lighten_color(self, color_hex: str) -> str:
        """Lighten a hex color for hover state."""
        if color_hex.startswith("#"):
            color_hex = color_hex[1:]
        r = int(color_hex[0:2], 16)
        g = int(color_hex[2:4], 16)
        b = int(color_hex[4:6], 16)

        r = min(255, r + 30)
        g = min(255, g + 30)
        b = min(255, b + 30)

        return f"#{r:02X}{g:02X}{b:02X}"

    def _darken_color(self, color_hex: str) -> str:
        """Darken a hex color for pressed state."""
        if color_hex.startswith("#"):
            color_hex = color_hex[1:]
        r = int(color_hex[0:2], 16)
        g = int(color_hex[2:4], 16)
        b = int(color_hex[4:6], 16)

        r = max(0, r - 30)
        g = max(0, g - 30)
        b = max(0, b - 30)

        return f"#{r:02X}{g:02X}{b:02X}"

    def _rgb_to_hex(self, rgb: tuple[int, int, int]) -> str:
        """Convert RGB tuple to a hex color string."""
        r, g, b = rgb
        return f"#{r:02x}{g:02x}{b:02x}"

    def _on_button_clicked(self, value: int) -> None:
        """Handle number button click."""
        self.selected_value = value
        self.accept()

    def _on_freeform_enter(self) -> None:
        """Handle Enter key in freeform input."""
        text = self.freeform_input.text().strip()
        try:
            value = int(text)
            if value > 0:
                self.selected_value = value
                self.accept()
        except ValueError:
            # Invalid input, ignore
            pass

    def get_value(self) -> int:
        """Return the selected value."""
        return self.selected_value


def show_damage_heal_dialog(parent=None, mode: str = "damage") -> Optional[int]:
    """
    Show the damage/heal dialog and return the selected value if accepted, None if canceled.

    Args:
        parent: Parent widget
        mode: Either "damage" or "heal"

    Returns:
        Selected integer value, or None if canceled
    """
    dialog = DamageHealDialog(parent, mode)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.get_value()
    return None
