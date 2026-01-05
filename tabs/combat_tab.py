"""
Combat tab controller: keeps the combat monsters table in sync with CombatManager.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QWidget,
    QHBoxLayout,
)

# Make sure we can import CombatManager from the project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_UI_DIR = PROJECT_ROOT
for _path in (PROJECT_ROOT,):
    if _path.exists() and str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from modules.combatManager import CombatManager  # noqa: E402
from modules.combatants import MonsterInstance  # noqa: E402
from modules.config import CONFIG  # noqa: E402
from tabs.marker_dialog import show_marker_dialog  # noqa: E402
from tabs.bulk_marker_dialog import show_bulk_marker_dialog  # noqa: E402
from tabs.conditions_dialog import show_conditions_dialog  # noqa: E402
from tabs.damage_heal_dialog import show_damage_heal_dialog  # noqa: E402
from modules.condition_descriptions import CONDITION_DESCRIPTIONS  # noqa: E402
from modules.shared_statblock import render_stat_block  # noqa: E402


def calculate_text_color(bg_hex: str) -> QColor:
    """Calculate contrasting text color (black or white) based on background luminosity."""
    try:
        color = QColor(bg_hex)
        # Calculate relative luminosity using ITU-R BT.709 formula
        r, g, b = color.red(), color.green(), color.blue()
        luminosity = 0.2126 * r + 0.7152 * g + 0.0722 * b
        # Use black text for light backgrounds, white for dark
        return QColor("black") if luminosity > 128 else QColor("white")
    except Exception:
        return QColor("black")  # Default to black on error

# Column indices for monsters_table_combat (10 columns)
COMBAT_COL_ACTIVE = 0
COMBAT_COL_HEAL = 1
COMBAT_COL_NAME = 2
COMBAT_COL_MARKER = 4
COMBAT_COL_HURT = 3
COMBAT_COL_CON = 5
COMBAT_COL_CONDS = 6
COMBAT_COL_HP = 7
COMBAT_COL_TMP = 8
COMBAT_COL_MAX = 9


class CombatTabController:
    """Manage the Combat tab monster table view."""

    def __init__(
        self,
        manager: CombatManager,
        table: QTableWidget,
        stat_preview: Optional[QTextEdit] = None,
        loot_view: Optional[QTextEdit] = None,
        btn_reset: Optional[QPushButton] = None,
        label_difficulty: Optional[QLabel] = None,
        btn_add: Optional[QPushButton] = None,
        btn_delete: Optional[QPushButton] = None,
        btn_clear: Optional[QPushButton] = None,
        btn_set_color: Optional[QPushButton] = None,
    ):
        self.manager = manager
        self.table = table
        self.stat_preview = stat_preview
        self.loot_view = loot_view
        self.btn_reset = btn_reset
        self.label_difficulty = label_difficulty
        self.btn_add = btn_add
        self.btn_delete = btn_delete
        self.btn_clear = btn_clear
        self.btn_set_color = btn_set_color
        self._last_selected_index: Optional[int] = None
        self._dialog_open = False  # Flag to prevent multiple dialogs
        self._current_sorted_monsters: list[MonsterInstance] = []

        # Ensure we have the expected number of columns
        if self.table.columnCount() < 10:
            self.table.setColumnCount(10)

        header = self.table.horizontalHeader()

        # Strip padding so narrow columns can actually be narrow, add horizontal grid lines
        self.table.setStyleSheet("""
        QHeaderView::section {
            padding-left: 0px;
            padding-right: 0px;
            border-bottom: 2px solid #4a4a4a;
        }
        QTableWidget {
            gridline-color: #3a3a3a;
            padding: 0px;
        }
        QTableWidget::item {
            padding-left: 0px;
            padding-right: 0px;
        }
        """)

        # Set minimum section size first
        header.setMinimumSectionSize(1)

        # Increase row height for better readability
        self.table.verticalHeader().setDefaultSectionSize(28)

        # Set each column to Fixed mode individually, then apply width
        for col in range(self.table.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)

        # Apply width dict once at startup
        self._apply_column_widths()

        # Connect double-click handler for marker and conditions columns
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)

        # Connect click handler for heal and hurt columns
        self.table.cellClicked.connect(self._on_cell_clicked)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

        # Connect reset combat button
        if self.btn_reset:
            self.btn_reset.clicked.connect(self._on_reset_combat)

        # Connect add/delete monster buttons
        if self.btn_add:
            self.btn_add.clicked.connect(self._on_add_monster)
        if self.btn_delete:
            self.btn_delete.clicked.connect(self._on_delete_monster)

        # Connect clear encounter button
        if self.btn_clear:
            self.btn_clear.clicked.connect(self._on_clear_encounter)

        # Connect set color button
        if self.btn_set_color:
            self.btn_set_color.clicked.connect(self._on_set_color_for_selected)

    def _on_selection_changed(self) -> None:
        """Update the stat preview to reflect the currently selected monster."""
        row = self.table.currentRow()

        monsters = self._current_sorted_monsters or self._sorted_monsters()
        if not self._current_sorted_monsters:
            self._current_sorted_monsters = monsters

        if row < 0 or row >= len(monsters):
            self._last_selected_index = None
            self._update_stat_preview(None)
            return

        self._last_selected_index = row
        monster = monsters[row]
        self._update_stat_preview(monster)

    def _update_stat_preview(self, monster: Optional[MonsterInstance]) -> None:
        """Render the selected monster into the preview pane."""
        if not self.stat_preview:
            return
        if monster is None:
            self.stat_preview.clear()
            return
        html = render_stat_block(monster, mode="lite")
        self.stat_preview.setHtml(html)

    def _sorted_monsters(self) -> list[MonsterInstance]:
        """Return the list of monsters ordered the same way as the table."""
        return sorted(
            self.manager.monsters,
            key=lambda m: (
                getattr(m, "is_dead", False),
                not getattr(m, "active", True),
                not getattr(m, "legendary", False),
            )
        )

    def _monster_at_row(self, row: int) -> Optional[MonsterInstance]:
        """Return the monster that should appear at the given table row."""
        if 0 <= row < len(self._current_sorted_monsters):
            return self._current_sorted_monsters[row]
        return None

    # ------------------------------------------------------------------#
    # Public entry points
    # ------------------------------------------------------------------#

    def refresh_table(self) -> None:
        """Rebuild the table from the current monsters in CombatManager."""
        monsters = self._sorted_monsters()
        self._current_sorted_monsters = monsters
        self.table.setRowCount(len(monsters))

        for row, m in enumerate(monsters):
            is_active = getattr(m, "active", True)
            is_legendary = getattr(m, "legendary", False)

            # Clear any stale formatting from previous refresh
            self._clear_row_formatting(row)

            # Active column - checkbox (pass monster reference for correct handling after sorting)
            self._set_checkbox(row, COMBAT_COL_ACTIVE, is_active, monster=m)

            # Heal column - green heart emoji
            self._set_item(row, COMBAT_COL_HEAL, "💚")

            # Name (legendary formatting applied after alternating)
            name_item = self._set_item(row, COMBAT_COL_NAME, getattr(m, "name", ""))

            # Hurt column - crossed swords emoji
            self._set_item(row, COMBAT_COL_HURT, "⚔")

            # Marker (number only, colors applied after alternating)
            marker_color = getattr(m, "marker_color", "")
            marker_number = getattr(m, "marker_number", 0)
            marker_text = str(marker_number) if marker_number else ""
            marker_item = self._set_item(row, COMBAT_COL_MARKER, marker_text)
            if marker_item is not None:
                # Make text bold and center-aligned
                font = QFont()
                font.setBold(True)
                font.setPointSize(CONFIG.monster_table_font_size)
                marker_item.setFont(font)
                marker_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Concentrating column - checkbox (pass monster reference)
            self._set_checkbox(row, COMBAT_COL_CON, getattr(m, "concentrating", False), monster=m)

            # Conditions (comma-separated) - show blank if no conditions
            conditions = getattr(m, "conditions", [])
            if conditions is None:
                conditions = []

            # Create Tmp and Max items
            self._set_item(row, COMBAT_COL_TMP, str(getattr(m, "temp_hp", 0)))
            self._set_item(row, COMBAT_COL_MAX, str(getattr(m, "hp_max", 0)))

            if name_item and is_legendary:
                # Legendary monsters: dark blue background with white text (matches label_legendary)
                name_item.setBackground(QColor(0, 0, 127))  # Dark blue
                name_item.setForeground(QColor("white"))
                font = QFont()
                font.setBold(True)
                font.setPointSize(CONFIG.monster_table_font_size)
                name_item.setFont(font)
                self._maybe_show_legendary_mode(m)

            if marker_item is not None:
                if marker_color:
                    try:
                        marker_item.setBackground(QColor(marker_color))
                        # Set contrasting text color
                        text_color = calculate_text_color(marker_color)
                        marker_item.setForeground(text_color)
                    except Exception:
                        marker_item.setBackground(QColor("white"))
                        marker_item.setForeground(QColor("black"))
                # If no marker color, use transparent background
                # (removed else block that referenced undefined row_color)

            # Reapply condition coloring after alternating
            self._set_conditions_cell(row, conditions, COMBAT_COL_CONDS)

            # HP (effective_hp = current + temp), Temp, Max - with health state highlighting
            hp_item = self._set_item(row, COMBAT_COL_HP, str(getattr(m, "effective_hp", 0)))
            if hp_item:
                # Make HP bold
                font = QFont()
                font.setBold(True)
                font.setPointSize(CONFIG.monster_table_font_size)
                hp_item.setFont(font)

                # Determine health state and apply colors from CONFIG
                if getattr(m, "is_dying", False) or getattr(m, "is_dead", False):
                    # Down/Dead
                    hp_item.setBackground(QColor(*CONFIG.hp_down_color))
                    hp_item.setForeground(QColor("white"))
                elif getattr(m, "is_critical", False):
                    # Critical
                    hp_item.setBackground(QColor(*CONFIG.hp_critical_color))
                    hp_item.setForeground(QColor("white"))
                elif getattr(m, "is_bloodied", False):
                    # Bloodied
                    hp_item.setBackground(QColor(*CONFIG.hp_bloodied_color))
                    hp_item.setForeground(QColor("white"))
                else:
                    # Healthy
                    hp_item.setBackground(QColor(*CONFIG.hp_healthy_color))
                    hp_item.setForeground(QColor("white"))

            # Apply or clear inactive row styling based on active state (will override alternating colors if needed)
            if not is_active:
                self._apply_inactive_row_style(row)
            else:
                self._clear_inactive_row_style(row)

        # NOTE: we do NOT call _apply_column_widths() here,
        # so widths are not constantly reset on every refresh.

        if not monsters:
            self._last_selected_index = None
            self.table.clearSelection()
            self._update_stat_preview(None)
        else:
            target_row = self._last_selected_index if self._last_selected_index is not None else 0
            if target_row >= len(monsters):
                target_row = 0
            self.table.selectRow(target_row)

        self._update_loot_notes()
        self._update_difficulty_label()

    # ------------------------------------------------------------------#
    # Helpers
    # ------------------------------------------------------------------#

    def _update_difficulty_label(self) -> None:
        """Update the difficulty label based on current encounter."""
        if not self.label_difficulty:
            return

        from modules.config import CONFIG

        difficulty = self.manager.encounter_difficulty_label()
        ratio = self.manager.encounter_difficulty_ratio()

        # Format text with percentage
        if ratio > 0:
            percentage = int(ratio * 100)
            text = f"{difficulty} ({percentage}%)"
        else:
            text = difficulty

        self.label_difficulty.setText(text)

        # Set tooltip with difficulty explanation
        tooltip_map = {
            "No Encounter": "No active monsters in the encounter.",
            "Easy": "Heroes will lose minimal HP and resources. Great for testing new abilities or gauging progress.",
            "Medium": "Expect some HP loss and moderate resource expenditure. Heroes will get hurt but shouldn't drop to 0 HP.",
            "Hard": "Challenging but fair. Heroes must use significant resources; some may drop to 0 HP, but none should die barring poor tactics or bad luck.",
            "Deadly": "Requires strategic thinking and teamwork. Suitable for tough battles, well-equipped parties, or campaign bosses.",
            "Very Deadly": "Extremely dangerous. Unless heroes are well optimized and play exquisitely, they will almost certainly need to retreat—or die.",
        }
        tooltip = tooltip_map.get(difficulty, "")
        self.label_difficulty.setToolTip(tooltip)

        # Get background color from config based on difficulty
        color_map = {
            "No Encounter": (50, 50, 50),
            "Easy": CONFIG.difficulty_color_easy,
            "Medium": CONFIG.difficulty_color_medium,
            "Hard": CONFIG.difficulty_color_hard,
            "Deadly": CONFIG.difficulty_color_deadly,
            "Very Deadly": CONFIG.difficulty_color_very_deadly,
        }

        bg_color = color_map.get(difficulty, (50, 50, 50))

        # Calculate contrasting text color
        text_color = calculate_text_color(f"#{bg_color[0]:02x}{bg_color[1]:02x}{bg_color[2]:02x}")

        # Match the style from label_encounter_diff in UI (with border and border-radius)
        style = f"""QLabel {{
    background-color: rgb({bg_color[0]}, {bg_color[1]}, {bg_color[2]});
    color: {text_color.name()};
    font-weight: bold;
    border: 2px solid white;
    border-radius: 6px;
}}"""
        self.label_difficulty.setStyleSheet(style)

    def _clear_row_formatting(self, row: int) -> None:
        """Clear all formatting from a row (to prevent stale formatting after sorting)."""
        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item is not None:
                item.setData(Qt.ItemDataRole.BackgroundRole, None)
                item.setData(Qt.ItemDataRole.ForegroundRole, None)
                item.setData(Qt.ItemDataRole.FontRole, None)


    def _wrap_text(self, text: str, width: int) -> str:
        """Wrap text to a specified character width."""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            if current_length + len(word) + len(current_line) > width:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                    current_length = len(word)
                else:
                    lines.append(word)
                    current_length = 0
            else:
                current_line.append(word)
                current_length += len(word)

        if current_line:
            lines.append(" ".join(current_line))

        return "<br>".join(lines)

    def _apply_inactive_row_style(self, row: int) -> None:
        """Apply gray/dimmed styling to an entire row for inactive monsters."""
        # Match label_inactive: gray background (113, 113, 113) with blue text
        bg_gray = QColor(113, 113, 113)  # Gray background
        text_blue = QColor("blue")  # Blue text
        bg_style = f"background-color: rgb({bg_gray.red()}, {bg_gray.green()}, {bg_gray.blue()});"

        # Skip columns that have special styling we want to preserve
        # HP column has health state colors, Marker has color backgrounds
        skip_cols = {COMBAT_COL_HP, COMBAT_COL_MARKER, COMBAT_COL_NAME}  # Keep special colors visible (HP status, markers, legendary)

        for col in range(self.table.columnCount()):
            if col in skip_cols:
                continue

            # Handle regular table items
            item = self.table.item(row, col)
            if item is not None:
                # Apply gray background and blue text (matches label_inactive)
                item.setBackground(bg_gray)
                item.setForeground(text_blue)

            # Handle cell widgets (checkboxes for Active and Concentrating columns)
            widget = self.table.cellWidget(row, col)
            if widget is not None:
                widget.setStyleSheet(bg_style)

    def _clear_inactive_row_style(self, row: int) -> None:
        """Clear inactive styling from a row (used when monster becomes active again)."""
        # Clear the gray background by resetting all cell backgrounds to transparent
        skip_cols = {COMBAT_COL_HP, COMBAT_COL_MARKER, COMBAT_COL_NAME}  # Keep special colors

        for col in range(self.table.columnCount()):
            if col in skip_cols:
                continue

            item = self.table.item(row, col)
            if item is not None:
                item.setBackground(QColor(0, 0, 0, 0))  # Transparent
                item.setForeground(QColor("white"))

            widget = self.table.cellWidget(row, col)
            if widget is not None:
                widget.setStyleSheet("")  # Clear styling

    def _set_item(self, row: int, col: int, text: str) -> Optional[QTableWidgetItem]:
        """Helper to set a table item, creating it if necessary."""
        if col < 0:
            return None
        item = self.table.item(row, col)
        if item is None:
            item = QTableWidgetItem()
            self.table.setItem(row, col, item)
        item.setText(text)

        # Center-align all columns except Name and Conds
        if col not in (COMBAT_COL_NAME, COMBAT_COL_CONDS):
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        # Make all items read-only (not editable)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        font = item.font()
        font.setPointSize(CONFIG.monster_table_font_size)
        item.setFont(font)

        return item

    def _set_checkbox(self, row: int, col: int, checked: bool, monster=None) -> None:
        """Helper to set a centered checkbox in a table cell."""
        if col < 0:
            return

        # Create a widget container for centering
        widget = QWidget()
        checkbox = QCheckBox()
        checkbox.setChecked(checked)

        # Center the checkbox
        layout = QHBoxLayout(widget)
        layout.addWidget(checkbox)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)

        # Connect checkbox to update monster state
        # Store monster reference with the checkbox to handle sorting correctly
        checkbox.stateChanged.connect(
            lambda state, m=monster, c=col: self._on_checkbox_changed_with_monster(m, c, state)
        )

        self.table.setCellWidget(row, col, widget)


    def _set_conditions_cell(
        self,
        row: int,
        conditions: list,
        col: int,
    ) -> None:
        """Render the comma-separated condition cell with tooltips."""
        conditions = conditions or []
        conds_text = ", ".join(conditions) if conditions else ""
        conds_item = self._set_item(row, col, conds_text)

        if conds_item and conditions:
            tooltip_lines = []
            for cond in conditions:
                desc = CONDITION_DESCRIPTIONS.get(cond, "No description available.")
                wrapped_desc = self._wrap_text(desc, 60)
                tooltip_lines.append(f"<b>{cond}:</b><br>{wrapped_desc}")
            conds_item.setToolTip("<html>" + "<br><br>".join(tooltip_lines) + "</html>")
            conds_item.setBackground(QColor(*CONFIG.hp_conditions_color))
            conds_item.setForeground(QColor("white"))
        elif conds_item:
            conds_item.setToolTip("")
            # Clear background - no alternating colors
            conds_item.setBackground(QColor(0, 0, 0, 0))  # Transparent
            conds_item.setForeground(QColor("white"))

    def _on_checkbox_changed_with_monster(self, monster, col: int, state: int) -> None:
        """Handle checkbox state changes using direct monster reference."""
        if monster is None:
            return

        checked = (state == Qt.CheckState.Checked.value)

        if col == COMBAT_COL_ACTIVE:
            monster.active = checked
        elif col == COMBAT_COL_CON:
            monster.concentrating = checked

        # Notify manager of state change
        if hasattr(self.manager, "_changed"):
            self.manager._changed()

    def _on_checkbox_changed(self, row: int, col: int, state: int) -> None:
        """Handle checkbox state changes and update monster data (legacy handler)."""
        monster = self._monster_at_row(row)
        if monster is None:
            return
        checked = (state == Qt.CheckState.Checked.value)

        if col == COMBAT_COL_ACTIVE:
            monster.active = checked
        elif col == COMBAT_COL_CON:
            monster.concentrating = checked

        # Notify manager of state change
        if hasattr(self.manager, "_changed"):
            self.manager._changed()

    def _on_cell_clicked(self, row: int, col: int) -> None:
        """Handle single clicks on table cells (for Heal and Hurt columns)."""
        monster = self._monster_at_row(row)
        if monster is None:
            return

        # Handle Heal column
        if col == COMBAT_COL_HEAL:
            # Use a dialog so we can log or cancel without mutating state.
            result = show_damage_heal_dialog(parent=self.table, mode="heal")
            if result is not None and result > 0:
                self.manager.heal_monster(monster, result)
                # Refresh will be triggered by manager's _changed callback

        # Handle Hurt column
        elif col == COMBAT_COL_HURT:
            # Damage dialog supports quick-entry buttons and manual entry.
            result = show_damage_heal_dialog(parent=self.table, mode="damage")
            if result is not None and result > 0:
                self.manager.damage_monster(monster, result)
                self._notify_concentration_crit(monster)
                # Refresh will be triggered by manager's _changed callback

    def _on_reset_combat(self) -> None:
        """Reset all heroes and monsters to full HP and clear temp HP."""
        from PySide6.QtWidgets import QMessageBox

        # Count how many creatures will be affected
        hero_count = len(self.manager.heroes)
        monster_count = len(self.manager.monsters)
        total_count = hero_count + monster_count

        if total_count == 0:
            QMessageBox.information(
                self.table,
                "Reset Combat",
                "No heroes or monsters to reset."
            )
            return

        # Create info message
        msg = f"This will reset {hero_count} hero(es) and {monster_count} monster(s):\n\n"
        msg += "• Set all HP to maximum\n"
        msg += "• Clear all temporary HP\n\n"
        msg += "Continue?"

        # Ask for confirmation
        reply = QMessageBox.question(
            self.table,
            "Reset Combat",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Reset all heroes
            for hero in self.manager.heroes:
                hero.hp_current = hero.hp_max
                hero.temp_hp = 0
                hero.conditions.clear()

            # Reset all monsters
            for monster in self.manager.monsters:
                monster.hp_current = monster.hp_max
                monster.temp_hp = 0
                monster.last_stand_triggered = False
                monster.dead = False
                monster.conditions.clear()
                monster.shown_bloodied_popup = False
                monster.shown_last_stand_popup = False

            # Notify manager of state change
            if hasattr(self.manager, "_changed"):
                self.manager._changed()

    def _on_add_monster(self) -> None:
        """Show add monster dialog."""
        from tabs.add_edit_monster_dialog import show_add_edit_monster_dialog

        monster = show_add_edit_monster_dialog(
            manager=self.manager,
            monster=None,
            parent=self.table,
        )

        if monster:
            self.manager.add_monster_instance(monster)

    def _on_delete_monster(self) -> None:
        """Delete the currently selected monster."""
        from PySide6.QtWidgets import QMessageBox

        row = self.table.currentRow()
        if row < 0 or row >= len(self.manager.monsters):
            QMessageBox.information(
                self.table,
                "Delete Monster",
                "No monster selected."
            )
            return

        # Get the actual monster (accounting for sorting)
        monsters = sorted(
            self.manager.monsters,
            key=lambda m: (
                getattr(m, "is_dead", False),
                not getattr(m, "active", True),
                not getattr(m, "legendary", False),
            )
        )

        if row >= len(monsters):
            return

        monster = monsters[row]

        # Ask for confirmation
        reply = QMessageBox.question(
            self.table,
            "Delete Monster",
            f"Delete {monster.name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.manager.remove_monster(monster)

    def _on_clear_encounter(self) -> None:
        """Clear all monsters from the encounter."""
        self.manager.monsters.clear()
        if hasattr(self.manager, "_changed"):
            self.manager._changed()
        self.refresh_table()

    def _on_set_color_for_selected(self) -> None:
        """Set color for all selected monsters using bulk marker dialog."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(
                self.table,
                "No Selection",
                "Please select one or more monsters to set their color."
            )
            return

        # Get all selected monsters
        monsters = self._current_sorted_monsters or self._sorted_monsters()
        if not self._current_sorted_monsters:
            self._current_sorted_monsters = monsters

        selected_monsters = []
        for model_index in selected_rows:
            row = model_index.row()
            if 0 <= row < len(monsters):
                selected_monsters.append(monsters[row])

        if not selected_monsters:
            return

        # Show bulk marker dialog with list of selected monsters
        assignments = show_bulk_marker_dialog(
            parent=self.table,
            monsters=selected_monsters,
            manager=self.manager
        )

        if assignments is not None:
            # Assign colors and numbers from the dialog
            for i, monster in enumerate(selected_monsters):
                color, number = assignments[i]
                monster.marker_color = color
                monster.marker_number = number

            self.refresh_table()
            if hasattr(self.manager, "_changed"):
                self.manager._changed()

    def _on_cell_double_clicked(self, row: int, col: int) -> None:
        """Handle double-click on a cell."""
        monster = self._monster_at_row(row)
        if monster is None:
            return

        if col == COMBAT_COL_MARKER:
            result = show_marker_dialog(
                parent=self.table,
                current_color=monster.marker_color,
                current_number=monster.marker_number,
                manager=self.manager
            )

            if result is not None:
                color, number = result
                monster.marker_color = color
                monster.marker_number = number
                self.refresh_table()
                if hasattr(self.manager, "_changed"):
                    self.manager._changed()
            return

        if col == COMBAT_COL_CONDS:
            current_conditions = getattr(monster, "conditions", []) or []
            result = show_conditions_dialog(
                parent=self.table,
                current_conditions=current_conditions
            )

            if result is not None:
                monster.conditions = result
                self.refresh_table()
                if hasattr(self.manager, "_changed"):
                    self.manager._changed()
            return

        if self._dialog_open:
            return

        self._dialog_open = True
        try:
            from tabs.add_edit_monster_dialog import show_add_edit_monster_dialog
            show_add_edit_monster_dialog(
                manager=self.manager,
                monster=monster,
                parent=self.table,
            )
        finally:
            self._dialog_open = False

    def _apply_column_widths(self) -> None:
        """Apply the configured column widths from CONFIG."""
        from modules.config import CONFIG

        column_widths = {
            COMBAT_COL_ACTIVE: CONFIG.combat_col_active_width,
            COMBAT_COL_HEAL: CONFIG.combat_col_heal_width,
            COMBAT_COL_NAME: CONFIG.combat_col_name_width,
            COMBAT_COL_MARKER: CONFIG.combat_col_marker_width,
            COMBAT_COL_HURT: CONFIG.combat_col_hurt_width,
            COMBAT_COL_CON: CONFIG.combat_col_con_width,
            COMBAT_COL_CONDS: CONFIG.combat_col_conds_width,
            COMBAT_COL_HP: CONFIG.combat_col_hp_width,
            COMBAT_COL_TMP: CONFIG.combat_col_tmp_width,
            COMBAT_COL_MAX: CONFIG.combat_col_max_width,
        }

        for col, width in column_widths.items():
            try:
                self.table.setColumnWidth(col, width)
            except Exception:
                # Silently ignore invalid columns
                pass

    def _maybe_show_legendary_mode(self, monster) -> None:
        """Show popups when a legendary monster becomes bloodied or enters last stand."""
        if not getattr(monster, "legendary", False):
            return

        if getattr(monster, "is_bloodied", False) and not getattr(
            monster, "shown_bloodied_popup", False
        ):
            monster.shown_bloodied_popup = True
            text = monster.bloodied_text or f"{monster.name} is bloodied and fighting harder."
            self._show_legendary_popup(f"{monster.name} is Bloodied", text)

        if getattr(monster, "last_stand_triggered", False) and not getattr(
            monster, "shown_last_stand_popup", False
        ):
            monster.shown_last_stand_popup = True
            text = monster.last_stand_text or (
                f"{monster.name} enters a Last Stand—keep dealing damage to finish them!"
            )
            monster.remove_condition("Dying")
            monster.add_condition("Last Stand")
            self._show_legendary_popup(f"{monster.name} Last Stand", text)

    def _show_legendary_popup(self, title: str, text: str) -> None:
        """Display an informational popup for legendary state changes."""
        if not self.table:
            return
        QMessageBox.information(self.table, title, text)

    def _notify_concentration_crit(self, creature) -> None:
        """Inform the user that concentrating creatures take crit damage consequences."""
        if creature is None or not getattr(creature, "concentrating", False):
            return
        QMessageBox.information(
            self.table,
            "Concentration Note",
            (
                "Whenever a character is **crit** while concentrating, they must make a "
                "**DC 10 STR save**. Failing this means Concentration is broken and the activity fails."
            ),
        )

    def _collect_loot_entries(self) -> list[tuple[str, str]]:
        entries: list[tuple[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for monster in self.manager.monsters:
            biome = monster.biome or "Unknown Biome"
            for note in monster.biome_loot or []:
                text = note.strip()
                if not text:
                    continue
                key = (biome, text)
                if key in seen:
                    continue
                seen.add(key)
                entries.append(key)
        return entries

    def _update_loot_notes(self) -> None:
        if self.loot_view is None:
            return
        entries = self._collect_loot_entries()
        if not entries:
            self.loot_view.clear()
            return

        html_lines = []
        for biome, note in entries:
            html_lines.append(f"<div style='font-weight:bold;margin-bottom:4px;'>{biome}</div>")
            html_lines.append(
                "<div style='border-bottom:1px solid #666;margin:0 0 6px 0;height:0;'></div>"
            )
            html_lines.append(f"<div>{note}</div>")
            html_lines.append(
                "<hr style='border:none;border-top:1px solid #555;margin:8px 0;'>"
            )
        if html_lines:
            html_lines.pop()  # remove last divider

        html = "<html><head><meta charset='utf-8'></head><body>"
        html += "".join(html_lines)
        html += "</body></html>"
        self.loot_view.setHtml(html)
