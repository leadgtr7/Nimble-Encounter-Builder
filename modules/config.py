# config.py
# ========================================================================
# NIMBLE COMBAT TRACKER — GLOBAL CONFIGURATION
# ========================================================================
#
# This module defines all user-tunable configuration values for the
# Nimble Combat Tracker. It is intentionally centralized so that:
#
#   • Core modules (combatants, combatManager, persistence, UI) can
#     read behavior flags and thresholds from a single place.
#   • Users (or a future Config Editor UI) can adjust behavior without
#     touching the rest of the codebase.
#
# The configuration is represented as a single dataclass instance:
#
#   CONFIG: TrackerConfig
#
# and can be persisted to / restored from a JSON file using:
#
#   load_config("config.json")
#   save_config("config.json")
#
# ------------------------------------------------------------------------
# MAJOR GROUPS OF SETTINGS
# ------------------------------------------------------------------------
#
#   • HP Thresholds
#   • Map Markers
#   • Autosave
#   • Logging Verbosity
#   • Monster Vault
#   • Encounter Difficulty
#
# ========================================================================
# END OF TITLE BLOCK
# ========================================================================

from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List
import sys


def _get_project_root() -> Path:
    # In a frozen exe, write the pointer next to the executable.
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


PROJECT_ROOT = _get_project_root()
CONFIG_POINTER_FILE = PROJECT_ROOT / "config_location.json"


def _read_config_pointer() -> Path | None:
    """Return the config path stored in the app directory pointer file."""
    if not CONFIG_POINTER_FILE.exists():
        return None
    try:
        # Keep the pointer as a tiny JSON file so we can evolve keys later.
        data = json.loads(CONFIG_POINTER_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
    raw = str(data.get("config_path", "")).strip()
    if not raw:
        return None
    return Path(raw)


def get_config_path() -> Path | None:
    """Return the current config path from the pointer file or CONFIG."""
    pointer = _read_config_pointer()
    if pointer:
        # Pointer file takes priority to remember per-user config locations.
        return pointer
    raw = getattr(CONFIG, "config_file_path", "").strip()
    if not raw:
        return None
    return Path(raw)


def set_config_path(path: str | Path) -> None:
    """Store the config path in CONFIG and in the app directory pointer file."""
    CONFIG.config_file_path = str(path)
    try:
        # Store only the path; keep this file stable for easy troubleshooting.
        CONFIG_POINTER_FILE.write_text(
            json.dumps({"config_path": str(path)}, indent=2),
            encoding="utf-8",
        )
    except Exception:  # noqa: BLE001
        pass


@dataclass
class TrackerConfig:
    # --------------------------
    # HP Thresholds
    # --------------------------
    # Fractions of max HP
    hero_bloodied_threshold: float = 0.5
    hero_critical_threshold: float = 0.25
    monster_bloodied_threshold: float = 0.5
    monster_critical_threshold: float = 0.25

    # --------------------------
    # Map Markers
    # --------------------------
    # Colors may be names or hex strings; CombatManager doesn't care.
    marker_palette: List[str] = field(default_factory=list)
    marker_start_number: int = 1

    # --------------------------
    # Conditions
    # --------------------------
    # Common conditions that can be applied to creatures
    available_conditions: List[str] = field(default_factory=list)

    # --------------------------
    # Table Alternating Row Colors
    # --------------------------
    # RGB tuples for alternating row backgrounds in tables
    # Heroes tables use dark blue/dark gray alternating colors
    hero_table_row_color_1: tuple = (40, 60, 90)   # Dark blue
    hero_table_row_color_2: tuple = (60, 60, 60)   # Dark gray
    # Monster tables use dark green/dark gray alternating colors
    monster_table_row_color_1: tuple = (40, 70, 40)   # Dark green
    monster_table_row_color_2: tuple = (60, 60, 60)   # Dark gray

    # --------------------------
    # HP Condition Colors (for Legend Labels)
    # --------------------------
    # RGB tuples for HP status background colors
    hp_healthy_color: tuple = (0, 85, 0)        # Dark green
    hp_bloodied_color: tuple = (167, 111, 0)    # Orange
    hp_critical_color: tuple = (170, 0, 0)      # Dark red
    hp_down_color: tuple = (48, 48, 48)         # Dark gray
    hp_conditions_color: tuple = (61, 0, 182)   # Purple (for condition highlights)

    # --------------------------
    # Combat Tab Column Widths (Monster Table)
    # --------------------------
    combat_col_active_width: int = 25
    combat_col_heal_width: int = 25
    combat_col_name_width: int = 120
    combat_col_marker_width: int = 30
    combat_col_hurt_width: int = 25
    combat_col_con_width: int = 25
    combat_col_conds_width: int = 100
    combat_col_hp_width: int = 30
    combat_col_tmp_width: int = 30
    combat_col_max_width: int = 30

    # --------------------------
    # Heroes Tab (Combat Mode) Column Widths
    # --------------------------
    hero_combat_col_heal_width: int = 25
    hero_combat_col_name_width: int = 120
    hero_combat_col_hurt_width: int = 25
    hero_combat_col_con_width: int = 25
    hero_combat_col_conds_width: int = 100
    hero_combat_col_hp_width: int = 30
    hero_combat_col_tmp_width: int = 30
    hero_combat_col_max_width: int = 30

    # --------------------------
    # Heroes Tab (Heroes Tab Mode) Column Widths
    # --------------------------
    hero_tab_col_name_width: int = 140
    hero_tab_col_player_width: int = 75
    hero_tab_col_level_width: int = 30
    hero_tab_col_max_width: int = 25
    hero_tab_col_class_width: int = 60
    hero_tab_col_gm_notes_width: int = 120
    hero_tab_col_player_notes_width: int = 120
    hero_table_font_size: int = 11
    monster_table_font_size: int = 11

    # --------------------------
    # Bestiary Tab Column Widths
    # --------------------------
    bestiary_col_active_width: int = 25
    bestiary_col_name_width: int = 120
    bestiary_col_wave_width: int = 80
    bestiary_col_marker_width: int = 30
    bestiary_col_level_width: int = 30
    bestiary_col_max_width: int = 30

    # --------------------------
    # Autosave
    # --------------------------
    autosave_enabled: bool = True
    # Autosave path will be resolved to absolute path on initialization
    autosave_path: str = ""

    # --------------------------
    # Config File Path
    # --------------------------
    # Stored inside the config itself to avoid separate sidecar files.
    config_file_path: str = ""

    # --------------------------
    # Logging Verbosity
    # --------------------------
    log_damage_events: bool = True
    log_heal_events: bool = True
    log_condition_changes: bool = True
    log_last_stand_triggers: bool = True
    log_deaths: bool = True

    # --------------------------
    # Monster Vault
    # --------------------------
    # Default path to a JSON file containing the monster library.
    # If non-empty, CombatManager will attempt to auto-load this on init.
    default_monster_vault_path: str = "Bestiary/bestiary.json"

    # Auto-refresh monster data from vault when loading encounters
    auto_refresh_on_encounter_load: bool = False

    # Obsidian vault base path - if set, all folders below will be relative to this
    obsidian_vault_path: str = ""

    # Default folder for encounters
    default_encounter_folder: str = ""

    # Default folder for party files
    default_party_folder: str = ""

    # Default folder for combat logs
    default_combat_log_folder: str = ""

    # --------------------------
    # Encounter Difficulty
    # --------------------------
    # Thresholds for encounter difficulty based on ratio of monster levels to hero levels.
    #
    # Easy: Monster levels < 50% of hero levels
    #   Heroes will lose minimal HP and resources. Great for testing new abilities or
    #   gauging progress. Makes players feel powerful after leveling up.
    #   Use 1-2 easy encounters in a typical session.
    #
    # Medium: Monster levels ≈ 75% of hero levels
    #   Expect some HP loss and moderate resource expenditure. Heroes will get hurt but
    #   shouldn't drop to 0 HP.
    #   Use 1-2 medium encounters in a typical session.
    #
    # Hard: Monster levels = 100% of hero levels
    #   Challenging but fair. Heroes must use significant resources; some may drop to 0 HP,
    #   but none should die barring poor tactics or bad luck.
    #   Use 1 hard encounter in a typical session.
    #
    # Deadly: Monster levels = 100-125% of hero levels
    #   Requires strategic thinking and teamwork. Suitable for tough battles, well-equipped
    #   parties, or campaign bosses. Use sparingly!
    #
    # Very Deadly: Monster levels ≥ 150% of hero levels
    #   Extremely dangerous. Unless heroes are well optimized and play exquisitely, they will
    #   almost certainly need to retreat—or die. Use only when heroes made a bad mistake after
    #   you telegraphed danger and they failed to heed.

    encounter_difficulty_easy: float = 0.5          # Monster levels < 50% of hero levels
    encounter_difficulty_medium: float = 0.75       # Monster levels ~75% of hero levels
    encounter_difficulty_hard: float = 1.0          # Monster levels = hero levels
    encounter_difficulty_deadly_min: float = 1.0    # Deadly: 100-125% of hero levels
    encounter_difficulty_deadly_max: float = 1.25
    encounter_difficulty_very_deadly: float = 1.5   # Very deadly: 150%+ of hero levels

    # Difficulty label colors (RGB tuples)
    difficulty_color_easy: tuple = (0, 120, 0)       # Green
    difficulty_color_medium: tuple = (200, 150, 0)   # Yellow/Orange
    difficulty_color_hard: tuple = (200, 100, 0)     # Orange
    difficulty_color_deadly: tuple = (170, 0, 0)     # Red
    difficulty_color_very_deadly: tuple = (100, 0, 100)  # Purple

    def resolve_monster_vault_path(self) -> str:
        """
        Return the configured monster vault path, falling back to the legacy
        Beastiary spelling if that file exists.
        """
        if not self.default_monster_vault_path:
            return ""
        raw = self._split_monster_vault_paths()[0]
        candidates = [Path(raw)]
        if "Beastiary" in raw:
            candidates.append(Path(raw.replace("Beastiary", "Bestiary")))
        elif "Bestiary" in raw:
            candidates.append(Path(raw.replace("Bestiary", "Beastiary")))
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        return str(candidates[0])

    def _split_monster_vault_paths(self) -> list[str]:
        """Split the configured monster vault paths into a list."""
        raw = (self.default_monster_vault_path or "").strip()
        if not raw:
            return []
        parts = []
        for token in raw.replace("\n", ";").split(";"):
            # Normalize whitespace and ignore accidental double-separators.
            token = token.strip()
            if token:
                parts.append(token)
        return parts

    def resolve_monster_vault_paths(self) -> list[str]:
        """Return all configured monster vault paths with legacy fallbacks."""
        resolved = []
        for raw in self._split_monster_vault_paths():
            # Support old folder naming typos for smoother migrations.
            candidates = [Path(raw)]
            if "Beastiary" in raw:
                candidates.append(Path(raw.replace("Beastiary", "Bestiary")))
            elif "Bestiary" in raw:
                candidates.append(Path(raw.replace("Bestiary", "Beastiary")))
            for candidate in candidates:
                if candidate.exists():
                    resolved.append(str(candidate))
                    break
            else:
                # Keep the raw path even if missing so UI can surface it.
                resolved.append(str(candidates[0]))
        return resolved

    def get_encounter_folder(self) -> Path:
        """
        Get the encounter folder path, using Obsidian vault as base if configured.
        Returns an absolute Path object.
        """
        if self.obsidian_vault_path and Path(self.obsidian_vault_path).exists():
            base = Path(self.obsidian_vault_path)
            if self.default_encounter_folder:
                # If relative path, join with vault base
                folder_path = Path(self.default_encounter_folder)
                if not folder_path.is_absolute():
                    return base / folder_path
                return folder_path
            else:
                # Default to "Encounters" folder in vault
                return base / "Encounters"
        elif self.default_encounter_folder:
            folder_path = Path(self.default_encounter_folder)
            if not folder_path.is_absolute():
                # Relative path - make it relative to project root
                return PROJECT_ROOT / folder_path
            return folder_path
        else:
            # Fallback to project root / Encounters
            return PROJECT_ROOT / "Encounters"

    def get_party_folder(self) -> Path:
        """
        Get the party folder path, using Obsidian vault as base if configured.
        Returns an absolute Path object.
        """
        if self.obsidian_vault_path and Path(self.obsidian_vault_path).exists():
            base = Path(self.obsidian_vault_path)
            if self.default_party_folder:
                folder_path = Path(self.default_party_folder)
                if not folder_path.is_absolute():
                    return base / folder_path
                return folder_path
            else:
                # Default to "Heroes" or "Party" folder in vault
                return base / "Heroes"
        elif self.default_party_folder:
            folder_path = Path(self.default_party_folder)
            if not folder_path.is_absolute():
                # Relative path - make it relative to project root
                return PROJECT_ROOT / folder_path
            return folder_path
        else:
            return PROJECT_ROOT / "Party"

    def get_combat_log_folder(self) -> Path:
        """
        Get the combat log folder path, using Obsidian vault as base if configured.
        Returns an absolute Path object.
        """
        if self.obsidian_vault_path and Path(self.obsidian_vault_path).exists():
            base = Path(self.obsidian_vault_path)
            if self.default_combat_log_folder:
                folder_path = Path(self.default_combat_log_folder)
                if not folder_path.is_absolute():
                    return base / folder_path
                return folder_path
            else:
                # Default to "Combat Logs" folder in vault
                return base / "Combat Logs"
        elif self.default_combat_log_folder:
            folder_path = Path(self.default_combat_log_folder)
            if not folder_path.is_absolute():
                # Relative path - make it relative to project root
                return PROJECT_ROOT / folder_path
            return folder_path
        else:
            return PROJECT_ROOT / "Combat Logs"

    def auto_detect_vault_from_monster_path(self) -> bool:
        """
        Try to automatically detect the Obsidian vault path from the monster vault path.
        If the monster vault path contains "Nimble Vault" or "TTRPG_Vault", extract the vault root.
        Returns True if vault was detected and set, False otherwise.
        """
        if self.obsidian_vault_path:
            # Already set, don't override
            return False

        if not self.default_monster_vault_path:
            return False

        paths = self._split_monster_vault_paths()
        if not paths:
            return False
        path = Path(paths[0])

        # Look for vault folders in the path, prioritizing specific vault names
        # Strategy: Find the LAST occurrence of a folder with "vault" in it
        # This handles cases like C:\TTRPG_Vault\Nimble Vault\... correctly

        vault_candidates = []

        # Collect all parts that might be vault folders
        for i, part in enumerate(path.parts):
            part_lower = part.lower()
            # Prioritize folders with "vault" in the name
            if "vault" in part_lower:
                vault_path = Path(*path.parts[:i + 1])
                if vault_path.exists() and vault_path.is_dir():
                    # Give higher priority to folders with specific vault names
                    priority = 0
                    if "nimble" in part_lower or "obsidian" in part_lower:
                        priority = 2
                    elif "_vault" in part_lower or " vault" in part_lower:
                        priority = 1
                    vault_candidates.append((priority, vault_path))

        # Use the highest priority vault, or the last one if priorities are equal
        if vault_candidates:
            vault_candidates.sort(key=lambda x: (x[0], len(str(x[1]))), reverse=True)
            self.obsidian_vault_path = str(vault_candidates[0][1])
            return True

        return False

    def infer_folder_paths(self):
        """
        Automatically infer folder paths based on the Obsidian vault path.
        Only sets paths if they're currently empty and vault path exists.
        """
        if not self.obsidian_vault_path:
            return

        vault = Path(self.obsidian_vault_path)
        if not vault.exists():
            return

        # Infer encounter folder if empty
        if not self.default_encounter_folder:
            # Look for existing folders
            candidates = ["Encounters", "Sessions", "Campaign/Encounters"]
            for candidate in candidates:
                test_path = vault / candidate
                if test_path.exists():
                    self.default_encounter_folder = candidate
                    break
            else:
                # Default to "Encounters"
                self.default_encounter_folder = "Encounters"

        # Infer party folder if empty
        if not self.default_party_folder:
            candidates = ["Heroes", "Party", "Characters", "Campaign/Heroes"]
            for candidate in candidates:
                test_path = vault / candidate
                if test_path.exists():
                    self.default_party_folder = candidate
                    break
            else:
                # Default to "Heroes"
                self.default_party_folder = "Heroes"

        # Infer combat log folder if empty
        if not self.default_combat_log_folder:
            candidates = ["Combat Logs", "Logs", "Campaign/Logs"]
            for candidate in candidates:
                test_path = vault / candidate
                if test_path.exists():
                    self.default_combat_log_folder = candidate
                    break
            else:
                # Default to "Combat Logs"
                self.default_combat_log_folder = "Combat Logs"

    def __post_init__(self):
        # Try to auto-detect vault from monster path if not already set
        vault_detected = self.auto_detect_vault_from_monster_path()

        # If vault was detected or already exists, infer folder paths
        if vault_detected or self.obsidian_vault_path:
            self.infer_folder_paths()

        # If no palette was provided (empty list), use these defaults.
        if not self.marker_palette:
            self.marker_palette = [
                "#FFFFFF",  # white
                "#FF0000",  # red
                "#0000FF",  # blue
                "#00AA00",  # green
                "#FFFF00",  # yellow
                "#800080",  # purple
                "#000000",  # black
            ]

        # If no conditions provided, use these common D&D 5e conditions
        if not self.available_conditions:
            self.available_conditions = [
                "Blinded",
                "Bloodied",
                "Charmed",
                "Dazed",
                "Deafened",
                "Dying",
                "Frightened",
                "Grappled",
                "Hampered",
                "Incapacitated",
                "Invisible",
                "Paralyzed",
                "Petrified",
                "Poisoned",
                "Prone",
                "Riding",
                "Restrained",
                "Slowed",
                "Stunned",
                "Last Stand",
                "Taunted",
                "Unconscious",
            ]

        # Set autosave path to absolute path next to this module if not already set
        if not self.autosave_path:
            self.autosave_path = str(PROJECT_ROOT / "autosave_session.json")


# Global configuration instance
CONFIG = TrackerConfig()


# ========================================================================
# CONFIG LOAD / SAVE HELPERS
# ========================================================================

def save_config(path: str | Path | None = None) -> None:
    """
    Write the current CONFIG values to a JSON file.

    Only the dataclass fields are persisted; the file is intended to be
    user-editable.
    """
    actual_path = Path(path) if path else get_config_path()
    if actual_path is None:
        return
    p = actual_path
    p.parent.mkdir(parents=True, exist_ok=True)
    set_config_path(p)
    data = asdict(CONFIG)
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_config(path: str | Path | None = None) -> None:
    """
    Load configuration values from a JSON file into CONFIG.

    Unknown keys in the JSON are ignored.
    Missing keys keep their current values.
    """
    actual_path = Path(path) if path else get_config_path()
    if actual_path is None:
        return
    p = Path(actual_path)
    # Persist pointer even if the file doesn't exist yet.
    set_config_path(p)
    if not p.is_file():
        return

    with p.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    if not isinstance(raw, dict):
        return

    for key, value in raw.items():
        if hasattr(CONFIG, key):
            setattr(CONFIG, key, value)

    # After loading, run auto-detection and folder inference
    # (normally done in __post_init__, but that doesn't run when loading from JSON)
    vault_detected = CONFIG.auto_detect_vault_from_monster_path()
    if vault_detected or CONFIG.obsidian_vault_path:
        CONFIG.infer_folder_paths()



# Automatically load the config file if one is already configured.
load_config()
