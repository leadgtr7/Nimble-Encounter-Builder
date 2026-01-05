"""
Add/Edit Monster dialog for the Combat tab.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Optional
import sys

from PySide6.QtCore import QFile, QIODevice, Qt
from PySide6.QtWidgets import (
    QCompleter,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QComboBox,
    QCheckBox,
    QPlainTextEdit,
    QGroupBox,
)
from PySide6.QtUiTools import QUiLoader

PROJECT_ROOT = Path(__file__).resolve().parents[1]
for _path in (PROJECT_ROOT,):
    if _path.exists() and str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from modules.combatManager import CombatManager  # noqa: E402
from modules.combatants import MonsterInstance, MonsterTemplate  # noqa: E402


def show_add_edit_monster_dialog(
    manager: CombatManager,
    monster: Optional[MonsterInstance] = None,
    parent=None,
) -> Optional[MonsterInstance]:
    """
    Show the add/edit monster dialog.

    Args:
        manager: CombatManager instance (for accessing monster library)
        monster: Existing monster to edit, or None to add new
        parent: Parent widget

    Returns:
        MonsterInstance if user clicked OK, None if cancelled
    """
    # Load UI
    ui_path = PROJECT_ROOT / "uiDesign" / "addEditMonster.ui"
    loader = QUiLoader()
    ui_file = QFile(str(ui_path))
    if not ui_file.open(QIODevice.OpenModeFlag.ReadOnly):
        return None
    dialog: QDialog = loader.load(ui_file, parent)
    ui_file.close()

    if dialog is None:
        return None

    # Find widgets
    name_edit = dialog.findChild(QLineEdit, "monsterNameEdit")
    hp_spin = dialog.findChild(QSpinBox, "hpSpin")
    level_spin = dialog.findChild(QDoubleSpinBox, "levelSpin")
    armor_combo = dialog.findChild(QComboBox, "armorCombo")
    speed_edit = dialog.findChild(QLineEdit, "speedEdit")
    size_combo = dialog.findChild(QComboBox, "sizeCombo")
    type_combo = dialog.findChild(QComboBox, "typeCombo")
    biome_edit = dialog.findChild(QLineEdit, "biomeEdit")
    saves_edit = dialog.findChild(QLineEdit, "savesEdit")
    flavor_edit = dialog.findChild(QPlainTextEdit, "flavorEdit")
    actions_edit = dialog.findChild(QPlainTextEdit, "actionsEdit")
    special_edit = dialog.findChild(QPlainTextEdit, "specialActionsEdit")
    bloodied_edit = dialog.findChild(QPlainTextEdit, "bloodiedEdit")
    last_stand_edit = dialog.findChild(QPlainTextEdit, "lastStandEdit")
    last_stand_hp_spin = dialog.findChild(QSpinBox, "lastStandHpSpin")
    loot_edit = dialog.findChild(QPlainTextEdit, "lootEdit")
    legendary_checkbox = dialog.findChild(QCheckBox, "legendaryCheck")
    group_edit = dialog.findChild(QLineEdit, "groupEdit")
    legendary_groupbox = dialog.findChild(QGroupBox, "groupBox_legendary")

    # Function to show/hide legendary abilities section
    def update_legendary_visibility():
        if legendary_groupbox:
            legendary_groupbox.setVisible(legendary_checkbox.isChecked())

    # Connect legendary checkbox to show/hide legendary abilities
    if legendary_checkbox:
        legendary_checkbox.toggled.connect(update_legendary_visibility)
        # Set initial visibility
        update_legendary_visibility()

    # Connect dialog buttons
    button_box = dialog.findChild(QDialogButtonBox, "buttonBox")
    if button_box:
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

    def _level_to_spin_value(value) -> float:
        # Accept numeric, string, or fractional levels and clamp to non-negative.
        if isinstance(value, (int, float)):
            return max(0.0, float(value))
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return 0.0
            token = raw.split()[0]
            try:
                if "/" in token:
                    return max(0.0, float(Fraction(token)))
                return max(0.0, float(token))
            except (ValueError, ZeroDivisionError):
                return 0.0
        return 0.0

    # Setup autocomplete for monster name using library templates.
    if manager.monster_library:
        monster_names = [t.name for t in manager.monster_library]
        completer = QCompleter(monster_names)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        name_edit.setCompleter(completer)

        # Connect to auto-fill on selection
        def on_name_selected(name: str):
            # Find template in library to auto-fill dialog fields.
            template = None
            for t in manager.monster_library:
                if t.name == name:
                    template = t
                    break

            if template:
                # Auto-fill all fields from template; treat template as read-only.
                # Parse HP (template.hp is a string like "50" or "40-60")
                try:
                    hp_val = int(template.hp.split("-")[0]) if template.hp else 1
                except (ValueError, AttributeError):
                    hp_val = 1
                hp_spin.setValue(hp_val)

                # Parse level
                level_spin.setValue(_level_to_spin_value(template.level))

                # Set combo boxes
                armor_index = armor_combo.findText(template.armor or "None")
                if armor_index >= 0:
                    armor_combo.setCurrentIndex(armor_index)

                size_index = size_combo.findText(template.size or "Medium")
                if size_index >= 0:
                    size_combo.setCurrentIndex(size_index)

                type_index = type_combo.findText(template.type or "Monsters")
                if type_index >= 0:
                    type_combo.setCurrentIndex(type_index)

                speed_edit.setText(template.speed or "")
                biome_edit.setText(template.biome or "")
                saves_edit.setText(template.saves or "")
                flavor_edit.setPlainText(template.flavor or "")

                # Join lists to text
                actions_edit.setPlainText("\n".join(template.actions or []))
                special_edit.setPlainText("\n".join(template.special_actions or []))
                loot_edit.setPlainText("\n".join(template.biome_loot or []))

                # Template uses different field names than instance
                bloodied_edit.setPlainText(template.bloodied or "")
                last_stand_edit.setPlainText(template.last_stand or "")

                # Parse last_stand_hp (template.last_stand_hp is a string)
                try:
                    ls_hp = int(template.last_stand_hp) if template.last_stand_hp else 0
                except (ValueError, AttributeError):
                    ls_hp = 0
                last_stand_hp_spin.setValue(ls_hp)

                legendary_checkbox.setChecked(template.legendary)

                # Set group to biome or type
                group_edit.setText(template.biome or template.type or "")

        completer.activated.connect(on_name_selected)

    # If editing existing monster, populate fields
    if monster:
        dialog.setWindowTitle("Edit Monster")
        name_edit.setText(monster.name or "")
        hp_spin.setValue(monster.hp_max)
        level_spin.setValue(_level_to_spin_value(monster.level))

        armor_index = armor_combo.findText(monster.armor or "None")
        if armor_index >= 0:
            armor_combo.setCurrentIndex(armor_index)

        size_index = size_combo.findText(monster.size or "Medium")
        if size_index >= 0:
            size_combo.setCurrentIndex(size_index)

        type_index = type_combo.findText(monster.type or "Monsters")
        if type_index >= 0:
            type_combo.setCurrentIndex(type_index)

        speed_edit.setText(monster.speed or "")
        biome_edit.setText(monster.biome or "")
        saves_edit.setText(monster.saves or "")
        flavor_edit.setPlainText(monster.flavor or "")
        actions_edit.setPlainText("\n".join(monster.actions or []))
        special_edit.setPlainText("\n".join(monster.special_actions or []))
        loot_edit.setPlainText("\n".join(monster.biome_loot or []))
        bloodied_edit.setPlainText(monster.bloodied_text or "")
        last_stand_edit.setPlainText(monster.last_stand_text or "")
        last_stand_hp_spin.setValue(monster.last_stand_hp_value or 0)
        legendary_checkbox.setChecked(monster.legendary)
        group_edit.setText(monster.group or "")
    else:
        dialog.setWindowTitle("Add Monster")

    # Show dialog
    result = dialog.exec()

    if result != QDialog.DialogCode.Accepted:
        return None

    # Create or update monster
    if monster is None:
        monster = MonsterInstance(
            name=name_edit.text() or "New Monster",
            template_file="",  # Custom monster, no template file
            hp_max=hp_spin.value(),
            level=str(level_spin.value()),
            armor=armor_combo.currentText(),
            speed=speed_edit.text(),
            size=size_combo.currentText(),
            type=type_combo.currentText(),
            biome=biome_edit.text(),
            saves=saves_edit.text(),
            flavor=flavor_edit.toPlainText(),
            actions=[line for line in actions_edit.toPlainText().split("\n") if line.strip()],
            special_actions=[line for line in special_edit.toPlainText().split("\n") if line.strip()],
            bloodied_text=bloodied_edit.toPlainText(),
            last_stand_text=last_stand_edit.toPlainText(),
            last_stand_hp_value=last_stand_hp_spin.value(),
            biome_loot=[line for line in loot_edit.toPlainText().split("\n") if line.strip()],
            legendary=legendary_checkbox.isChecked(),
            group=group_edit.text() or biome_edit.text() or type_combo.currentText(),
            hp_current=hp_spin.value(),
            temp_hp=0,
            last_stand_triggered=False,
            dead=False,
            active=True,
            concentrating=False,
            conditions=[],
            notes_public="",
            notes_gm="",
            marker_color="",
            marker_number=0,
        )
    else:
        # Update existing monster
        monster.name = name_edit.text() or "New Monster"
        monster.hp_max = hp_spin.value()
        monster.level = str(level_spin.value())
        monster.armor = armor_combo.currentText()
        monster.speed = speed_edit.text()
        monster.size = size_combo.currentText()
        monster.type = type_combo.currentText()
        monster.biome = biome_edit.text()
        monster.saves = saves_edit.text()
        monster.flavor = flavor_edit.toPlainText()
        monster.actions = [line for line in actions_edit.toPlainText().split("\n") if line.strip()]
        monster.special_actions = [line for line in special_edit.toPlainText().split("\n") if line.strip()]
        monster.bloodied_text = bloodied_edit.toPlainText()
        monster.last_stand_text = last_stand_edit.toPlainText()
        monster.last_stand_hp_value = last_stand_hp_spin.value()
        monster.biome_loot = [line for line in loot_edit.toPlainText().split("\n") if line.strip()]
        monster.legendary = legendary_checkbox.isChecked()
        monster.group = group_edit.text() or biome_edit.text() or type_combo.currentText()

    return monster
