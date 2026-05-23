"""Extension contracts and plugin discovery for Nimble Encounter Builder.

The core app owns the session state. Extensions add capabilities around it:
import/export formats, encounter generators, rulesets, or optional UI hooks.
"""

from __future__ import annotations

import importlib
import pkgutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Protocol

from modules.combatants import Encounter, MonsterTemplate, Party


LogFn = Callable[[str], None]


class MonsterLibraryImporter(Protocol):
    """Load monster templates from an external source."""

    id: str
    label: str
    file_extensions: tuple[str, ...]

    def load(self, path: str | Path) -> list[MonsterTemplate]:
        """Return monster templates loaded from path."""


class PartyImporter(Protocol):
    """Load a saved party from an external source."""

    id: str
    label: str
    file_extensions: tuple[str, ...]

    def load(self, path: str | Path) -> Party:
        """Return a party loaded from path."""


class EncounterImporter(Protocol):
    """Load a saved encounter from an external source."""

    id: str
    label: str
    file_extensions: tuple[str, ...]

    def load(self, path: str | Path) -> Encounter:
        """Return an encounter loaded from path."""


class EncounterGenerator(Protocol):
    """Create an encounter from app state and caller-provided options."""

    id: str
    label: str

    def generate(self, context: object, options: dict) -> Encounter:
        """Return a generated encounter."""


class RulesetPlugin(Protocol):
    """Optional rules hooks for variants of Nimble or other systems."""

    id: str
    label: str


class UiContribution(Protocol):
    """Optional UI contribution hook.

    UI plugins receive the loaded main app object so they can attach actions,
    tabs, or dialogs without changing the core startup path.
    """

    id: str
    label: str

    def attach(self, app: object) -> None:
        """Attach UI behavior to the running app."""


@dataclass
class ExtensionRegistry:
    """Registry of extension points available to the app."""

    monster_library_importers: dict[str, MonsterLibraryImporter] = field(default_factory=dict)
    party_importers: dict[str, PartyImporter] = field(default_factory=dict)
    encounter_importers: dict[str, EncounterImporter] = field(default_factory=dict)
    encounter_generators: dict[str, EncounterGenerator] = field(default_factory=dict)
    rulesets: dict[str, RulesetPlugin] = field(default_factory=dict)
    ui_contributions: dict[str, UiContribution] = field(default_factory=dict)

    def register_monster_library_importer(self, importer: MonsterLibraryImporter) -> None:
        self.monster_library_importers[importer.id] = importer

    def register_party_importer(self, importer: PartyImporter) -> None:
        self.party_importers[importer.id] = importer

    def register_encounter_importer(self, importer: EncounterImporter) -> None:
        self.encounter_importers[importer.id] = importer

    def register_encounter_generator(self, generator: EncounterGenerator) -> None:
        self.encounter_generators[generator.id] = generator

    def register_ruleset(self, ruleset: RulesetPlugin) -> None:
        self.rulesets[ruleset.id] = ruleset

    def register_ui_contribution(self, contribution: UiContribution) -> None:
        self.ui_contributions[contribution.id] = contribution


def load_plugins(
    registry: ExtensionRegistry,
    plugin_package: str = "plugins",
    project_root: str | Path | None = None,
    log_fn: LogFn | None = None,
) -> None:
    """Discover and load Python plugins from a package.

    A plugin module can expose either:
      - register(registry)
      - PLUGIN with a register(registry) method
    """

    root = Path(project_root) if project_root is not None else Path.cwd()
    plugins_dir = root / plugin_package
    if not plugins_dir.exists():
        return

    root_text = str(root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)

    try:
        package = importlib.import_module(plugin_package)
    except Exception as exc:  # noqa: BLE001
        if log_fn:
            log_fn(f"Plugin package '{plugin_package}' could not be loaded: {exc}")
        return

    for module_info in pkgutil.iter_modules(package.__path__, f"{plugin_package}."):
        try:
            module = importlib.import_module(module_info.name)
            register = getattr(module, "register", None)
            if callable(register):
                register(registry)
                continue
            plugin = getattr(module, "PLUGIN", None)
            plugin_register = getattr(plugin, "register", None)
            if callable(plugin_register):
                plugin_register(registry)
        except Exception as exc:  # noqa: BLE001
            if log_fn:
                log_fn(f"Plugin '{module_info.name}' could not be loaded: {exc}")
