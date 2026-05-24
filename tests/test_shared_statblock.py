import unittest

from modules.shared_statblock import render_stat_block


class SharedStatBlockRenderTests(unittest.TestCase):
    def test_paired_lite_limit_counts_actions_not_fragments(self) -> None:
        html = render_stat_block(
            {
                "name": "Rime Tongue",
                "level": "1/4",
                "hp": "8",
                "actions": [
                    "Bash.",
                    "1d4+1 Bludgeoning",
                    "Ice Spit.",
                    "(Range 3), 1d4 cold damage.",
                    "Third Action.",
                    "Hidden in lite mode.",
                ],
            },
            mode="lite",
        )

        self.assertIn("<b>Bash</b> - 1d4+1 Bludgeoning", html)
        self.assertIn("<b>Ice Spit</b> - (Range 3), 1d4 cold damage.", html)
        self.assertNotIn("Third Action", html)
        self.assertIn("...", html)

    def test_paired_details_can_contain_trigger_colons(self) -> None:
        html = render_stat_block(
            {
                "name": "Bandit Assassin",
                "actions": ["Poison Blade.", "1d8+2. On damage: Dazed."],
            },
            mode="full",
        )

        self.assertIn("<b>Poison Blade</b> - 1d8+2. On damage: Dazed.", html)

    def test_long_abilities_wrap_and_keep_sentence_punctuation(self) -> None:
        html = render_stat_block(
            {
                "name": "Rime Tongue",
                "level": "1",
                "hp_max": 28,
                "special_actions": [
                    "Drag Beneath",
                    (
                        "Rime tongue hits Slow their targets. If a Slowed creature is "
                        "hit again, it becomes Grappled/Restrained. Attacks that miss "
                        "the rime tongue instead strike the grappled target."
                    ),
                ],
            },
            mode="full",
        )

        self.assertIn("targets. If a Slowed creature", html)
        self.assertIn("Grappled/Restrained. Attacks", html)
        self.assertIn("<div style='margin-left:16px;'>", html)
        self.assertNotIn("display:inline-block", html)

    def test_passives_render_before_actions(self) -> None:
        html = render_stat_block(
            {
                "name": "Bandit Assassin",
                "passives": ["Sneak", "You are invisible until you attack."],
                "actions": ["Poison Blade", "1d8+2. On damage: Dazed."],
            },
            mode="full",
        )

        self.assertLess(html.index("Passives"), html.index("Actions"))
        self.assertIn("<b>Sneak</b> - You are invisible until you attack.", html)

    def test_html_escapes_monster_content(self) -> None:
        html = render_stat_block(
            {
                "name": "<script>alert(1)</script>",
                "actions": ["Bite.", "<b>not trusted</b>"],
            },
            mode="full",
        )

        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertIn("&lt;b&gt;not trusted&lt;/b&gt;", html)
        self.assertNotIn("<script>", html)


if __name__ == "__main__":
    unittest.main()
