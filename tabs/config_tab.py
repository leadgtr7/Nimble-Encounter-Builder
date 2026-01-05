"""
config_tab.py
=============================================================================
Controller for the Config tab in the main UI.

Wires up the config UI elements to the CONFIG object from config.py.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QWidget,
    QDoubleSpinBox,
    QSpinBox,
    QLineEdit,
    QCheckBox,
    QPushButton,
    QFileDialog,
    QColorDialog,
    QComboBox,
    QInputDialog,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QListWidget,
    QListWidgetItem,
    QTextEdit,
    QMessageBox,
    QLabel,
)

from modules.config import CONFIG, save_config, load_config, get_config_path
from modules.condition_descriptions import CONDITION_DESCRIPTIONS
from tabs.vault_viewer_controller import VaultViewerController


class ConfigTabController:
    """Manage the Config tab and wire UI elements to CONFIG."""

    def __init__(
        self,
        config_widget: QWidget,
        btn_save_config: Optional[QPushButton] = None,
        btn_load_config: Optional[QPushButton] = None,
        on_config_changed: Optional[callable] = None,
        log_fn: Optional[callable] = None,
        on_vault_scanned: Optional[callable] = None,
    ):
        self.config_widget = config_widget
        self.btn_save_config = btn_save_config
        self.btn_save_config_as = None  # Will be found in _find_widgets
        self.btn_load_config = btn_load_config
        self.on_config_changed = on_config_changed  # Callback when config changes
        self.log_fn = log_fn or print
        self.on_vault_scanned = on_vault_scanned  # Callback when vault is scanned

        # Find all the UI widgets by name
        self._find_widgets()

        # Current selected marker color
        self.current_marker_color = "#FFFFFF"

        # Initialize vault viewer controller
        self.vault_viewer = None
        self._init_vault_viewer()

        # Load current CONFIG values into UI
        self.load_from_config()

        # Connect buttons
        if self.btn_save_config:
            self.btn_save_config.clicked.connect(self._on_save_config)
        if self.btn_save_config_as:
            self.btn_save_config_as.clicked.connect(self._on_save_config_as)
        if self.btn_load_config:
            self.btn_load_config.clicked.connect(self._on_load_config)
        if self.btn_refresh_ui:
            self.btn_refresh_ui.clicked.connect(self._on_refresh_ui)

        # Connect browse buttons
        self._connect_browse_buttons()

        # Connect color pickers
        self._connect_color_pickers()

        # Connect condition buttons
        self._connect_condition_buttons()

        # Connect config path helper UI
        self._connect_config_path_buttons()

    def _find_widgets(self):
        """Find all UI widgets in the config tab."""
        # HP Thresholds
        self.spin_monster_bloodied = self.config_widget.findChild(QDoubleSpinBox, "spin_monster_bloodied")
        self.spin_hero_bloodied = self.config_widget.findChild(QDoubleSpinBox, "spin_hero_bloodied")
        self.spin_monster_critical = self.config_widget.findChild(QDoubleSpinBox, "spin_monster_critical")
        self.spin_hero_critical = self.config_widget.findChild(QDoubleSpinBox, "spin_hero_critical")

        # Encounter Difficulty Thresholds
        self.spin_difficulty_easy = self.config_widget.findChild(QDoubleSpinBox, "spin_difficulty_easy")
        self.spin_difficulty_medium = self.config_widget.findChild(QDoubleSpinBox, "spin_difficulty_medium")
        self.spin_difficulty_hard = self.config_widget.findChild(QDoubleSpinBox, "spin_difficulty_hard")
        self.spin_difficulty_deadly_max = self.config_widget.findChild(QDoubleSpinBox, "spin_difficulty_deadly_max")

        # Map Markers
        self.spin_marker_start = self.config_widget.findChild(QSpinBox, "spin_marker_start")

        # Logging
        self.check_log_damage = self.config_widget.findChild(QCheckBox, "check_log_damage")
        self.check_log_heal = self.config_widget.findChild(QCheckBox, "check_log_heal")
        self.check_log_deaths = self.config_widget.findChild(QCheckBox, "check_log_deaths")
        self.check_log_conditions = self.config_widget.findChild(QCheckBox, "check_log_conditions")
        self.check_log_laststand = self.config_widget.findChild(QCheckBox, "check_log_laststand")

        # Autosave
        self.check_autosave_enabled = self.config_widget.findChild(QCheckBox, "check_autosave_enabled")
        self.edit_autosave_path = self.config_widget.findChild(QLineEdit, "edit_autosave_path")

        # Auto-refresh monster data
        self.check_auto_refresh_encounter = self.config_widget.findChild(QCheckBox, "check_auto_refresh_encounter")

        # Config file picker
        self.edit_config_path = self.config_widget.findChild(QLineEdit, "edit_config_path")
        self.btn_browse_config = self.config_widget.findChild(QPushButton, "btn_browse_config")

        # Paths
        self.edit_vault_path = self.config_widget.findChild(QLineEdit, "edit_vault_path")
        self.edit_obsidian_path = self.config_widget.findChild(QLineEdit, "edit_obsidian_path")
        self.edit_encounter_path = self.config_widget.findChild(QLineEdit, "edit_encounter_path")
        self.edit_party_path = self.config_widget.findChild(QLineEdit, "edit_party_path")
        self.edit_combat_log_path = self.config_widget.findChild(QLineEdit, "edit_combat_log_path")

        # Browse buttons for paths
        self.btn_browse_autosave = self.config_widget.findChild(QPushButton, "btn_browse_autosave")
        self.btn_browse_vault_path = self.config_widget.findChild(QPushButton, "btn_browse_vault_path")
        self.btn_browse_obsidian = self.config_widget.findChild(QPushButton, "btn_browse_obsidian")
        self.btn_browse_encounter = self.config_widget.findChild(QPushButton, "btn_browse_encounter")
        self.btn_browse_party = self.config_widget.findChild(QPushButton, "btn_browse_party")
        self.btn_browse_combat_log = self.config_widget.findChild(QPushButton, "btn_browse_combat_log")

        # Config save/load buttons
        self.btn_save_config_as = self.config_widget.findChild(QPushButton, "btn_save_config_as")
        self.label_config_status = self.config_widget.findChild(QLabel, "label_config_status")

        # Marker color picker and palette
        self.btn_marker_color_preview = self.config_widget.findChild(QPushButton, "btn_marker_color_preview")
        self.btn_add_marker_color = self.config_widget.findChild(QPushButton, "btn_add_marker_color")
        self.list_marker_palette = self.config_widget.findChild(QListWidget, "list_marker_palette")

        # HP/Condition color pickers (for legend colors)
        self.btn_color_healthy = self.config_widget.findChild(QPushButton, "btn_color_healthy")
        self.btn_color_bloodied = self.config_widget.findChild(QPushButton, "btn_color_bloodied")
        self.btn_color_critical = self.config_widget.findChild(QPushButton, "btn_color_critical")
        self.btn_color_down = self.config_widget.findChild(QPushButton, "btn_color_down")
        self.btn_color_conditions = self.config_widget.findChild(QPushButton, "btn_color_conditions")
        self.btn_refresh_ui = self.config_widget.findChild(QPushButton, "btn_refresh_ui")

        # Heroes tab column widths
        self.spin_heroes_col_name = self.config_widget.findChild(QSpinBox, "spin_heroes_col_name")
        self.spin_heroes_col_player = self.config_widget.findChild(QSpinBox, "spin_heroes_col_player")
        self.spin_heroes_col_lvl = self.config_widget.findChild(QSpinBox, "spin_heroes_col_lvl")
        self.spin_heroes_col_max = self.config_widget.findChild(QSpinBox, "spin_heroes_col_max")
        self.spin_heroes_col_class = self.config_widget.findChild(QSpinBox, "spin_heroes_col_class")
        self.spin_heroes_col_gm_notes = self.config_widget.findChild(QSpinBox, "spin_heroes_col_gm_notes")
        self.spin_heroes_col_player_notes = self.config_widget.findChild(QSpinBox, "spin_heroes_col_player_notes")
        self.spin_heroes_col_tmp = self.config_widget.findChild(QSpinBox, "spin_heroes_col_tmp")
        self.spin_heroes_col_conds = self.config_widget.findChild(QSpinBox, "spin_heroes_col_conds")

        # Monsters tab column widths
        self.spin_monsters_col_act = self.config_widget.findChild(QSpinBox, "spin_monsters_col_act")
        self.spin_monsters_col_health = self.config_widget.findChild(QSpinBox, "spin_monsters_col_health")
        self.spin_monsters_col_name = self.config_widget.findChild(QSpinBox, "spin_monsters_col_name")
        self.spin_monsters_col_marker = self.config_widget.findChild(QSpinBox, "spin_monsters_col_marker")
        self.spin_monsters_col_attack = self.config_widget.findChild(QSpinBox, "spin_monsters_col_attack")
        self.spin_monsters_col_con = self.config_widget.findChild(QSpinBox, "spin_monsters_col_con")
        self.spin_monsters_col_conds = self.config_widget.findChild(QSpinBox, "spin_monsters_col_conds")
        self.spin_monsters_col_hp = self.config_widget.findChild(QSpinBox, "spin_monsters_col_hp")
        self.spin_monsters_col_tmp = self.config_widget.findChild(QSpinBox, "spin_monsters_col_tmp")
        self.spin_monsters_col_max = self.config_widget.findChild(QSpinBox, "spin_monsters_col_max")

        # Table text sizes
        self.spin_heroes_table_text_size = self.config_widget.findChild(QSpinBox, "spin_heroes_table_text_size")
        self.spin_monsters_table_text_size = self.config_widget.findChild(QSpinBox, "spin_monsters_table_text_size")

        # Conditions table & buttons
        self.table_conditions = self.config_widget.findChild(QTableWidget, "table_conditions")
        self.btn_add_condition = self.config_widget.findChild(QPushButton, "btn_add_condition")
        self.btn_remove_condition = self.config_widget.findChild(QPushButton, "btn_remove_condition")
        if self.table_conditions:
            header = self.table_conditions.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        # Vault viewer widgets
        self.vault_edit = self.config_widget.findChild(QLineEdit, "vault_edit")
        self.btn_browse_vault = self.config_widget.findChild(QPushButton, "btn_browse_vault")
        self.btn_scan_vault = self.config_widget.findChild(QPushButton, "btn_scan_vault")
        self.btn_export_bestiary = self.config_widget.findChild(QPushButton, "btn_export_bestiary")
        self.btn_add_vault = self.config_widget.findChild(QPushButton, "btn_add_vault")
        self.file_list = self.config_widget.findChild(QListWidget, "file_list")
        self.biome_list = self.config_widget.findChild(QListWidget, "biome_list")
        self.legend_list = self.config_widget.findChild(QListWidget, "legend_list")
        self.debug_view = self.config_widget.findChild(QTextEdit, "debug_view")
        self.raw_view = self.config_widget.findChild(QTextEdit, "raw_view")
        self.stat_block_view = self.config_widget.findChild(QTextEdit, "stat_block_view")
        self.json_meta_view = self.config_widget.findChild(QTextEdit, "json_meta_view")
        self.json_raw_view = self.config_widget.findChild(QTextEdit, "json_raw_view")

    def load_from_config(self):
        """Load values from CONFIG into the UI widgets."""
        # HP Thresholds
        if self.spin_monster_bloodied:
            self.spin_monster_bloodied.setValue(CONFIG.monster_bloodied_threshold)
        if self.spin_hero_bloodied:
            self.spin_hero_bloodied.setValue(CONFIG.hero_bloodied_threshold)
        if self.spin_monster_critical:
            self.spin_monster_critical.setValue(CONFIG.monster_critical_threshold)
        if self.spin_hero_critical:
            self.spin_hero_critical.setValue(CONFIG.hero_critical_threshold)

        # Encounter Difficulty Thresholds
        if self.spin_difficulty_easy:
            self.spin_difficulty_easy.setValue(CONFIG.encounter_difficulty_easy)
        if self.spin_difficulty_medium:
            self.spin_difficulty_medium.setValue(CONFIG.encounter_difficulty_medium)
        if self.spin_difficulty_hard:
            self.spin_difficulty_hard.setValue(CONFIG.encounter_difficulty_hard)
        if self.spin_difficulty_deadly_max:
            self.spin_difficulty_deadly_max.setValue(CONFIG.encounter_difficulty_deadly_max)

        # Map Markers
        if self.spin_marker_start:
            self.spin_marker_start.setValue(CONFIG.marker_start_number)

        # Load marker palette
        if self.list_marker_palette:
            self.list_marker_palette.clear()
            for color in CONFIG.marker_palette:
                self._add_color_to_palette_list(color)

        # Logging
        if self.check_log_damage:
            self.check_log_damage.setChecked(CONFIG.log_damage_events)
        if self.check_log_heal:
            self.check_log_heal.setChecked(CONFIG.log_heal_events)
        if self.check_log_deaths:
            self.check_log_deaths.setChecked(CONFIG.log_deaths)
        if self.check_log_conditions:
            self.check_log_conditions.setChecked(CONFIG.log_condition_changes)
        if self.check_log_laststand:
            self.check_log_laststand.setChecked(CONFIG.log_last_stand_triggers)

        # Autosave
        if self.check_autosave_enabled:
            self.check_autosave_enabled.setChecked(CONFIG.autosave_enabled)
        if self.edit_autosave_path:
            self.edit_autosave_path.setText(CONFIG.autosave_path)

        # Auto-refresh
        if self.check_auto_refresh_encounter:
            self.check_auto_refresh_encounter.setChecked(CONFIG.auto_refresh_on_encounter_load)
            # Auto-save when this checkbox is toggled for better UX
            self.check_auto_refresh_encounter.toggled.connect(self._on_auto_refresh_toggled)

        # Paths
        if self.edit_vault_path:
            self.edit_vault_path.setText(CONFIG.default_monster_vault_path)
        if self.edit_obsidian_path:
            self.edit_obsidian_path.setText(CONFIG.obsidian_vault_path)
        if self.edit_config_path:
            current_path = get_config_path()
            self.edit_config_path.setText(str(current_path) if current_path else "")
        if self.edit_encounter_path:
            self.edit_encounter_path.setText(CONFIG.default_encounter_folder)
        if self.edit_party_path:
            self.edit_party_path.setText(CONFIG.default_party_folder)
        if self.edit_combat_log_path:
            self.edit_combat_log_path.setText(CONFIG.default_combat_log_folder)

        # Heroes tab column widths (Heroes Tab Mode)
        if self.spin_heroes_col_name:
            self.spin_heroes_col_name.setValue(CONFIG.hero_tab_col_name_width)
        if self.spin_heroes_col_player:
            self.spin_heroes_col_player.setValue(CONFIG.hero_tab_col_player_width)
        if self.spin_heroes_col_lvl:
            self.spin_heroes_col_lvl.setValue(CONFIG.hero_tab_col_level_width)
        if self.spin_heroes_col_max:
            self.spin_heroes_col_max.setValue(CONFIG.hero_tab_col_max_width)
        if self.spin_heroes_col_class:
            self.spin_heroes_col_class.setValue(CONFIG.hero_tab_col_class_width)
        if self.spin_heroes_col_gm_notes:
            self.spin_heroes_col_gm_notes.setValue(CONFIG.hero_tab_col_gm_notes_width)
        if self.spin_heroes_col_player_notes:
            self.spin_heroes_col_player_notes.setValue(CONFIG.hero_tab_col_player_notes_width)

        # Note: These might map to combat mode hero columns or notes columns
        # Based on the UI names, tmp and conds likely map to combat mode
        if self.spin_heroes_col_tmp:
            self.spin_heroes_col_tmp.setValue(CONFIG.hero_combat_col_tmp_width)
        if self.spin_heroes_col_conds:
            self.spin_heroes_col_conds.setValue(CONFIG.hero_combat_col_conds_width)

        if self.spin_heroes_table_text_size:
            self.spin_heroes_table_text_size.setValue(CONFIG.hero_table_font_size)
        if self.spin_monsters_table_text_size:
            self.spin_monsters_table_text_size.setValue(CONFIG.monster_table_font_size)

        # Monsters tab column widths (Combat Tab)
        if self.spin_monsters_col_act:
            self.spin_monsters_col_act.setValue(CONFIG.combat_col_active_width)
        if self.spin_monsters_col_health:
            self.spin_monsters_col_health.setValue(CONFIG.combat_col_heal_width)
        if self.spin_monsters_col_name:
            self.spin_monsters_col_name.setValue(CONFIG.combat_col_name_width)
        if self.spin_monsters_col_marker:
            self.spin_monsters_col_marker.setValue(CONFIG.combat_col_marker_width)
        if self.spin_monsters_col_attack:
            self.spin_monsters_col_attack.setValue(CONFIG.combat_col_hurt_width)
        if self.spin_monsters_col_con:
            self.spin_monsters_col_con.setValue(CONFIG.combat_col_con_width)
        if self.spin_monsters_col_conds:
            self.spin_monsters_col_conds.setValue(CONFIG.combat_col_conds_width)
        if self.spin_monsters_col_hp:
            self.spin_monsters_col_hp.setValue(CONFIG.combat_col_hp_width)
        if self.spin_monsters_col_tmp:
            self.spin_monsters_col_tmp.setValue(CONFIG.combat_col_tmp_width)
        if self.spin_monsters_col_max:
            self.spin_monsters_col_max.setValue(CONFIG.combat_col_max_width)

        # Conditions table needs to reflect the list
        self._populate_conditions_table()

    def _init_vault_viewer(self):
        """Initialize the vault viewer controller if UI widgets are present."""
        # Only initialize if we have at least some of the vault viewer widgets
        if self.vault_edit or self.file_list or self.biome_list or self.legend_list:
            # Vault viewer is optional; only wire when widgets exist in the UI.
            self.vault_viewer = VaultViewerController(
                parent_widget=self.config_widget,
                vault_edit=self.vault_edit,
                btn_browse_vault=self.btn_browse_vault,
                btn_add_vault=self.btn_add_vault,
                btn_scan_vault=self.btn_scan_vault,
                btn_export_bestiary=self.btn_export_bestiary,
                file_list=self.file_list,
                biome_list=self.biome_list,
                legend_list=self.legend_list,
                debug_view=self.debug_view,
                raw_view=self.raw_view,
                stat_block_view=self.stat_block_view,
                json_meta_view=self.json_meta_view,
                json_raw_view=self.json_raw_view,
                log_fn=self.log_fn,
                on_vault_scanned=self.on_vault_scanned,
            )

    def save_to_config(self):
        """Save values from UI widgets back to CONFIG."""
        # HP Thresholds
        if self.spin_monster_bloodied:
            CONFIG.monster_bloodied_threshold = self.spin_monster_bloodied.value()
        if self.spin_hero_bloodied:
            CONFIG.hero_bloodied_threshold = self.spin_hero_bloodied.value()
        if self.spin_monster_critical:
            CONFIG.monster_critical_threshold = self.spin_monster_critical.value()
        if self.spin_hero_critical:
            CONFIG.hero_critical_threshold = self.spin_hero_critical.value()

        # Encounter Difficulty Thresholds
        if self.spin_difficulty_easy:
            CONFIG.encounter_difficulty_easy = self.spin_difficulty_easy.value()
        if self.spin_difficulty_medium:
            CONFIG.encounter_difficulty_medium = self.spin_difficulty_medium.value()
        if self.spin_difficulty_hard:
            CONFIG.encounter_difficulty_hard = self.spin_difficulty_hard.value()
        if self.spin_difficulty_deadly_max:
            CONFIG.encounter_difficulty_deadly_max = self.spin_difficulty_deadly_max.value()

        # Map Markers
        if self.spin_marker_start:
            CONFIG.marker_start_number = self.spin_marker_start.value()

        # Logging
        if self.check_log_damage:
            CONFIG.log_damage_events = self.check_log_damage.isChecked()
        if self.check_log_heal:
            CONFIG.log_heal_events = self.check_log_heal.isChecked()
        if self.check_log_deaths:
            CONFIG.log_deaths = self.check_log_deaths.isChecked()
        if self.check_log_conditions:
            CONFIG.log_condition_changes = self.check_log_conditions.isChecked()
        if self.check_log_laststand:
            CONFIG.log_last_stand_triggers = self.check_log_laststand.isChecked()

        # Autosave
        if self.check_autosave_enabled:
            CONFIG.autosave_enabled = self.check_autosave_enabled.isChecked()
        if self.edit_autosave_path:
            CONFIG.autosave_path = self.edit_autosave_path.text()

        # Auto-refresh
        if self.check_auto_refresh_encounter:
            CONFIG.auto_refresh_on_encounter_load = self.check_auto_refresh_encounter.isChecked()

        # Paths
        if self.edit_vault_path:
            CONFIG.default_monster_vault_path = self.edit_vault_path.text()
        if self.edit_obsidian_path:
            CONFIG.obsidian_vault_path = self.edit_obsidian_path.text()
        if self.edit_encounter_path:
            CONFIG.default_encounter_folder = self.edit_encounter_path.text()
        if self.edit_party_path:
            CONFIG.default_party_folder = self.edit_party_path.text()
        if self.edit_combat_log_path:
            CONFIG.default_combat_log_folder = self.edit_combat_log_path.text()

        # Heroes tab column widths (Heroes Tab Mode)
        if self.spin_heroes_col_name:
            CONFIG.hero_tab_col_name_width = self.spin_heroes_col_name.value()
        if self.spin_heroes_col_player:
            CONFIG.hero_tab_col_player_width = self.spin_heroes_col_player.value()
        if self.spin_heroes_col_lvl:
            CONFIG.hero_tab_col_level_width = self.spin_heroes_col_lvl.value()
        if self.spin_heroes_col_max:
            CONFIG.hero_tab_col_max_width = self.spin_heroes_col_max.value()
        if self.spin_heroes_col_class:
            CONFIG.hero_tab_col_class_width = self.spin_heroes_col_class.value()
        if self.spin_heroes_col_gm_notes:
            CONFIG.hero_tab_col_gm_notes_width = self.spin_heroes_col_gm_notes.value()
        if self.spin_heroes_col_player_notes:
            CONFIG.hero_tab_col_player_notes_width = self.spin_heroes_col_player_notes.value()

        # Combat mode hero columns
        if self.spin_heroes_col_tmp:
            CONFIG.hero_combat_col_tmp_width = self.spin_heroes_col_tmp.value()
        if self.spin_heroes_col_conds:
            CONFIG.hero_combat_col_conds_width = self.spin_heroes_col_conds.value()

        # Monsters tab column widths (Combat Tab)
        if self.spin_monsters_col_act:
            CONFIG.combat_col_active_width = self.spin_monsters_col_act.value()
        if self.spin_monsters_col_health:
            CONFIG.combat_col_heal_width = self.spin_monsters_col_health.value()
        if self.spin_monsters_col_name:
            CONFIG.combat_col_name_width = self.spin_monsters_col_name.value()
        if self.spin_monsters_col_marker:
            CONFIG.combat_col_marker_width = self.spin_monsters_col_marker.value()
        if self.spin_monsters_col_attack:
            CONFIG.combat_col_hurt_width = self.spin_monsters_col_attack.value()
        if self.spin_monsters_col_con:
            CONFIG.combat_col_con_width = self.spin_monsters_col_con.value()
        if self.spin_monsters_col_conds:
            CONFIG.combat_col_conds_width = self.spin_monsters_col_conds.value()
        if self.spin_monsters_col_hp:
            CONFIG.combat_col_hp_width = self.spin_monsters_col_hp.value()
        if self.spin_monsters_col_tmp:
            CONFIG.combat_col_tmp_width = self.spin_monsters_col_tmp.value()
        if self.spin_monsters_col_max:
            CONFIG.combat_col_max_width = self.spin_monsters_col_max.value()

        if self.spin_heroes_table_text_size:
            CONFIG.hero_table_font_size = self.spin_heroes_table_text_size.value()
        if self.spin_monsters_table_text_size:
            CONFIG.monster_table_font_size = self.spin_monsters_table_text_size.value()

    def _on_auto_refresh_toggled(self, checked: bool):
        """Auto-save config when auto-refresh checkbox is toggled."""
        CONFIG.auto_refresh_on_encounter_load = checked
        # Save to the currently selected config file
        config_path = get_config_path()
        if config_path:
            save_config(str(config_path))

    def _on_save_config(self):
        """Handle Save Config button click - quick save to current config file."""
        from datetime import datetime

        # First save UI values to CONFIG
        self.save_to_config()

        # Notify that config has changed (so tables can update their column widths)
        if self.on_config_changed:
            self.on_config_changed()

        # Save to the currently selected config file
        config_path = get_config_path()
        if config_path:
            save_config(str(config_path))
            timestamp = datetime.now().strftime("%I:%M:%S %p")
            status_msg = f"Saved successfully at {timestamp}"
            if self.label_config_status:
                self.label_config_status.setText(status_msg)
            self.log_fn(f"Config saved to {config_path}")
        else:
            # No config file selected, fall back to Save As dialog
            self._on_save_config_as()

    def _on_save_config_as(self):
        """Handle Save Config As button click - save to a new file."""
        from datetime import datetime

        # First save UI values to CONFIG
        self.save_to_config()

        # Notify that config has changed (so tables can update their column widths)
        if self.on_config_changed:
            self.on_config_changed()

        # Open dialog to choose where to save
        current_path = get_config_path()
        default_path = current_path if current_path else Path("config.json")
        path, _ = QFileDialog.getSaveFileName(
            self.config_widget,
            "Save Config As",
            str(default_path),
            "JSON Files (*.json);;All Files (*)",
        )
        if path:
            save_config(path)
            timestamp = datetime.now().strftime("%I:%M:%S %p")
            status_msg = f"Saved successfully at {timestamp}"
            if self.label_config_status:
                self.label_config_status.setText(status_msg)
            self.log_fn(f"Config saved to {path}")

    def _on_load_config(self):
        """Handle Load Config button click."""
        path_text = self.edit_config_path.text().strip() if self.edit_config_path else ""
        if path_text:
            candidate = Path(path_text)
            if candidate.is_file():
                self._load_config_from_path(candidate)
                return

        current_path = get_config_path()
        default_path = current_path if current_path else Path("config.json")
        path, _ = QFileDialog.getOpenFileName(
            self.config_widget,
            "Load Config",
            str(default_path),
            "JSON Files (*.json);;All Files (*)",
        )
        if path:
            self._load_config_from_path(Path(path))

    def _on_refresh_ui(self):
        """Refresh the UI using the current configuration."""
        current_path = get_config_path()
        if current_path:
            self._load_config_from_path(current_path)

    def _on_browse_config(self):
        """Let the user pick a config file using a file dialog."""
        current = self.edit_config_path.text().strip() if self.edit_config_path else ""
        current_path = get_config_path()
        default_path = Path(current) if current else (current_path if current_path else Path.cwd())
        if not default_path.exists():
            default_path = default_path.parent if default_path.parent.exists() else Path.cwd()
        path, _ = QFileDialog.getOpenFileName(
            self.config_widget,
            "Select Config File",
            str(default_path),
            "JSON Files (*.json);;All Files (*)",
        )
        if path:
            if self.edit_config_path:
                self.edit_config_path.setText(path)
            self._load_config_from_path(Path(path))

    def _load_config_from_path(self, path: Path) -> None:
        """Load configuration from the provided path and refresh the UI."""
        load_config(path)
        if self.edit_config_path:
            self.edit_config_path.setText(str(path))
        self.load_from_config()
        if self.on_config_changed:
            self.on_config_changed()

    def _connect_browse_buttons(self):
        """Connect all browse buttons to their respective handlers."""
        if self.btn_browse_autosave:
            self.btn_browse_autosave.clicked.connect(self._on_browse_autosave)
        if self.btn_browse_vault_path:
            self.btn_browse_vault_path.clicked.connect(self._on_browse_vault_folder)
        if self.btn_browse_obsidian:
            self.btn_browse_obsidian.clicked.connect(self._on_browse_obsidian_folder)
        if self.btn_browse_encounter:
            self.btn_browse_encounter.clicked.connect(self._on_browse_encounter_folder)
        if self.btn_browse_party:
            self.btn_browse_party.clicked.connect(self._on_browse_party_folder)
        if self.btn_browse_combat_log:
            self.btn_browse_combat_log.clicked.connect(self._on_browse_combat_log_folder)

    def _connect_config_path_buttons(self):
        """Connect the config file picker button."""
        if self.btn_browse_config:
            self.btn_browse_config.clicked.connect(self._on_browse_config)

    def _connect_color_pickers(self):
        """Connect all color picker buttons and initialize displays."""
        # Marker color picker
        if self.btn_marker_color_preview:
            self.btn_marker_color_preview.clicked.connect(self._on_pick_marker_color)
            self._update_color_button(self.btn_marker_color_preview, self.current_marker_color)
        if self.btn_add_marker_color:
            self.btn_add_marker_color.clicked.connect(self._on_add_marker_to_palette)

        # Connect double-click on palette list to delete colors
        if self.list_marker_palette:
            self.list_marker_palette.itemDoubleClicked.connect(self._on_palette_item_double_clicked)

        # HP/Condition color pickers (for legend label colors)
        if self.btn_color_healthy:
            self.btn_color_healthy.clicked.connect(lambda: self._on_pick_hp_color("healthy"))
            self._update_color_button_from_rgb(self.btn_color_healthy, CONFIG.hp_healthy_color)
        if self.btn_color_bloodied:
            self.btn_color_bloodied.clicked.connect(lambda: self._on_pick_hp_color("bloodied"))
            self._update_color_button_from_rgb(self.btn_color_bloodied, CONFIG.hp_bloodied_color)
        if self.btn_color_critical:
            self.btn_color_critical.clicked.connect(lambda: self._on_pick_hp_color("critical"))
            self._update_color_button_from_rgb(self.btn_color_critical, CONFIG.hp_critical_color)
        if self.btn_color_down:
            self.btn_color_down.clicked.connect(lambda: self._on_pick_hp_color("down"))
            self._update_color_button_from_rgb(self.btn_color_down, CONFIG.hp_down_color)
        if self.btn_color_conditions:
            self.btn_color_conditions.clicked.connect(lambda: self._on_pick_hp_color("conditions"))
            self._update_color_button_from_rgb(self.btn_color_conditions, CONFIG.hp_conditions_color)

    def _connect_condition_buttons(self):
        """Wire add/remove buttons for the conditions table."""
        if self.btn_add_condition:
            self.btn_add_condition.clicked.connect(self._on_add_condition)
        if self.btn_remove_condition:
            self.btn_remove_condition.clicked.connect(self._on_remove_condition)

    def _populate_conditions_table(self):
        """Fill the conditions table from CONFIG.available_conditions."""
        if self.table_conditions is None:
            return
        self.table_conditions.setRowCount(0)
        for row, name in enumerate(CONFIG.available_conditions):
            self.table_conditions.insertRow(row)
            name_item = QTableWidgetItem(name)
            desc = CONDITION_DESCRIPTIONS.get(name, "")
            desc_item = QTableWidgetItem(desc)
            for item in (name_item, desc_item):
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_conditions.setItem(row, 0, name_item)
            self.table_conditions.setItem(row, 1, desc_item)

    def _on_add_condition(self):
        """Prompt the user for a new condition name."""
        if self.table_conditions is None:
            return
        name, ok = QInputDialog.getText(self.config_widget, "Add Condition", "Condition name:")
        if not ok or not name:
            return
        name = name.strip()
        if not name:
            return
        if name in CONFIG.available_conditions:
            return
        CONFIG.available_conditions.append(name)
        self._populate_conditions_table()
        if self.on_config_changed:
            self.on_config_changed()

    def _on_remove_condition(self):
        """Remove the currently selected condition."""
        if self.table_conditions is None:
            return
        row = self.table_conditions.currentRow()
        if row < 0:
            return
        item = self.table_conditions.item(row, 0)
        if not item:
            return
        name = item.text()
        CONFIG.available_conditions = [c for c in CONFIG.available_conditions if c != name]
        self._populate_conditions_table()
        if self.on_config_changed:
            self.on_config_changed()

    def _on_browse_autosave(self):
        """Browse for autosave file location."""
        current_path = self.edit_autosave_path.text() if self.edit_autosave_path else ""
        path, _ = QFileDialog.getSaveFileName(
            self.config_widget,
            "Select Autosave File Location",
            current_path or str(Path.home()),
            "JSON Files (*.json);;All Files (*)",
        )
        if path and self.edit_autosave_path:
            self.edit_autosave_path.setText(path)

    def _on_browse_vault_folder(self):
        """Browse for monster vault files."""
        current_path = self.edit_vault_path.text() if self.edit_vault_path else ""
        paths, _ = QFileDialog.getOpenFileNames(
            self.config_widget,
            "Select Monster Vault File(s)",
            current_path or str(Path.home()),
            "JSON Files (*.json);;All Files (*)",
        )
        if paths and self.edit_vault_path:
            # Persist multiple paths as a semicolon-delimited string.
            self.edit_vault_path.setText(";".join(paths))

    def _on_browse_obsidian_folder(self):
        """Browse for Obsidian folder."""
        current_path = self.edit_obsidian_path.text() if self.edit_obsidian_path else ""
        path = QFileDialog.getExistingDirectory(
            self.config_widget,
            "Select Obsidian Vault Folder",
            current_path or str(Path.home()),
        )
        if path and self.edit_obsidian_path:
            self.edit_obsidian_path.setText(path)
            # Auto-infer folder paths when vault is set
            self._auto_infer_folders_from_vault(path)

    def _auto_infer_folders_from_vault(self, vault_path: str):
        """Auto-detect and set folder paths based on the vault."""
        from PySide6.QtWidgets import QMessageBox

        vault = Path(vault_path)
        if not vault.exists():
            return

        inferred_paths = {}

        # Check for encounter folder
        if not self.edit_encounter_path or not self.edit_encounter_path.text():
            for candidate in ["Encounters", "Sessions", "Campaign/Encounters"]:
                test_path = vault / candidate
                if test_path.exists():
                    inferred_paths["Encounters"] = candidate
                    break
            else:
                inferred_paths["Encounters"] = "Encounters"

        # Check for party folder
        if not self.edit_party_path or not self.edit_party_path.text():
            for candidate in ["Heroes", "Party", "Characters", "Campaign/Heroes"]:
                test_path = vault / candidate
                if test_path.exists():
                    inferred_paths["Heroes"] = candidate
                    break
            else:
                inferred_paths["Heroes"] = "Heroes"

        # Check for combat log folder
        if not self.edit_combat_log_path or not self.edit_combat_log_path.text():
            for candidate in ["Combat Logs", "Logs", "Campaign/Logs"]:
                test_path = vault / candidate
                if test_path.exists():
                    inferred_paths["Combat Logs"] = candidate
                    break
            else:
                inferred_paths["Combat Logs"] = "Combat Logs"

        # Apply inferred paths
        if inferred_paths:
            msg_parts = ["Auto-detected the following folders:"]
            for folder_type, folder_name in inferred_paths.items():
                msg_parts.append(f"  • {folder_type}: {folder_name}")

            if self.edit_encounter_path and "Encounters" in inferred_paths:
                self.edit_encounter_path.setText(inferred_paths["Encounters"])
            if self.edit_party_path and "Heroes" in inferred_paths:
                self.edit_party_path.setText(inferred_paths["Heroes"])
            if self.edit_combat_log_path and "Combat Logs" in inferred_paths:
                self.edit_combat_log_path.setText(inferred_paths["Combat Logs"])

            QMessageBox.information(
                self.config_widget,
                "Folders Auto-Detected",
                "\n".join(msg_parts) + "\n\nThese are relative to the vault path."
            )

    def _on_browse_encounter_folder(self):
        """Browse for encounter folder."""
        current_path = self.edit_encounter_path.text() if self.edit_encounter_path else ""
        path = QFileDialog.getExistingDirectory(
            self.config_widget,
            "Select Encounter Folder",
            current_path or str(Path.home()),
        )
        if path and self.edit_encounter_path:
            self.edit_encounter_path.setText(path)

    def _on_browse_party_folder(self):
        """Browse for party folder."""
        current_path = self.edit_party_path.text() if self.edit_party_path else ""
        path = QFileDialog.getExistingDirectory(
            self.config_widget,
            "Select Party Folder",
            current_path or str(Path.home()),
        )
        if path and self.edit_party_path:
            self.edit_party_path.setText(path)

    def _on_browse_combat_log_folder(self):
        """Browse for combat log folder."""
        current_path = self.edit_combat_log_path.text() if self.edit_combat_log_path else ""
        path = QFileDialog.getExistingDirectory(
            self.config_widget,
            "Select Combat Log Folder",
            current_path or str(Path.home()),
        )
        if path and self.edit_combat_log_path:
            self.edit_combat_log_path.setText(path)

    def _on_pick_marker_color(self):
        """Open color picker for marker color."""
        initial_color = QColor(self.current_marker_color)
        color = QColorDialog.getColor(initial_color, self.config_widget, "Pick Marker Color")
        if color.isValid():
            self.current_marker_color = color.name()
            self._update_color_button(self.btn_marker_color_preview, self.current_marker_color)

    def _on_add_marker_to_palette(self):
        """Add the currently selected marker color to the palette."""
        if not self.list_marker_palette:
            return

        # Add to CONFIG first to avoid duplicates
        if self.current_marker_color not in CONFIG.marker_palette:
            CONFIG.marker_palette.append(self.current_marker_color)
            self._add_color_to_palette_list(self.current_marker_color)

    def _on_palette_item_double_clicked(self, item: QListWidgetItem):
        """Handle double-click on a palette item to delete it."""
        if not item or not self.list_marker_palette:
            return

        # Get the color hex from the item data
        color_hex = item.data(Qt.ItemDataRole.UserRole)
        if not color_hex:
            return

        # Show confirmation dialog
        reply = QMessageBox.question(
            self.config_widget,
            "Delete Color",
            f"Are you sure you want to delete {color_hex} from the marker palette?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Remove from CONFIG
            if color_hex in CONFIG.marker_palette:
                CONFIG.marker_palette.remove(color_hex)

            # Remove from list widget
            row = self.list_marker_palette.row(item)
            self.list_marker_palette.takeItem(row)

    def _on_pick_hp_color(self, color_type: str):
        """Open color picker for HP condition colors."""
        button_map = {
            "healthy": (self.btn_color_healthy, CONFIG.hp_healthy_color),
            "bloodied": (self.btn_color_bloodied, CONFIG.hp_bloodied_color),
            "critical": (self.btn_color_critical, CONFIG.hp_critical_color),
            "down": (self.btn_color_down, CONFIG.hp_down_color),
            "conditions": (self.btn_color_conditions, CONFIG.hp_conditions_color),
        }

        button_info = button_map.get(color_type)
        if not button_info:
            return

        button, current_rgb = button_info
        if not button:
            return

        # Get current color from CONFIG
        current_color = QColor(*current_rgb)
        color = QColorDialog.getColor(current_color, self.config_widget, f"Pick {color_type.title()} Color")

        if color.isValid():
            rgb_tuple = (color.red(), color.green(), color.blue())

            # Save to CONFIG
            if color_type == "healthy":
                CONFIG.hp_healthy_color = rgb_tuple
            elif color_type == "bloodied":
                CONFIG.hp_bloodied_color = rgb_tuple
            elif color_type == "critical":
                CONFIG.hp_critical_color = rgb_tuple
            elif color_type == "down":
                CONFIG.hp_down_color = rgb_tuple
            elif color_type == "conditions":
                CONFIG.hp_conditions_color = rgb_tuple

            # Update button display
            self._update_color_button_from_rgb(button, rgb_tuple)

            # Update legend labels if they exist
            self._update_legend_labels()

    def _update_color_button(self, button: QPushButton, color: str):
        """Update a button's background color to show the selected color."""
        if not button:
            return
        button.setStyleSheet(f"background-color: {color}; color: white;")
        button.setText(color)

    def _add_color_to_palette_list(self, color_hex: str):
        """Add a color to the marker palette list widget with proper visual display."""
        if not self.list_marker_palette:
            return

        # Create list item with colored background
        item = QListWidgetItem(f"  {color_hex}")

        # Set background to the marker color
        item.setBackground(QColor(color_hex))

        # Calculate contrasting text color
        color = QColor(color_hex)
        r, g, b = color.red(), color.green(), color.blue()
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        text_color = QColor("black") if luminance > 0.5 else QColor("white")
        item.setForeground(text_color)

        # Make text bold and larger
        font = QFont()
        font.setBold(True)
        font.setPointSize(11)
        item.setFont(font)

        # Store the hex value in the item data for retrieval
        item.setData(Qt.ItemDataRole.UserRole, color_hex)

        # Add to list
        self.list_marker_palette.addItem(item)

    def _update_color_button_from_rgb(self, button: QPushButton, rgb_tuple: tuple):
        """Update a button's background color from an RGB tuple."""
        if not button:
            return
        r, g, b = rgb_tuple
        button.setStyleSheet(f"background-color: rgb({r}, {g}, {b}); color: white;")
        button.setText(f"rgb({r}, {g}, {b})")

    def _update_legend_labels(self):
        """Update the legend labels on the Combat tab with the current HP colors."""
        from PySide6.QtWidgets import QLabel

        # Try to find legend labels in the main window
        # These labels are named: label_legendHealthy, label_legendBloodied, etc.
        window = self.config_widget.window()

        label_map = {
            "label_legendHealthy": CONFIG.hp_healthy_color,
            "label_legendBloodied": CONFIG.hp_bloodied_color,
            "label_legendCritical": CONFIG.hp_critical_color,
            "label_legendDown": CONFIG.hp_down_color,
            "label_legendConditions": CONFIG.hp_conditions_color,
        }

        for label_name, rgb_tuple in label_map.items():
            label = window.findChild(QLabel, label_name)
            if label:
                r, g, b = rgb_tuple
                label.setStyleSheet(f"background-color: rgb({r}, {g}, {b}); color: white; padding: 2px;")
