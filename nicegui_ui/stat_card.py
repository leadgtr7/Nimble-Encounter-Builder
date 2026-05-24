"""GMG-inspired monster stat card rendering for the NiceGUI UI."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from html import escape
from typing import Any, Iterable


def _as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    try:
        return dict(vars(value))
    except Exception:
        return {}


def _get(data: dict[str, Any], *keys: str, default: Any = "") -> Any:
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return default


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, Iterable):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]


def _format_action_items(items: list[str]) -> str:
    if not items:
        return "<p class=\"stat-card-empty-line\">No entries.</p>"

    lines = []
    paired = (
        len(items) >= 2
        and len(items) % 2 == 0
        and not any(":" in items[index] for index in range(0, len(items), 2))
    )
    if paired:
        for index in range(0, len(items), 2):
            title = escape(items[index].strip().rstrip("."))
            detail = escape(items[index + 1].strip().rstrip("."))
            lines.append(f"<li><strong>{title}.</strong> {detail}</li>")
    else:
        for item in items:
            text = item.strip().rstrip(".")
            if ":" in text:
                title, detail = text.split(":", 1)
                lines.append(
                    f"<li><strong>{escape(title.strip())}.</strong> {escape(detail.strip())}</li>"
                )
            else:
                lines.append(f"<li><strong>{escape(text)}.</strong></li>")
    return "<ul>" + "".join(lines) + "</ul>"


def render_empty_stat_card() -> str:
    return """
    <article class="stat-card stat-card-empty">
      <div class="stat-card-name">Select a monster</div>
      <p class="stat-card-flavor">The reference card will appear here.</p>
    </article>
    """


def render_monster_stat_card(monster: Any) -> str:
    data = _as_mapping(monster)
    name = escape(str(_get(data, "name", default="Unknown Monster")))
    level = str(_get(data, "level", default="-"))
    size = str(_get(data, "size", default="-") or "-")
    monster_type = str(_get(data, "type", default="")).strip()
    biome = str(_get(data, "biome", default="")).strip()
    armor = escape(str(_get(data, "armor", default="-") or "-"))
    speed = escape(str(_get(data, "speed", default="-") or "-"))
    saves = escape(str(_get(data, "saves", default="-") or "-"))
    flavor = escape(str(_get(data, "flavor", "description", default="")).strip())

    hp_current = _get(data, "hp_current", default=None)
    hp_max = _get(data, "hp_max", "max_hp", "hp", default="-")
    temp_hp = _get(data, "temp_hp", default=0)
    hp_label = escape(f"{hp_current}/{hp_max}" if hp_current is not None else str(hp_max))
    temp_label = f" +{temp_hp} temp" if temp_hp else ""

    passives = _as_list(_get(data, "passives", "passive", default=[]))
    specials = _as_list(_get(data, "special_actions", default=[]))
    actions = _as_list(_get(data, "actions", default=[]))
    bloodied = escape(str(_get(data, "bloodied_text", "bloodied", default="")).strip())
    last_stand = escape(str(_get(data, "last_stand_text", "last_stand", default="")).strip())
    last_stand_hp = escape(str(_get(data, "last_stand_hp_value", "last_stand_hp", default="")).strip())
    legendary = bool(_get(data, "legendary", default=False))

    meta_bits = [f"Lvl {level}", size]
    if monster_type:
        meta_bits.append(monster_type)
    if biome:
        meta_bits.append(biome)
    meta = escape(", ".join(bit for bit in meta_bits if bit))

    legendary_class = " stat-card-legendary" if legendary else ""
    legendary_tag = "<span class=\"stat-card-tag\">Legendary</span>" if legendary else ""
    last_stand_tail = f" <span>(HP {last_stand_hp})</span>" if last_stand_hp and last_stand_hp != "0" else ""

    return f"""
    <article class="stat-card{legendary_class}">
      <header class="stat-card-header">
        <div>
          <div class="stat-card-name">{name}</div>
          <div class="stat-card-meta">{meta}</div>
        </div>
        <div class="stat-card-hp">HP {hp_label}{escape(temp_label)}</div>
      </header>
      {legendary_tag}
      <p class="stat-card-flavor">{flavor}</p>
      <div class="stat-card-strip">
        <span><b>Armor</b> {armor}</span>
        <span><b>Speed</b> {speed}</span>
        <span><b>Saves</b> {saves}</span>
      </div>
      <section>
        <h3>Passives</h3>
        {_format_action_items(passives)}
      </section>
      <section>
        <h3>Special Actions</h3>
        {_format_action_items(specials)}
      </section>
      <section>
        <h3>Actions</h3>
        {_format_action_items(actions)}
      </section>
      <section class="stat-card-callouts">
        {f'<p><b>Bloodied.</b> {bloodied}</p>' if bloodied else ''}
        {f'<p><b>Last Stand.</b> {last_stand}{last_stand_tail}</p>' if last_stand else ''}
      </section>
    </article>
    """
