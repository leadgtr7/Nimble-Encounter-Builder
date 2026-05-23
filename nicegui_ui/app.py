"""NiceGUI encounter builder front end."""

from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

from nicegui import app as nicegui_app
from nicegui import ui

from modules import config

from .stat_card import render_empty_stat_card, render_monster_stat_card
from .state import PROJECT_ROOT, EncounterUiState, create_state
from .styles import APP_CSS


STATIC_ROUTE = "/nimble-assets"
ICON_PATH = PROJECT_ROOT / "EncounterBuilderIconImage.png"

try:
    nicegui_app.add_static_files(STATIC_ROUTE, str(PROJECT_ROOT))
except Exception:
    pass


def _selected_uid_from_args(args: Any) -> str | None:
    if not isinstance(args, dict):
        return None
    data = args.get("data")
    if isinstance(data, dict):
        return str(data.get("uid") or "") or None
    return str(args.get("uid") or "") or None


def _read_positive_int(value: Any, default: int = 1, allow_zero: bool = False) -> int:
    try:
        parsed = int(float(value))
    except (TypeError, ValueError):
        parsed = default
    minimum = 0 if allow_zero else 1
    return max(minimum, parsed)


def _split_conditions(raw: str) -> list[str]:
    parts = raw.replace("\n", ",").replace(";", ",").split(",")
    return [part.strip() for part in parts if part.strip()]


def _render_difficulty(summary: dict[str, str]) -> str:
    return f"""
    <div class="difficulty-pill" style="background:{escape(summary['color'])}">
      {escape(summary['label'])} ({escape(summary['ratio'])})
    </div>
    <div class="difficulty-table">
      <span>Party total</span><b>{escape(summary['party_total'])}</b>
      <span>Monster total</span><b>{escape(summary['monster_total'])}</b>
      <span>Easy</span><b>{escape(summary['easy'])}</b>
      <span>Medium</span><b>{escape(summary['medium'])}</b>
      <span>Hard</span><b>{escape(summary['hard'])}</b>
      <span>Deadly</span><b>{escape(summary['deadly'])}</b>
      <span>Very Deadly</span><b>{escape(summary['very_deadly'])}</b>
    </div>
    """


def _render_loot(items: list[str]) -> str:
    if not items:
        return '<div class="loot-list">No loot candidates in the current selection.</div>'
    rows = "".join(f"<li>{escape(item)}</li>" for item in items)
    return f'<ul class="loot-list">{rows}</ul>'


def _default_encounter_path() -> str:
    folder = config.CONFIG.get_encounter_folder()
    filename = f"encounter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    return str(folder / filename)


def _combat_grid_options() -> dict[str, Any]:
    return {
        "columnDefs": [
            {"headerName": "Active", "field": "active", "width": 82},
            {
                "headerName": "#",
                "field": "marker",
                "width": 58,
                ":cellStyle": (
                    "params => ({backgroundColor: params.data.marker_color || 'transparent', "
                    "color: params.data.marker_text_color || '#ffffff', "
                    "fontWeight: 800, textAlign: 'center'})"
                ),
            },
            {"headerName": "Name", "field": "name", "minWidth": 160, "flex": 2},
            {"headerName": "Group", "field": "group", "width": 105},
            {"headerName": "Lvl", "field": "level", "width": 70},
            {
                "headerName": "HP",
                "field": "hp",
                "width": 76,
                ":cellClass": "params => 'hp-' + params.data.status_class",
            },
            {"headerName": "Tmp", "field": "temp_hp", "width": 72},
            {"headerName": "Max", "field": "max_hp", "width": 72},
            {"headerName": "Status", "field": "status", "width": 112},
            {"headerName": "Con", "field": "concentrating", "width": 74},
            {"headerName": "Conditions", "field": "conditions", "minWidth": 150, "flex": 2},
            {"field": "uid", "hide": True},
            {"field": "status_class", "hide": True},
            {"field": "marker_color", "hide": True},
            {"field": "marker_text_color", "hide": True},
        ],
        "defaultColDef": {
            "sortable": True,
            "resizable": True,
            "filter": False,
            "suppressMenu": True,
        },
        "rowData": [],
        "rowSelection": "single",
        "animateRows": True,
        "suppressCellFocus": True,
    }


def create_page() -> None:
    state = create_state()
    ui.add_css(APP_CSS)
    ui.dark_mode().enable()

    with ui.header().classes("app-header"):
        with ui.row().classes("items-center no-wrap q-gutter-sm"):
            if ICON_PATH.exists():
                ui.image(f"{STATIC_ROUTE}/{ICON_PATH.name}").classes("app-logo")
            ui.label("Nimble Encounter Builder").classes("app-title")
            ui.space()
            ui.label("NiceGUI Encounter View").classes("text-caption text-grey-5")

    with ui.element("main").classes("app-shell"):
        with ui.element("div").classes("app-grid"):
            with ui.element("section").classes("panel"):
                ui.label("Monster Library").classes("panel-title")
                search_input = ui.input("Search").props("dense outlined clearable").classes("compact-field w-full")
                with ui.row().classes("w-full q-gutter-sm"):
                    level_input = ui.input("Level").props("dense outlined clearable").classes("compact-field")
                    biome_select = ui.select([], label="Biome").props("dense outlined clearable").classes("compact-field")
                legendary_switch = ui.switch("Include legendary", value=False)
                library_count = ui.label("")
                bestiary_select = ui.select({}, label="Monster").props("dense outlined").classes("w-full")
                group_input = ui.input("Group / wave").props("dense outlined clearable").classes("w-full")
                with ui.row().classes("q-gutter-sm"):
                    add_button = ui.button("Add", icon="add")
                    reload_button = ui.button("Reload", icon="refresh")

            with ui.element("section").classes("panel"):
                ui.label("Combat Tracker").classes("panel-title")
                with ui.row().classes("w-full items-end q-gutter-sm"):
                    encounter_path = ui.input("Encounter file").props("dense outlined").classes("col")
                    save_button = ui.button("Save", icon="save")
                    load_button = ui.button("Load", icon="folder_open")
                with ui.row().classes("q-gutter-sm"):
                    remove_button = ui.button("Remove", icon="delete")
                    clear_button = ui.button("Clear", icon="clear_all")
                grid = ui.aggrid(_combat_grid_options()).classes("combat-grid ag-theme-balham-dark")

            with ui.element("section").classes("panel"):
                ui.label("Encounter Tools").classes("panel-title")
                with ui.row().classes("w-full q-gutter-sm"):
                    player_count_input = ui.number(
                        "Players",
                        value=getattr(config.CONFIG, "default_player_count", 4),
                        min=1,
                        max=12,
                        step=1,
                    ).props("dense outlined").classes("compact-field")
                    avg_level_input = ui.number(
                        "Avg level",
                        value=getattr(config.CONFIG, "default_average_party_level", 1.0),
                        min=0.25,
                        step=0.25,
                    ).props("dense outlined").classes("compact-field")
                difficulty_html = ui.html("").classes("w-full")

                ui.separator()
                stat_card = ui.html(render_empty_stat_card()).classes("stat-card-host")

                ui.separator()
                ui.label("Selected Monster").classes("panel-title")
                with ui.row().classes("w-full q-gutter-sm"):
                    active_switch = ui.switch("Active")
                    concentration_switch = ui.switch("Concentrating")
                with ui.row().classes("w-full q-gutter-sm"):
                    amount_input = ui.number("Amount", value=1, min=0, step=1).props("dense outlined")
                    damage_button = ui.button("Damage", icon="flash_on")
                    heal_button = ui.button("Heal", icon="favorite")
                    temp_button = ui.button("Temp HP", icon="shield")
                    reset_button = ui.button("Reset", icon="restart_alt")
                conditions_input = ui.input("Conditions, comma-separated").props("dense outlined clearable").classes("w-full")
                conditions_button = ui.button("Set Conditions", icon="check")

                ui.separator()
                ui.label("Loot Hook").classes("panel-title")
                loot_candidates = ui.html("").classes("w-full")
                loot_draft = ui.textarea("Loot draft").props("outlined autogrow").classes("w-full")
                with ui.row().classes("q-gutter-sm"):
                    add_loot_button = ui.button("Add Selected Loot", icon="playlist_add")
                    clear_loot_button = ui.button("Clear Draft", icon="backspace")

                ui.separator()
                ui.label("Combat Hook").classes("panel-title")
                log_text = ui.textarea("Combat log").props("readonly outlined autogrow").classes("w-full combat-log")

    syncing_selection = {"active": False}

    def refresh_template_options() -> None:
        options = state.template_options(
            search=search_input.value or "",
            level=level_input.value or "",
            biome=biome_select.value or "",
            include_legendary=bool(legendary_switch.value),
        )
        if state.selected_template_key not in options:
            state.selected_template_key = next(iter(options), None)
        bestiary_select.options = options
        bestiary_select.value = state.selected_template_key
        bestiary_select.update()
        library_count.text = f"{len(options)} shown / {len(state.monster_library)} loaded"

    def refresh_selection_controls() -> None:
        monster = state.selected_monster()
        syncing_selection["active"] = True
        try:
            if monster is None:
                stat_card.content = render_empty_stat_card()
                active_switch.value = False
                concentration_switch.value = False
                conditions_input.value = ""
            else:
                stat_card.content = render_monster_stat_card(monster)
                active_switch.value = bool(monster.active)
                concentration_switch.value = bool(monster.concentrating)
                conditions_input.value = ", ".join(monster.conditions or [])
            stat_card.update()
            active_switch.update()
            concentration_switch.update()
            conditions_input.update()
        finally:
            syncing_selection["active"] = False

    def refresh_loot() -> None:
        loot_candidates.content = _render_loot(state.loot_candidates(selected_only=True))
        loot_candidates.update()
        loot_draft.value = state.loot_draft
        loot_draft.update()

    def refresh_log() -> None:
        log_text.value = "\n".join(state.event_log[-120:])
        log_text.update()

    def refresh_difficulty() -> None:
        difficulty_html.content = _render_difficulty(state.difficulty_summary())
        difficulty_html.update()

    def refresh_combat_grid() -> None:
        grid.options["rowData"] = state.combat_rows()
        grid.update()

    def refresh_all() -> None:
        refresh_combat_grid()
        refresh_selection_controls()
        refresh_difficulty()
        refresh_loot()
        refresh_log()

    def on_template_value_change(event: Any) -> None:
        state.selected_template_key = event.value

    def add_selected_template() -> None:
        template = state.selected_template()
        if template is None:
            ui.notify("Select a monster first.", color="warning")
            return
        monster = state.manager.add_monster_from_template(
            template,
            group=(group_input.value or "").strip() or None,
        )
        state.select_monster_uid(state.monster_uid(monster))
        refresh_all()

    def reload_library() -> None:
        state.load_monster_library_from_config()
        biome_select.options = state.biome_options()
        biome_select.update()
        refresh_template_options()
        refresh_all()

    def select_grid_row(event: Any) -> None:
        uid = _selected_uid_from_args(event.args)
        state.select_monster_uid(uid)
        refresh_all()

    def selected_monster_or_notify():
        monster = state.selected_monster()
        if monster is None:
            ui.notify("Select a combat row first.", color="warning")
        return monster

    def damage_selected() -> None:
        monster = selected_monster_or_notify()
        if monster is None:
            return
        state.manager.damage_monster(monster, _read_positive_int(amount_input.value))

    def heal_selected() -> None:
        monster = selected_monster_or_notify()
        if monster is None:
            return
        state.manager.heal_monster(monster, _read_positive_int(amount_input.value))

    def temp_selected() -> None:
        monster = selected_monster_or_notify()
        if monster is None:
            return
        state.manager.set_monster_temp_hp(
            monster,
            _read_positive_int(amount_input.value, allow_zero=True),
        )

    def reset_selected() -> None:
        monster = selected_monster_or_notify()
        if monster is None:
            return
        state.manager.reset_monster_combat_state(monster)

    def remove_selected() -> None:
        monster = selected_monster_or_notify()
        if monster is None:
            return
        state.manager.remove_monster(monster)
        state.select_monster_uid(None)
        refresh_all()

    def clear_encounter() -> None:
        state.select_monster_uid(None)
        state.manager.clear_monsters()
        refresh_all()

    def set_conditions() -> None:
        monster = selected_monster_or_notify()
        if monster is None:
            return
        state.manager.set_monster_conditions(monster, _split_conditions(conditions_input.value or ""))

    def toggle_active(event: Any) -> None:
        if syncing_selection["active"]:
            return
        monster = state.selected_monster()
        if monster is not None:
            state.manager.set_monster_active(monster, bool(event.value))

    def toggle_concentration(event: Any) -> None:
        if syncing_selection["active"]:
            return
        monster = state.selected_monster()
        if monster is not None:
            state.manager.set_monster_concentrating(monster, bool(event.value))

    def update_difficulty_profile() -> None:
        try:
            state.manager.set_difficulty_profile(
                _read_positive_int(player_count_input.value),
                float(avg_level_input.value or 1),
            )
        except ValueError as exc:
            ui.notify(str(exc), color="negative")
        refresh_difficulty()

    def save_encounter() -> None:
        path = (encounter_path.value or "").strip()
        if not path:
            ui.notify("Enter an encounter file path.", color="warning")
            return
        try:
            state.manager.save_encounter(path, name=Path(path).stem)
        except Exception as exc:  # noqa: BLE001
            ui.notify(f"Could not save encounter: {exc}", color="negative")
        refresh_log()

    def load_encounter() -> None:
        path = (encounter_path.value or "").strip()
        if not path:
            ui.notify("Enter an encounter file path.", color="warning")
            return
        try:
            state.manager.load_encounter(path)
        except Exception as exc:  # noqa: BLE001
            ui.notify(f"Could not load encounter: {exc}", color="negative")
        state.select_monster_uid(None)
        refresh_all()

    def add_selected_loot() -> None:
        items = state.loot_candidates(selected_only=True)
        if not items:
            ui.notify("No selected-monster loot candidates.", color="warning")
            return
        addition = "\n".join(f"- {item}" for item in items)
        state.loot_draft = f"{state.loot_draft.rstrip()}\n{addition}".strip()
        refresh_loot()

    def clear_loot_draft() -> None:
        state.loot_draft = ""
        refresh_loot()

    state.manager.on_state_changed = refresh_all
    search_input.on_value_change(lambda _: refresh_template_options())
    level_input.on_value_change(lambda _: refresh_template_options())
    biome_select.on_value_change(lambda _: refresh_template_options())
    legendary_switch.on_value_change(lambda _: refresh_template_options())
    bestiary_select.on_value_change(on_template_value_change)
    add_button.on_click(add_selected_template)
    reload_button.on_click(reload_library)
    grid.on("rowClicked", select_grid_row)
    damage_button.on_click(damage_selected)
    heal_button.on_click(heal_selected)
    temp_button.on_click(temp_selected)
    reset_button.on_click(reset_selected)
    remove_button.on_click(remove_selected)
    clear_button.on_click(clear_encounter)
    conditions_button.on_click(set_conditions)
    active_switch.on_value_change(toggle_active)
    concentration_switch.on_value_change(toggle_concentration)
    player_count_input.on_value_change(lambda _: update_difficulty_profile())
    avg_level_input.on_value_change(lambda _: update_difficulty_profile())
    save_button.on_click(save_encounter)
    load_button.on_click(load_encounter)
    add_loot_button.on_click(add_selected_loot)
    clear_loot_button.on_click(clear_loot_draft)

    encounter_path.value = _default_encounter_path()
    encounter_path.update()
    biome_select.options = state.biome_options()
    biome_select.update()
    refresh_template_options()
    refresh_all()


@ui.page("/")
def index() -> None:
    create_page()


def run(host: str = "127.0.0.1", port: int = 8789) -> None:
    kwargs: dict[str, Any] = {
        "title": "Nimble Encounter Builder",
        "host": host,
        "port": port,
        "reload": False,
    }
    if ICON_PATH.exists():
        kwargs["favicon"] = str(ICON_PATH)
    ui.run(**kwargs)

