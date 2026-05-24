"""Portrait PDF combat worksheet export for handwritten encounter tracking."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from fpdf import FPDF

from modules.combatants import MonsterInstance


PAGE_WIDTH = 215.9
PAGE_HEIGHT = 279.4
MARGIN = 10.0


def _text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text if text else fallback


def _pdf_text(value: Any, fallback: str = "") -> str:
    text = _text(value, fallback)
    return text.encode("latin-1", "replace").decode("latin-1")


def _level(value: Any) -> str:
    return _text(value, "-")


def _line(pdf: FPDF, x1: float, y1: float, x2: float, y2: float) -> None:
    pdf.line(x1, y1, x2, y2)


def _checkbox(pdf: FPDF, x: float, y: float, label: str) -> None:
    pdf.rect(x, y, 3.2, 3.2)
    pdf.set_xy(x + 4.4, y - 0.6)
    pdf.set_font("Helvetica", "", 7)
    pdf.cell(18, 4, label)


def _field(pdf: FPDF, x: float, y: float, label: str, width: float) -> None:
    pdf.set_xy(x, y)
    pdf.set_font("Helvetica", "", 6.5)
    pdf.cell(width, 3, _pdf_text(label))
    _line(pdf, x, y + 6.4, x + width, y + 6.4)


def _wrapped_lines(pdf: FPDF, text: str, width: float, max_lines: int = 4) -> list[str]:
    words = _pdf_text(text).split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and pdf.get_string_width(candidate) > width:
            lines.append(current)
            current = word
            if len(lines) >= max_lines:
                return lines
        else:
            current = candidate
    if current and len(lines) < max_lines:
        lines.append(current)
    return lines


def _draw_wrapped_text(
    pdf: FPDF,
    x: float,
    y: float,
    width: float,
    text: str,
    *,
    size: float = 6.5,
    style: str = "",
    line_height: float = 3.2,
    max_lines: int = 3,
) -> None:
    pdf.set_font("Helvetica", style, size)
    for index, line in enumerate(_wrapped_lines(pdf, text, width, max_lines=max_lines)):
        pdf.set_xy(x, y + (index * line_height))
        pdf.cell(width, line_height, line)


def _draw_header(pdf: FPDF, encounter_name: str, difficulty: dict[str, str]) -> None:
    pdf.set_fill_color(34, 34, 34)
    pdf.rect(0, 0, PAGE_WIDTH, 15, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_xy(MARGIN, 4)
    pdf.cell(95, 6, _pdf_text(encounter_name, "Encounter Sheet"))
    pdf.set_font("Helvetica", "", 8)
    pdf.set_xy(143, 4.5)
    pdf.cell(62, 4, _pdf_text(f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}"), align="R")
    pdf.set_text_color(30, 30, 30)

    y = 19
    _field(pdf, MARGIN, y, "Encounter / Scene", 70)
    _field(pdf, 86, y, "Date", 28)
    _field(pdf, 120, y, "Party", 24)
    _field(pdf, 150, y, "Round", 20)
    _field(pdf, 176, y, "Page", 19)

    pdf.set_xy(MARGIN, 30)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(18, 4, "Balance")
    pdf.set_font("Helvetica", "", 7)
    parts = [
        f"Party {difficulty.get('party_total', '-')}",
        f"Monsters {difficulty.get('monster_total', '-')}",
        f"{difficulty.get('label', '-')}",
        f"Ratio {difficulty.get('ratio', '-')}",
        f"Easy {difficulty.get('easy', '-')}",
        f"Med {difficulty.get('medium', '-')}",
        f"Hard {difficulty.get('hard', '-')}",
        f"Deadly {difficulty.get('deadly', '-')}",
    ]
    pdf.cell(178, 4, _pdf_text("   ".join(parts[:8])))

    pdf.set_xy(MARGIN, 38)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(18, 4, "Rounds")
    x = 30
    for number in range(1, 11):
        pdf.rect(x, 37.2, 6, 6)
        pdf.set_xy(x, 38.4)
        pdf.set_font("Helvetica", "", 6)
        pdf.cell(6, 3, str(number), align="C")
        x += 8


MONSTER_COLUMNS = [
    ("Monster", 40),
    ("Group", 18),
    ("Lvl", 8),
    ("Max", 10),
    ("HP Track", 42),
    ("Temp", 10),
    ("Cond / Notes", 67),
]


def _draw_monster_table_header(pdf: FPDF, y: float) -> float:
    pdf.set_draw_color(80, 80, 80)
    pdf.set_fill_color(222, 222, 222)
    pdf.set_font("Helvetica", "B", 6.8)
    x = MARGIN
    for label, width in MONSTER_COLUMNS:
        pdf.rect(x, y, width, 7, "DF")
        pdf.set_xy(x + 1, y + 2)
        pdf.cell(width - 2, 3, _pdf_text(label))
        x += width
    return y + 7


def _draw_condition_cell(pdf: FPDF, x: float, y: float, width: float, height: float) -> None:
    pdf.set_draw_color(188, 188, 188)
    for line_y in (y + 7, y + 14, y + 21, y + 28):
        if line_y < y + height - 1:
            _line(pdf, x + 2, line_y, x + width - 2, line_y)
    pdf.set_draw_color(110, 110, 110)


def _draw_monster_table_row(
    pdf: FPDF,
    monster: MonsterInstance | None,
    y: float,
) -> float:
    row_height = 18
    values = {
        "Monster": _text(getattr(monster, "name", ""), ""),
        "Group": _text(getattr(monster, "group", ""), ""),
        "Lvl": _level(getattr(monster, "level", "")) if monster is not None else "",
        "Max": str(getattr(monster, "hp_max", "") or ""),
        "Temp": "",
    }
    x = MARGIN
    pdf.set_draw_color(110, 110, 110)
    pdf.set_font("Helvetica", "", 6.8)
    for label, width in MONSTER_COLUMNS:
        pdf.rect(x, y, width, row_height)
        if label == "HP Track":
            for line_y in (y + 7, y + 14):
                _line(pdf, x + 2, line_y, x + width - 2, line_y)
        elif label == "Cond / Notes":
            _draw_condition_cell(pdf, x, y, width, row_height)
        elif label == "Temp":
            for offset in (7, 14):
                _line(pdf, x + 2, y + offset, x + width - 2, y + offset)
        else:
            text = values.get(label, "")
            style = "B" if label == "Monster" else ""
            max_lines = 3 if label == "Monster" else 2
            _draw_wrapped_text(
                pdf,
                x + 1,
                y + 2,
                width - 2,
                text,
                size=6.2 if label == "Monster" else 5.8,
                style=style,
                line_height=3.0,
                max_lines=max_lines,
            )
        x += width
    return y + row_height


def _unique_monsters(monsters: Iterable[MonsterInstance]) -> list[MonsterInstance]:
    unique: list[MonsterInstance] = []
    seen: set[tuple[str, str, str]] = set()
    for monster in monsters:
        key = (
            _text(getattr(monster, "template_file", "")),
            _text(getattr(monster, "name", "")),
            _level(getattr(monster, "level", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(monster)
    return unique


def _draw_reference_card(pdf: FPDF, monster: MonsterInstance, x: float, y: float, width: float, height: float) -> None:
    pdf.set_draw_color(165, 145, 112)
    pdf.set_fill_color(238, 225, 197)
    pdf.rect(x, y, width, height, "DF")
    pdf.set_text_color(30, 25, 18)

    pdf.set_font("Times", "BI", 9)
    pdf.set_xy(x + 2, y + 2)
    pdf.cell(width - 4, 4, _pdf_text(monster.name)[:42])

    pdf.set_font("Helvetica", "B", 5.8)
    meta = f"LVL {_level(monster.level)}, {_text(monster.size, 'Medium')}, {_text(monster.type, 'Monster')}"
    pdf.set_xy(x + 2, y + 7)
    pdf.cell(width - 4, 3, _pdf_text(meta.upper())[:70])

    pdf.set_fill_color(218, 205, 170)
    pdf.rect(x + 2, y + 12, width - 4, 7, "F")
    pdf.set_font("Helvetica", "", 5.5)
    strip = (
        f"HP {getattr(monster, 'hp_max', '')}   "
        f"Armor {_text(getattr(monster, 'armor', ''), '-')}   "
        f"Speed {_text(getattr(monster, 'speed', ''), '-')}   "
        f"Saves {_text(getattr(monster, 'saves', ''), '-')}"
    )
    pdf.set_xy(x + 3, y + 14)
    pdf.cell(width - 6, 2.8, _pdf_text(strip)[:92])

    cursor_y = y + 21
    if _text(getattr(monster, "flavor", "")):
        _draw_wrapped_text(
            pdf,
            x + 2,
            cursor_y,
            width - 4,
            getattr(monster, "flavor", ""),
            size=5.2,
            style="I",
            line_height=2.8,
            max_lines=2,
        )
        cursor_y += 6

    actions = (
        list(getattr(monster, "passives", []) or [])
        + list(getattr(monster, "special_actions", []) or [])
        + list(getattr(monster, "actions", []) or [])
    )
    if actions:
        pdf.set_font("Helvetica", "B", 5.6)
        pdf.set_xy(x + 2, cursor_y)
        pdf.cell(width - 4, 3, "Passives / Actions")
        cursor_y += 3.5
    for action in actions[:3]:
        if cursor_y > y + height - 7:
            break
        _draw_wrapped_text(
            pdf,
            x + 3,
            cursor_y,
            width - 6,
            f"- {action}",
            size=5.2,
            style="",
            line_height=2.8,
            max_lines=2,
        )
        cursor_y += 5.6

    callouts = [
        ("Bloodied", getattr(monster, "bloodied_text", "")),
        ("Last Stand", getattr(monster, "last_stand_text", "")),
    ]
    for label, text in callouts:
        if not _text(text) or cursor_y > y + height - 4:
            continue
        _draw_wrapped_text(
            pdf,
            x + 3,
            cursor_y,
            width - 6,
            f"{label}: {text}",
            size=5.0,
            style="B",
            line_height=2.7,
            max_lines=1,
        )
        cursor_y += 3
    pdf.set_text_color(30, 30, 30)


def _draw_reference_cards(pdf: FPDF, monsters: list[MonsterInstance], y: float) -> None:
    if not monsters:
        return
    if y > 214:
        pdf.add_page()
        y = MARGIN
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_xy(MARGIN, y)
    pdf.cell(PAGE_WIDTH - (MARGIN * 2), 4, "Reference Cards")
    y += 6

    columns = 4
    gap = 2.0
    card_width = (PAGE_WIDTH - (MARGIN * 2) - (gap * (columns - 1))) / columns
    card_height = 58
    x_positions = [MARGIN + (index * (card_width + gap)) for index in range(columns)]
    column = 0
    for monster in monsters:
        if y + card_height > PAGE_HEIGHT - MARGIN:
            pdf.add_page()
            y = MARGIN
            column = 0
        _draw_reference_card(pdf, monster, x_positions[column], y, card_width, card_height)
        column += 1
        if column >= columns:
            column = 0
            y += card_height + 5


def export_combat_sheet_pdf(
    monsters: Iterable[MonsterInstance],
    difficulty: dict[str, str],
    path: str | Path,
    encounter_name: str = "Encounter Sheet",
    available_conditions: Iterable[str] | None = None,
) -> Path:
    """Write a portrait PDF worksheet and return the final path."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    monster_list = list(monsters)
    _ = available_conditions

    pdf = FPDF(orientation="P", unit="mm", format="Letter")
    pdf.set_auto_page_break(False)
    pdf.set_compression(False)

    y = 48.0
    pdf.add_page()
    _draw_header(pdf, encounter_name, difficulty)
    y = _draw_monster_table_header(pdf, y)

    for monster in [*monster_list, *([None] * 4)]:
        if y > 221:
            pdf.add_page()
            _draw_header(pdf, encounter_name, difficulty)
            y = _draw_monster_table_header(pdf, 48.0)
        y = _draw_monster_table_row(pdf, monster, y)

    _draw_reference_cards(pdf, _unique_monsters(monster_list), y + 5)

    pdf.output(target)
    return target
