from __future__ import annotations

import unittest

from modules.combatants import MonsterInstance
from nicegui_ui.stat_card import render_empty_stat_card, render_monster_stat_card


def make_monster(**overrides) -> MonsterInstance:
    data = {
        "name": "Clockwork Guard",
        "template_file": "clockwork.md",
        "legendary": False,
        "level": "2",
        "armor": "Medium",
        "speed": "6",
        "size": "Medium",
        "saves": "Might +2",
        "flavor": "A precise brass sentinel.",
        "actions": ["Slam", "1d8+2"],
        "special_actions": ["Wind Up: Gain advantage on the next strike."],
        "bloodied_text": "",
        "last_stand_text": "",
        "last_stand_hp_value": 0,
        "biome_loot": [],
        "type": "Construct",
        "biome": "Foundry",
        "hp_max": 18,
        "hp_current": 18,
    }
    data.update(overrides)
    return MonsterInstance(**data)


class StatCardTests(unittest.TestCase):
    def test_empty_card_prompts_for_selection(self) -> None:
        self.assertIn("Select a monster", render_empty_stat_card())

    def test_normal_monster_renders_core_stats(self) -> None:
        html = render_monster_stat_card(make_monster())

        self.assertIn("Clockwork Guard", html)
        self.assertIn("Lvl 2", html)
        self.assertIn("HP 18/18", html)
        self.assertIn("Armor", html)
        self.assertIn("Slam", html)

    def test_legendary_callouts_render(self) -> None:
        html = render_monster_stat_card(
            make_monster(
                legendary=True,
                bloodied_text="Vents steam.",
                last_stand_text="Restarts once.",
                last_stand_hp_value=9,
            )
        )

        self.assertIn("Legendary", html)
        self.assertIn("Bloodied", html)
        self.assertIn("Last Stand", html)
        self.assertIn("HP 9", html)

    def test_missing_fields_render_without_crashing(self) -> None:
        html = render_monster_stat_card({"name": "Sparse", "actions": []})

        self.assertIn("Sparse", html)
        self.assertIn("No entries", html)

    def test_html_is_escaped(self) -> None:
        html = render_monster_stat_card(make_monster(name="<script>alert(1)</script>"))

        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertNotIn("<script>", html)

    def test_long_actions_are_not_truncated(self) -> None:
        actions = [f"Action {index}: detail" for index in range(8)]
        html = render_monster_stat_card(make_monster(actions=actions))

        self.assertIn("Action 7", html)


if __name__ == "__main__":
    unittest.main()

