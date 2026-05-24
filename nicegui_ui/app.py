"""NiceGUI encounter builder front end."""

from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

from nicegui import app as nicegui_app
from nicegui import run as nicegui_run
from nicegui import ui

from modules import config
from modules.combatants import MonsterInstance

from .combat_sheet import export_combat_sheet_pdf
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
    if isinstance(args, str):
        return args or None
    if isinstance(args, (list, tuple)) and args:
        return _selected_uid_from_args(args[0])
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


def _read_lines(raw: str) -> list[str]:
    return [line.strip() for line in str(raw or "").splitlines() if line.strip()]


def _join_lines(items: list[str] | None) -> str:
    return "\n".join(items or [])


def _conditions_from_value(value: Any) -> list[str]:
    def normalize_item(item: Any) -> str:
        if isinstance(item, dict):
            item = item.get("value") or item.get("label") or item.get("name") or ""
        return str(item).strip()

    if isinstance(value, (list, tuple, set)):
        return [normalized for item in value if (normalized := normalize_item(item))]
    if isinstance(value, dict):
        normalized = normalize_item(value)
        return [normalized] if normalized else []
    return _split_conditions(str(value or ""))


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


def _default_log_path() -> str:
    folder = config.CONFIG.get_combat_log_folder()
    filename = f"combat_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    return str(folder / filename)


def _default_combat_sheet_path() -> Path:
    folder = config.CONFIG.get_encounter_folder() / "Combat Sheets"
    filename = f"combat_sheet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return folder / filename


def _encounter_file_options() -> dict[str, str]:
    folder = config.CONFIG.get_encounter_folder()
    if not folder.exists():
        return {}
    files = sorted(folder.glob("*.json"), key=lambda path: path.name.lower())
    return {str(path): path.name for path in files}


def _log_file_options() -> dict[str, str]:
    folder = config.CONFIG.get_combat_log_folder()
    if not folder.exists():
        return {}
    files = sorted(folder.glob("*.txt"), key=lambda path: path.name.lower())
    return {str(path): path.name for path in files}


def _render_selected_summary(monster: MonsterInstance | None) -> str:
    if monster is None:
        return "No monster selected"
    marker = ""
    if monster.marker_color and monster.marker_number:
        marker = f" | Mk {monster.marker_number}"
    return (
        f"{monster.name}{marker} | HP {monster.effective_hp}/{monster.hp_max} "
        f"| {', '.join(monster.conditions or []) or 'No conditions'}"
    )


def _combat_grid_options() -> dict[str, Any]:
    return {
        "columnDefs": [
            {"headerName": "Act", "field": "active", "width": 62},
            {
                "headerName": "#",
                "field": "marker",
                "width": 46,
                ":cellStyle": (
                    "params => params.data.marker_color ? "
                    "({backgroundColor: params.data.marker_color, "
                    "color: params.data.marker_text_color || '#fff', fontWeight: 800}) : null"
                ),
            },
            {"headerName": "Name", "field": "name", "minWidth": 150, "flex": 1.4},
            {"headerName": "Group", "field": "group", "width": 84},
            {"headerName": "Lvl", "field": "level", "width": 52},
            {
                "headerName": "HP",
                "field": "hp",
                "width": 58,
                ":cellClass": "params => params.data.status_class ? 'hp-' + params.data.status_class : ''",
            },
            {"headerName": "Tmp", "field": "temp_hp", "width": 52},
            {"headerName": "Max", "field": "max_hp", "width": 52},
            {"headerName": "Status", "field": "status", "width": 92},
            {"headerName": "Con", "field": "concentrating", "width": 54},
            {"headerName": "Conditions", "field": "conditions", "minWidth": 120, "flex": 1.2},
            {"field": "uid", "hide": True},
            {"field": "status_class", "hide": True},
            {"field": "marker_color", "hide": True},
            {"field": "marker_text_color", "hide": True},
            {"field": "selected", "hide": True},
        ],
        "defaultColDef": {
            "sortable": True,
            "resizable": True,
            "filter": False,
            "suppressMenu": True,
        },
        "rowData": [],
        "rowSelection": "single",
        ":getRowId": "params => params.data.uid",
        "rowClassRules": {"selected-row": "data.selected === true"},
        "animateRows": True,
        "suppressCellFocus": True,
    }


def create_page() -> None:
    state = create_state()
    ui.add_css(APP_CSS)
    ui.dark_mode().enable()

    def icon_button(icon: str, tooltip: str, color: str = "primary"):
        button = ui.button(icon=icon, color=color).props("dense round unelevated")
        button.tooltip(tooltip)
        return button

    with ui.header().classes("app-header"):
        with ui.row().classes("items-center no-wrap q-gutter-sm"):
            if ICON_PATH.exists():
                ui.image(f"{STATIC_ROUTE}/{ICON_PATH.name}").classes("app-logo")
            ui.label("Nimble Encounter Builder").classes("app-title")
            ui.space()
            ui.label("NiceGUI Encounter View").classes("text-caption text-grey-5")

    with ui.element("main").classes("app-shell"):
        with ui.element("div").classes("focus-grid"):
            with ui.element("section").classes("panel stat-panel"):
                with ui.row().classes("w-full items-center q-gutter-sm"):
                    ui.label("Reference Card").classes("panel-title")
                    ui.space()
                    selected_summary = ui.label("No monster selected").classes("selected-summary").mark("selected-summary")
                stat_card = ui.html(render_empty_stat_card()).classes("stat-card-host").mark("reference-card")

            with ui.element("section").classes("panel setup-panel"):
                ui.label("Build Encounter").classes("panel-title")
                with ui.row().classes("w-full items-end q-gutter-sm setup-row"):
                    search_input = ui.input("Search").props("dense outlined clearable").classes("compact-field")
                    level_input = ui.input("Level").props("dense outlined clearable").classes("level-field")
                    biome_select = ui.select([], label="Biome").props("dense outlined clearable").classes("compact-field")
                    legendary_switch = ui.switch("Legendary", value=False).props("dense")
                    reload_button = icon_button("refresh", "Reload monster library", "grey-8").mark("reload-library")
                library_count = ui.label("").classes("library-count")
                with ui.row().classes("w-full items-end q-gutter-sm setup-row"):
                    bestiary_select = ui.select({}, label="Monster").props("dense outlined").classes("monster-select").mark("monster-select")
                    group_input = ui.input("Group / wave").props("dense outlined clearable").classes("compact-field").mark("group-input")
                    add_button = ui.button("Add", icon="add").props("unelevated").mark("add-monster")

            with ui.element("section").classes("panel balance-panel"):
                with ui.row().classes("w-full items-center q-gutter-sm"):
                    ui.label("Encounter Balance").classes("panel-title")
                    ui.space()
                    difficulty_badge = ui.html("").classes("combat-difficulty-badge")
                    export_sheet_button = ui.button("Export Portrait Sheet", icon="picture_as_pdf").props("unelevated").mark("export-sheet")
                with ui.row().classes("w-full items-end q-gutter-sm"):
                    player_count_input = ui.number(
                        "Players",
                        value=getattr(config.CONFIG, "default_player_count", 4),
                        min=1,
                        max=12,
                        step=1,
                    ).props("dense outlined").classes("small-number-field").mark("players-input")
                    avg_level_input = ui.number(
                        "Avg level",
                        value=getattr(config.CONFIG, "default_average_party_level", 1.0),
                        min=0.25,
                        step=0.25,
                    ).props("dense outlined").classes("small-number-field").mark("avg-level-input")
                difficulty_html = ui.html("").classes("w-full").mark("difficulty-summary")

            with ui.element("section").classes("panel combat-panel"):
                with ui.row().classes("w-full items-center q-gutter-sm"):
                    ui.label("Combat List").classes("panel-title")
                    ui.space()
                    remove_button = icon_button("delete", "Remove selected monster", "negative").mark("remove-selected")
                    clear_button = icon_button("clear_all", "Clear encounter", "grey-8").mark("clear-encounter")
                grid = ui.aggrid(
                    _combat_grid_options(),
                    theme="balham",
                    auto_size_columns=False,
                ).classes("combat-grid").mark("combat-grid")

    with ui.dialog() as monster_dialog, ui.card().classes("monster-edit-dialog"):
        ui.label("Monster").classes("panel-title")
        with ui.grid(columns=2).classes("w-full q-gutter-sm"):
            edit_name = ui.input("Name").props("dense outlined")
            edit_group = ui.input("Group / wave").props("dense outlined")
            edit_hp_max = ui.number("Max HP", value=1, min=0, step=1).props("dense outlined")
            edit_level = ui.input("Level").props("dense outlined")
            edit_armor = ui.input("Armor").props("dense outlined")
            edit_speed = ui.input("Speed").props("dense outlined")
            edit_size = ui.input("Size").props("dense outlined")
            edit_type = ui.input("Type").props("dense outlined")
            edit_biome = ui.input("Biome").props("dense outlined")
            edit_saves = ui.input("Saves").props("dense outlined")
            edit_last_stand_hp = ui.number("Last Stand HP", value=0, min=0, step=1).props("dense outlined")
            edit_legendary = ui.switch("Legendary")
        edit_flavor = ui.textarea("Flavor").props("outlined autogrow").classes("w-full")
        edit_passives = ui.textarea("Passives, one per line").props("outlined autogrow").classes("w-full")
        edit_actions = ui.textarea("Actions, one per line").props("outlined autogrow").classes("w-full")
        edit_special_actions = ui.textarea("Special actions, one per line").props("outlined autogrow").classes("w-full")
        edit_bloodied = ui.textarea("Bloodied").props("outlined autogrow").classes("w-full")
        edit_last_stand = ui.textarea("Last Stand").props("outlined autogrow").classes("w-full")
        edit_loot = ui.textarea("Loot, one per line").props("outlined autogrow").classes("w-full")
        with ui.row().classes("w-full justify-end q-gutter-sm"):
            cancel_edit_button = ui.button("Cancel", icon="close")
            save_edit_button = ui.button("Save", icon="save")

    with ui.dialog() as amount_dialog, ui.card().classes("amount-dialog"):
        amount_title = ui.label("Damage").classes("panel-title")
        amount_hint = ui.label("Choose an amount for the selected monster.").classes("amount-hint")
        with ui.element("div").classes("amount-grid"):
            amount_buttons = [
                ui.button(str(value)).props("dense unelevated").classes("amount-option").mark(f"amount-{value}")
                for value in range(1, 31)
            ]
        with ui.row().classes("w-full justify-end"):
            cancel_amount_button = ui.button("Cancel", icon="close").props("flat")

    syncing_selection = {"active": False}
    editing_monster: dict[str, MonsterInstance | None] = {"monster": None}
    pending_amount_action = {"mode": "damage"}

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
        library_count.update()

    def refresh_selection_controls() -> None:
        monster = state.selected_monster()
        syncing_selection["active"] = True
        try:
            summary = _render_selected_summary(monster)
            selected_summary.text = summary
            if monster is None:
                stat_card.content = render_empty_stat_card()
            else:
                stat_card.content = render_monster_stat_card(monster)
            stat_card.update()
            selected_summary.update()
        finally:
            syncing_selection["active"] = False

    def refresh_loot() -> None:
        return

    def refresh_log() -> None:
        return

    def refresh_difficulty() -> None:
        summary = state.difficulty_summary()
        difficulty_html.content = _render_difficulty(summary)
        difficulty_badge.content = (
            f"<span class='difficulty-pill-mini' style='background:{escape(summary['color'])}'>"
            f"{escape(summary['label'])} {escape(summary['ratio'])}</span>"
        )
        difficulty_html.update()
        difficulty_badge.update()

    def refresh_combat_grid() -> None:
        rows = state.combat_rows()
        if rows and state.selected_monster() is None:
            state.select_monster_uid(rows[0]["uid"])
            rows = state.combat_rows()
        grid.options["rowData"] = rows
        grid.update()

    def refresh_encounter_options(selected_path: str | None = None) -> None:
        options = _encounter_file_options()
        encounter_select.options = options
        if selected_path and selected_path in options:
            encounter_select.value = selected_path
        elif encounter_select.value not in options:
            encounter_select.value = next(iter(options), None)
        encounter_select.update()

    def refresh_log_options(selected_path: str | None = None) -> None:
        options = _log_file_options()
        log_select.options = options
        if selected_path and selected_path in options:
            log_select.value = selected_path
        elif log_select.value not in options:
            log_select.value = next(iter(options), None)
        log_select.update()

    def set_path_from_saved_encounter(event: Any) -> None:
        if event.value:
            encounter_path.value = event.value
            encounter_path.update()

    def set_path_from_saved_log(event: Any) -> None:
        if event.value:
            log_path.value = event.value
            log_path.update()

    def refresh_all() -> None:
        refresh_combat_grid()
        refresh_selection_controls()
        refresh_difficulty()

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
        refresh_selection_controls()
        refresh_difficulty()

    def select_and_edit_grid_row(event: Any) -> None:
        uid = _selected_uid_from_args(event.args)
        state.select_monster_uid(uid)
        refresh_selection_controls()
        refresh_difficulty()

    def selected_monster_or_notify() -> MonsterInstance | None:
        monster = state.selected_monster()
        if monster is None:
            ui.notify("Select a combat row first.", color="warning")
        return monster

    def show_post_damage_notices(monster: MonsterInstance) -> None:
        if monster.concentrating:
            message = "Concentration reminder: on a crit, make a DC 10 STR save."
            state.log(message)
            ui.notify(message, color="warning")
        if monster.legendary and monster.is_bloodied and not monster.shown_bloodied_popup:
            monster.shown_bloodied_popup = True
            message = monster.bloodied_text or f"{monster.name} is bloodied."
            state.log(f"{monster.name} bloodied: {message}")
            ui.notify(message, color="warning")
        if monster.is_last_stand and not monster.shown_last_stand_popup:
            monster.shown_last_stand_popup = True
            message = monster.last_stand_text or f"{monster.name} enters Last Stand."
            state.log(f"{monster.name} last stand: {message}")
            ui.notify(message, color="warning")

    def open_amount_dialog(mode: str) -> None:
        monster = selected_monster_or_notify()
        if monster is None:
            return
        pending_amount_action["mode"] = mode
        labels = {
            "damage": ("Damage", f"Hurt {monster.name} by:"),
            "heal": ("Heal", f"Heal {monster.name} by:"),
            "temp": ("Temporary HP", f"Set {monster.name}'s temporary HP to:"),
        }
        title, hint = labels.get(mode, labels["damage"])
        amount_title.text = title
        amount_hint.text = hint
        amount_title.update()
        amount_hint.update()
        amount_dialog.open()

    def apply_amount(value: int) -> None:
        monster = selected_monster_or_notify()
        if monster is None:
            amount_dialog.close()
            return
        mode = pending_amount_action["mode"]
        if mode == "heal":
            state.manager.heal_monster(monster, value)
        elif mode == "temp":
            state.manager.set_monster_temp_hp(monster, value)
        else:
            state.manager.damage_monster(monster, value)
            show_post_damage_notices(monster)
        amount_dialog.close()
        refresh_log()

    def damage_selected() -> None:
        open_amount_dialog("damage")

    def heal_selected() -> None:
        open_amount_dialog("heal")

    def temp_selected() -> None:
        open_amount_dialog("temp")

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
        state.manager.set_monster_conditions(
            monster,
            _conditions_from_value(conditions_input.value),
        )

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

    def set_marker() -> None:
        monster = selected_monster_or_notify()
        if monster is None:
            return
        state.manager.set_monster_marker(
            monster,
            marker_color.value or "",
            _read_positive_int(marker_number.value, default=0, allow_zero=True),
        )

    def suggest_next_marker() -> None:
        color = marker_color.value or None
        if not color:
            options = list(state.marker_color_options())
            color = options[0] if options else ""
            marker_color.value = color
            marker_color.update()
        if color:
            marker_number.value = state.manager._next_marker_number_for_color(color)
            marker_number.update()

    def set_group() -> None:
        monster = selected_monster_or_notify()
        if monster is None:
            return
        state.manager.set_monster_group(monster, selected_group_input.value or "")

    def populate_monster_editor(monster: MonsterInstance | None) -> None:
        edit_name.value = getattr(monster, "name", "") if monster else ""
        edit_group.value = getattr(monster, "group", "") if monster else (group_input.value or "")
        edit_hp_max.value = getattr(monster, "hp_max", 1) if monster else 1
        edit_level.value = str(getattr(monster, "level", "1") if monster else "1")
        edit_armor.value = getattr(monster, "armor", "") if monster else "None"
        edit_speed.value = getattr(monster, "speed", "") if monster else ""
        edit_size.value = getattr(monster, "size", "") if monster else "Medium"
        edit_type.value = getattr(monster, "type", "") if monster else "Monsters"
        edit_biome.value = getattr(monster, "biome", "") if monster else ""
        edit_saves.value = getattr(monster, "saves", "") if monster else ""
        edit_last_stand_hp.value = getattr(monster, "last_stand_hp_value", 0) if monster else 0
        edit_legendary.value = bool(getattr(monster, "legendary", False)) if monster else False
        edit_flavor.value = getattr(monster, "flavor", "") if monster else ""
        edit_passives.value = _join_lines(getattr(monster, "passives", [])) if monster else ""
        edit_actions.value = _join_lines(getattr(monster, "actions", [])) if monster else ""
        edit_special_actions.value = _join_lines(getattr(monster, "special_actions", [])) if monster else ""
        edit_bloodied.value = getattr(monster, "bloodied_text", "") if monster else ""
        edit_last_stand.value = getattr(monster, "last_stand_text", "") if monster else ""
        edit_loot.value = _join_lines(getattr(monster, "biome_loot", [])) if monster else ""
        for element in (
            edit_name,
            edit_group,
            edit_hp_max,
            edit_level,
            edit_armor,
            edit_speed,
            edit_size,
            edit_type,
            edit_biome,
            edit_saves,
            edit_last_stand_hp,
            edit_legendary,
            edit_flavor,
            edit_passives,
            edit_actions,
            edit_special_actions,
            edit_bloodied,
            edit_last_stand,
            edit_loot,
        ):
            element.update()

    def open_selected_editor() -> None:
        monster = selected_monster_or_notify()
        if monster is None:
            return
        editing_monster["monster"] = monster
        populate_monster_editor(monster)
        monster_dialog.open()

    def open_custom_editor() -> None:
        editing_monster["monster"] = None
        populate_monster_editor(None)
        monster_dialog.open()

    def save_monster_edits() -> None:
        hp_max = _read_positive_int(edit_hp_max.value, default=1, allow_zero=True)
        last_stand_hp = _read_positive_int(edit_last_stand_hp.value, default=0, allow_zero=True)
        values = {
            "name": (edit_name.value or "New Monster").strip(),
            "group": (edit_group.value or "").strip(),
            "hp_max": hp_max,
            "level": str(edit_level.value or "1").strip(),
            "armor": str(edit_armor.value or "None").strip(),
            "speed": str(edit_speed.value or "").strip(),
            "size": str(edit_size.value or "Medium").strip(),
            "type": str(edit_type.value or "Monsters").strip(),
            "biome": str(edit_biome.value or "").strip(),
            "saves": str(edit_saves.value or "").strip(),
            "flavor": str(edit_flavor.value or "").strip(),
            "passives": _read_lines(edit_passives.value or ""),
            "actions": _read_lines(edit_actions.value or ""),
            "special_actions": _read_lines(edit_special_actions.value or ""),
            "bloodied_text": str(edit_bloodied.value or "").strip(),
            "last_stand_text": str(edit_last_stand.value or "").strip(),
            "last_stand_hp_value": last_stand_hp,
            "biome_loot": _read_lines(edit_loot.value or ""),
            "legendary": bool(edit_legendary.value),
        }
        monster = editing_monster["monster"]
        if monster is None:
            created = MonsterInstance(
                name=values["name"],
                template_file="",
                legendary=values["legendary"],
                level=values["level"],
                armor=values["armor"],
                speed=values["speed"],
                size=values["size"],
                saves=values["saves"],
                flavor=values["flavor"],
                passives=values["passives"],
                actions=values["actions"],
                special_actions=values["special_actions"],
                bloodied_text=values["bloodied_text"],
                last_stand_text=values["last_stand_text"],
                last_stand_hp_value=values["last_stand_hp_value"],
                biome_loot=values["biome_loot"],
                type=values["type"],
                biome=values["biome"],
                hp_max=values["hp_max"],
                hp_current=values["hp_max"],
                group=values["group"],
            )
            state.manager.add_monster_instance(created)
            state.select_monster_uid(state.monster_uid(created))
        else:
            for key, value in values.items():
                setattr(monster, key, value)
            if monster.hp_current > monster.hp_max:
                monster.hp_current = monster.hp_max
            state.log(f"Monster edited: {monster.name}")
            state.manager._changed()
        monster_dialog.close()
        refresh_all()

    def update_difficulty_profile() -> None:
        try:
            state.manager.set_difficulty_profile(
                _read_positive_int(player_count_input.value),
                float(avg_level_input.value or 1),
            )
        except ValueError as exc:
            ui.notify(str(exc), color="negative")
        refresh_difficulty()

    def export_portrait_sheet() -> None:
        monsters = state.sorted_monsters()
        if not monsters:
            ui.notify("Add monsters before exporting a combat sheet.", color="warning")
            return
        path = _default_combat_sheet_path()
        try:
            exported = export_combat_sheet_pdf(
                monsters,
                state.difficulty_summary(),
                path,
                encounter_name=f"Encounter - {datetime.now().strftime('%Y-%m-%d')}",
                available_conditions=config.CONFIG.available_conditions,
            )
        except Exception as exc:  # noqa: BLE001
            ui.notify(f"Could not export combat sheet: {exc}", color="negative")
            return
        ui.download(exported.read_bytes(), filename=exported.name, media_type="application/pdf")
        ui.notify(f"Combat sheet exported: {exported.name}", color="positive")

    def save_encounter() -> None:
        path = (encounter_path.value or "").strip()
        if not path:
            ui.notify("Enter an encounter file path.", color="warning")
            return
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            state.manager.save_encounter(path, name=Path(path).stem)
        except Exception as exc:  # noqa: BLE001
            ui.notify(f"Could not save encounter: {exc}", color="negative")
        else:
            refresh_encounter_options(path)
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
            return
        if config.CONFIG.auto_refresh_on_encounter_load:
            state.refresh_monsters_from_library()
        first_monster = state.sorted_monsters()[0] if state.manager.monsters else None
        state.select_monster_uid(state.monster_uid(first_monster) if first_monster else None)
        refresh_encounter_options(path)
        refresh_all()

    def refresh_loaded_monsters() -> None:
        count = state.refresh_monsters_from_library()
        if count:
            ui.notify(f"Refreshed {count} monster(s).", color="positive")
        else:
            ui.notify("No matching monsters found in the library.", color="warning")
        refresh_all()

    def generate_random_encounter() -> None:
        count = state.add_random_encounter(
            _read_positive_int(random_count.value, default=3),
            random_difficulty.value or "Medium",
            random_biome.value or "",
            bool(random_exclude_legendary.value),
        )
        if count:
            ui.notify(f"Added {count} random monster(s).", color="positive")
        else:
            ui.notify("No random encounter generated.", color="warning")
        refresh_all()

    def add_selected_loot() -> None:
        items = state.loot_candidates(selected_only=loot_scope.value == "Selected")
        if not items:
            ui.notify("No loot candidates for that scope.", color="warning")
            return
        addition = "\n".join(f"- {item}" for item in items)
        state.loot_draft = f"{state.loot_draft.rstrip()}\n{addition}".strip()
        refresh_loot()

    def add_manual_loot_note() -> None:
        note = (loot_note.value or "").strip()
        if not note:
            ui.notify("Enter a loot note first.", color="warning")
            return
        state.loot_draft = f"{state.loot_draft.rstrip()}\n- {note}".strip()
        loot_note.value = ""
        loot_note.update()
        refresh_loot()

    def clear_loot_draft() -> None:
        state.loot_draft = ""
        refresh_loot()

    def save_log() -> None:
        path = (log_path.value or "").strip()
        if not path:
            ui.notify("Enter a combat log path.", color="warning")
            return
        try:
            target = Path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            content = "\n".join(state.event_log)
            target.write_text(
                f"Combat Log - Saved {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                + "=" * 60
                + "\n\n"
                + content,
                encoding="utf-8",
            )
        except Exception as exc:  # noqa: BLE001
            ui.notify(f"Could not save combat log: {exc}", color="negative")
            return
        state.log(f"Combat log saved to {path}")
        refresh_log_options(path)
        refresh_log()

    def load_log(append: bool = False) -> None:
        path = (log_path.value or "").strip()
        if not path:
            ui.notify("Enter a combat log path.", color="warning")
            return
        try:
            lines = Path(path).read_text(encoding="utf-8").splitlines()
        except Exception as exc:  # noqa: BLE001
            ui.notify(f"Could not load combat log: {exc}", color="negative")
            return
        if append:
            state.event_log.extend(lines)
            state.log(f"Combat log appended from {path}")
        else:
            state.event_log = lines[-250:]
            state.log(f"Combat log loaded from {path}")
        refresh_log()

    def clear_log() -> None:
        state.event_log = []
        refresh_log()

    state.manager.on_state_changed = refresh_all
    search_input.on_value_change(lambda _: refresh_template_options())
    level_input.on_value_change(lambda _: refresh_template_options())
    biome_select.on_value_change(lambda _: refresh_template_options())
    legendary_switch.on_value_change(lambda _: refresh_template_options())
    bestiary_select.on_value_change(on_template_value_change)
    add_button.on_click(add_selected_template)
    reload_button.on_click(reload_library)
    grid.on("rowClicked", select_grid_row, js_handler="(event) => emit(event.data?.uid || '')")
    grid.on("rowDoubleClicked", select_grid_row, js_handler="(event) => emit(event.data?.uid || '')")
    remove_button.on_click(remove_selected)
    clear_button.on_click(clear_encounter)
    player_count_input.on_value_change(lambda _: update_difficulty_profile())
    avg_level_input.on_value_change(lambda _: update_difficulty_profile())
    export_sheet_button.on_click(export_portrait_sheet)

    biome_select.options = state.biome_options()
    biome_select.update()
    refresh_template_options()
    refresh_all()


@ui.page("/")
def index() -> None:
    create_page()


def run(host: str = "127.0.0.1", port: int = 8789) -> None:
    original_setup = nicegui_run.setup

    def safe_setup() -> None:
        try:
            original_setup()
        except PermissionError:
            # Some locked-down Windows shells block ProcessPoolExecutor pipes.
            # This UI does not use run.cpu_bound, so the process pool is optional.
            nicegui_run.process_pool = None

    nicegui_run.setup = safe_setup
    kwargs: dict[str, Any] = {
        "title": "Nimble Encounter Builder",
        "host": host,
        "port": port,
        "reload": False,
    }
    if ICON_PATH.exists():
        kwargs["favicon"] = str(ICON_PATH)
    ui.run(**kwargs)
