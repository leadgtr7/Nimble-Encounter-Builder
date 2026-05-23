from __future__ import annotations

import importlib.util
import unittest


@unittest.skipUnless(importlib.util.find_spec("nicegui"), "NiceGUI is not installed")
class NiceGuiDependencyTests(unittest.TestCase):
    def test_nicegui_app_and_testing_tools_import(self) -> None:
        import nicegui_ui.app as app_module
        from nicegui import ui
        from nicegui import testing

        self.assertTrue(callable(app_module.create_page))
        self.assertTrue(hasattr(ui, "aggrid"))
        self.assertIsNotNone(testing)


if __name__ == "__main__":
    unittest.main()

