from __future__ import annotations

import unittest

from modules import config
from modules.combatManager import CombatManager
from modules.combatants import Hero, MonsterInstance


def make_monster(level: str | int | float) -> MonsterInstance:
    return MonsterInstance(
        name=f"Monster {level}",
        template_file="monster.md",
        legendary=False,
        level=str(level),
        armor="Light",
        speed="6",
        size="Medium",
        saves="-",
        flavor="",
        hp_max=10,
        hp_current=10,
    )


class DifficultyProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_autosave = config.CONFIG.autosave_enabled
        config.CONFIG.autosave_enabled = False

    def tearDown(self) -> None:
        config.CONFIG.autosave_enabled = self.original_autosave

    def test_profile_replaces_hero_total_for_difficulty(self) -> None:
        manager = CombatManager()
        manager.heroes = [Hero(name="Ignored", level=10)]
        manager.monsters = [make_monster(4)]
        manager.set_difficulty_profile(player_count=4, average_party_level=2)

        self.assertEqual(manager.difficulty_party_total_level(), 8)
        self.assertEqual(manager.encounter_difficulty_ratio(), 0.5)
        self.assertEqual(manager.encounter_difficulty_label(), "Medium")

    def test_fractional_monster_levels_are_supported(self) -> None:
        manager = CombatManager()
        manager.monsters = [make_monster("1/2"), make_monster("1/4")]
        manager.set_difficulty_profile(player_count=3, average_party_level=1)

        self.assertEqual(manager.total_monster_levels(), 0.75)
        self.assertEqual(manager.encounter_difficulty_label(), "Easy")

    def test_current_very_deadly_band_starts_above_125_percent(self) -> None:
        manager = CombatManager()
        manager.monsters = [make_monster(6)]
        manager.set_difficulty_profile(player_count=4, average_party_level=1)

        self.assertEqual(manager.encounter_difficulty_ratio(), 1.5)
        self.assertEqual(manager.encounter_difficulty_label(), "Very Deadly")

    def test_clear_profile_falls_back_to_existing_hero_behavior(self) -> None:
        manager = CombatManager()
        manager.heroes = [Hero(name="A", level=2), Hero(name="B", level=2)]
        manager.monsters = [make_monster(2)]
        manager.set_difficulty_profile(player_count=1, average_party_level=10)
        manager.clear_difficulty_profile()

        self.assertEqual(manager.difficulty_party_total_level(), 4)
        self.assertEqual(manager.encounter_difficulty_ratio(), 0.5)

    def test_invalid_profile_values_are_rejected(self) -> None:
        manager = CombatManager()

        with self.assertRaises(ValueError):
            manager.set_difficulty_profile(player_count=0, average_party_level=1)
        with self.assertRaises(ValueError):
            manager.set_difficulty_profile(player_count=4, average_party_level=0)


if __name__ == "__main__":
    unittest.main()

