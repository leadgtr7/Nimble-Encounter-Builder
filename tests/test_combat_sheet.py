from __future__ import annotations

import unittest
from pathlib import Path

from modules.combatants import MonsterInstance
from nicegui_ui.combat_sheet import export_combat_sheet_pdf


class CombatSheetExportTests(unittest.TestCase):
    def test_exports_portrait_pdf_with_current_monsters(self) -> None:
        monster = MonsterInstance(
            name="Bandit Assassin",
            template_file="bandit.md",
            legendary=False,
            level="2",
            armor="None",
            speed="6",
            size="Medium",
            saves="-",
            flavor="",
            type="Monster",
            hp_max=24,
            hp_current=24,
            group="Bandits",
            marker_color="Red",
            marker_number=1,
            actions=["Poison Blade. 1d8+2. On damage, Dazed"],
        )
        difficulty = {
            "party_total": "8",
            "monster_total": "2",
            "label": "Easy",
            "ratio": "25%",
            "easy": "< 4",
            "medium": "< 6",
            "hard": "< 8",
            "deadly": "<= 10",
        }

        path = Path.cwd() / "tmp" / "test_combat_sheet.pdf"
        try:
            exported = export_combat_sheet_pdf(
                [monster],
                difficulty,
                path,
                "Test Encounter",
                available_conditions=["Blinded", "Dazed", "Last Stand"],
            )
            content = exported.read_bytes()
        finally:
            path.unlink(missing_ok=True)

        self.assertTrue(content.startswith(b"%PDF"))
        self.assertIn(b"Test Encounter", content)
        self.assertIn(b"Bandit Assassin", content)
        self.assertIn(b"HP Track", content)
        self.assertIn(b"Cond / Notes", content)
        self.assertIn(b"Reference Cards", content)
        self.assertIn(b"Poison Blade", content)
        self.assertIn(b"Round", content)
        self.assertNotIn(b"Blinded", content)
        self.assertNotIn(b"Last Stand", content)
        self.assertNotIn(b"Red", content)
        self.assertNotIn(b"Init", content)
        self.assertNotIn(b"Mk", content)


if __name__ == "__main__":
    unittest.main()
