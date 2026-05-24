import unittest

from modules.combatants import MonsterInstance, MonsterTemplate


class MonsterPassiveTests(unittest.TestCase):
    def test_template_passives_copy_to_instance(self) -> None:
        template = MonsterTemplate(
            name="Bandit Assassin",
            file="bandit.md",
            legendary=False,
            level="2",
            hp="24",
            armor="None",
            speed="6",
            size="Medium",
            saves="",
            flavor="",
            actions=["Poison Blade", "1d8+2"],
            special_actions=[],
            bloodied="",
            last_stand="",
            last_stand_hp="",
            biome_loot=[],
            type="Monsters",
            biome="Bandits",
            passives=["Sneak", "You are invisible until you attack."],
        )

        monster = MonsterInstance.from_template(template)

        self.assertEqual(template.passives, monster.passives)

    def test_old_template_json_without_passives_still_loads(self) -> None:
        template = MonsterTemplate.from_dict(
            {
                "name": "Old Monster",
                "file": "old.md",
                "legendary": False,
                "level": "1",
                "hp": "10",
                "armor": "None",
                "speed": "6",
                "size": "Medium",
                "saves": "",
                "flavor": "",
                "actions": [],
                "special_actions": [],
                "bloodied": "",
                "last_stand": "",
                "last_stand_hp": "",
                "biome_loot": [],
                "type": "Monsters",
                "biome": "",
            }
        )

        self.assertEqual([], template.passives)


if __name__ == "__main__":
    unittest.main()
