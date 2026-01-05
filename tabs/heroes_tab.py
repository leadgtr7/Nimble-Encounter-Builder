"""
Heroes tab controller: manages the heroes table in sync with CombatManager.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable, Optional
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QHeaderView,
    QFileDialog,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
    QHBoxLayout,
)

# Make sure we can import CombatManager from the project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_UI_DIR = PROJECT_ROOT
for _path in (PROJECT_ROOT,):
    if _path.exists() and str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from modules import config  # noqa: E402
from modules.combatManager import CombatManager  # noqa: E402
from modules.config import CONFIG  # noqa: E402
from tabs.conditions_dialog import show_conditions_dialog  # noqa: E402
from tabs.damage_heal_dialog import show_damage_heal_dialog  # noqa: E402
from tabs.hero_dialog import show_add_edit_hero_dialog  # noqa: E402
from modules.condition_descriptions import CONDITION_DESCRIPTIONS  # noqa: E402

# Column indices for heroes_table_combat (8 columns - no Act or Marker)
# Heroes table order: 💚, Name, ⚔, Con, Conds, HP, Tmp, Max
HERO_COL_HEAL = 0
HERO_COL_NAME = 1
HERO_COL_HURT = 2
HERO_COL_CON = 3
HERO_COL_CONDS = 4
HERO_COL_HP = 5
HERO_COL_TMP = 6
HERO_COL_MAX = 7

# Column widths for combat heroes table
# Column widths are now in config.py

# Heroes tab column indexes (matches UI: Name, Player, Lvl, Max, Class, GM Notes, Player Notes)
HERO_TAB_COL_NAME = 0
HERO_TAB_COL_PLAYER = 1
HERO_TAB_COL_LEVEL = 2
HERO_TAB_COL_MAX = 3
HERO_TAB_COL_CLASS = 4
HERO_TAB_COL_GM_NOTES = 5
HERO_TAB_COL_PLAYER_NOTES = 6


class HeroesTabController:
    """Manage the Heroes tab table view."""

    def __init__(
        self,
        manager: CombatManager,
        table: QTableWidget,
        btn_import: Optional[QPushButton] = None,
        btn_export: Optional[QPushButton] = None,
        mode: str = "combat",
        log_fn: Callable[[str], None] | None = None,
    ):
        self.manager = manager
        self.table = table
        self.btn_import = btn_import
        self.btn_export = btn_export
        self.log = log_fn or (lambda msg: None)
        self.mode = mode
        # Two modes share this controller; UI wiring diverges by table layout.
        self._heroes_tab_mode = mode == "heroes_tab"

        # Ensure we have the expected number of columns
        # Combat mode: 8 columns (💚, Name, ⚔, Con, Conds, HP, Tmp, Max)
        # Heroes tab mode: 7 columns (Name, Player, Lvl, Max, Class, GM Notes, Player Notes)
        expected_cols = 7 if self._heroes_tab_mode else 8
        if self.table.columnCount() < expected_cols:
            self.table.setColumnCount(expected_cols)

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
        }
        QTableWidget::item {
            padding-left: 0px;
            padding-right: 0px;
            border-bottom: 1px solid #3a3a3a;
            border-right: none;
        }
        """)

        # Set minimum section size first
        header.setMinimumSectionSize(1)

        # Increase row height for better readability
        self.table.verticalHeader().setDefaultSectionSize(28)

        # Enable row selection for heroes tab mode
        if self._heroes_tab_mode:
            self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        # Allow user to resize all columns
        for col in range(self.table.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)

        # Apply width dict once at startup
        self._apply_column_widths()

        # Connect double-click handler for conditions column
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)

        if not self._heroes_tab_mode:
            # Connect click handler for heal and hurt columns
            self.table.cellClicked.connect(self._on_cell_clicked)

        if self._heroes_tab_mode and self.btn_import is not None:
            self.btn_import.clicked.connect(self._on_import_party)
        if self._heroes_tab_mode and self.btn_export is not None:
            self.btn_export.clicked.connect(self._on_export_party)

    # ------------------------------------------------------------------#
    # Public entry points
    # ------------------------------------------------------------------#

    def refresh_table(self) -> None:
        """Rebuild the table from the current heroes in CombatManager."""
        if self._heroes_tab_mode:
            self._refresh_heroes_tab_table()
        else:
            self._refresh_combat_table()

    def _refresh_combat_table(self) -> None:
        heroes = self.manager.heroes
        self.table.setRowCount(len(heroes))

        for row, h in enumerate(heroes):
            # Clear any stale formatting before repopulating the row
            self._clear_row_formatting(row)
            self._set_item(row, HERO_COL_HEAL, "💚")
            self._set_item(row, HERO_COL_NAME, getattr(h, "name", ""))
            self._set_item(row, HERO_COL_HURT, "⚔")
            self._set_checkbox(
                row,
                HERO_COL_CON,
                getattr(h, "concentrating", False),
                hero=h,
            )
            self._set_hp_columns(row, h)
            self._set_conditions_cell(row, h.conditions, HERO_COL_CONDS)

    def _refresh_heroes_tab_table(self) -> None:
        heroes = self.manager.heroes
        self.table.setRowCount(len(heroes))

        for row, h in enumerate(heroes):
            # Clear any stale formatting from previous refresh
            self._clear_row_formatting(row)
            self._set_item(row, HERO_TAB_COL_NAME, getattr(h, "name", ""))
            self._set_item(row, HERO_TAB_COL_PLAYER, getattr(h, "player", ""))
            self._set_item(row, HERO_TAB_COL_LEVEL, str(getattr(h, "level", "")))
            self._set_item(row, HERO_TAB_COL_MAX, str(getattr(h, "hp_max", "")))
            self._set_item(row, HERO_TAB_COL_CLASS, getattr(h, "class_name", ""))
            self._set_item(row, HERO_TAB_COL_GM_NOTES, getattr(h, "notes_gm", ""))
            self._set_item(row, HERO_TAB_COL_PLAYER_NOTES, getattr(h, "notes_public", ""))

    def _set_hp_columns(self, row: int, hero) -> None:
        hp_item = self._set_item(row, HERO_COL_HP, str(getattr(hero, "effective_hp", 0)))
        if not hp_item:
            return
        font = QFont()
        font.setBold(True)
        font.setPointSize(CONFIG.hero_table_font_size)
        hp_item.setFont(font)
        # Ensure HP is center-aligned
        hp_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        if getattr(hero, "is_dying", False):
            hp_item.setBackground(QColor(*CONFIG.hp_down_color))
            hp_item.setForeground(QColor("white"))
        elif getattr(hero, "is_critical", False):
            hp_item.setBackground(QColor(*CONFIG.hp_critical_color))
            hp_item.setForeground(QColor("white"))
        elif getattr(hero, "is_bloodied", False):
            hp_item.setBackground(QColor(*CONFIG.hp_bloodied_color))
            hp_item.setForeground(QColor("white"))
        else:
            hp_item.setBackground(QColor(*CONFIG.hp_healthy_color))
            hp_item.setForeground(QColor("white"))

        # Set TMP and MAX columns with center alignment
        tmp_item = self._set_item(row, HERO_COL_TMP, str(getattr(hero, "temp_hp", 0)))
        if tmp_item:
            tmp_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        max_item = self._set_item(row, HERO_COL_MAX, str(getattr(hero, "hp_max", 0)))
        if max_item:
            max_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    # ------------------------------------------------------------------#
    # Helpers
    # ------------------------------------------------------------------#

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

    def _clear_row_formatting(self, row: int) -> None:
        """Clear all formatting from a row (to prevent stale formatting after sorting)."""
        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item is not None:
                item.setData(Qt.ItemDataRole.BackgroundRole, None)
                item.setData(Qt.ItemDataRole.ForegroundRole, None)
                item.setData(Qt.ItemDataRole.FontRole, None)


    def _set_conditions_cell(
        self,
        row: int,
        conditions: list,
        col: int,
    ) -> None:
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
            conds_item.setBackground(QColor(61, 0, 182))
            conds_item.setForeground(QColor("white"))
        elif conds_item:
            conds_item.setToolTip("")
            conds_item.setData(Qt.ItemDataRole.BackgroundRole, None)
            conds_item.setData(Qt.ItemDataRole.ForegroundRole, None)

    def _resource_display(self, hero) -> str:
        name = getattr(hero, "resource_1_name", "").strip()
        if not name:
            return ""
        current = getattr(hero, "resource_1_current", 0)
        maximum = getattr(hero, "resource_1_max", 0)
        return f"{name} ({current}/{maximum})"

    def _heroes_folder(self) -> Path:
        # Use configured party folder (respects Obsidian vault if set)
        return config.CONFIG.get_party_folder()

    def _ensure_heroes_folder(self, parent: QWidget | None) -> Path | None:
        folder = self._heroes_folder()
        if folder.exists():
            return folder
        if parent is None:
            parent = self.table
        choice = QMessageBox.question(
            parent,
            "Create Heroes Folder?",
            f"The folder does not exist:\n{folder}\nCreate it?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if choice != QMessageBox.StandardButton.Yes:
            return None
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            self.log(f"Could not create heroes folder: {exc}")
            return None
        return folder

    def _set_item(self, row: int, col: int, text: str) -> Optional[QTableWidgetItem]:
        """Helper to set a table item, creating it if necessary."""
        if col < 0:
            return None
        item = self.table.item(row, col)
        if item is None:
            item = QTableWidgetItem()
            self.table.setItem(row, col, item)
        item.setText(text)

        # Center-align all columns except Name and text columns
        non_center_cols = {
            HERO_COL_NAME,
            HERO_COL_CONDS,
            HERO_TAB_COL_NAME,
            HERO_TAB_COL_GM_NOTES,
            HERO_TAB_COL_PLAYER_NOTES
        }
        if col not in non_center_cols:
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        # Make all items read-only (not editable)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        font = item.font()
        font.setPointSize(CONFIG.hero_table_font_size)
        item.setFont(font)

        return item

    def _set_checkbox(self, row: int, col: int, checked: bool, hero=None) -> None:
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

        if hero is not None:
            checkbox.stateChanged.connect(
                lambda state, h=hero: self._on_checkbox_changed_with_hero(h, state)
            )
        self.table.setCellWidget(row, col, widget)

    def _on_checkbox_changed_with_hero(self, hero, state: int) -> None:
        """Update hero state when concentration checkbox changes."""
        if hero is None:
            return
        hero.concentrating = (state == Qt.CheckState.Checked.value)
        if hasattr(self.manager, "_changed"):
            self.manager._changed()

    def _on_cell_double_clicked(self, row: int, col: int) -> None:
        """Handle double-clicks on table cells."""
        if row < 0 or row >= len(self.manager.heroes):
            return

        hero = self.manager.heroes[row]

        # Double-click on Name column (in either mode) opens edit dialog
        name_col = HERO_TAB_COL_NAME if self._heroes_tab_mode else HERO_COL_NAME
        if col == name_col:
            edited_hero = show_add_edit_hero_dialog(parent=self.table, hero=hero)
            if edited_hero is not None:
                # Update the hero in the manager
                idx = self.manager.heroes.index(hero)
                self.manager.heroes[idx] = edited_hero

                # Refresh the table to show updated hero
                self.refresh_table()

                # Notify manager of state change
                if hasattr(self.manager, "_changed"):
                    self.manager._changed()
            return

        # Only combat mode has a Conditions column
        if not self._heroes_tab_mode and col == HERO_COL_CONDS:
            current_conditions = getattr(hero, "conditions", []) or []
            result = show_conditions_dialog(
                parent=self.table,
                current_conditions=current_conditions
            )

            if result is not None:
                hero.conditions = result

                # Refresh the table to show updated conditions
                self.refresh_table()

                # Notify manager of state change
                if hasattr(self.manager, "_changed"):
                    self.manager._changed()

    def _notify_concentration_crit(self, creature) -> None:
        """Warn about the STR save when concentrating creatures suffer crit hits."""
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

    def handle_concentration_note(self, creature) -> None:
        """Entry point for external hooks to show the concentration reminder."""
        self._notify_concentration_crit(creature)

    def _on_cell_clicked(self, row: int, col: int) -> None:
        """Handle single clicks on table cells (for Heal and Hurt columns)."""
        if row < 0 or row >= len(self.manager.heroes):
            return

        hero = self.manager.heroes[row]

        # Handle Heal column
        if col == HERO_COL_HEAL:
            result = show_damage_heal_dialog(parent=self.table, mode="heal")
            if result is not None and result > 0:
                self.manager.heal_hero(hero, result)
                # Refresh will be triggered by manager's _changed callback

        # Handle Hurt column
        elif col == HERO_COL_HURT:
            result = show_damage_heal_dialog(parent=self.table, mode="damage")
            if result is not None and result > 0:
                self.manager.damage_hero(hero, result)
                # Refresh will be triggered by manager's _changed callback

    def _apply_column_widths(self) -> None:
        """Apply the configured column widths from CONFIG depending on mode."""
        if self._heroes_tab_mode:
            # Heroes tab mode
            widths = {
                HERO_TAB_COL_NAME: CONFIG.hero_tab_col_name_width,
                HERO_TAB_COL_PLAYER: CONFIG.hero_tab_col_player_width,
                HERO_TAB_COL_LEVEL: CONFIG.hero_tab_col_level_width,
                HERO_TAB_COL_MAX: CONFIG.hero_tab_col_max_width,
                HERO_TAB_COL_CLASS: CONFIG.hero_tab_col_class_width,
                HERO_TAB_COL_GM_NOTES: CONFIG.hero_tab_col_gm_notes_width,
                HERO_TAB_COL_PLAYER_NOTES: CONFIG.hero_tab_col_player_notes_width,
            }
        else:
            # Combat mode
            # Use consistent column width settings for columns whose names appear in both hero tables.
            widths = {
                HERO_COL_HEAL: CONFIG.hero_combat_col_heal_width,
                HERO_COL_NAME: CONFIG.hero_tab_col_name_width,
                HERO_COL_HURT: CONFIG.hero_combat_col_hurt_width,
                HERO_COL_CON: CONFIG.hero_combat_col_con_width,
                HERO_COL_CONDS: CONFIG.hero_combat_col_conds_width,
                HERO_COL_HP: CONFIG.hero_combat_col_hp_width,
                HERO_COL_TMP: CONFIG.hero_combat_col_tmp_width,
                HERO_COL_MAX: CONFIG.hero_tab_col_max_width,
            }

        for col, width in widths.items():
            try:
                self.table.setColumnWidth(col, width)
            except Exception:
                # Silently ignore invalid columns
                pass

    def _on_export_party(self) -> None:
        """Export the current heroes list as a party JSON file."""
        if not self.manager.heroes:
            self.log("Party export skipped: no heroes to save.")
            return

        parent = self.table.window()
        heroes_dir = self._ensure_heroes_folder(parent)
        if heroes_dir is None:
            return

        default_name = f"party_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path, _ = QFileDialog.getSaveFileName(
            parent,
            "Export Party",
            str(heroes_dir / default_name),
            "JSON Files (*.json);;All Files (*)",
        )
        if not path:
            return

        try:
            self.manager.save_party(path, name=Path(path).stem)
        except Exception as exc:  # noqa: BLE001
            self.log(f"Could not export party: {exc}")
        else:
            self.log(f"Exported party to {path}")

    def _on_import_party(self) -> None:
        """Import a party JSON file into the hero list."""
        parent = self.table.window()
        heroes_dir = self._heroes_folder()
        default_dir = str(heroes_dir if heroes_dir.exists() else PROJECT_ROOT)
        path, _ = QFileDialog.getOpenFileName(
            parent,
            "Import Party",
            default_dir,
            "JSON Files (*.json);;All Files (*)",
        )
        if not path:
            return

        try:
            self.manager.load_party(path)
        except Exception as exc:  # noqa: BLE001
            self.log(f"Could not import party: {exc}")
        else:
            self.log(f"Imported party from {path}")
