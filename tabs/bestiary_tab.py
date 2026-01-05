"""
Bestiary tab controller: wires UI widgets to CombatManager for the Bestiary tab.
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import Callable, List, Optional
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QHeaderView,
    QWidget,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_UI_DIR = PROJECT_ROOT
for _path in (PROJECT_ROOT,):
    if _path.exists() and str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from modules import config
from modules.combatManager import CombatManager
from modules.combatants import MonsterTemplate
from modules import persistence
from modules.shared_statblock import render_stat_block
from tabs.marker_dialog import show_marker_dialog
from tabs.bulk_marker_dialog import show_bulk_marker_dialog
from tabs.add_edit_monster_dialog import show_add_edit_monster_dialog
from tabs.random_encounter_dialog import show_random_encounter_dialog


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

# Column indices for monsters_table_bestiary (6 columns)
BESTIARY_COL_ACTIVE = 0
BESTIARY_COL_NAME = 1
BESTIARY_COL_WAVE = 2        # group/wave tag
BESTIARY_COL_MARKER = 3      # marker color + number
BESTIARY_COL_LEVEL = 4       # monster level
BESTIARY_COL_MAX = 5         # max HP

# Column widths are now in config.py


class BestiaryTabController:
    """Manage filtering, preview, and encounter table for the Bestiary tab."""

    def __init__(
        self,
        manager: CombatManager,
        list_monsters: QListWidget,
        stat_preview: QTextEdit,
        table_encounter: QTableWidget,
        edit_name: Optional[QLineEdit] = None,
        combo_biome: Optional[QComboBox] = None,
        edit_level: Optional[QLineEdit] = None,
        checkbox_legendary: Optional[QCheckBox] = None,
        btn_add: Optional[QPushButton] = None,
        btn_del: Optional[QPushButton] = None,
        btn_clear: Optional[QPushButton] = None,
        btn_load: Optional[QPushButton] = None,
        btn_save: Optional[QPushButton] = None,
        btn_random: Optional[QPushButton] = None,
        btn_set_color: Optional[QPushButton] = None,
        table_combat: Optional[QTableWidget] = None,
        label_difficulty: Optional[QLabel] = None,
        log_fn: Callable[[str], None] | None = None,
    ):
        self.manager = manager
        self.list_monsters = list_monsters
        self.stat_preview = stat_preview
        self.table_encounter = table_encounter
        self.table_combat = table_combat
        self.label_difficulty = label_difficulty
        self.edit_name = edit_name
        self.combo_biome = combo_biome
        self.edit_level = edit_level
        self.checkbox_legendary = checkbox_legendary
        self.btn_add = btn_add
        self.btn_del = btn_del
        self.btn_clear = btn_clear
        self.btn_save = btn_save
        self.btn_load = btn_load
        self.btn_random = btn_random
        self.btn_set_color = btn_set_color
        self.log = log_fn or (lambda msg: None)

        self._filtered_templates: List[MonsterTemplate] = []

        self._prepare_widgets()
        self._wire_signals()

    # ------------------------------------------------------------------#
    # Public entry points
    # ------------------------------------------------------------------#

    def load_vault_from_config(self) -> None:
        paths = config.CONFIG.resolve_monster_vault_paths()
        if not paths:
            self.log("No default monster vault path set in config.")
            return
        try:
            # Merge multiple libraries while deduplicating name/file pairs.
            self.manager.monster_library = []
            seen = set()
            for path in paths:
                templates = persistence.load_monster_library(path)
                for tpl in templates:
                    key = (tpl.name, tpl.file)
                    if key in seen:
                        continue
                    seen.add(key)
                    self.manager.monster_library.append(tpl)
                self.log(
                    f"Monster vault loaded from config: {path} "
                    f"({len(templates)} templates)"
                )
        except Exception as exc:
            self.log(f"ERROR loading monster vault(s) from config: {exc}")

    def populate_biome_filter(self) -> None:
        if self.combo_biome is None:
            return
        biomes = sorted(
            {
                (tpl.biome or "").strip()
                for tpl in self.manager.monster_library
                if (tpl.biome or "").strip()
            }
        )
        self.combo_biome.blockSignals(True)
        self.combo_biome.clear()
        self.combo_biome.addItem("")  # empty = no biome filter
        for biome in biomes:
            self.combo_biome.addItem(biome)
        self.combo_biome.blockSignals(False)

    def apply_filters(self) -> None:
        """Apply name/biome/level/legendary filters and rebuild list."""
        name_filter = (
            self.edit_name.text().strip().lower() if self.edit_name else ""
        )
        biome_filter = (
            self.combo_biome.currentText().strip().lower()
            if self.combo_biome
            else ""
        )
        level_filter = self.edit_level.text().strip() if self.edit_level else ""
        legendary_only = (
            self.checkbox_legendary.isChecked() if self.checkbox_legendary else False
        )

        # Build a fresh filtered list so the UI stays deterministic.
        filtered: List[MonsterTemplate] = []
        for tpl in self.manager.monster_library:
            if legendary_only and not tpl.legendary:
                continue
            if not legendary_only and tpl.legendary:
                continue
            if name_filter and name_filter not in tpl.name.lower():
                continue
            biome_value = (tpl.biome or "").lower()
            if biome_filter and biome_filter not in biome_value:
                continue
            # Level filter is an exact string match (supports fractions like "1/4").
            if level_filter and level_filter != str(tpl.level):
                continue
            filtered.append(tpl)

        self._filtered_templates = filtered
        self._refresh_bestiary_list()

    def on_state_changed(self) -> None:
        """Manager state callback: refresh encounter table."""
        self.refresh_encounter_table()

    def refresh_encounter_table(self) -> None:
        monsters = self.manager.monsters
        # Always re-render to keep marker formatting and HP colors accurate.
        self._fill_bestiary_table(self.table_encounter, monsters)
        self._update_difficulty_label()

    # ------------------------------------------------------------------#
    # Internal wiring/helpers
    # ------------------------------------------------------------------#

    def _prepare_widgets(self) -> None:
        self.list_monsters.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_encounter.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        # Allow multiple selection for bulk marker assignment
        self.table_encounter.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        # Enable context menu
        self.table_encounter.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_encounter.customContextMenuRequested.connect(self._show_context_menu)
        if self.table_encounter.columnCount() < 6:
            self.table_encounter.setColumnCount(6)

        # Strip padding so narrow columns can actually be narrow, add horizontal grid lines
        self.table_encounter.setStyleSheet("""
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
        header = self.table_encounter.horizontalHeader()
        header.setMinimumSectionSize(1)

        # Increase row height for better readability
        self.table_encounter.verticalHeader().setDefaultSectionSize(28)

        # Allow user to resize all columns
        for col in range(self.table_encounter.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)

        # Apply width dict once at startup
        self._apply_column_widths()

        # Connect double-click handler for marker column
        self.table_encounter.cellDoubleClicked.connect(self._on_cell_double_clicked)

    def _wire_signals(self) -> None:
        self.list_monsters.currentRowChanged.connect(self._on_bestiary_selection_changed)
        self.table_encounter.currentCellChanged.connect(self._on_encounter_selection_changed)
        if self.edit_name is not None:
            self.edit_name.textChanged.connect(self.apply_filters)
        if self.edit_level is not None:
            self.edit_level.textChanged.connect(self.apply_filters)
        if self.combo_biome is not None:
            self.combo_biome.currentTextChanged.connect(self.apply_filters)
        if self.checkbox_legendary is not None:
            self.checkbox_legendary.toggled.connect(self.apply_filters)
        if self.btn_add is not None:
            self.btn_add.clicked.connect(self._on_add_selected_template_to_encounter)
        if self.btn_del is not None:
            self.btn_del.clicked.connect(self._on_delete_selected_encounter_monster)
        if self.btn_clear is not None:
            self.btn_clear.clicked.connect(self._on_clear_encounter)
        if self.btn_save is not None:
            self.btn_save.clicked.connect(self._on_save_encounter)
        if self.btn_load is not None:
            self.btn_load.clicked.connect(self._on_load_encounter)
        if self.btn_random is not None:
            self.btn_random.clicked.connect(self._on_random_encounter)
        if self.btn_set_color is not None:
            self.btn_set_color.clicked.connect(self._on_set_color_for_selected)

    def _refresh_bestiary_list(self) -> None:
        self.list_monsters.blockSignals(True)
        self.list_monsters.clear()

        for tpl in self._filtered_templates:
            display = f"[Lvl {tpl.level}] {tpl.name}"
            if tpl.biome:
                display += f" – {tpl.biome}"
            elif tpl.type:
                display += f" – {tpl.type}"
            self.list_monsters.addItem(QListWidgetItem(display))

        self.list_monsters.blockSignals(False)
        if self._filtered_templates:
            self.list_monsters.setCurrentRow(0)
        else:
            self.stat_preview.clear()

    # ------------------------------------------------------------------#
    # Shared table population (bestiary + combat)
    # ------------------------------------------------------------------#

    def _fill_bestiary_table(self, table: QTableWidget, monsters: list) -> None:
        table.setRowCount(len(monsters))
        for row, m in enumerate(monsters):
            # Clear any stale formatting from previous refresh
            self._clear_row_formatting(table, row)

            # Active column - checkbox
            self._set_checkbox(table, row, BESTIARY_COL_ACTIVE, getattr(m, "active", True))

            # Create all items first
            self._set_item(table, row, BESTIARY_COL_NAME, m.name)
            self._set_item(table, row, BESTIARY_COL_WAVE, m.group or "")

            # Marker (number only, color is background)
            marker_color = getattr(m, "marker_color", "")
            marker_number = getattr(m, "marker_number", 0)
            marker_text = str(marker_number) if marker_number else ""
            marker_item = self._set_item(table, row, BESTIARY_COL_MARKER, marker_text)

            self._set_item(table, row, BESTIARY_COL_LEVEL, str(getattr(m, "level", "")))
            self._set_item(table, row, BESTIARY_COL_MAX, str(getattr(m, "hp_max", "")))

            # Apply marker-specific formatting
            if marker_item is not None:
                # Make text bold and center-aligned
                font = QFont()
                font.setBold(True)
                marker_item.setFont(font)
                marker_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                if marker_color:
                    try:
                        marker_item.setBackground(QColor(marker_color))
                        # Set contrasting text color
                        text_color = calculate_text_color(marker_color)
                        marker_item.setForeground(text_color)
                    except Exception:
                        marker_item.setBackground(QColor("white"))
                        marker_item.setForeground(QColor("black"))
                # If no marker color, keep the row striping color (don't override to white)

    def _clear_row_formatting(self, table: QTableWidget, row: int) -> None:
        """Clear all formatting from a row (to prevent stale formatting after sorting)."""
        for col in range(table.columnCount()):
            item = table.item(row, col)
            if item is not None:
                item.setData(Qt.ItemDataRole.BackgroundRole, None)
                item.setData(Qt.ItemDataRole.ForegroundRole, None)
                item.setData(Qt.ItemDataRole.FontRole, None)


    # ------------------------------------------------------------------#
    # Column widths
    # ------------------------------------------------------------------#

    def _apply_column_widths(self) -> None:
        """Apply the configured column widths from CONFIG."""
        from modules.config import CONFIG

        column_widths = {
            BESTIARY_COL_ACTIVE: CONFIG.bestiary_col_active_width,
            BESTIARY_COL_NAME: CONFIG.bestiary_col_name_width,
            BESTIARY_COL_WAVE: CONFIG.bestiary_col_wave_width,
            BESTIARY_COL_MARKER: CONFIG.bestiary_col_marker_width,
            BESTIARY_COL_LEVEL: CONFIG.bestiary_col_level_width,
            BESTIARY_COL_MAX: CONFIG.bestiary_col_max_width,
        }

        # Bestiary table widths
        if self.table_encounter is not None:
            for col, width in column_widths.items():
                try:
                    self.table_encounter.setColumnWidth(col, width)
                except Exception:
                    pass

    def _update_difficulty_label(self) -> None:
        """Update the difficulty label based on current encounter."""
        if not self.label_difficulty:
            return

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
            "Easy": config.CONFIG.difficulty_color_easy,
            "Medium": config.CONFIG.difficulty_color_medium,
            "Hard": config.CONFIG.difficulty_color_hard,
            "Deadly": config.CONFIG.difficulty_color_deadly,
            "Very Deadly": config.CONFIG.difficulty_color_very_deadly,
        }

        bg_color = color_map.get(difficulty, (50, 50, 50))

        # Calculate contrasting text color
        text_color = calculate_text_color(f"#{bg_color[0]:02x}{bg_color[1]:02x}{bg_color[2]:02x}")

        # Keep border and border-radius from UI
        style = f"""QLabel {{
    background-color: rgb({bg_color[0]}, {bg_color[1]}, {bg_color[2]});
    color: {text_color.name()};
    font-weight: bold;
    border: 2px solid white;
    border-radius: 6px;
}}"""
        self.label_difficulty.setStyleSheet(style)

    # ------------------------------------------------------------------#
    # Selection / preview
    # ------------------------------------------------------------------#

    def _on_bestiary_selection_changed(self, row: int) -> None:
        if row < 0 or row >= len(self._filtered_templates):
            self.stat_preview.clear()
            return
        tpl = self._filtered_templates[row]
        html = render_stat_block(tpl, mode="lite")
        self.stat_preview.setHtml(html)

    def _on_encounter_selection_changed(self, current_row: int, current_col: int, prev_row: int, prev_col: int) -> None:
        """Show stat block preview when a monster is selected in the encounter table."""
        if current_row < 0 or current_row >= len(self.manager.monsters):
            # Don't clear the preview - keep showing the search list selection
            return
        monster = self.manager.monsters[current_row]
        html = render_stat_block(monster, mode="lite")
        self.stat_preview.setHtml(html)

    # ------------------------------------------------------------------#
    # Encounter actions
    # ------------------------------------------------------------------#

    def _get_selected_template(self) -> Optional[MonsterTemplate]:
        row = self.list_monsters.currentRow()
        if row < 0 or row >= len(self._filtered_templates):
            return None
        return self._filtered_templates[row]

    def _get_selected_encounter_index(self) -> Optional[int]:
        indexes = self.table_encounter.selectedIndexes()
        if not indexes:
            return None
        row = min(idx.row() for idx in indexes)
        if 0 <= row < len(self.manager.monsters):
            return row
        return None

    def _on_add_selected_template_to_encounter(self) -> None:
        tpl = self._get_selected_template()
        if tpl is None:
            self.log("No monster selected in Bestiary.")
            return
        group = tpl.biome or tpl.type or ""
        self.manager.add_monster_from_template(tpl, group=group)

    def _on_delete_selected_encounter_monster(self) -> None:
        idx = self._get_selected_encounter_index()
        if idx is None:
            return
        monster = self.manager.monsters[idx]
        self.manager.remove_monster(monster)

    def _on_clear_encounter(self) -> None:
        self.manager.monsters.clear()
        if hasattr(self.manager, "_changed"):
            self.manager._changed()
        self.log("Encounter cleared (Bestiary tab).")
        self.refresh_encounter_table()

    def _on_random_encounter(self) -> None:
        """Generate a random encounter using the random encounter dialog."""
        parent_widget = self.list_monsters.window()

        # Show the random encounter dialog
        generated_monsters = show_random_encounter_dialog(parent_widget, self.manager)

        if generated_monsters:
            # Add the generated monsters to the encounter
            for template in generated_monsters:
                group = template.biome or template.type or ""
                self.manager.add_monster_from_template(template, group=group)

            self.log(f"Random encounter generated: {len(generated_monsters)} monster(s) added.")
            self.refresh_encounter_table()

    def _on_save_encounter(self) -> None:
        """Save the current encounter to a JSON file via CombatManager."""
        if not self.manager.monsters:
            self.log("Encounter save skipped: no monsters in encounter.")
            return

        # Use configured encounter folder (respects Obsidian vault if set)
        encounters_dir = config.CONFIG.get_encounter_folder()

        parent_widget = self.list_monsters.window()
        if not encounters_dir.exists():
            choice = QMessageBox.question(
                parent_widget,
                "Create Encounters Folder?",
                f"The folder does not exist:\n{encounters_dir}\nCreate it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if choice == QMessageBox.StandardButton.Yes:
                try:
                    encounters_dir.mkdir(parents=True, exist_ok=True)
                except Exception as exc:
                    self.log(f"Could not create encounters folder: {exc}")
                    return
            else:
                return

        default_name = f"encounter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path, _ = QFileDialog.getSaveFileName(
            parent_widget,
            "Save Encounter JSON",
            str(encounters_dir / default_name),
            "JSON Files (*.json);;All Files (*)",
        )
        if not path:
            return

        try:
            self.manager.save_encounter(path, name=Path(path).stem)
        except Exception as exc:  # noqa: BLE001
            self.log(f"Could not save encounter: {exc}")
        else:
            self.log(f"Encounter saved to {path}")

    def _on_load_encounter(self) -> None:
        """Load an encounter JSON file into the manager."""
        # Use configured encounter folder (respects Obsidian vault if set)
        encounters_dir = config.CONFIG.get_encounter_folder()

        parent_widget = self.list_monsters.window()
        default_dir = str(encounters_dir if encounters_dir.exists() else PROJECT_ROOT)

        path, _ = QFileDialog.getOpenFileName(
            parent_widget,
            "Load Encounter JSON",
            default_dir,
            "JSON Files (*.json);;All Files (*)",
        )
        if not path:
            return

        try:
            self.manager.load_encounter(path)
        except Exception as exc:  # noqa: BLE001
            self.log(f"Could not load encounter: {exc}")
            return

        self.log(f"Encounter loaded from {path}")

        # Check if we should refresh monster data from vault
        should_refresh = config.CONFIG.auto_refresh_on_encounter_load

        if not should_refresh:
            # Prompt user to refresh monster data
            reply = QMessageBox.question(
                parent_widget,
                "Refresh Monster Data",
                "Do you want to refresh monster data from the vault?\n\n"
                "This will update all monsters in the encounter with the latest data from your monster library.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            should_refresh = (reply == QMessageBox.StandardButton.Yes)

        if should_refresh:
            self._refresh_monsters_from_vault()

    def _refresh_monsters_from_vault(self) -> None:
        """Refresh all monsters in the encounter with latest data from the monster library."""
        if not self.manager.monster_library:
            self.log("No monster library loaded - cannot refresh monster data")
            return

        updated_count = 0
        for monster in self.manager.monsters:
            # Find matching template in library by name
            template = None
            for t in self.manager.monster_library:
                if t.name == monster.name:
                    template = t
                    break

            if template:
                # Update monster with template data (preserve instance-specific fields)
                monster.level = template.level
                monster.hp_max = int(template.hp.split("-")[0]) if template.hp else monster.hp_max
                monster.armor = template.armor
                monster.size = template.size
                monster.type = template.type
                monster.speed = template.speed
                monster.biome = template.biome
                monster.saves = template.saves
                monster.flavor = template.flavor
                monster.actions = template.actions
                monster.special_actions = template.special_actions
                monster.biome_loot = template.biome_loot
                monster.bloodied = template.bloodied
                monster.last_stand = template.last_stand
                monster.last_stand_hp = int(template.last_stand_hp) if template.last_stand_hp else 0
                monster.legendary = template.legendary
                updated_count += 1

        self.log(f"Refreshed {updated_count} monster(s) from vault")
        self.refresh_encounter_table()

    # ------------------------------------------------------------------#
    # Table helpers
    # ------------------------------------------------------------------#

    @staticmethod
    def _set_item(
        table: QTableWidget, row: int, col: int, text: str
    ) -> Optional[QTableWidgetItem]:
        if col < 0:
            return None
        item = table.item(row, col)
        if item is None:
            item = QTableWidgetItem()
            table.setItem(row, col, item)
        item.setText(text)

        # Make all items read-only (not editable)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        return item

    def _set_checkbox(self, table: QTableWidget, row: int, col: int, checked: bool) -> None:
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
        checkbox.stateChanged.connect(
            lambda state, r=row, c=col: self._on_checkbox_changed(r, c, state)
        )

        table.setCellWidget(row, col, widget)

    def _on_checkbox_changed(self, row: int, col: int, state: int) -> None:
        """Handle checkbox state changes and update monster data."""
        if row < 0 or row >= len(self.manager.monsters):
            return

        monster = self.manager.monsters[row]
        checked = (state == Qt.CheckState.Checked.value)

        if col == BESTIARY_COL_ACTIVE:
            monster.active = checked

        # Notify manager of state change
        if hasattr(self.manager, "_changed"):
            self.manager._changed()

    def _show_context_menu(self, position) -> None:
        """Show context menu for bulk marker assignment."""
        from PySide6.QtWidgets import QMenu

        selected_rows = set(index.row() for index in self.table_encounter.selectedIndexes())
        if not selected_rows:
            return

        menu = QMenu(self.table_encounter)
        assign_marker_action = menu.addAction(f"Assign Marker to {len(selected_rows)} Monster(s)")

        action = menu.exec(self.table_encounter.viewport().mapToGlobal(position))

        if action == assign_marker_action:
            self._bulk_assign_markers(selected_rows)

    def _bulk_assign_markers(self, rows: set) -> None:
        """Assign the same marker color/number to multiple monsters."""
        if not rows:
            return

        # Show marker dialog (use first selected monster's current values as defaults)
        first_row = min(rows)
        if first_row < 0 or first_row >= len(self.manager.monsters):
            return

        first_monster = self.manager.monsters[first_row]

        result = show_marker_dialog(
            parent=self.table_encounter,
            current_color=first_monster.marker_color,
            current_number=first_monster.marker_number,
            manager=self.manager
        )

        if result is not None:
            color, number = result
            # Apply to all selected monsters
            for row in rows:
                if 0 <= row < len(self.manager.monsters):
                    monster = self.manager.monsters[row]
                    monster.marker_color = color
                    monster.marker_number = number

            # Refresh the table to show updated markers
            self.refresh_encounter_table()

            # Notify manager of state change
            if hasattr(self.manager, "_changed"):
                self.manager._changed()

    def _on_cell_double_clicked(self, row: int, col: int) -> None:
        """Handle double-clicks on table cells."""
        if row < 0 or row >= len(self.manager.monsters):
            return

        monster = self.manager.monsters[row]

        # Double-click on Name column opens edit monster dialog
        if col == BESTIARY_COL_NAME:
            edited_monster = show_add_edit_monster_dialog(
                manager=self.manager,
                monster=monster,
                parent=self.table_encounter
            )
            if edited_monster is not None:
                # Update the monster in the manager
                idx = self.manager.monsters.index(monster)
                self.manager.monsters[idx] = edited_monster

                # Refresh the table to show updated monster
                self.refresh_encounter_table()

                # Notify manager of state change
                if hasattr(self.manager, "_changed"):
                    self.manager._changed()
            return

        # Double-click on Marker column opens marker dialog
        if col == BESTIARY_COL_MARKER:
            result = show_marker_dialog(
                parent=self.table_encounter,
                current_color=monster.marker_color,
                current_number=monster.marker_number,
                manager=self.manager
            )

            if result is not None:
                color, number = result
                monster.marker_color = color
                monster.marker_number = number

                # Refresh the table to show updated marker
                self.refresh_encounter_table()

                # Notify manager of state change
                if hasattr(self.manager, "_changed"):
                    self.manager._changed()

    def _on_set_color_for_selected(self) -> None:
        """Set color for all selected monsters in the encounter table using bulk marker dialog."""
        selected_rows = self.table_encounter.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(
                self.table_encounter,
                "No Selection",
                "Please select one or more monsters to set their color."
            )
            return

        # Get all selected monsters
        selected_monsters = []
        for model_index in selected_rows:
            row = model_index.row()
            if 0 <= row < len(self.manager.monsters):
                selected_monsters.append(self.manager.monsters[row])

        if not selected_monsters:
            return

        # Show bulk marker dialog with list of selected monsters
        assignments = show_bulk_marker_dialog(
            parent=self.table_encounter,
            monsters=selected_monsters,
            manager=self.manager
        )

        if assignments is not None:
            # Apply the assignments (assignments is a list indexed by position)
            for i, monster in enumerate(selected_monsters):
                color, number = assignments[i]
                monster.marker_color = color
                monster.marker_number = number

            # Refresh the table to show updated markers
            self.refresh_encounter_table()

            # Notify manager of state change
            if hasattr(self.manager, "_changed"):
                self.manager._changed()
