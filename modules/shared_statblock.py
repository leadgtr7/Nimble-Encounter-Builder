"""
shared_statblock.py
=======================================================================
Purpose:
  Render Nimble monster data (dicts or combatant dataclasses) into a
  compact HTML stat block for preview panes across UIs and tools.

Key inputs:
  - Dicts from legacy JSON exports.
  - combatants.MonsterTemplate (library entries).
  - combatants.MonsterInstance (live encounter copies).

Key outputs:
  - HTML string suitable for QTextEdit / web previews.
  - Supports mode="lite" (default) or mode="full" for truncation control.
=======================================================================
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from html import escape
from typing import Any, Dict, Iterable, List


def _as_mapping(meta: Any) -> Dict[str, Any]:
    """Normalize meta into a dict, handling dataclasses and objects with attributes."""
    if isinstance(meta, dict):
        return meta
    # Only call asdict on dataclass instances (not classes)
    if is_dataclass(meta) and not isinstance(meta, type):
        return asdict(meta)
    try:
        return dict(vars(meta))
    except Exception:
        return {"value": meta}


def _get(meta: Dict[str, Any], *keys: str, default: Any = "") -> Any:
    for k in keys:
        if k in meta and meta[k] is not None:
            return meta[k]
    return default


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        # Keep a single string as a single list entry (don't split characters).
        return [value]
    if isinstance(value, Iterable):
        return [str(v) for v in value]
    return [str(value)]


def _strip_title_period(text: str) -> str:
    return text.strip().rstrip(".").strip()


def _html_text(text: Any) -> str:
    return escape(str(text).strip()).replace("\n", "<br>")


def _fmt_actions(title: str, glyph: str, items: List[str], limit: int | None = None) -> List[str]:
    """Format action lists with indentation; supports paired title/detail lists."""
    if not items:
        return []

    items = list(items)

    # Detect paired format (title/detail alternating)
    paired = False
    if len(items) >= 2 and len(items) % 2 == 0:
        paired = True
        for index in range(0, len(items), 2):
            if isinstance(items[index], str) and ":" in items[index]:
                # Already has a title/detail marker; treat as single-line entries.
                paired = False
                break

    entries: List[str] = []
    if paired:
        for i in range(0, len(items), 2):
            title_part = _html_text(_strip_title_period(str(items[i])))
            detail_part = _html_text(items[i + 1]) if i + 1 < len(items) else ""
            line = f"{glyph} <b>{title_part}</b>"
            if detail_part:
                line += f" - {detail_part}"
            entries.append(line)
    else:
        for it in items:
            clean = str(it).strip()
            if ":" in clean:
                # Preserve explicit "Title: detail" formatting.
                entries.append(f"{glyph} {_html_text(clean)}")
            else:
                entries.append(f"{glyph} <b>{_html_text(_strip_title_period(clean))}</b>")

    truncated = False
    if limit is not None and len(entries) > limit:
        # Truncate by rendered action entries, not by raw title/detail fragments.
        entries = entries[:limit]
        truncated = True

    lines: List[str] = [f"<span style='font-weight:bold;'>{escape(title)}</span>"]
    for entry in entries:
        # QTextEdit wraps normal block content reliably; inline-block spans clip long
        # abilities like Rime Tongue's Drag Beneath instead of wrapping them.
        lines.append(f"<div style='margin-left:16px;'>{entry}</div>")

    if truncated:
        # Visual continuation indicator for truncated action lists.
        lines.append("<div style='margin-left:16px;'>...</div>")

    return lines


def render_stat_block(meta: Dict | Any, mode: str = "lite") -> str:
    """
    Render monster meta into an HTML stat block.

    mode: "lite" (default) shows header + short flavor and truncated actions/specials;
    "full" shows the entire action lists.
    """
    meta_map = _as_mapping(meta)
    # Default to full to avoid losing data if caller passes empty mode.
    mode = (mode or "full").lower()

    name = _get(meta_map, "name", default="Unknown")
    level = str(_get(meta_map, "level", default="")).strip()

    # HP display prefers max values; fall back to raw hp field for legacy data.
    hp_val = _get(meta_map, "hp_max", "max_hp", "hp", default="")
    try:
        hp_display = str(int(hp_val))
    except Exception:
        hp_display = str(hp_val).strip()

    size = _get(meta_map, "size", default="-") or "-"
    armor = _get(meta_map, "armor", default="-") or "-"
    speed = _get(meta_map, "speed", default="-") or "-"
    saves = _get(meta_map, "saves", default="-") or "-"
    flavor = _get(meta_map, "flavor", "description", default="")
    mtype = _get(meta_map, "type", default="")
    biome = _get(meta_map, "biome", default="")

    passives = _as_list(_get(meta_map, "passives", "passive", default=[]))
    specials = _as_list(_get(meta_map, "special_actions", default=[]))
    actions = _as_list(_get(meta_map, "actions", default=[]))

    bloodied = _get(meta_map, "bloodied_text", "bloodied", default="")
    last_stand = _get(meta_map, "last_stand_text", "last_stand", default="")
    # Check both MonsterInstance.last_stand_hp_value (int) and MonsterTemplate.last_stand_hp (str)
    last_stand_hp = _get(meta_map, "last_stand_hp_value", "last_stand_hp", default="")

    # Title/header line collects common fields in a compact summary.
    lines: List[str] = [f"<span style='font-size:18px; font-weight:bold;'>{_html_text(name)}</span>"]
    header_bits = []
    if level:
        header_bits.append(f"<b>Level:</b> {_html_text(level)}")
    if hp_display:
        header_bits.append(f"<b>HP:</b> {_html_text(hp_display)}")
    if mtype:
        header_bits.append(f"<b>Type:</b> {_html_text(mtype)}")
    if biome:
        header_bits.append(f"<b>Biome:</b> {_html_text(biome)}")
    header_bits.append(f"<b>Size:</b> {_html_text(size)}")
    header_bits.append(f"<b>Armor:</b> {_html_text(armor)}")
    header_bits.append(f"<b>Speed:</b> {_html_text(speed)}")
    header_bits.append(f"<b>Saves:</b> {_html_text(saves)}")
    lines.append(" | ".join(header_bits))

    if flavor:
        lines.append(f"<i>{_html_text(flavor)}</i>")
    lines.append("--------------------")

    limit = None
    if mode == "lite":
        limit = 2  # show just a taste of each

    lines.extend(_fmt_actions("Passives", "&bull;", passives, limit=limit))
    if passives:
        lines.append("--------------------")
    lines.extend(_fmt_actions("Special Actions", "&bull;", specials, limit=limit))
    if specials:
        lines.append("--------------------")
    lines.extend(_fmt_actions("Actions", "&bull;", actions, limit=limit))
    if actions:
        lines.append("--------------------")

    leg_lines: List[str] = []
    if bloodied:
        leg_lines.append(f"<div style='margin-left:16px;'>&bull; <b>Bloodied:</b> {_html_text(bloodied)}</div>")
    if last_stand:
        tail = f" (HP: {last_stand_hp})" if last_stand_hp else ""
        leg_lines.append(f"<div style='margin-left:16px;'>&bull; <b>Last Stand:</b> {_html_text(last_stand)}{_html_text(tail)}</div>")
    if leg_lines:
        lines.append("<span style='font-weight:bold;'>Legendary</span>")
        lines.extend(leg_lines)

    # Remove empty entries, then join with single breaks for separation
    lines = [ln for ln in lines if ln.strip()]
    html = "<br>".join(lines)
    while "<br><br>" in html:
        html = html.replace("<br><br>", "<br>")
    return html
