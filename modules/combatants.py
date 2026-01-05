# combatants.py
# ========================================================================
# NIMBLE COMBAT TRACKER — CORE DATA MODELS & COMBAT STATE LOGIC
# ========================================================================
#
# This module defines the core data structures for the Nimble Combat
# Tracker. It is UI-agnostic and focuses on:
#
#   • Hero, MonsterTemplate, and MonsterInstance models
#   • Party and Encounter containers
#   • HP / temp HP interaction
#   • Legendary "last stand" logic for monsters
#   • Derived status flags (bloodied, critical, dying, dead)
#   • Effective HP used for UI display (HP + temp HP)
#   • Serialization helpers (to_dict / from_dict) for persistence
#
# ------------------------------------------------------------------------
# ARCHITECTURE CONTEXT
# ------------------------------------------------------------------------
#
#   config.py       – defines thresholds, marker palette, autosave flags
#   combatants.py   – THIS FILE, data and low-level rules
#   combatManager.py – orchestrates sessions, markers, logging, autosave
#   persistence.py  – disk I/O using the to_dict/from_dict contracts
#   ui_*            – Qt or other UIs that bind to these models
#
# ------------------------------------------------------------------------
# HP / TEMP HP RULES
# ------------------------------------------------------------------------
#
#   • Damage is applied to temp HP first, then to current HP.
#   • Healing restores current HP only (not temp HP), capped at hp_max.
#   • effective_hp = hp_current + temp_hp
#       - This is what should be displayed in UI HP columns.
#
# ------------------------------------------------------------------------
# STATUS RULES (CONFIG-DRIVEN)
# ------------------------------------------------------------------------
#
# Thresholds are configured in config.CONFIG:
#
#   • hero_bloodied_threshold      (fraction of max HP)
#   • hero_critical_threshold
#   • monster_bloodied_threshold
#   • monster_critical_threshold
#
# Derived properties:
#
#   Hero:
#       is_bloodied:   hp_current <= hp_max * hero_bloodied_threshold
#       is_critical:   hp_current <= hp_max * hero_critical_threshold
#       is_dying:      hp_current <= 0
#
#   MonsterInstance:
#       is_bloodied:   hp_current <= hp_max * monster_bloodied_threshold
#       is_critical:   hp_current <= hp_max * monster_critical_threshold
#       is_dead:       hp_current <= 0 AND not in last stand
#       is_last_stand: internal flag (see below)
#
# ------------------------------------------------------------------------
# LEGENDARY LAST STAND LOGIC
# ------------------------------------------------------------------------
#
#   • For legendary monsters with a non-empty last_stand string and
#     a valid last_stand_hp:
#
#       - On damage, if hp_current <= 0 and last stand not triggered:
#             -> set is_last_stand = True
#             -> set hp_current = last_stand_hp
#             -> monster is NOT dead
#
#       - If hp_current <= 0 and is_last_stand is already True:
#             -> monster is_dead = True
#
#   • Non-legendary monsters (or legendary without last_stand text)
#     simply die at hp_current <= 0.
#
# ========================================================================
# END OF TITLE BLOCK
# ========================================================================

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

from modules import config


# ========================================================================
# HERO
# ========================================================================

@dataclass
class Hero:
    """
    Player character / ally representation for Nimble.

    This is intentionally rules-light and system-agnostic: we expose
    basic HP, temp HP, and a few generic fields that can be repurposed
    for different TTRPGs (class_name, resources, etc.).
    """

    # Identity & player-facing fields
    name: str
    level: int = 1
    class_name: str = ""         # e.g. "Fighter", "Mage", "Healer"
    player: str = ""             # which player owns this hero
    faction: str = "Heroes"      # simple tag ("Heroes", "Allies", etc.)

    # HP & temp HP
    hp_max: int = 10
    hp_current: int = 10
    temp_hp: int = 0

    # Generic resource track (repurposable)
    resource_1_name: str = ""    # e.g. "Spell Points"
    resource_1_current: int = 0
    resource_1_max: int = 0

    # Conditions
    conditions: List[str] = field(default_factory=list)

    # Notes – visible vs GM-only
    notes_public: str = ""
    notes_gm: str = ""
    concentrating: bool = False

    # --------------------------------------------------------------------
    # Construction helpers
    # --------------------------------------------------------------------

    @classmethod
    def new(cls, name: str = "New Hero") -> "Hero":
        return cls(name=name)

    # --------------------------------------------------------------------
    # Derived HP & status properties
    # --------------------------------------------------------------------

    @property
    def effective_hp(self) -> int:
        """
        Effective HP for display purposes: current HP + temp HP.
        """
        return self.hp_current + self.temp_hp

    @property
    def is_bloodied(self) -> bool:
        """True if HP is below bloodied threshold but above critical threshold."""
        if self.hp_max <= 0:
            return False
        bloodied_threshold = self.hp_max * config.CONFIG.hero_bloodied_threshold
        critical_threshold = self.hp_max * config.CONFIG.hero_critical_threshold
        # Bloodied is between critical and bloodied thresholds (not critical yet)
        return self.hp_current > 0 and self.hp_current <= bloodied_threshold and self.hp_current > critical_threshold

    @property
    def is_critical(self) -> bool:
        """True if HP is at or below critical threshold (but still alive)."""
        if self.hp_max <= 0:
            return False
        threshold = self.hp_max * config.CONFIG.hero_critical_threshold
        return self.hp_current > 0 and self.hp_current <= threshold

    @property
    def is_dying(self) -> bool:
        return self.hp_current <= 0

    # --------------------------------------------------------------------
    # HP / damage / healing
    # --------------------------------------------------------------------

    def apply_damage(self, amount: int) -> None:
        """Apply damage, consuming temp HP first."""
        if amount <= 0:
            return

        # temp HP first
        if self.temp_hp > 0:
            used = min(self.temp_hp, amount)
            self.temp_hp -= used
            amount -= used

        # then real HP
        if amount > 0:
            self.hp_current -= amount
            if self.hp_current < 0:
                self.hp_current = 0
        if self.hp_current > 0:
            self.remove_condition("Dying")
            return
        self.add_condition("Dying")

    def apply_healing(self, amount: int) -> None:
        """Heal real HP only, up to hp_max."""
        if amount <= 0:
            return
        if self.hp_current <= 0 and self.hp_max > 0:
            self.hp_current = 0

        self.hp_current += amount
        if self.hp_current > self.hp_max:
            self.hp_current = self.hp_max
        if self.hp_current > 0:
            self.remove_condition("Dying")

    def set_temp_hp(self, amount: int) -> None:
        """Set temp HP directly (replace existing)."""
        self.temp_hp = max(0, amount)

    # --------------------------------------------------------------------
    # Conditions
    # --------------------------------------------------------------------

    def add_condition(self, cond: str) -> None:
        cond = cond.strip()
        if cond and cond not in self.conditions:
            self.conditions.append(cond)

    def remove_condition(self, cond: str) -> None:
        cond = cond.strip()
        if cond in self.conditions:
            self.conditions.remove(cond)

    # --------------------------------------------------------------------
    # Serialization
    # --------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Hero":
        return cls(**data)


# ========================================================================
# MONSTER TEMPLATE
# ========================================================================

@dataclass
class MonsterTemplate:
    """
    Immutable "library" definition for a monster, as parsed from Nimble
    vault JSON / markdown metadata.

    These are never modified in combat; instead, MonsterInstance is
    created from a template for each copy used in an encounter.
    """
    name: str
    file: str
    legendary: bool
    level: str
    hp: str
    armor: str
    speed: str
    size: str
    saves: str
    flavor: str
    actions: List[str]
    special_actions: List[str]
    bloodied: str
    last_stand: str
    last_stand_hp: str
    biome_loot: List[str]
    type: str
    biome: str

    # Serialization helpers for persistence
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MonsterTemplate":
        return cls(**data)


# ========================================================================
# MONSTER INSTANCE
# ========================================================================

@dataclass
class MonsterInstance:
    """
    A single monster as it appears in an encounter.

    It is created from a MonsterTemplate but then gains mutable combat
    state (hp_current, temp_hp, conditions, group, markers, etc.).
    """

    # Base identity
    name: str
    template_file: str
    legendary: bool
    level: str
    armor: str
    speed: str
    size: str
    saves: str
    flavor: str
    actions: List[str] = field(default_factory=list)
    special_actions: List[str] = field(default_factory=list)
    bloodied_text: str = ""
    last_stand_text: str = ""
    last_stand_hp_value: int = 0
    biome_loot: List[str] = field(default_factory=list)
    type: str = ""
    biome: str = ""

    # HP state
    hp_max: int = 0
    hp_current: int = 0
    temp_hp: int = 0

    # Legendary status
    last_stand_triggered: bool = False
    dead: bool = False

    # Encounter-related metadata
    group: str = ""             # wave / group tag
    active: bool = True         # whether this monster is currently in play
    concentrating: bool = False # whether this monster is concentrating on a spell

    # Conditions & notes
    conditions: List[str] = field(default_factory=list)
    notes_public: str = ""
    notes_gm: str = ""

    # Map marker info (for VTT / battlemaps)
    marker_color: str = ""      # hex color; assigned by CombatManager
    marker_number: int = 0      # small integer; assigned by CombatManager
    shown_bloodied_popup: bool = False
    shown_last_stand_popup: bool = False

    # --------------------------------------------------------------------
    # Construction helpers
    # --------------------------------------------------------------------

    @staticmethod
    def _safe_int(value: Any, default: int = 0) -> int:
        try:
            if isinstance(value, int):
                return value
            if isinstance(value, float):
                return int(value)
            if isinstance(value, str):
                value = value.strip()
                if not value:
                    return default
                # Accept forms like "24", "24 HP", etc.
                parts = value.split()
                return int(parts[0])
        except Exception:
            return default
        return default

    @classmethod
    def from_template(cls, tpl: MonsterTemplate) -> "MonsterInstance":
        hp_max = cls._safe_int(tpl.hp, 0)
        last_stand_hp = cls._safe_int(tpl.last_stand_hp, 0)

        return cls(
            name=tpl.name,
            template_file=tpl.file,
            legendary=tpl.legendary,
            level=tpl.level,
            armor=tpl.armor,
            speed=tpl.speed,
            size=tpl.size,
            saves=tpl.saves,
            flavor=tpl.flavor,
            actions=list(tpl.actions),
            special_actions=list(tpl.special_actions),
            bloodied_text=tpl.bloodied,
            last_stand_text=tpl.last_stand,
            last_stand_hp_value=last_stand_hp,
            biome_loot=list(tpl.biome_loot),
            type=tpl.type,
            biome=tpl.biome,
            hp_max=hp_max,
            hp_current=hp_max,
        )

    # --------------------------------------------------------------------
    # Derived HP & status properties
    # --------------------------------------------------------------------

    @property
    def effective_hp(self) -> int:
        """
        Effective HP for display purposes: current HP + temp HP.
        During last stand, hp_current is set to last_stand_hp_value,
        so this always reflects the current active HP pool.
        """
        return self.hp_current + self.temp_hp

    @property
    def is_last_stand(self) -> bool:
        return self.last_stand_triggered and not self.dead

    @property
    def is_dead(self) -> bool:
        return self.dead

    @property
    def is_legendary(self) -> bool:
        return self.legendary

    @property
    def is_bloodied(self) -> bool:
        """True if HP is below bloodied threshold but above critical threshold."""
        if self.hp_max <= 0:
            return False
        bloodied_threshold = self.hp_max * config.CONFIG.monster_bloodied_threshold
        critical_threshold = self.hp_max * config.CONFIG.monster_critical_threshold
        # Bloodied is between critical and bloodied thresholds (not critical yet)
        return self.hp_current > 0 and self.hp_current <= bloodied_threshold and self.hp_current > critical_threshold

    @property
    def is_critical(self) -> bool:
        """True if HP is at or below critical threshold (but still alive/not in last stand)."""
        if self.hp_max <= 0:
            return False
        threshold = self.hp_max * config.CONFIG.monster_critical_threshold
        return self.hp_current > 0 and self.hp_current <= threshold

    # --------------------------------------------------------------------
    # HP / damage / healing with legendary last stand
    # --------------------------------------------------------------------

    def apply_damage(self, amount: int) -> None:
        """Apply damage, consuming temp HP first, then HP with last-stand logic."""
        if amount <= 0 or self.dead:
            return

        # temp HP first
        if self.temp_hp > 0:
            used = min(self.temp_hp, amount)
            self.temp_hp -= used
            amount -= used

        # then real HP
        if amount > 0:
            self.hp_current -= amount

        # Remove dying condition when still above 0
        if self.hp_current > 0:
            self.remove_condition("Dying")
            return

        # hp_current <= 0 here
        if self.legendary and self.last_stand_text and not self.last_stand_triggered:
            # Trigger last stand
            self.last_stand_triggered = True
            # If configured last stand HP is 0, fall back to 1
            self.hp_current = self.last_stand_hp_value or 1
            self.dead = False
            self.add_condition("Last Stand")
            self.remove_condition("Dying")
        else:
            # Either not legendary, or last stand already used
            self.hp_current = 0
            self.dead = True
            if "Last Stand" in self.conditions:
                self.remove_condition("Last Stand")

    def apply_healing(self, amount: int) -> None:
        """Heal real HP only, up to hp_max. Does not resurrect dead monsters."""
        if amount <= 0 or self.dead:
            return

        self.hp_current += amount
        if self.hp_current > self.hp_max:
            self.hp_current = self.hp_max

    def set_temp_hp(self, amount: int) -> None:
        """Set temp HP directly (replace existing)."""
        self.temp_hp = max(0, amount)

    # --------------------------------------------------------------------
    # Conditions
    # --------------------------------------------------------------------

    def add_condition(self, cond: str) -> None:
        cond = cond.strip()
        if cond and cond not in self.conditions:
            self.conditions.append(cond)

    def remove_condition(self, cond: str) -> None:
        cond = cond.strip()
        if cond in self.conditions:
            self.conditions.remove(cond)

    # --------------------------------------------------------------------
    # Serialization
    # --------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MonsterInstance":
        return cls(**data)


# ========================================================================
# PARTY & ENCOUNTER
# ========================================================================

@dataclass
class Party:
    """
    Named collection of heroes, saved/loaded as a unit.
    """
    name: str
    heroes: List[Hero] = field(default_factory=list)
    notes: str = ""

    @classmethod
    def new(cls, name: str = "Party") -> "Party":
        return cls(name=name)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "notes": self.notes,
            "heroes": [h.to_dict() for h in self.heroes],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Party":
        heroes_data = data.get("heroes", [])
        heroes = [Hero.from_dict(hd) for hd in heroes_data]
        return cls(
            name=data.get("name", "Party"),
            heroes=heroes,
            notes=data.get("notes", ""),
        )


@dataclass
class Encounter:
    """
    Named collection of monster instances, saved/loaded as a unit.
    """
    name: str
    monsters: List[MonsterInstance] = field(default_factory=list)
    notes: str = ""

    @classmethod
    def new(cls, name: str = "Encounter") -> "Encounter":
        return cls(name=name)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "notes": self.notes,
            "monsters": [m.to_dict() for m in self.monsters],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Encounter":
        mons_data = data.get("monsters", [])
        monsters = [MonsterInstance.from_dict(md) for md in mons_data]
        return cls(
            name=data.get("name", "Encounter"),
            monsters=monsters,
            notes=data.get("notes", ""),
        )
