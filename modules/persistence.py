# persistence.py
# ========================================================================
# NIMBLE COMBAT TRACKER — PERSISTENCE LAYER (JSON I/O)
# ========================================================================
#
# This module handles all disk I/O for the Nimble Combat Tracker:
#
#   • Monster library load/save    (MonsterTemplate objects)
#   • Party load/save              (Party with Hero objects)
#   • Encounter load/save          (Encounter with MonsterInstance objects)
#   • Session autosave/load        (current heroes + monsters)
#
# DESIGN GOALS
# ------------------------------------------------------------------------
#   • Keep ALL file format knowledge here, not in UI or CombatManager.
#   • Use simple, human-readable JSON structures.
#   • Be robust against "extra" keys from older/newer versions of data.
#   • Never pass unknown keyword args (like "id") into dataclasses.
#
# FILE FORMATS
# ------------------------------------------------------------------------
#
# 1) Monster Library JSON
#    ---------------------
#    Either of these shapes is accepted on load:
#
#      A) { "monsters": [ MonsterTemplateDict, ... ] }
#      B) [ MonsterTemplateDict, ... ]   (top-level list)
#
#    Each MonsterTemplateDict must match MonsterTemplate.to_dict()
#
# 2) Party JSON
#    ----------
#      {
#          "name": "My Party",
#          "notes": "Optional string",
#          "heroes": [ HeroDict, ... ]
#      }
#
# 3) Encounter JSON
#    ---------------
#      {
#          "name": "Goblin Ambush",
#          "notes": "Optional string",
#          "monsters": [ MonsterInstanceDict, ... ]
#      }
#
# 4) Session Autosave JSON
#    ----------------------
#      {
#          "heroes":   [ HeroDict, ... ],
#          "monsters": [ MonsterInstanceDict, ... ]
#      }
#
# For each Dict above, we only keep fields that are declared in the
# corresponding dataclass. Unknown keys (like legacy "id") are ignored.
#
# ========================================================================
# END OF TITLE BLOCK
# ========================================================================

from __future__ import annotations

import json
from dataclasses import fields
from pathlib import Path
from typing import List, Tuple, Dict, Any

from modules.combatants import (
    Hero,
    MonsterTemplate,
    MonsterInstance,
    Party,
    Encounter,
)


# ------------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------------

def _read_json(path: str | Path) -> Any:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"JSON file not found: {p}")
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str | Path, data: Any) -> None:
    p = Path(path)
    # Always create the parent tree to avoid scattered caller checks.
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        # Keep data human-readable; preserve any non-ASCII in names/notes.
        json.dump(data, f, indent=2, ensure_ascii=False)


def _filter_fields(data: Dict[str, Any], cls) -> Dict[str, Any]:
    """
    Return a copy of 'data' containing only keys that are dataclass
    fields on 'cls'. This lets us safely ignore extra keys like "id".
    """
    valid = {f.name for f in fields(cls)}
    return {k: v for k, v in data.items() if k in valid}


# ========================================================================
# MONSTER LIBRARY
# ========================================================================

def load_monster_library(path: str | Path) -> List[MonsterTemplate]:
    """
    Load a monster library JSON file and return a list of MonsterTemplate
    objects.

    Accepted JSON shapes:

        { "monsters": [ {...}, {...} ] }
        [ {...}, {...} ]
    """
    raw = _read_json(path)

    items = raw
    if isinstance(raw, dict):
        # Support legacy layouts that split base/legendary lists.
        base_list = raw.get("monsters", [])
        legendary_list = raw.get("legendary_monsters", [])
        if isinstance(base_list, list) or isinstance(legendary_list, list):
            merged = []
            if isinstance(base_list, list):
                # Ensure legendary defaults to False for base monsters
                for entry in base_list:
                    if isinstance(entry, dict) and "legendary" not in entry:
                        entry["legendary"] = False
                merged.extend(base_list)
            if isinstance(legendary_list, list):
                # Ensure legendary defaults to True for legendary monsters
                for entry in legendary_list:
                    if isinstance(entry, dict) and "legendary" not in entry:
                        entry["legendary"] = True
                merged.extend(legendary_list)
            items = merged

    if not isinstance(items, list):
        raise ValueError("Monster library JSON must be a list or have 'monsters' list.")

    result: List[MonsterTemplate] = []
    for entry in items:
        if not isinstance(entry, dict):
            continue
        # Ensure legendary field exists with default False
        if "legendary" not in entry:
            entry["legendary"] = False
        filtered = _filter_fields(entry, MonsterTemplate)
        result.append(MonsterTemplate.from_dict(filtered))

    return result


def save_monster_library(path: str | Path, monsters: List[MonsterTemplate]) -> None:
    """
    Save a list of MonsterTemplate objects as JSON.

    The format used is:
        { "monsters": [ MonsterTemplate.to_dict(), ... ] }
    """
    data = {
        "monsters": [m.to_dict() for m in monsters],
    }
    _write_json(path, data)


# ========================================================================
# PARTY (HERO GROUP)
# ========================================================================

def load_party(path: str | Path) -> Party:
    """
    Load a Party from a JSON file.
    """
    raw = _read_json(path)
    if not isinstance(raw, dict):
        raise ValueError("Party JSON must be an object.")

    # Heroes
    heroes_data = raw.get("heroes", [])
    heroes: List[Hero] = []
    for h in heroes_data:
        if not isinstance(h, dict):
            continue
        filtered = _filter_fields(h, Hero)
        heroes.append(Hero.from_dict(filtered))

    party = Party.new(raw.get("name", "Party"))
    party.notes = raw.get("notes", "")
    party.heroes = heroes
    return party


def save_party(path: str | Path, party: Party) -> None:
    """
    Save a Party to a JSON file.
    """
    data = party.to_dict()
    _write_json(path, data)


# ========================================================================
# ENCOUNTER (MONSTER GROUP)
# ========================================================================

def load_encounter(path: str | Path) -> Encounter:
    """
    Load an Encounter from a JSON file.
    """
    raw = _read_json(path)
    if not isinstance(raw, dict):
        raise ValueError("Encounter JSON must be an object.")

    monsters_data = raw.get("monsters", [])
    monsters: List[MonsterInstance] = []
    for m in monsters_data:
        if not isinstance(m, dict):
            continue
        filtered = _filter_fields(m, MonsterInstance)
        monsters.append(MonsterInstance.from_dict(filtered))

    enc = Encounter.new(raw.get("name", "Encounter"))
    enc.notes = raw.get("notes", "")
    enc.monsters = monsters
    return enc


def save_encounter(path: str | Path, encounter: Encounter) -> None:
    """
    Save an Encounter to a JSON file.
    """
    data = encounter.to_dict()
    _write_json(path, data)


# ========================================================================
# SESSION AUTOSAVE (HEROES + MONSTERS TOGETHER)
# ========================================================================

def autosave_session(
    heroes: List[Hero],
    monsters: List[MonsterInstance],
    path: str | Path,
) -> None:
    """
    Save the current heroes + monsters as a session JSON file.
    """
    data = {
        "heroes": [h.to_dict() for h in heroes],
        "monsters": [m.to_dict() for m in monsters],
    }
    _write_json(path, data)


def load_session(path: str | Path) -> Tuple[List[Hero], List[MonsterInstance]]:
    """
    Load a session JSON file containing heroes + monsters.

    If the file does not exist, returns EMPTY lists.
    """
    p = Path(path)
    if not p.is_file():
        # No session yet – return empty state
        return [], []

    raw = _read_json(p)
    if not isinstance(raw, dict):
        raise ValueError("Session JSON must be an object.")

    heroes_data = raw.get("heroes", [])
    monsters_data = raw.get("monsters", [])

    heroes: List[Hero] = []
    monsters: List[MonsterInstance] = []

    for h in heroes_data:
        if not isinstance(h, dict):
            continue
        filtered = _filter_fields(h, Hero)
        heroes.append(Hero.from_dict(filtered))

    for m in monsters_data:
        if not isinstance(m, dict):
            continue
        filtered = _filter_fields(m, MonsterInstance)
        monsters.append(MonsterInstance.from_dict(filtered))

    return heroes, monsters
