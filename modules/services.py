"""Application services used by the manager and UI.

This module gives the app explicit seams for persistence and extensions while
keeping the existing JSON file format as the default implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from modules import persistence
from modules.combatants import Encounter, Hero, MonsterInstance, MonsterTemplate, Party
from modules.extensions import ExtensionRegistry, LogFn, load_plugins


class StorageService(Protocol):
    """Persistence operations needed by CombatManager."""

    def load_monster_library(self, path: str | Path) -> list[MonsterTemplate]:
        """Load monster templates."""

    def save_monster_library(self, path: str | Path, monsters: list[MonsterTemplate]) -> None:
        """Save monster templates."""

    def load_party(self, path: str | Path) -> Party:
        """Load a party."""

    def save_party(self, path: str | Path, party: Party) -> None:
        """Save a party."""

    def load_encounter(self, path: str | Path) -> Encounter:
        """Load an encounter."""

    def save_encounter(self, path: str | Path, encounter: Encounter) -> None:
        """Save an encounter."""

    def autosave_session(
        self,
        heroes: list[Hero],
        monsters: list[MonsterInstance],
        path: str | Path,
    ) -> None:
        """Save current session state."""

    def load_session(self, path: str | Path) -> tuple[list[Hero], list[MonsterInstance]]:
        """Load current session state."""


class JsonStorageService:
    """Default storage implementation backed by the existing JSON helpers."""

    def load_monster_library(self, path: str | Path) -> list[MonsterTemplate]:
        return persistence.load_monster_library(path)

    def save_monster_library(self, path: str | Path, monsters: list[MonsterTemplate]) -> None:
        persistence.save_monster_library(path, monsters)

    def load_party(self, path: str | Path) -> Party:
        return persistence.load_party(path)

    def save_party(self, path: str | Path, party: Party) -> None:
        persistence.save_party(path, party)

    def load_encounter(self, path: str | Path) -> Encounter:
        return persistence.load_encounter(path)

    def save_encounter(self, path: str | Path, encounter: Encounter) -> None:
        persistence.save_encounter(path, encounter)

    def autosave_session(
        self,
        heroes: list[Hero],
        monsters: list[MonsterInstance],
        path: str | Path,
    ) -> None:
        persistence.autosave_session(heroes, monsters, path)

    def load_session(self, path: str | Path) -> tuple[list[Hero], list[MonsterInstance]]:
        return persistence.load_session(path)


@dataclass
class JsonMonsterLibraryImporter:
    """Built-in importer for the current monster library JSON format."""

    storage: StorageService
    id: str = "json.monster_library"
    label: str = "Nimble JSON Monster Library"
    file_extensions: tuple[str, ...] = (".json",)

    def load(self, path: str | Path) -> list[MonsterTemplate]:
        return self.storage.load_monster_library(path)


@dataclass
class JsonPartyImporter:
    """Built-in importer for the current party JSON format."""

    storage: StorageService
    id: str = "json.party"
    label: str = "Nimble JSON Party"
    file_extensions: tuple[str, ...] = (".json",)

    def load(self, path: str | Path) -> Party:
        return self.storage.load_party(path)


@dataclass
class JsonEncounterImporter:
    """Built-in importer for the current encounter JSON format."""

    storage: StorageService
    id: str = "json.encounter"
    label: str = "Nimble JSON Encounter"
    file_extensions: tuple[str, ...] = (".json",)

    def load(self, path: str | Path) -> Encounter:
        return self.storage.load_encounter(path)


@dataclass
class AppServices:
    """Container for app-wide services and extension registries."""

    storage: StorageService
    extensions: ExtensionRegistry


def create_default_services(
    project_root: str | Path,
    log_fn: LogFn | None = None,
) -> AppServices:
    """Build default services and load optional plugins."""

    storage = JsonStorageService()
    registry = ExtensionRegistry()
    registry.register_monster_library_importer(JsonMonsterLibraryImporter(storage))
    registry.register_party_importer(JsonPartyImporter(storage))
    registry.register_encounter_importer(JsonEncounterImporter(storage))
    load_plugins(
        registry=registry,
        project_root=project_root,
        log_fn=log_fn,
    )
    return AppServices(
        storage=storage,
        extensions=registry,
    )
