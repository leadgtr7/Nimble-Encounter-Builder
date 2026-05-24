"""Exercise the NiceGUI combat workflow without opening a browser.

This script uses NiceGUI's in-process user simulation. It drives the encounter
prep flow used for the reMarkable workflow: add monsters, select a row for the
reference card, check balancing state, export the portrait PDF, remove, and
clear.
"""

from __future__ import annotations

import asyncio
import os
import sys
import warnings
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import httpx

warnings.filterwarnings(
    "ignore",
    message="coroutine 'Outbox.loop' was never awaited",
    category=RuntimeWarning,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from nicegui import ElementFilter, core, run as nicegui_run, ui  # noqa: E402
from nicegui.functions.download import download  # noqa: E402
from nicegui.functions.navigate import Navigate  # noqa: E402
from nicegui.functions.notify import notify  # noqa: E402
from nicegui.testing import User, UserInteraction  # noqa: E402
from nicegui.testing.general import nicegui_reset_globals, prepare_simulation  # noqa: E402

from modules import config  # noqa: E402
from nicegui_ui.app import create_page  # noqa: E402


@asynccontextmanager
async def root_simulation(root: Callable) -> AsyncGenerator[User]:
    """Run NiceGUI's ASGI test client in root-function mode for scripts."""
    with nicegui_reset_globals():
        os.environ["NICEGUI_USER_SIMULATION"] = "true"
        try:
            prepare_simulation()
            core.script_mode = False
            core.script_client = None
            ui.run(root)
            async with core.app.router.lifespan_context(core.app):
                transport = httpx.ASGITransport(core.app)
                async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                    yield User(client)
        finally:
            os.environ.pop("NICEGUI_USER_SIMULATION", None)
            ui.navigate = Navigate()
            ui.notify = notify
            ui.download = download


def element(user: User, marker: str) -> ui.element:
    with user:
        matches = sorted(ElementFilter(marker=marker), key=lambda item: item.id)
    if not matches:
        raise AssertionError(f"Could not find UI marker: {marker}")
    return matches[0]


def click(user: User, marker: str) -> None:
    item = element(user, marker)
    UserInteraction(user, {item}, marker).click()


def trigger(user: User, marker: str, event: str, args: Any = None) -> None:
    item = element(user, marker)
    UserInteraction(user, {item}, marker).trigger(event, args)


def set_value(user: User, marker: str, value: Any) -> None:
    item = element(user, marker)
    if not hasattr(item, "value"):
        raise AssertionError(f"Element {marker} has no value property.")
    with user:
        item.value = value


def grid_rows(user: User) -> list[dict[str, Any]]:
    grid = element(user, "combat-grid")
    rows = getattr(grid, "options", {}).get("rowData", [])
    return list(rows)


async def wait_for_rows(user: User, count: int, label: str) -> list[dict[str, Any]]:
    for _ in range(20):
        rows = grid_rows(user)
        if len(rows) == count:
            return rows
        await asyncio.sleep(0.05)
    raise AssertionError(f"{label}: expected {count} combat row(s), found {len(grid_rows(user))}.")


def selected_row(user: User) -> dict[str, Any]:
    rows = grid_rows(user)
    for row in rows:
        if row.get("selected"):
            return row
    if rows:
        return rows[0]
    raise AssertionError("No combat rows available.")


def select_first_row(user: User) -> dict[str, Any]:
    row = selected_row(user)
    trigger(user, "combat-grid", "rowClicked", row["uid"])
    return selected_row(user)


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


async def run_simulation() -> None:
    config.CONFIG.autosave_enabled = False

    def safe_setup() -> None:
        nicegui_run.process_pool = None

    nicegui_run.setup = safe_setup

    async with root_simulation(create_page) as user:
        await user.open("/")
        await user.should_see("Nimble Encounter Builder")

        click(user, "clear-encounter")
        await wait_for_rows(user, 0, "clear encounter")

        click(user, "add-monster")
        click(user, "add-monster")
        rows = await wait_for_rows(user, 2, "add monsters")

        row = select_first_row(user)
        await user.should_see(row["name"])
        await user.should_see("Encounter Balance")

        click(user, "export-sheet")
        download = await user.download.next()
        if not download.content.startswith(b"%PDF"):
            raise AssertionError("export-sheet did not download a PDF.")

        click(user, "remove-selected")
        rows = await wait_for_rows(user, 1, "remove selected")
        assert_equal(len(rows), 1, "remove selected leaves one row")

        click(user, "clear-encounter")
        await wait_for_rows(user, 0, "clear after export")

        print("NiceGUI combat simulation passed.")
        print(f"Exported portrait sheet bytes: {len(download.content)}")


if __name__ == "__main__":
    asyncio.run(run_simulation())
