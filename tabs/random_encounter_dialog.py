"""
Random Encounter Generator Dialog
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Optional, List
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QSpinBox,
    QPushButton,
    QDialogButtonBox,
    QGroupBox,
    QRadioButton,
    QButtonGroup,
    QCheckBox,
)

# Make sure we can import from the project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if PROJECT_ROOT.exists() and str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules.combatManager import CombatManager  # noqa: E402
from modules import config  # noqa: E402


class RandomEncounterDialog(QDialog):
    """Dialog for generating random encounters."""

    def __init__(self, parent=None, manager: CombatManager = None):
        super().__init__(parent)
        self.manager = manager
        self.generated_monsters = []

        self.setWindowTitle("Random Encounter Generator")
        self.setMinimumWidth(450)
        self.setMinimumHeight(400)

        # Main layout
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Generate Random Encounter")
        title.setStyleSheet("font-weight: bold; font-size: 14pt;")
        layout.addWidget(title)

        # Difficulty selection
        difficulty_group = QGroupBox("Encounter Difficulty")
        difficulty_layout = QVBoxLayout(difficulty_group)

        self.difficulty_group = QButtonGroup(self)

        self.radio_trivial = QRadioButton("Trivial - Easy fight, minimal resources")
        self.radio_easy = QRadioButton("Easy - Minor challenge, some HP/resources")
        self.radio_medium = QRadioButton("Medium - Balanced, moderate challenge")
        self.radio_hard = QRadioButton("Hard - Tough fight, significant resources")
        self.radio_deadly = QRadioButton("Deadly - Life threatening, major resources")

        self.difficulty_group.addButton(self.radio_trivial, 0)
        self.difficulty_group.addButton(self.radio_easy, 1)
        self.difficulty_group.addButton(self.radio_medium, 2)
        self.difficulty_group.addButton(self.radio_hard, 3)
        self.difficulty_group.addButton(self.radio_deadly, 4)

        difficulty_layout.addWidget(self.radio_trivial)
        difficulty_layout.addWidget(self.radio_easy)
        difficulty_layout.addWidget(self.radio_medium)
        difficulty_layout.addWidget(self.radio_hard)
        difficulty_layout.addWidget(self.radio_deadly)

        # Default to medium
        self.radio_medium.setChecked(True)

        layout.addWidget(difficulty_group)

        # Biome selection
        biome_group = QGroupBox("Monster Biome")
        biome_layout = QVBoxLayout(biome_group)

        biome_row = QHBoxLayout()
        biome_row.addWidget(QLabel("Biome:"))

        self.biome_combo = QComboBox()
        self.biome_combo.addItem("All Biomes", "all")
        self.biome_combo.addItem("Random Biome", "random")

        # Add separator
        self.biome_combo.insertSeparator(2)

        biome_row.addWidget(self.biome_combo)
        biome_layout.addLayout(biome_row)

        layout.addWidget(biome_group)

        # Monster count
        count_group = QGroupBox("Number of Monsters")
        count_layout = QHBoxLayout(count_group)

        count_layout.addWidget(QLabel("Monster Count:"))
        self.monster_count_spin = QSpinBox()
        self.monster_count_spin.setMinimum(1)
        self.monster_count_spin.setMaximum(20)
        self.monster_count_spin.setValue(3)
        count_layout.addWidget(self.monster_count_spin)

        # Add "Use Suggested" button
        self.btn_use_suggested = QPushButton("Use Suggested")
        self.btn_use_suggested.setToolTip("Set monster count to suggested value based on difficulty")
        # Suggested counts are heuristic only; user can override freely.
        self.btn_use_suggested.clicked.connect(self._on_use_suggested)
        count_layout.addWidget(self.btn_use_suggested)

        count_layout.addStretch()

        layout.addWidget(count_group)

        # Exclude legendary checkbox
        self.checkbox_exclude_legendary = QCheckBox("Exclude Legendary Monsters")
        self.checkbox_exclude_legendary.setToolTip("Exclude legendary monsters from the random selection")
        self.checkbox_exclude_legendary.setChecked(False)
        layout.addWidget(self.checkbox_exclude_legendary)

        # Info label
        self.info_label = QLabel("")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: gray; font-style: italic; padding: 10px;")
        layout.addWidget(self.info_label)

        layout.addStretch()

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_generate)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Populate biomes from manager's monster library
        self._populate_biomes()

        # Update info when selections change
        self.difficulty_group.buttonClicked.connect(self._update_info)
        self.biome_combo.currentIndexChanged.connect(self._update_info)
        self.monster_count_spin.valueChanged.connect(self._update_info)

        self._update_info()

    def _populate_biomes(self):
        """Populate biome dropdown from monster library."""
        if not self.manager or not self.manager.monster_library:
            return

        # Collect unique biomes
        biomes = set()
        for monster in self.manager.monster_library:
            biome = getattr(monster, "biome", "")
            if biome:
                biomes.add(biome)

        # Add biomes to combo box (sorted)
        for biome in sorted(biomes):
            self.biome_combo.addItem(biome, biome)

    def _get_difficulty_multiplier(self) -> float:
        """Get level multiplier based on difficulty using config values."""
        difficulty_id = self.difficulty_group.checkedId()

        # Use config values for encounter difficulty thresholds
        # Map difficulty levels to midpoints between thresholds
        cfg = config.CONFIG
        multipliers = {
            0: cfg.encounter_difficulty_easy * 0.8,       # Trivial - below Easy threshold
            1: cfg.encounter_difficulty_easy,             # Easy
            2: cfg.encounter_difficulty_medium,           # Medium
            3: cfg.encounter_difficulty_hard,             # Hard
            4: cfg.encounter_difficulty_deadly_max,       # Deadly
        }

        return multipliers.get(difficulty_id, cfg.encounter_difficulty_medium)

    def _get_party_total_level(self) -> int:
        """Calculate total party level (sum of all hero levels)."""
        if not self.manager or not self.manager.heroes:
            return 1  # Default to level 1

        total_level = sum(hero.level for hero in self.manager.heroes)
        return max(1, total_level)

    def _get_suggested_creature_count(self) -> int:
        """Suggest number of creatures based on difficulty and party size."""
        if not self.manager or not self.manager.heroes:
            return 3  # Default suggestion

        party_size = len(self.manager.heroes)
        difficulty_id = self.difficulty_group.checkedId()

        # Suggested creature counts based on difficulty and party size
        # Trivial: fewer creatures, easier fight
        # Easy: balanced against smaller group
        # Medium: roughly equal to party
        # Hard: outnumber party slightly
        # Deadly: significantly outnumber party
        suggestions = {
            0: max(1, party_size - 2),      # Trivial: 2 fewer than party (min 1)
            1: max(1, party_size - 1),      # Easy: 1 fewer than party (min 1)
            2: party_size,                  # Medium: equal to party
            3: party_size + 1,              # Hard: 1 more than party
            4: party_size + 2,              # Deadly: 2 more than party
        }

        return suggestions.get(difficulty_id, party_size)

    def _on_use_suggested(self):
        """Set the monster count to the suggested value."""
        suggested = self._get_suggested_creature_count()
        self.monster_count_spin.setValue(suggested)

    def _update_info(self):
        """Update info label with current selections."""
        if not self.manager or not self.manager.monster_library:
            self.info_label.setText("⚠ No monster library loaded. Load monsters from the Bestiary tab first.")
            return

        difficulty_id = self.difficulty_group.checkedId()
        difficulty_names = ["Trivial", "Easy", "Medium", "Hard", "Deadly"]
        difficulty = difficulty_names[difficulty_id] if 0 <= difficulty_id < len(difficulty_names) else "Medium"

        biome_data = self.biome_combo.currentData()
        biome_text = "any biome" if biome_data == "all" else (
            "a random biome" if biome_data == "random" else f"{biome_data}"
        )

        count = self.monster_count_spin.value()
        suggested_count = self._get_suggested_creature_count()

        party_total_level = self._get_party_total_level()
        party_size = len(self.manager.heroes) if self.manager and self.manager.heroes else 0
        multiplier = self._get_difficulty_multiplier()
        target_total_level = int(party_total_level * multiplier)

        # Build info message
        info_parts = [
            f"Will generate {count} monster(s) from {biome_text}.",
            f"Difficulty: {difficulty} (Party total: {party_total_level} levels, Target encounter total: {target_total_level} levels)"
        ]

        # Add suggestion if different from current count
        if count != suggested_count:
            info_parts.append(f"💡 Suggested: {suggested_count} creatures for this difficulty")

        self.info_label.setText("\n".join(info_parts))

    def _on_generate(self):
        """Generate the encounter."""
        if not self.manager or not self.manager.monster_library:
            self.info_label.setText("⚠ Cannot generate encounter - no monsters loaded!")
            return

        # Get parameters
        count = self.monster_count_spin.value()
        biome_data = self.biome_combo.currentData()
        difficulty_multiplier = self._get_difficulty_multiplier()
        party_total_level = self._get_party_total_level()

        # Calculate target total levels for the encounter (based on party total, not per monster)
        target_total_levels = int(party_total_level * difficulty_multiplier)

        # Filter monsters by biome
        available_monsters = []

        if biome_data == "all":
            # All monsters
            available_monsters = list(self.manager.monster_library)
        elif biome_data == "random":
            # Pick a random biome first
            biomes = set()
            for monster in self.manager.monster_library:
                biome = getattr(monster, "biome", "")
                if biome:
                    biomes.add(biome)

            if biomes:
                selected_biome = random.choice(list(biomes))
                available_monsters = [
                    m for m in self.manager.monster_library
                    if getattr(m, "biome", "") == selected_biome
                ]
        else:
            # Specific biome
            available_monsters = [
                m for m in self.manager.monster_library
                if getattr(m, "biome", "") == biome_data
            ]

        if not available_monsters:
            self.info_label.setText("⚠ No monsters found matching criteria!")
            return

        # Filter out legendary monsters if checkbox is checked
        exclude_legendary = self.checkbox_exclude_legendary.isChecked()
        if exclude_legendary:
            available_monsters = [
                m for m in available_monsters
                if not getattr(m, "is_legendary", False)
            ]

        if not available_monsters:
            self.info_label.setText("⚠ No non-legendary monsters found matching criteria!")
            return

        # Normalize monster levels to int (fix TypeError if levels are stored as strings)
        normalized_monsters = []
        for m in available_monsters:
            try:
                level = int(m.level) if isinstance(m.level, str) else m.level
                if level > 0:
                    normalized_monsters.append((m, level))
            except (ValueError, AttributeError):
                # Skip monsters with invalid levels
                continue

        if not normalized_monsters:
            self.info_label.setText("⚠ No valid monsters found!")
            return

        # Select monsters whose levels sum to approximately the target total
        # Use a greedy algorithm: repeatedly pick random monsters whose level fits the remaining budget
        self.generated_monsters = []
        remaining_levels = target_total_levels

        for i in range(count):
            if not normalized_monsters:
                break

            # Calculate target level for this monster (remaining budget / remaining slots)
            remaining_slots = count - i
            avg_remaining = max(1, remaining_levels // remaining_slots)

            # Find monsters within reasonable range of the target
            # Allow ±50% of average remaining, but ensure at least level 1
            min_level = max(1, int(avg_remaining * 0.5))
            max_level = int(avg_remaining * 1.5) if avg_remaining > 1 else avg_remaining + 1

            candidates = [
                (m, level) for m, level in normalized_monsters
                if min_level <= level <= max_level
            ]

            # If no candidates in range, pick from all available
            if not candidates:
                candidates = normalized_monsters

            # Randomly select from candidates
            selected_monster, selected_level = random.choice(candidates)
            self.generated_monsters.append(selected_monster)
            remaining_levels -= selected_level

        # Accept the dialog
        self.accept()

    def get_generated_monsters(self) -> List:
        """Return the list of generated monster templates."""
        return self.generated_monsters


def show_random_encounter_dialog(parent=None, manager: CombatManager = None) -> Optional[List]:
    """
    Show the random encounter generator dialog.

    Returns:
        List of monster templates if accepted, None if canceled.
    """
    dialog = RandomEncounterDialog(parent, manager)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.get_generated_monsters()
    return None
