# combatManager.py
# ========================================================================
# NIMBLE COMBAT TRACKER — COMBAT MANAGER
# ========================================================================
#
# CENTRAL RULES ENGINE & STATE CONTROLLER FOR THE NIMBLE COMBAT TRACKER
#
# Responsibilities:
#
#   • Maintain active session state (heroes + monsters)
#   • Monster library loading and template lookup
#   • Add/remove heroes and monsters
#   • Apply damage, healing, conditions (delegating to combatants logic)
#   • Legendary last-stand transitions (via MonsterInstance methods)
#   • Map marker auto-assignment by GROUP & COLOR
#   • PER-COLOR marker numbering (each color tracks its own sequence)
#   • Load/save parties, encounters, sessions
#   • Autosave behavior driven by configuration
#   • Log message dispatch to UI (on_log callback)
#   • State-change notifications to UI (on_state_changed callback)
#
# This module is UI-agnostic: no Qt imports.
#
# ------------------------------------------------------------------------
# MAP MARKER BEHAVIOR
# ------------------------------------------------------------------------
#
#   COLOR:
#       • Each monster.group string gets a color assigned from
#         CONFIG.marker_palette, in round-robin fashion.
#
#       • group → color is tracked in group_color_map.
#
#   NUMBER (PER COLOR):
#       • For a given color C:
#
#             marker_number = max(
#                 m.marker_number
#                 for m in monsters
#                 if m.marker_color == C
#             ) + 1
#
#         or CONFIG.marker_start_number if none exist for that color.
#
#       • Different groups that share the same color also share that
#         color's sequence.
#
#       • Existing numbers are preserved when loading; new monsters
#         continue the existing per-color sequences.
#
# ------------------------------------------------------------------------
# AUTOSAVE & LOGGING
# ------------------------------------------------------------------------
#
#   Autosave:
#       • Controlled by CONFIG.autosave_enabled and CONFIG.autosave_path.
#       • Called after every state mutation.
#
#   Logging:
#       • Controlled by CONFIG.log_* flags.
#       • Messages emitted via on_log callback (if set).
#
# ========================================================================
# END OF TITLE BLOCK
# ========================================================================

from __future__ import annotations

from fractions import Fraction
from typing import List, Optional, Callable, Dict

from modules.combatants import (
    Hero,
    MonsterInstance,
    MonsterTemplate,
    Party,
    Encounter,
)

from modules import persistence
from modules import config


class CombatManager:
    """
    High-level controller that coordinates heroes, monsters, and
    persistence. The UI should talk only to this class and never to
    persistence or config directly.
    """

    # --------------------------------------------------------------------
    # 1. Constructor / event hooks
    # --------------------------------------------------------------------

    def __init__(self):
        self.heroes: List[Hero] = []
        self.monsters: List[MonsterInstance] = []
        self.monster_library: List[MonsterTemplate] = []

        # Map marker management
        self.group_color_map: Dict[str, str] = {}   # group string -> hex color

        # Optional callbacks for UI
        self.on_log: Optional[Callable[[str], None]] = None
        self.on_state_changed: Optional[Callable[[], None]] = None
        self.on_concentration_note: Optional[Callable[[Hero | MonsterInstance], None]] = None

        # Marker palette is driven by configuration
        self._marker_palette: List[str] = list(config.CONFIG.marker_palette)

    # --------------------------------------------------------------------
    # Internal helpers
    # --------------------------------------------------------------------

    def _log(self, msg: str):
        if self.on_log:
            self.on_log(msg)

    def _changed(self):
        # Autosave every mutation if enabled
        self.autosave()
        if self.on_state_changed:
            self.on_state_changed()

    def _notify_concentration_note(self, creature) -> None:
        """Trigger the external concentration notification hook, if one is registered."""
        if not self.on_concentration_note:
            return
        try:
            self.on_concentration_note(creature)
        except Exception as exc:  # noqa: BLE001
            self._log(f"Concentration note handler failed: {exc}")

    # ====================================================================
    # MARKER ASSIGNMENT (PER-COLOR COUNTERS)
    # ====================================================================

    def _get_or_assign_group_color(self, group: str) -> str:
        """
        Get the hex color for a group, assigning a new palette color if
        the group doesn't yet have one. Empty/None group becomes "".
        """
        key = group or ""
        if key in self.group_color_map:
            return self.group_color_map[key]

        if not self._marker_palette:
            color = "#FFFFFF"
        else:
            idx = len(self.group_color_map) % len(self._marker_palette)
            color = self._marker_palette[idx]

        self.group_color_map[key] = color
        return color

    def _next_marker_number_for_color(self, color: str) -> int:
        """
        Compute the next marker_number for the given color by scanning
        existing monsters with that exact marker_color.
        """
        start = config.CONFIG.marker_start_number
        max_found = 0

        for m in self.monsters:
            if m.marker_color == color and m.marker_number > max_found:
                max_found = m.marker_number

        if max_found <= 0:
            return start
        return max_found + 1

    def _assign_marker_for_monster(self, monster: MonsterInstance) -> None:
        """
        Ensure marker_color and marker_number are set in a consistent
        way for a monster as it is added to the encounter.

        - Color:
            * If monster.marker_color is non-empty, keep it.
            * Otherwise, assign based on group using _get_or_assign_group_color.
        - Number:
            * If monster.marker_number > 0, keep it.
            * Otherwise, assign using _next_marker_number_for_color(color).
        """
        # Color by group
        group = monster.group or ""
        auto_color = self._get_or_assign_group_color(group)

        if monster.marker_color:
            color = monster.marker_color
        else:
            color = auto_color
            monster.marker_color = color

        # Number per color
        if monster.marker_number and monster.marker_number > 0:
            return

        monster.marker_number = self._next_marker_number_for_color(color)

    def _rebuild_marker_maps(self) -> None:
        """
        Rebuild group_color_map from current monsters.

        We do not renumber existing markers here; we only ensure that
        groups have stable colors going forward. Per-color numbering
        continues from current monsters.
        """
        self.group_color_map = {}

        # First pass: respect existing group/color combos
        for m in self.monsters:
            group = m.group or ""
            color = m.marker_color or ""
            if group not in self.group_color_map and color:
                self.group_color_map[group] = color

        # Second pass: assign colors to monsters with no color yet
        for m in self.monsters:
            if not m.marker_color:
                group = m.group or ""
                color = self._get_or_assign_group_color(group)
                m.marker_color = color

    # ====================================================================
    # 2. Monster Library
    # ====================================================================

    def load_monster_library(self, path: str):
        self.monster_library = persistence.load_monster_library(path)
        self._log(f"Loaded {len(self.monster_library)} monsters from library.")
        self._changed()

    def find_template_by_file(self, template_file: str) -> Optional[MonsterTemplate]:
        for tpl in self.monster_library:
            if tpl.file == template_file:
                return tpl
        return None

    # ====================================================================
    # 3. Hero Management
    # ====================================================================

    def add_hero(self, hero: Hero):
        self.heroes.append(hero)
        self._log(f"Hero added: {hero.name}")
        self._changed()

    def new_hero(self, name: str = "New Hero") -> Hero:
        hero = Hero.new(name)
        self.add_hero(hero)
        return hero

    def remove_hero(self, hero: Hero):
        if hero in self.heroes:
            self.heroes.remove(hero)
            self._log(f"Hero removed: {hero.name}")
            self._changed()

    # ====================================================================
    # 4. Monster Management
    # ====================================================================

    def add_monster_from_template(
        self,
        template: MonsterTemplate,
        group: Optional[str] = None,
    ) -> MonsterInstance:
        """
        Create a MonsterInstance from a template, apply group if given,
        then auto-assign marker color/number and add to encounter.
        """
        m = MonsterInstance.from_template(template)
        if group is not None:
            m.group = group

        self._assign_marker_for_monster(m)
        self.monsters.append(m)

        self._log(
            f"Monster added: {m.name} "
            f"(group='{m.group}', color={m.marker_color}, #={m.marker_number})"
        )
        self._changed()
        return m

    def add_monster_instance(self, instance: MonsterInstance):
        """
        Add a pre-built MonsterInstance to the encounter, normalizing
        its marker metadata.
        """
        self._assign_marker_for_monster(instance)
        self.monsters.append(instance)
        self._log(
            f"Monster added (instance): {instance.name} "
            f"(group='{instance.group}', color={instance.marker_color}, #={instance.marker_number})"
        )
        self._changed()

    def remove_monster(self, monster: MonsterInstance):
        if monster in self.monsters:
            self.monsters.remove(monster)
            self._log(f"Monster removed: {monster.name}")
            # No renumbering
            self._changed()

    # ====================================================================
    # 5. Combat Actions
    # ====================================================================

    # --- HEROES ---

    def damage_hero(self, hero: Hero, amount: int):
        before = (hero.hp_current, hero.temp_hp)
        hero.apply_damage(amount)
        after = (hero.hp_current, hero.temp_hp)

        if config.CONFIG.log_damage_events:
            self._log(
                f"Hero {hero.name} takes {amount} damage "
                f"(HP {before[0]}→{after[0]}, Temp {before[1]}→{after[1]})"
            )

        if hero.is_dying and config.CONFIG.log_deaths:
            self._log(f"⚠ Hero {hero.name} is DYING!")

        if getattr(hero, "concentrating", False):
            self._notify_concentration_note(hero)

        self._changed()

    def heal_hero(self, hero: Hero, amount: int):
        before = hero.hp_current
        hero.apply_healing(amount)
        after = hero.hp_current

        if config.CONFIG.log_heal_events:
            self._log(f"Hero {hero.name} heals {amount} HP ({before}→{after})")
        self._changed()

    def set_hero_temp_hp(self, hero: Hero, amount: int):
        hero.set_temp_hp(amount)
        if config.CONFIG.log_condition_changes:
            self._log(f"Hero {hero.name} gains {amount} temporary HP.")
        self._changed()

    def add_hero_condition(self, hero: Hero, cond: str):
        hero.add_condition(cond)
        if config.CONFIG.log_condition_changes:
            self._log(f"Hero {hero.name} gains condition: {cond}")
        self._changed()

    def remove_hero_condition(self, hero: Hero, cond: str):
        hero.remove_condition(cond)
        if config.CONFIG.log_condition_changes:
            self._log(f"Hero {hero.name} loses condition: {cond}")
        self._changed()

    # --- MONSTERS ---

    def damage_monster(self, monster: MonsterInstance, amount: int):
        before_hp = monster.hp_current
        before_temp = monster.temp_hp

        monster.apply_damage(amount)

        after_hp = monster.hp_current
        after_temp = monster.temp_hp

        if config.CONFIG.log_damage_events:
            self._log(
                f"Monster {monster.name} takes {amount} damage "
                f"(HP {before_hp}→{after_hp}, Temp {before_temp}→{after_temp})"
            )

        if monster.is_last_stand and config.CONFIG.log_last_stand_triggers:
            self._log(
                f"🔥 {monster.name} triggers LAST STAND ({monster.last_stand_hp_value} HP)!"
            )

        if monster.is_dead and config.CONFIG.log_deaths:
            self._log(f"💀 Monster {monster.name} is DEAD.")

        self._changed()

    def heal_monster(self, monster: MonsterInstance, amount: int):
        before = monster.hp_current
        monster.apply_healing(amount)
        after = monster.hp_current

        if config.CONFIG.log_heal_events:
            self._log(f"Monster {monster.name} heals {amount} HP ({before}→{after})")
        self._changed()

    def set_monster_temp_hp(self, monster: MonsterInstance, amount: int):
        monster.set_temp_hp(amount)
        if config.CONFIG.log_condition_changes:
            self._log(f"Monster {monster.name} gains {amount} temporary HP.")
        self._changed()

    def add_monster_condition(self, monster: MonsterInstance, cond: str):
        monster.add_condition(cond)
        if config.CONFIG.log_condition_changes:
            self._log(f"Monster {monster.name} gains condition: {cond}")
        self._changed()

    def remove_monster_condition(self, monster: MonsterInstance, cond: str):
        monster.remove_condition(cond)
        if config.CONFIG.log_condition_changes:
            self._log(f"Monster {monster.name} loses condition: {cond}")
        self._changed()

    # ====================================================================
    # 6. Party Load/Save
    # ====================================================================

    def load_party(self, path: str):
        party = persistence.load_party(path)
        self.heroes = party.heroes
        self._log(f"Loaded party: {party.name} ({len(self.heroes)} heroes)")
        self._changed()

    def save_party(self, path: str, name: Optional[str] = None):
        party = Party.new(name or "Party")
        party.heroes = self.heroes.copy()
        persistence.save_party(path, party)
        self._log(f"Saved party: {party.name}")

    # ====================================================================
    # 7. Encounter Load/Save
    # ====================================================================

    def load_encounter(self, path: str):
        enc = persistence.load_encounter(path)
        self.monsters = enc.monsters
        self._log(f"Loaded encounter: {enc.name} ({len(self.monsters)} monsters)")
        self._rebuild_marker_maps()
        self._changed()

    def save_encounter(self, path: str, name: Optional[str] = None):
        enc = Encounter.new(name or "Encounter")
        enc.monsters = self.monsters.copy()
        persistence.save_encounter(path, enc)
        self._log(f"Saved encounter: {enc.name}")

    # ====================================================================
    # 8. Session Autosave
    # ====================================================================

    def autosave(self):
        """
        Autosave current heroes/monsters if enabled in config.
        """
        if not config.CONFIG.autosave_enabled:
            return
        persistence.autosave_session(
            self.heroes,
            self.monsters,
            path=config.CONFIG.autosave_path,
        )

    def load_session(self, path: str | None = None):
        """
        Load a session from the configured autosave path by default.
        """
        actual_path = path or config.CONFIG.autosave_path
        heroes, monsters = persistence.load_session(actual_path)
        self.heroes = heroes
        self.monsters = monsters
        self._log(
            f"Session loaded: {len(self.heroes)} heroes, {len(self.monsters)} monsters"
        )
        self._rebuild_marker_maps()
        # Notify UI of state change without triggering autosave
        if self.on_state_changed:
            self.on_state_changed()

    # ====================================================================
    # 9. Encounter Difficulty Calculation
    # ====================================================================

    def total_hero_levels(self) -> int:
        """Calculate the sum of all hero levels."""
        return sum(getattr(h, "level", 0) for h in self.heroes)

    def total_monster_levels(self) -> int:
        """
        Calculate the sum of all non-dead monster levels.
        Includes both active and inactive monsters (only excludes dead monsters).
        """
        total = 0.0
        for m in self.monsters:
            if getattr(m, "dead", False):
                continue
            # Monster level might be stored as string or int
            level = getattr(m, "level", 0)
            try:
                total += self._parse_level_value(level)
            except (ValueError, TypeError):
                continue
        return total

    @staticmethod
    def _parse_level_value(level) -> float:
        """Parse integer, float, or fractional level values like '1/2'."""
        if isinstance(level, (int, float)):
            return float(level)
        if isinstance(level, str):
            raw = level.strip()
            if not raw:
                return 0.0
            token = raw.split()[0]
            if "/" in token:
                return float(Fraction(token))
            return float(token)
        return 0.0

    def encounter_difficulty_ratio(self) -> float:
        """
        Calculate the encounter difficulty ratio (monster levels / hero levels).
        Returns 0.0 if there are no heroes.
        """
        hero_total = self.total_hero_levels()
        if hero_total == 0:
            return 0.0
        monster_total = self.total_monster_levels()
        return monster_total / hero_total

    def encounter_difficulty_label(self) -> str:
        """
        Return a difficulty label based on the current encounter.

        Returns one of: "Easy", "Medium", "Hard", "Deadly", "Very Deadly", or "No Encounter"
        """
        ratio = self.encounter_difficulty_ratio()

        if ratio == 0.0:
            return "No Encounter"

        cfg = config.CONFIG

        if ratio < cfg.encounter_difficulty_easy:
            return "Easy"
        elif ratio < cfg.encounter_difficulty_medium:
            return "Medium"
        elif ratio < cfg.encounter_difficulty_hard:
            return "Hard"
        elif ratio <= cfg.encounter_difficulty_deadly_max:
            return "Deadly"
        else:
            return "Very Deadly"
