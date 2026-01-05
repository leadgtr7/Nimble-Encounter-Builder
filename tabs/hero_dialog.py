"""
Hero dialog: allows creating or editing hero metadata via addEditHero.ui.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, List
import sys

from PySide6.QtCore import QFile, QIODevice
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLineEdit,
    QSpinBox,
    QTextEdit,
)
from PySide6.QtUiTools import QUiLoader

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if PROJECT_ROOT.exists() and str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules.combatants import Hero  # noqa: E402


class AddEditHeroDialog(QDialog):
    """Dialog backed by addEditHero.ui."""

    def __init__(self, parent=None, hero: Optional[Hero] = None):
        super().__init__(parent)

        ui_path = PROJECT_ROOT / "uiDesign" / "addEditHero.ui"
        loader = QUiLoader()
        ui_file = QFile(str(ui_path))
        if not ui_file.open(QIODevice.OpenModeFlag.ReadOnly):
            raise RuntimeError(f"Cannot open UI file: {ui_path}")
        ui_widget = loader.load(ui_file)
        ui_file.close()

        if ui_widget is None:
            raise RuntimeError(f"Failed to load UI from: {ui_path}")

        # Use the loaded UI layout as this dialog's content.
        self.setLayout(ui_widget.layout())
        self.setWindowTitle("Add / Edit Hero")

        self.line_name: QLineEdit = self.findChild(QLineEdit, "lineEdit_name")
        self.line_player: QLineEdit = self.findChild(QLineEdit, "lineEdit_player")
        self.line_class: QLineEdit = self.findChild(QLineEdit, "lineEdit_class")
        self.line_faction: QLineEdit = self.findChild(QLineEdit, "lineEdit_faction")
        self.line_resource_name: QLineEdit = self.findChild(QLineEdit, "lineEdit_resource_name")
        self.line_conditions: QLineEdit = self.findChild(QLineEdit, "lineEdit_conditions")
        self.spin_level: QSpinBox = self.findChild(QSpinBox, "spinBox_level")
        self.spin_hp_max: QSpinBox = self.findChild(QSpinBox, "spinBox_hp_max")
        self.spin_hp_current: QSpinBox = self.findChild(QSpinBox, "spinBox_hp_current")
        self.spin_temp_hp: QSpinBox = self.findChild(QSpinBox, "spinBox_temp_hp")
        self.spin_resource_current: QSpinBox = self.findChild(
            QSpinBox, "spinBox_resource_current"
        )
        self.spin_resource_max: QSpinBox = self.findChild(QSpinBox, "spinBox_resource_max")
        self.text_notes_public: QTextEdit = self.findChild(QTextEdit, "textEdit_notes_public")
        self.text_notes_gm: QTextEdit = self.findChild(QTextEdit, "textEdit_notes_gm")
        self.button_box: QDialogButtonBox = self.findChild(QDialogButtonBox, "buttonBox")

        required = (
            self.line_name,
            self.spin_level,
            self.spin_hp_max,
            self.spin_hp_current,
            self.spin_temp_hp,
            self.line_resource_name,
            self.spin_resource_current,
            self.spin_resource_max,
            self.line_conditions,
            self.button_box,
        )
        if any(widget is None for widget in required):
            raise RuntimeError("addEditHero.ui is missing required widgets.")

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        if hero is not None:
            self._populate(hero)

    def _populate(self, hero: Hero) -> None:
        """Fill the dialog with values from an existing hero."""
        self.line_name.setText(hero.name)
        self.line_player.setText(hero.player)
        self.line_class.setText(hero.class_name)
        self.line_faction.setText(hero.faction)
        self.spin_level.setValue(hero.level)
        self.spin_hp_max.setValue(hero.hp_max)
        self.spin_hp_current.setValue(hero.hp_current)
        self.spin_temp_hp.setValue(hero.temp_hp)
        self.line_resource_name.setText(hero.resource_1_name)
        self.spin_resource_current.setValue(hero.resource_1_current)
        self.spin_resource_max.setValue(hero.resource_1_max)
        self.line_conditions.setText(", ".join(hero.conditions))
        self.text_notes_public.setPlainText(hero.notes_public)
        self.text_notes_gm.setPlainText(hero.notes_gm)

    def get_hero(self) -> Hero:
        """Return a Hero constructed from the current form values."""
        name = self.line_name.text().strip() or "New Hero"
        hero = Hero.new(name)
        hero.player = self.line_player.text().strip()
        hero.class_name = self.line_class.text().strip()
        hero.faction = self.line_faction.text().strip() or "Heroes"
        hero.level = self.spin_level.value()
        hero.hp_max = self.spin_hp_max.value()
        hero.hp_current = min(self.spin_hp_current.value(), hero.hp_max)
        hero.temp_hp = self.spin_temp_hp.value()
        hero.resource_1_name = self.line_resource_name.text().strip()
        hero.resource_1_current = self.spin_resource_current.value()
        hero.resource_1_max = self.spin_resource_max.value()
        hero.conditions = self._parse_conditions()
        hero.notes_public = self.text_notes_public.toPlainText().strip()
        hero.notes_gm = self.text_notes_gm.toPlainText().strip()
        return hero

    def _parse_conditions(self) -> List[str]:
        raw = self.line_conditions.text()
        parts = [part.strip() for part in raw.split(",") if part.strip()]
        return parts


def show_add_edit_hero_dialog(parent=None, hero: Optional[Hero] = None) -> Optional[Hero]:
    """
    Show the hero dialog and return a new Hero if accepted, otherwise None.
    """
    dialog = AddEditHeroDialog(parent, hero=hero)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.get_hero()
    return None
