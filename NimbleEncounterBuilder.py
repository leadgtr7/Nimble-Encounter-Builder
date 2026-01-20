"""
NimbleEncounterBuilder.py
======================================================================
Main loader for nimbleHandy.ui that wires tab controllers to the core
CombatManager. Tabs are split into dedicated modules; currently the
Bestiary tab is powered by tabs.bestiary_tab.BestiaryTabController.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QFile, QIODevice, Qt
from PySide6.QtGui import QColor, QPalette, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QBoxLayout,
    QCheckBox,
    QComboBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSplashScreen,
    QTableWidget,
    QTextEdit,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtUiTools import QUiLoader

PROJECT_ROOT = Path(__file__).resolve().parent
PROJECT_UI_DIR = PROJECT_ROOT
for path in (PROJECT_ROOT, PROJECT_UI_DIR):
    if path.exists() and str(path) not in sys.path:
        sys.path.insert(0, str(path))

from modules import config
from modules import make_snapshot
from modules.combatManager import CombatManager
from tabs.bestiary_tab import BestiaryTabController
from tabs.combat_tab import CombatTabController
from tabs.config_tab import ConfigTabController
from tabs.hero_dialog import show_add_edit_hero_dialog
from tabs.heroes_tab import HeroesTabController


class NimbleMainApp:
    """Load the UI, initialize core services, and attach tab controllers."""

    LICENSE_BANNER_TEXT = (
        "Nimble Encounter Builder is an independent product published under the "
        "Nimble 3rd Party Creator License. Nimble © Nimble Co."
    )

    def __init__(self, ui_path: Path):
        self.ui_path = ui_path

        # Load UI
        loader = QUiLoader()
        ui_file = QFile(str(ui_path))
        if not ui_file.open(QIODevice.OpenModeFlag.ReadOnly):
            raise RuntimeError(f"Cannot open UI file: {ui_path}")
        self.window: QWidget = loader.load(ui_file)
        ui_file.close()
        if self.window is None:
            raise RuntimeError(f"Failed to load UI from: {ui_path}")

        # Set Combat tab as the default tab on startup
        tab_widget = self.window.findChild(QTabWidget, "mainTabs")
        if tab_widget:
            combat_tab_widget = self.window.findChild(QWidget, "tab_combat")
            if combat_tab_widget:
                tab_widget.setCurrentWidget(combat_tab_widget)

        self._add_license_banners()

        # Core manager
        self.manager = CombatManager()

        # Optional log widget (Combat Extras tab)
        self.combat_log: Optional[QTextEdit] = self.window.findChild(
            QTextEdit, "combat_log_text"
        )

        # Wire logging
        self.manager.on_log = self._append_log

        # Ensure config path is set before wiring tabs that read config values
        # (tab controllers read CONFIG during init for widths/paths)
        self._ensure_config_path()

        # Tab controllers
        self.bestiary = None
        self.combat = None
        self.heroes = None
        self.heroes_tab = None
        self.config = None
        # Avoid loading autosave multiple times if tabs refresh early.
        self._session_loaded = False
        self._init_bestiary_tab()
        self._init_combat_tab()
        self._init_heroes_tab()
        self._init_config_tab()
        self._init_help_tab()
        self._init_log_buttons()
        self._prompt_load_latest_log()

        # Install close event handler to auto-save log
        # (we keep the UI open long enough for autosave to finish)
        self.window.closeEvent = self._on_window_close

    # ------------------------------------------------------------------#
    # Tabs
    # ------------------------------------------------------------------#

    def _init_bestiary_tab(self) -> None:
        """Setup the Bestiary tab controller."""
        lm = self.window.findChild(QListWidget, "list_monsters_bestiary")
        sp = self.window.findChild(QTextEdit, "stat_block_preview_bestiary")
        te = self.window.findChild(QTableWidget, "monsters_table_bestiary")
        if lm is None or sp is None or te is None:
            raise RuntimeError(
                "Bestiary widgets not found (list_monsters_bestiary / "
                "stat_block_preview_bestiary / monsters_table_bestiary)."
            )
        # Non-required widgets (filters/buttons) may be absent; pass through as Optional
        en = self.window.findChild(QLineEdit, "lineEdit_monsterSearch_bestiary")
        cb = self.window.findChild(QComboBox, "combo_biomeSearch_bestiary")
        el = self.window.findChild(QLineEdit, "lineEdit_levelSearch_bestiary")
        lg = self.window.findChild(QCheckBox, "checkbox_show_legendary_bestiary")
        ba = self.window.findChild(QPushButton, "btn_add_monster_bestiary")
        bd = self.window.findChild(QPushButton, "btn_del_monster_bestiary")
        bc = self.window.findChild(QPushButton, "btn_clear_encounter_bestiary")
        bs = self.window.findChild(QPushButton, "btn_save_encounter_bestiary")
        bl = self.window.findChild(QPushButton, "btn_load_encounter_bestiary")
        br = self.window.findChild(QPushButton, "btn_random_encounter_bestiary")
        bsc = self.window.findChild(QPushButton, "btn_set_color_bestiary")
        label_diff = self.window.findChild(QLabel, "label_encounter_diff_bestiary")

        self.bestiary = BestiaryTabController(
            manager=self.manager,
            list_monsters=lm,
            stat_preview=sp,
            table_encounter=te,
            edit_name=en,
            combo_biome=cb,
            edit_level=el,
            checkbox_legendary=lg,
            btn_add=ba,
            btn_del=bd,
            btn_clear=bc,
            btn_load=bl,
            btn_save=bs,
            btn_random=br,
            btn_set_color=bsc,
            label_difficulty=label_diff,
            log_fn=self._append_log,
        )
        self._refresh_all_tabs()

    def _init_combat_tab(self) -> None:
        """Setup the Combat tab controller (monsters table)."""
        te = self.window.findChild(QTableWidget, "monsters_table_combat")
        if te is None:
            # Combat tab not present in this UI layout.
            return
        stat_preview = self.window.findChild(QTextEdit, "combatStatBlockPreview")
        loot_text = self.window.findChild(QTextEdit, "loot_text")
        btn_reset = self.window.findChild(QPushButton, "btn_reset_combat")
        label_difficulty = self.window.findChild(QLabel, "label_encounter_diff")
        btn_add = self.window.findChild(QPushButton, "btn_add_monster")
        btn_delete = self.window.findChild(QPushButton, "btn_del_monster")
        btn_clear = self.window.findChild(QPushButton, "btn_clear_encounter")
        btn_set_color = self.window.findChild(QPushButton, "btn_set_color")
        self.combat = CombatTabController(
            manager=self.manager,
            table=te,
            stat_preview=stat_preview,
            loot_view=loot_text,
            btn_reset=btn_reset,
            label_difficulty=label_difficulty,
            btn_add=btn_add,
            btn_delete=btn_delete,
            btn_clear=btn_clear,
            btn_set_color=btn_set_color,
        )
        self._refresh_all_tabs()

    def _init_heroes_tab(self) -> None:
        """Setup the Heroes tab controller."""
        te_combat = self.window.findChild(QTableWidget, "heroes_table_combat")
        te_heroes_tab = self.window.findChild(QTableWidget, "heroes_table_heroesTab")
        btn_import = self.window.findChild(QPushButton, "btn_import_party_heroesTab")
        btn_export = self.window.findChild(QPushButton, "btn_export_party_heroesTab")
        if te_combat is None and te_heroes_tab is None:
            # No heroes tables in this UI layout.
            return

        if te_combat is not None:
            self.heroes = HeroesTabController(manager=self.manager, table=te_combat)
        if te_heroes_tab is not None:
            # Avoid double-wiring if both table references are the same widget
            if self.heroes is None or te_heroes_tab is not te_combat:
                self.heroes_tab = HeroesTabController(
                    manager=self.manager,
                    table=te_heroes_tab,
                    btn_import=btn_import,
                    btn_export=btn_export,
                    mode="heroes_tab",
                    log_fn=self._append_log,
                )

        add_button = self.window.findChild(QPushButton, "btn_add_hero_heroesTab")
        if add_button is not None:
            add_button.clicked.connect(self._on_add_hero_clicked)

        del_button = self.window.findChild(QPushButton, "btn_del_hero_heroesTab")
        if del_button is not None:
            del_button.clicked.connect(self._on_delete_hero_clicked)

        self._refresh_all_tabs()

    def _init_config_tab(self) -> None:
        """Setup the Config tab controller."""
        # Find the config tab widget
        config_widget = self.window.findChild(QWidget, "tab_config")
        if config_widget is None:
            # Config tab not present in this UI layout.
            return

        # Find Save/Load Config buttons (if they exist in the UI)
        btn_save = self.window.findChild(QPushButton, "btn_save_config")
        btn_load = self.window.findChild(QPushButton, "btn_load_config")

        # Initialize the config tab controller
        self.config = ConfigTabController(
            config_widget=config_widget,
            btn_save_config=btn_save,
            btn_load_config=btn_load,
            on_config_changed=self._on_config_changed,
            log_fn=self._append_log,
            on_vault_scanned=self._on_vault_scanned,
        )

    def _init_help_tab(self) -> None:
        """Load the README.html file into the Help tab."""
        help_text_widget = self.window.findChild(QTextEdit, "help_text")
        if help_text_widget is None:
            # Help tab is optional in some UI layouts.
            return

        # Load the README.html file
        readme_path = PROJECT_ROOT / "README.html"
        if readme_path.exists():
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                help_text_widget.setHtml(html_content)
            except Exception as exc:
                help_text_widget.setPlainText(f"Error loading help file: {exc}")
        else:
            help_text_widget.setPlainText("Help file not found. Please ensure README.html exists in the application directory.")

    def _add_license_banners(self) -> None:
        """Add a small license banner to the bottom of each main tab."""
        tab_names = [
            "tab_combat",
            "tab_bestiary",
            "tab_heroes",
            "tab_config",
            "tab_vault_viewer",
            "tab_help",
        ]
        for name in tab_names:
            tab = self.window.findChild(QWidget, name)
            if tab is None:
                continue
            if tab.findChild(QLabel, "label_license_banner"):
                continue
            layout = tab.layout()
            banner = QLabel(self.LICENSE_BANNER_TEXT, tab)
            banner.setObjectName("label_license_banner")
            banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
            banner.setWordWrap(True)
            banner.setStyleSheet(
                "color: #9aa0a6; font-size: 10px; padding: 4px 8px; "
                "border-top: 1px solid #3a3a3a;"
            )
            if layout is not None and isinstance(layout, QBoxLayout):
                layout.addWidget(banner)
            else:
                banner_height = 36

                def _position_banner(event=None, widget=tab, label=banner):
                    bottom_widgets = [
                        child
                        for child in widget.findChildren(QWidget)
                        if child is not label
                        and child.geometry().top() > widget.height() * 0.6
                    ]
                    if bottom_widgets:
                        top_edge = min(child.geometry().top() for child in bottom_widgets)
                        y_pos = max(0, top_edge - banner_height - 4)
                    else:
                        y_pos = max(0, widget.height() - banner_height)
                    label.setGeometry(0, y_pos, widget.width(), banner_height)

                _position_banner()
                original_resize = tab.resizeEvent

                def _resize_event(event, handler=original_resize):
                    if handler is not None:
                        handler(event)
                    _position_banner(event)

                tab.resizeEvent = _resize_event

    def _init_log_buttons(self) -> None:
        """Connect the Save Log and Load Log buttons."""
        from datetime import datetime

        btn_save_log = self.window.findChild(QPushButton, "btn_save_log")
        btn_load_log = self.window.findChild(QPushButton, "btn_load_log")
        btn_clear_log = self.window.findChild(QPushButton, "btn_clear_log")

        if btn_save_log:
            btn_save_log.clicked.connect(self._on_save_log)
        if btn_load_log:
            btn_load_log.clicked.connect(self._on_load_log)
        if btn_clear_log:
            btn_clear_log.clicked.connect(self._on_clear_log)

    def _on_save_log(self) -> None:
        """Save the combat log to a text file with timestamp."""
        from datetime import datetime
        from PySide6.QtWidgets import QFileDialog, QMessageBox

        if not self.combat_log:
            # Combat log widget is optional (depends on UI layout).
            return

        log_content = self.combat_log.toPlainText()
        if not log_content.strip():
            # Avoid creating empty log files.
            QMessageBox.information(
                self.window,
                "Empty Log",
                "Combat log is empty. Nothing to save.",
            )
            return

        # Use configured log folder (respects Obsidian vault if set)
        logs_dir = config.CONFIG.get_combat_log_folder()

        if not logs_dir.exists():
            choice = QMessageBox.question(
                self.window,
                "Create Combat Logs Folder?",
                f"The folder does not exist:\n{logs_dir}\nCreate it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if choice == QMessageBox.StandardButton.Yes:
                try:
                    logs_dir.mkdir(parents=True, exist_ok=True)
                except Exception as exc:
                    self._append_log(f"Could not create combat logs folder: {exc}")
                    return
            else:
                return

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"combat_log_{timestamp}.txt"

        path, _ = QFileDialog.getSaveFileName(
            self.window,
            "Save Combat Log",
            str(logs_dir / default_name),
            "Text Files (*.txt);;All Files (*)",
        )

        if not path:
            # User canceled the save dialog.
            return

        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"Combat Log - Saved {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 60 + "\n\n")
                f.write(log_content)
            self._append_log(f"Combat log saved to {path}")
        except Exception as exc:
            self._append_log(f"Error saving combat log: {exc}")
            QMessageBox.critical(
                self.window,
                "Save Error",
                f"Could not save combat log:\n{exc}",
            )

    def _on_load_log(self) -> None:
        """Load a combat log from a text file."""
        from PySide6.QtWidgets import QFileDialog, QMessageBox

        if not self.combat_log:
            # Combat log widget is optional (depends on UI layout).
            return

        # Use configured log folder (respects Obsidian vault if set)
        logs_dir = config.CONFIG.get_combat_log_folder()

        # Create default path if it doesn't exist
        if not logs_dir.exists():
            logs_dir = Path.home()

        path, _ = QFileDialog.getOpenFileName(
            self.window,
            "Load Combat Log",
            str(logs_dir),
            "Text Files (*.txt);;All Files (*)",
        )

        if not path:
            # User canceled the open dialog.
            return

        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Ask if they want to append or replace existing log content.
            if self.combat_log.toPlainText().strip():
                reply = QMessageBox.question(
                    self.window,
                    "Append or Replace?",
                    "Do you want to append to the current log or replace it?\n\nClick 'Yes' to append, 'No' to replace.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                )

                if reply == QMessageBox.StandardButton.Cancel:
                    # Explicit cancel preserves existing log.
                    return
                elif reply == QMessageBox.StandardButton.Yes:
                    # Append
                    self.combat_log.append("\n" + "=" * 60)
                    self.combat_log.append(f"Loaded from {Path(path).name}\n")
                    self.combat_log.append(content)
                else:
                    # Replace
                    self.combat_log.setPlainText(content)
            else:
                # Log is empty, just set content.
                self.combat_log.setPlainText(content)

            self._append_log(f"Combat log loaded from {path}")
        except Exception as exc:
            self._append_log(f"Error loading combat log: {exc}")
            QMessageBox.critical(
                self.window,
                "Load Error",
                f"Could not load combat log:\n{exc}",
            )

    def _on_clear_log(self) -> None:
        """Clear the combat log after confirmation."""
        from PySide6.QtWidgets import QMessageBox

        if not self.combat_log:
            # Combat log widget is optional (depends on UI layout).
            return

        if not self.combat_log.toPlainText().strip():
            # Nothing to clear.
            return  # Already empty

        reply = QMessageBox.question(
            self.window,
            "Clear Log?",
            "Are you sure you want to clear the combat log?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.combat_log.clear()
            self._append_log("Combat log cleared")

    def _prompt_load_latest_log(self) -> None:
        """Prompt user to load the most recent log file on startup."""
        from PySide6.QtWidgets import QMessageBox

        if not self.combat_log:
            # Combat log widget is optional (depends on UI layout).
            return

        # Use configured log folder (respects Obsidian vault if set)
        logs_dir = config.CONFIG.get_combat_log_folder()

        if not logs_dir.exists():
            # No logs folder yet, skip prompt.
            return  # No logs folder, skip prompt

        # Find the most recent log file
        try:
            log_files = list(logs_dir.glob("combat_log_*.txt"))
            if not log_files:
                return  # No log files found

            # Sort by modification time, most recent first
            log_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            latest_log = log_files[0]

            # Prompt user
            reply = QMessageBox.question(
                self.window,
                "Load Latest Log?",
                f"Found recent combat log:\n{latest_log.name}\n\nDo you want to load it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                with open(latest_log, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.combat_log.setPlainText(content)
                self._append_log(f"Loaded log from {latest_log.name}")
        except Exception as exc:
            # Silence errors here to avoid blocking startup for a convenience prompt.
            pass

    def _on_config_changed(self) -> None:
        """Called when config changes to refresh all table column widths."""
        if self.combat is not None:
            self.combat._apply_column_widths()
        if self.bestiary is not None:
            self.bestiary._apply_column_widths()
        if self.heroes is not None:
            self.heroes._apply_column_widths()
        if self.heroes_tab is not None:
            self.heroes_tab._apply_column_widths()
        self._refresh_all_tabs()

    def _on_vault_scanned(self, vault_path: Path) -> None:
        """Called when a vault is scanned in the Config tab to reload monster library."""
        if self.bestiary is None:
            # Bestiary tab isn't available in this UI layout.
            return

        # Export the scanned data to a temporary JSON file so the existing
        # loader codepath can parse it without a new interface.
        vault_viewer = self.config.vault_viewer if self.config else None
        if vault_viewer and vault_viewer.last_data:
            import json
            import tempfile
            import os

            # Create a temporary file to hold the bestiary JSON.
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp:
                json.dump(vault_viewer.last_data, tmp, indent=2)
                tmp_path = tmp.name

            try:
                # Load the monster library from the temporary JSON.
                self.manager.load_monster_library(tmp_path)
                self._append_log(f"Monster library reloaded from scanned vault: {len(self.manager.monster_library)} templates")

                # Refresh bestiary filters and lists to reflect new data.
                if self.bestiary:
                    self.bestiary.populate_biome_filter()
                    self.bestiary.apply_filters()
            finally:
                # Clean up temp file even if loading failed.
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

    def _on_add_hero_clicked(self) -> None:
        """Prompt to create a new hero and add it to the manager."""
        hero = show_add_edit_hero_dialog(parent=self.window)
        if hero is None:
            return
        self.manager.add_hero(hero)

    def _on_delete_hero_clicked(self) -> None:
        """Delete the selected hero from the heroes tab."""
        from PySide6.QtWidgets import QMessageBox

        if self.heroes_tab is None:
            return

        # Get the selected row from the heroes tab table
        table = self.heroes_tab.table
        selected_rows = table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.information(
                self.window,
                "No Selection",
                "Please select a hero to delete.",
            )
            return

        # Get the row index
        row = selected_rows[0].row()

        if row < 0 or row >= len(self.manager.heroes):
            return

        hero = self.manager.heroes[row]
        hero_name = getattr(hero, "name", "Unknown Hero")

        # Confirm deletion
        reply = QMessageBox.question(
            self.window,
            "Delete Hero?",
            f"Are you sure you want to delete {hero_name}?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.manager.remove_hero(hero)
            self._append_log(f"Deleted hero: {hero_name}")

    def _refresh_all_tabs(self) -> None:
        """Refresh all tabs that are present and hook manager callback."""
        # Load last session BEFORE performing any mutations that autosave
        if not self._session_loaded:
            # Avoid re-loading autosave after UI mutations that can trigger autosave.
            self._load_last_session()
            self._session_loaded = True

        # Load monster library first (only once) so filters/tables can render.
        if self.bestiary is not None:
            if not self.manager.monster_library:
                self.bestiary.load_vault_from_config()
                self.bestiary.populate_biome_filter()

        # Now refresh all tabs
        if self.bestiary is not None:
            self.bestiary.apply_filters()
            self.bestiary.refresh_encounter_table()
        if self.combat is not None:
            self.combat.refresh_table()
        if self.heroes is not None:
            self.heroes.refresh_table()
        if self.heroes_tab is not None:
            self.heroes_tab.refresh_table()

        # Manager state callback routed to all tabs (set only once).
        if not self.manager.on_state_changed:
            self.manager.on_state_changed = self._on_state_changed

        if self.manager.on_concentration_note is None:
            # Prefer heroes table handler, fall back to heroes-tab handler.
            handler = None
            if self.heroes is not None:
                handler = self.heroes.handle_concentration_note
            elif self.heroes_tab is not None:
                handler = self.heroes_tab.handle_concentration_note
            if handler is not None:
                self.manager.on_concentration_note = handler

    def _on_state_changed(self) -> None:
        if self.bestiary is not None:
            self.bestiary.on_state_changed()
        if self.combat is not None:
            self.combat.refresh_table()
        if self.heroes is not None:
            self.heroes.refresh_table()
        if self.heroes_tab is not None:
            self.heroes_tab.refresh_table()

    # ------------------------------------------------------------------#
    # Window Events
    # ------------------------------------------------------------------#

    def _on_window_close(self, event) -> None:
        """Handle window close event - auto-save combat log."""
        from datetime import datetime

        # Auto-save the combat log if it has content
        if self.combat_log and self.combat_log.toPlainText().strip():
            try:
                # Use configured log folder or fall back to PROJECT_ROOT/Combat Logs
                if config.CONFIG.default_combat_log_folder:
                    logs_dir = Path(config.CONFIG.default_combat_log_folder)
                else:
                    logs_dir = PROJECT_ROOT / "Combat Logs"

                # Create folder if it doesn't exist
                if not logs_dir.exists():
                    logs_dir.mkdir(parents=True, exist_ok=True)

                # Generate filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"combat_log_{timestamp}.txt"
                filepath = logs_dir / filename

                # Save the log
                log_content = self.combat_log.toPlainText()
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"Combat Log - Auto-saved on close {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(log_content)

                print(f"Combat log auto-saved to {filepath}")
            except Exception as exc:
                print(f"Error auto-saving combat log: {exc}")

        # Accept the close event
        event.accept()

    # ------------------------------------------------------------------#
    # Session Management
    # ------------------------------------------------------------------#

    def _load_last_session(self) -> None:
        """Load the last autosaved session if it exists."""
        autosave_path = Path(config.CONFIG.autosave_path)
        fallback_path = PROJECT_UI_DIR / "autosave_session.json"

        loaded_from: Optional[Path] = None

        def _try_load(path: Path) -> bool:
            try:
                self.manager.load_session(str(path))
                return True
            except Exception as exc:  # noqa: BLE001
                self._append_log(f"Could not load last session from {path}: {exc}")
                return False

        if autosave_path.exists():
            # Primary path is the configured autosave location.
            if _try_load(autosave_path):
                loaded_from = autosave_path

        should_try_fallback = (
            fallback_path.exists()
            and fallback_path != autosave_path
            and (loaded_from is None or not (self.manager.heroes or self.manager.monsters))
        )
        if should_try_fallback:
            # Fallback allows older autosave locations without breaking migrations.
            if _try_load(fallback_path):
                loaded_from = fallback_path

        if loaded_from:
            self._append_log(f"Loaded last session from {loaded_from}")
        else:
            self._append_log("No previous session found.")

    # ------------------------------------------------------------------#
    # Logging
    # ------------------------------------------------------------------#

    def _ensure_config_path(self) -> None:
        """Prompt for config file location if none is stored in CONFIG."""
        from PySide6.QtWidgets import QFileDialog, QMessageBox

        current_path = config.get_config_path()
        if current_path and current_path.is_file():
            # Load existing config and skip the prompt.
            config.load_config(current_path)
            return

        box = QMessageBox(self.window)
        box.setWindowTitle("Select Config File")
        box.setText(
            "No config file is set. Choose a config file in your vault to "
            "store settings and autosaves. The app will remember this "
            "location in a local pointer file."
        )
        btn_open = box.addButton("Select Existing", QMessageBox.ButtonRole.AcceptRole)
        btn_create = box.addButton("Create New", QMessageBox.ButtonRole.ActionRole)
        btn_skip = box.addButton("Skip for Now", QMessageBox.ButtonRole.RejectRole)
        box.exec()

        clicked = box.clickedButton()
        if clicked == btn_open:
            # Use an existing config file (typically in a vault).
            path, _ = QFileDialog.getOpenFileName(
                self.window,
                "Select Config File",
                str(config.PROJECT_ROOT),
                "JSON Files (*.json);;All Files (*)",
            )
            if not path:
                return
            config.set_config_path(path)
            if not config.CONFIG_POINTER_FILE.exists():
                QMessageBox.warning(
                    self.window,
                    "Config Pointer Not Written",
                    f"Could not write config_location.json to:\n{config.CONFIG_POINTER_FILE}\n"
                    "The app may prompt again on next launch.",
                )
            config.load_config(path)
            return

        if clicked == btn_create:
            # Create a fresh config file at a user-chosen path.
            path, _ = QFileDialog.getSaveFileName(
                self.window,
                "Create Config File",
                str(config.PROJECT_ROOT / "config.json"),
                "JSON Files (*.json);;All Files (*)",
            )
            if not path:
                return
            config.set_config_path(path)
            if not config.CONFIG_POINTER_FILE.exists():
                QMessageBox.warning(
                    self.window,
                    "Config Pointer Not Written",
                    f"Could not write config_location.json to:\n{config.CONFIG_POINTER_FILE}\n"
                    "The app may prompt again on next launch.",
                )
            config.save_config(path)
            return

        if clicked == btn_skip:
            # Local-only data mode: build a default data/ tree without a vault.
            base_dir = QFileDialog.getExistingDirectory(
                self.window,
                "Select Data Folder Base",
                str(config.PROJECT_ROOT),
            )
            if not base_dir:
                return

            base = Path(base_dir) / "data"
            config.CONFIG.obsidian_vault_path = str(base)
            config.CONFIG.default_encounter_folder = "Encounters"
            config.CONFIG.default_party_folder = "Heroes"
            config.CONFIG.default_combat_log_folder = "Combat Logs"

            # Pre-create standard folders to avoid prompts later.
            for folder in (
                base / config.CONFIG.default_encounter_folder,
                base / config.CONFIG.default_party_folder,
                base / config.CONFIG.default_combat_log_folder,
            ):
                try:
                    folder.mkdir(parents=True, exist_ok=True)
                except Exception:
                    pass

    def _append_log(self, message: str) -> None:
        if self.combat_log is not None:
            self.combat_log.append(message)
        else:
            print(message)


def main() -> int:
    # Optional snapshot on launch for quick backups (skip when frozen in exe).
    if not getattr(sys, "frozen", False):
        try:
            snap_path = make_snapshot.make_snapshot()
            print(f"[snapshot] Created {snap_path}")
        except Exception as exc:  # noqa: BLE001
            print(f"[snapshot] Skipped ({exc})")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Base, QColor(20, 20, 20))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(35, 35, 35))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Text, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 45))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(90, 110, 180))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(150, 150, 150))
    app.setPalette(palette)
    here = Path(__file__).resolve().parent
    ui_path = here / "uiDesign" / "nimbleHandy.ui"

    splash = None
    splash_path = PROJECT_ROOT / "EncounterBuilderAppImage.png"
    if splash_path.exists():
        pixmap = QPixmap(str(splash_path))
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                max(1, pixmap.width() // 2),
                max(1, pixmap.height() // 2),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            splash = QSplashScreen(scaled)
            splash.show()
            app.processEvents()

    nimble = NimbleMainApp(ui_path)
    nimble.window.move(0, 0)  # Position at top-left of screen
    nimble.window.show()
    if splash is not None:
        splash.finish(nimble.window)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
