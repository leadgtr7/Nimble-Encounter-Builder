"""State helpers for the NiceGUI encounter front end."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable

from modules import config, persistence
from modules.combatManager import CombatManager
from modules.combatants import MonsterInstance, MonsterTemplate
from modules.services import create_default_services


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _resolve_app_path(path: str | Path) -> Path:
    raw = Path(path)
    if raw.is_absolute():
        return raw
    for base in (Path.cwd(), PROJECT_ROOT, PROJECT_ROOT.parent):
        candidate = base / raw
        if candidate.exists():
            return candidate
    return PROJECT_ROOT / raw


def _rgb_to_css(value: tuple[int, int, int] | list[int]) -> str:
    try:
        r, g, b = value
        return f"rgb({int(r)}, {int(g)}, {int(b)})"
    except Exception:
        return "rgb(70, 70, 70)"


def _marker_text_color(bg_hex: str) -> str:
    try:
        raw = bg_hex.strip().lstrip("#")
        if len(raw) != 6:
            return "#111111"
        r = int(raw[0:2], 16)
        g = int(raw[2:4], 16)
        b = int(raw[4:6], 16)
        luminosity = 0.2126 * r + 0.7152 * g + 0.0722 * b
        return "#111111" if luminosity > 128 else "#ffffff"
    except Exception:
        return "#111111"


def monster_status(monster: MonsterInstance) -> str:
    if getattr(monster, "is_dead", False):
        return "Dead"
    if getattr(monster, "is_last_stand", False):
        return "Last Stand"
    if getattr(monster, "is_critical", False):
        return "Critical"
    if getattr(monster, "is_bloodied", False):
        return "Bloodied"
    return "Healthy"


@dataclass
class EncounterUiState:
    manager: CombatManager
    monster_library: list[MonsterTemplate] = field(default_factory=list)
    selected_monster_uid: str | None = None
    selected_template_key: str | None = None
    template_by_key: dict[str, MonsterTemplate] = field(default_factory=dict)
    event_log: list[str] = field(default_factory=list)
    loot_draft: str = ""

    def log(self, message: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        self.event_log.append(f"[{stamp}] {message}")
        if len(self.event_log) > 250:
            self.event_log = self.event_log[-250:]

    def apply_default_difficulty_profile(self) -> None:
        player_count = getattr(config.CONFIG, "default_player_count", 4)
        average_level = getattr(config.CONFIG, "default_average_party_level", 1.0)
        self.manager.set_difficulty_profile(player_count, average_level)

    def load_monster_library_from_config(self) -> None:
        paths = config.CONFIG.resolve_monster_vault_paths()
        self.monster_library = []
        if not paths:
            self.log("No monster vault path configured.")
            return

        seen: set[tuple[str, str]] = set()
        for raw_path in paths:
            path = _resolve_app_path(raw_path)
            if not path.exists():
                self.log(f"Monster vault not found: {path}")
                continue
            try:
                templates = persistence.load_monster_library(path)
            except Exception as exc:  # noqa: BLE001
                self.log(f"Could not load monster vault {path}: {exc}")
                continue
            added = 0
            for template in templates:
                key = (template.name, template.file)
                if key in seen:
                    continue
                seen.add(key)
                self.monster_library.append(template)
                added += 1
            self.log(f"Loaded {added} monsters from {path}")
        self.manager.monster_library = list(self.monster_library)

    def template_options(
        self,
        search: str = "",
        level: str = "",
        biome: str = "",
        include_legendary: bool = False,
    ) -> dict[str, str]:
        search_value = search.strip().lower()
        level_value = level.strip()
        biome_value = biome.strip().lower()
        options: dict[str, str] = {}
        self.template_by_key = {}

        for index, template in enumerate(self.monster_library):
            if not include_legendary and template.legendary:
                continue
            if search_value and search_value not in template.name.lower():
                continue
            if level_value and level_value != str(template.level).strip():
                continue
            template_biome = (template.biome or "").lower()
            if biome_value and biome_value not in template_biome:
                continue

            key = f"{index}:{template.file}:{template.name}"
            label_parts = [f"Lvl {template.level}", template.name]
            if template.biome:
                label_parts.append(template.biome)
            elif template.type:
                label_parts.append(template.type)
            label = " - ".join(str(part) for part in label_parts if part)
            options[key] = label
            self.template_by_key[key] = template

        return options

    def biome_options(self) -> list[str]:
        values = {
            (template.biome or "").strip()
            for template in self.monster_library
            if (template.biome or "").strip()
        }
        return [""] + sorted(values)

    def selected_template(self) -> MonsterTemplate | None:
        if not self.selected_template_key:
            return None
        return self.template_by_key.get(self.selected_template_key)

    @staticmethod
    def monster_uid(monster: MonsterInstance) -> str:
        return str(id(monster))

    def sorted_monsters(self) -> list[MonsterInstance]:
        return sorted(
            self.manager.monsters,
            key=lambda m: (
                getattr(m, "is_dead", False),
                not getattr(m, "active", True),
                not getattr(m, "legendary", False),
                getattr(m, "name", ""),
            ),
        )

    def selected_monster(self) -> MonsterInstance | None:
        if not self.selected_monster_uid:
            return None
        for monster in self.manager.monsters:
            if self.monster_uid(monster) == self.selected_monster_uid:
                return monster
        self.selected_monster_uid = None
        return None

    def select_monster_uid(self, uid: str | None) -> None:
        self.selected_monster_uid = uid
        if self.selected_monster() is None and uid is not None:
            self.selected_monster_uid = None

    def combat_rows(self) -> list[dict]:
        rows = []
        for monster in self.sorted_monsters():
            marker_number = getattr(monster, "marker_number", 0)
            marker_color = getattr(monster, "marker_color", "") or ""
            status = monster_status(monster)
            rows.append(
                {
                    "uid": self.monster_uid(monster),
                    "active": "Yes" if getattr(monster, "active", True) else "No",
                    "name": monster.name,
                    "group": monster.group or "",
                    "marker": str(marker_number) if marker_number else "",
                    "marker_color": marker_color,
                    "marker_text_color": _marker_text_color(marker_color),
                    "level": str(monster.level),
                    "hp": monster.effective_hp,
                    "temp_hp": monster.temp_hp,
                    "max_hp": monster.hp_max,
                    "conditions": ", ".join(monster.conditions or []),
                    "concentrating": "Yes" if monster.concentrating else "No",
                    "status": status,
                    "status_class": status.lower().replace(" ", "-"),
                    "legendary": "Yes" if monster.legendary else "No",
                }
            )
        return rows

    def difficulty_summary(self) -> dict[str, str]:
        cfg = config.CONFIG
        party_total = self.manager.difficulty_party_total_level()
        monster_total = self.manager.total_monster_levels()
        ratio = self.manager.encounter_difficulty_ratio()
        label = self.manager.encounter_difficulty_label()
        bands = {
            "Easy": cfg.encounter_difficulty_easy,
            "Medium": cfg.encounter_difficulty_medium,
            "Hard": cfg.encounter_difficulty_hard,
            "Deadly": cfg.encounter_difficulty_deadly_max,
        }
        return {
            "label": label,
            "party_total": f"{party_total:g}",
            "monster_total": f"{monster_total:g}",
            "ratio": f"{ratio * 100:.0f}%" if ratio else "0%",
            "easy": f"< {party_total * bands['Easy']:g}",
            "medium": f"< {party_total * bands['Medium']:g}",
            "hard": f"< {party_total * bands['Hard']:g}",
            "deadly": f"<= {party_total * bands['Deadly']:g}",
            "very_deadly": f"> {party_total * bands['Deadly']:g}",
            "color": _rgb_to_css(
                {
                    "Easy": cfg.difficulty_color_easy,
                    "Medium": cfg.difficulty_color_medium,
                    "Hard": cfg.difficulty_color_hard,
                    "Deadly": cfg.difficulty_color_deadly,
                    "Very Deadly": cfg.difficulty_color_very_deadly,
                }.get(label, (70, 70, 70))
            ),
        }

    def loot_candidates(self, selected_only: bool = False) -> list[str]:
        source: Iterable[MonsterInstance]
        selected = self.selected_monster()
        if selected_only and selected is not None:
            source = [selected]
        else:
            source = self.manager.monsters

        seen: set[str] = set()
        loot: list[str] = []
        for monster in source:
            for item in monster.biome_loot or []:
                text = str(item).strip()
                if text and text not in seen:
                    seen.add(text)
                    loot.append(text)
        return loot


def create_state() -> EncounterUiState:
    services = create_default_services(PROJECT_ROOT)
    manager = CombatManager(storage=services.storage)
    state = EncounterUiState(manager=manager)
    manager.on_log = state.log
    state.apply_default_difficulty_profile()
    state.load_monster_library_from_config()
    return state

