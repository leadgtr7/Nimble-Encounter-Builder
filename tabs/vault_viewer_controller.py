"""
vault_viewer_controller.py
======================================================================
Controller for the Vault Viewer tab - scans Obsidian vault for monsters
and displays them in the Config tab.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QWidget,
)

from modules.shared_statblock import render_stat_block

DEFAULT_VAULT = Path(r"C:\TTRPG_Vault\Nimble Vault\Foes")


class VaultViewerController:
    """Controller for the Vault Viewer tab in Config."""

    def __init__(
        self,
        parent_widget: QWidget,
        vault_edit: Optional[QLineEdit] = None,
        btn_browse_vault: Optional[QPushButton] = None,
        btn_add_vault: Optional[QPushButton] = None,
        btn_scan_vault: Optional[QPushButton] = None,
        btn_export_bestiary: Optional[QPushButton] = None,
        file_list: Optional[QListWidget] = None,
        biome_list: Optional[QListWidget] = None,
        legend_list: Optional[QListWidget] = None,
        debug_view: Optional[QTextEdit] = None,
        raw_view: Optional[QTextEdit] = None,
        stat_block_view: Optional[QTextEdit] = None,
        json_meta_view: Optional[QTextEdit] = None,
        json_raw_view: Optional[QTextEdit] = None,
        log_fn: Optional[Callable[[str], None]] = None,
        on_vault_scanned: Optional[Callable[[Path], None]] = None,
    ):
        self.parent_widget = parent_widget
        self.vault_edit = vault_edit
        self.btn_browse_vault = btn_browse_vault
        self.btn_add_vault = btn_add_vault
        self.btn_scan_vault = btn_scan_vault
        self.btn_export_bestiary = btn_export_bestiary
        self.file_list = file_list
        self.biome_list = biome_list
        self.legend_list = legend_list
        self.debug_view = debug_view
        self.raw_view = raw_view
        self.stat_block_view = stat_block_view
        self.json_meta_view = json_meta_view
        self.json_raw_view = json_raw_view
        self.log_fn = log_fn or print
        self.on_vault_scanned = on_vault_scanned

        # Data storage
        self.vault_path = DEFAULT_VAULT
        self.monsters: List[Dict] = []
        self.last_data: Optional[Dict] = None
        self.file_meta: List[Tuple[Path, Dict]] = []
        self.biome_meta: List[Tuple[Path, Dict]] = []
        self.legend_meta: List[Tuple[Path, Dict]] = []

        self._wire_signals()
        self._load_vault_path_from_config()

    def _wire_signals(self) -> None:
        """Connect button and list widget signals."""
        if self.btn_browse_vault:
            self.btn_browse_vault.clicked.connect(self._browse_vault)
        if self.btn_add_vault:
            self.btn_add_vault.clicked.connect(self._add_vault_folder)
        if self.btn_scan_vault:
            self.btn_scan_vault.clicked.connect(self._scan_vault_and_load)
        if self.btn_export_bestiary:
            self.btn_export_bestiary.clicked.connect(self._export_bestiary)
        if self.file_list:
            self.file_list.currentItemChanged.connect(self._on_file_selected)
        if self.biome_list:
            self.biome_list.currentItemChanged.connect(self._on_file_selected)
        if self.legend_list:
            self.legend_list.currentItemChanged.connect(self._on_file_selected)

    def _load_vault_path_from_config(self) -> None:
        """Load vault path from config if available."""
        try:
            from modules import config

            vault_path_str = getattr(config.CONFIG, "vault_path", None)
            if vault_path_str:
                self.vault_path = Path(vault_path_str)
                if self.vault_edit:
                    self.vault_edit.setText(str(self.vault_path))
        except Exception:
            pass

    def _browse_vault(self) -> None:
        """Open folder dialog to select one or more vault roots."""
        dialog = QFileDialog(self.parent_widget, "Select vault root(s)", str(self.vault_path))
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        if not dialog.exec():
            return
        folders = dialog.selectedFiles()
        if not folders:
            return
        # The first folder is used as the default root; all folders are stored in the UI.
        self.vault_path = Path(folders[0])
        if self.vault_edit:
            self.vault_edit.setText(";".join(folders))

    def _add_vault_folder(self) -> None:
        """Add a vault folder to the existing list."""
        folder = QFileDialog.getExistingDirectory(
            self.parent_widget, "Add vault folder", str(self.vault_path)
        )
        if not folder:
            return
        parts = []
        if self.vault_edit:
            existing = self.vault_edit.text().strip()
            if existing:
                for token in existing.replace("\n", ";").split(";"):
                    token = token.strip()
                    if token:
                        parts.append(token)
        if folder not in parts:
            parts.append(folder)
        if self.vault_edit:
            # Store as a single semicolon-delimited string for config compatibility.
            self.vault_edit.setText(";".join(parts))
        self.vault_path = Path(parts[0]) if parts else Path(folder)

    def _scan_vault_and_load(self) -> None:
        """Scan the vault and populate monster lists."""
        vaults = self._parse_vault_paths()
        if not vaults:
            QMessageBox.warning(
                self.parent_widget, "Vault Missing", "No valid vault folders found."
            )
            return

        all_monsters: List[Dict] = []
        all_legendary: List[Dict] = []
        all_loot: Dict[str, List[str]] = {}
        all_debug: List[str] = []
        all_file_meta: List[Tuple[Path, Dict]] = []
        all_biome_meta: List[Tuple[Path, Dict]] = []

        for vault in vaults:
            # Merge multiple vault roots into a single combined dataset.
            data, debug_lines, file_meta, biome_file_meta = self._collect_vault(vault)
            all_monsters.extend(data.get("monsters", []))
            all_legendary.extend(data.get("legendary_monsters", []))
            for biome, loot in data.get("loot_by_biome", {}).items():
                all_loot.setdefault(biome, []).extend(loot)
            all_debug.extend([f"[vault] {vault}"] + debug_lines)
            all_file_meta.extend(file_meta)
            all_biome_meta.extend(biome_file_meta)

        self.last_data = {
            "monsters": all_monsters,
            "legendary_monsters": all_legendary,
            "loot_by_biome": all_loot,
        }
        self.monsters = all_monsters
        self.file_meta = all_file_meta
        self.biome_meta = all_biome_meta
        self.legend_meta = [(p, m) for p, m in all_file_meta if m.get("legendary")]

        if self.debug_view:
            self.debug_view.setPlainText("\n".join(all_debug))

        self._populate_file_list()
        self._populate_biome_list()
        self._populate_legend_list()

        self.log_fn(f"Scanned vaults: {len(self.monsters)} monsters, {len(self.legend_meta)} legendary")

        # Trigger callback to reload monster library
        if self.on_vault_scanned:
            self.on_vault_scanned(vaults[0])

    def _parse_vault_paths(self) -> List[Path]:
        if self.vault_edit:
            vault_text = self.vault_edit.text().strip()
            if vault_text:
                raw_parts = []
                for token in vault_text.replace("\n", ";").split(";"):
                    token = token.strip()
                    if token:
                        raw_parts.append(token)
                vaults = [Path(p) for p in raw_parts]
            else:
                vaults = [self.vault_path]
        else:
            vaults = [self.vault_path]

        # Filter out missing paths to reduce noisy parse errors later.
        valid = [v for v in vaults if v.exists()]
        return valid

    def _populate_file_list(self) -> None:
        """Populate the Monsters list widget."""
        if not self.file_list:
            return
        self.file_list.clear()
        for path, meta in self.file_meta:
            if meta.get("legendary"):
                continue  # keep legendary out of Monsters tab
            item = QListWidgetItem(path.name)
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            self.file_list.addItem(item)

    def _populate_biome_list(self) -> None:
        """Populate the Biomes list widget."""
        if not self.biome_list:
            return
        self.biome_list.clear()
        for path, meta in self.biome_meta:
            item = QListWidgetItem(path.name)
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            self.biome_list.addItem(item)

    def _populate_legend_list(self) -> None:
        """Populate the Legendary list widget."""
        if not self.legend_list:
            return
        self.legend_list.clear()
        for path, meta in self.legend_meta:
            item = QListWidgetItem(path.name)
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            self.legend_list.addItem(item)

    def _on_file_selected(self, current: QListWidgetItem, _prev: QListWidgetItem) -> None:
        """Handle file selection from any of the list widgets."""
        if not current:
            if self.json_meta_view:
                self.json_meta_view.clear()
            if self.raw_view:
                self.raw_view.clear()
            if self.stat_block_view:
                self.stat_block_view.clear()
            if self.json_raw_view:
                self.json_raw_view.clear()
            return

        path_str = current.data(Qt.ItemDataRole.UserRole)
        if not path_str:
            return

        # Use the underlying file path as the source-of-truth for views.
        p = Path(path_str)
        try:
            raw_text = p.read_text(encoding="utf-8")
        except Exception as exc:
            raw_text = f"[Error reading file]\n{exc}"

        if self.raw_view:
            self.raw_view.setPlainText(raw_text)

        # Determine which list widget contains the current item by checking all lists
        source_meta = self.file_meta  # default to file_meta

        # Check which list contains this item
        if self.biome_list:
            for i in range(self.biome_list.count()):
                if self.biome_list.item(i) is current:
                    source_meta = self.biome_meta
                    break

        if self.legend_list and source_meta is self.file_meta:  # only check if not already found
            for i in range(self.legend_list.count()):
                if self.legend_list.item(i) is current:
                    source_meta = self.legend_meta
                    break

        meta = next((m for path, m in source_meta if str(path) == path_str), None)
        if meta:
            if self.json_meta_view:
                self.json_meta_view.setHtml(self._render_meta_json(meta))
            if self.json_raw_view:
                try:
                    self.json_raw_view.setPlainText(json.dumps(meta, indent=2))
                except Exception:
                    self.json_raw_view.setPlainText(str(meta))
            if self.stat_block_view:
                self.stat_block_view.setHtml(render_stat_block(meta))
        else:
            if self.json_meta_view:
                self.json_meta_view.clear()
            if self.json_raw_view:
                self.json_raw_view.clear()
            if self.stat_block_view:
                self.stat_block_view.clear()

    def _render_meta_json(self, meta: dict) -> str:
        """HTML render of meta with bold keys for quick inspection."""

        def fmt_list(label: str, items: list) -> str:
            if not items:
                return ""
            lines = [f"<b>{label}</b>"]
            for it in items:
                lines.append(f"&nbsp;&nbsp;• {it}")
            return "<br>".join(lines)

        parts = [
            f"<b>name</b>: {meta.get('name','')}",
            f"<b>type</b>: {meta.get('type','')}",
            f"<b>biome</b>: {meta.get('biome','')}",
            f"<b>file</b>: {meta.get('file','')}",
            f"<b>legendary</b>: {meta.get('legendary', False)}",
            f"<b>level</b>: {meta.get('level','')}",
            f"<b>hp</b>: {meta.get('hp','')}",
            f"<b>armor</b>: {meta.get('armor','')}",
            f"<b>speed</b>: {meta.get('speed','')}",
            f"<b>size</b>: {meta.get('size','')}",
            f"<b>saves</b>: {meta.get('saves','')}",
        ]
        flavor = meta.get("flavor", "")
        if flavor:
            parts.append(f"<b>flavor</b>: {flavor}")
        specials = meta.get("special_actions", []) or []
        actions = meta.get("actions", []) or []
        bloodied = meta.get("bloodied", "")
        last_stand = meta.get("last_stand", "")
        last_stand_hp = meta.get("last_stand_hp", "")
        loot = meta.get("biome_loot", [])

        for block in (
            fmt_list("special_actions", specials),
            fmt_list("actions", actions),
            fmt_list("biome_loot", loot),
        ):
            if block:
                parts.append(block)
        if bloodied:
            parts.append(f"<b>bloodied</b>: {bloodied}")
        if last_stand:
            parts.append(f"<b>last_stand</b>: {last_stand}")
        if last_stand_hp:
            parts.append(f"<b>last_stand_hp</b>: {last_stand_hp}")

        return "<br>".join(parts)

    def _export_bestiary(self) -> None:
        """Export the current monster data to a JSON file."""
        if not self.last_data:
            QMessageBox.warning(
                self.parent_widget, "No Data", "Please scan a vault first before exporting."
            )
            return

        # Create default directory and filename
        out_dir = Path("Bestiary")
        try:
            from modules import config

            configured = (config.CONFIG.default_monster_vault_path or "").strip()
            if configured:
                first_path = configured.replace("\n", ";").split(";")[0].strip()
                if first_path:
                    out_dir = Path(first_path).parent
        except Exception:
            pass
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = out_dir / f"bestiary_{ts}.json"

        # Ask user where to save
        path, _ = QFileDialog.getSaveFileName(
            self.parent_widget,
            "Export Bestiary",
            str(default_filename),
            "JSON Files (*.json);;All Files (*)",
        )

        if not path:
            return  # User cancelled

        out_path = Path(path)
        try:
            out_path.write_text(json.dumps(self.last_data, indent=2), encoding="utf-8")
        except Exception as exc:
            QMessageBox.critical(
                self.parent_widget, "Export Failed", f"Could not write file:\n{exc}"
            )
            return
        QMessageBox.information(
            self.parent_widget, "Export Complete", f"Wrote {out_path}"
        )
        self.log_fn(f"Exported bestiary to {out_path}")

    # ------------------------------------------------------------------
    # Vault parsing methods (ported from json_viewer_methods.py)
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_text(text: str) -> str:
        return " ".join(text.replace("\u00a0", " ").split()).strip()

    @staticmethod
    def _strip_danger_tag(text: str) -> str:
        """Remove Obsidian callout tag [!danger] from a line."""
        return re.sub(r"\[!danger\]\s*", "", text, flags=re.IGNORECASE)

    @staticmethod
    def _strip_markdown(text: str) -> str:
        """Remove basic markdown emphasis markers."""
        t = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
        t = re.sub(r"__(.*?)__", r"\1", t)
        t = re.sub(r"\*(.*?)\*", r"\1", t)
        t = re.sub(r"_(.*?)_", r"\1", t)
        t = re.sub(r"`(.*?)`", r"\1", t)
        return t.strip()

    @staticmethod
    def _split_action_line(text: str) -> List[str]:
        """
        If an action line uses a bolded title (**Title.**) followed by details,
        return two strings: title, detail. Otherwise return [text].
        """
        m = re.match(r"\*\*(.+?)\*\*\.?\s*(.*)", text)
        if m:
            title = VaultViewerController._strip_markdown(m.group(1).strip())
            rest = VaultViewerController._strip_markdown(m.group(2).strip())
            return [title, rest] if rest else [title]
        return [text]

    def _parse_biome_summary(self, path: Path) -> Tuple[Dict[str, List[str]], str, List[str]]:
        """Parse biome-level markdown (folder file) for shared actions, flavor, loot."""
        actions_by_name: Dict[str, List[str]] = {}
        flavor_lines: List[str] = []
        loot_items: List[str] = []

        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception:
            return actions_by_name, "", loot_items

        current_actions: List[str] = []
        pending_refs: List[str] = []
        seen_header = False
        in_loot = False
        global_actions: List[str] = []
        all_refs: set[str] = set()
        in_monsters_section = False

        def apply_actions():
            if not current_actions or not pending_refs:
                return
            for ref in pending_refs:
                actions_by_name.setdefault(ref.lower(), []).extend(current_actions)
                all_refs.add(ref.lower())

        for raw in lines:
            stripped = raw.strip()
            if not seen_header and stripped and not stripped.startswith(("#", ">", "![[", "---")):
                flavor_lines.append(stripped)
                continue
            if stripped.startswith("#"):
                is_monsters_header = stripped.strip().lower().startswith("# monsters")
                in_loot = "loot" in stripped.lower()
                if is_monsters_header and current_actions:
                    global_actions.extend(current_actions)
                apply_actions()
                pending_refs = []
                current_actions = []
                seen_header = True
                in_monsters_section = is_monsters_header
                continue
            if in_loot:
                if stripped:
                    loot_items.append(stripped)
                continue
            if stripped.startswith(">"):
                action = self._strip_markdown(self._clean_text(self._strip_danger_tag(stripped.lstrip(">").strip())))
                if in_monsters_section:
                    global_actions.append(action)
                else:
                    current_actions.append(action)
                continue
            if "[!danger]" in stripped.lower():
                action = self._strip_markdown(self._clean_text(self._strip_danger_tag(stripped)))
                if action:
                    if in_monsters_section:
                        global_actions.append(action)
                    else:
                        current_actions.append(action)
                continue
            if stripped.startswith("![[") and stripped.endswith("]]"):
                name = stripped[3:-2].strip()
                if name.lower().endswith(".md"):
                    name = name[:-3]
                elif name.lower().endswith(".markdown"):
                    name = name[: -len(".markdown")]
                name = name.strip()
                if name:
                    pending_refs.append(name)
                    all_refs.add(name.lower())
                continue

        apply_actions()
        flavor = self._strip_markdown(self._clean_text(" ".join(flavor_lines)))
        if global_actions:
            actions_by_name["__all__"] = global_actions
        return actions_by_name, flavor, loot_items

    def _parse_monster_file(
        self,
        path: Path,
        biome_actions: Dict[str, List[str]],
        biome_flavor: str,
        biome_loot: List[str],
        legendary_hint: bool = False,
    ) -> Dict:
        """Parse a single monster markdown file."""
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            return {}

        parent_lower = path.parent.name.lower()
        legendary = legendary_hint or parent_lower in {
            "legendary",
            "legendary monsters",
            "legendary-monsters",
            "legendary_monsters",
        }

        lines = content.splitlines()
        name = path.stem

        def find_first(pattern: str) -> str:
            rx = re.compile(pattern, re.IGNORECASE)
            for l in lines:
                m = rx.search(l)
                if m:
                    return m.group(1).strip()
                l_clean = re.sub(r"[*_`]+", "", l)
                m2 = rx.search(l_clean)
                if m2:
                    return m2.group(1).strip()
            return ""

        if legendary:
            level = find_first(r"Level\s*:?\s*([0-9]+(?:\/[0-9]+)?(?:\.\d+)?)")
        else:
            level = find_first(r"Level\s*:\s*([0-9]+(?:\/[0-9]+)?(?:\.\d+)?)")
        hp = find_first(r"HP[:\s\*]*([0-9]+)")
        armor = find_first(r"Armor[:\s\*]*([A-Za-z0-9\+\- ]+)")
        speed = find_first(r"Speed[:\s\*]*([A-Za-z0-9\+\- ]+)")
        saves = find_first(r"Saves[:\s\*]*([A-Za-z0-9\+\- ,]+)")
        size = find_first(r"Size[:\s\*]*([A-Za-z0-9\+\- ]+)")

        flavor = ""

        special_actions: List[str] = []
        for l in lines:
            ls = l.strip()
            if ls.startswith(">"):
                text = self._clean_text(self._strip_danger_tag(ls.lstrip(">").strip()))
                if text:
                    special_actions.append(text)

        actions: List[str] = []
        in_actions = False
        for l in lines:
            ls = l.strip()
            if ls.upper().startswith("**ACTIONS"):
                in_actions = True
                continue
            if in_actions and ls.startswith(("* ", "- ")):
                actions.append(self._clean_text(ls[2:]))
            elif in_actions and not ls:
                continue

        if not actions:
            actions = [self._clean_text(l[2:]) for l in lines if l.strip().startswith(("* ", "- "))]

        bloodied = ""
        last_stand = ""
        last_stand_hp = ""
        for l in lines:
            ls = l.strip()
            if ls.lower().startswith("**bloodied") or ls.lower().startswith("bloodied"):
                bloodied = self._clean_text(ls.split(":", 1)[1] if ":" in ls else ls)
            if ls.lower().startswith("**last stand") or ls.lower().startswith("last stand"):
                payload = ls.split(":", 1)[1] if ":" in ls else ls
                last_stand = self._clean_text(payload)
                # Try multiple patterns to capture the HP value
                # Pattern 1: Bold number like "**160** more damage"
                hp_match = re.search(r"\*\*(\d+)\*\*\s+more\s+damage", ls, re.IGNORECASE)
                if not hp_match:
                    # Pattern 2: Regular number like "160 more damage"
                    hp_match = re.search(r"(\d+)\s+more\s+damage", ls, re.IGNORECASE)
                if not hp_match:
                    # Pattern 3: Just any number before "damage"
                    hp_match = re.search(r"\*\*(\d+)\*\*\s+damage", ls, re.IGNORECASE)
                if not hp_match:
                    hp_match = re.search(r"(\d+)\s+damage", ls, re.IGNORECASE)
                if not hp_match:
                    # Pattern 4: Any bold number in the last stand text
                    hp_match = re.search(r"\*\*(\d+)\*\*", ls)
                if not hp_match:
                    # Pattern 5: Any standalone number in the last stand text
                    hp_match = re.search(r"(\d+)", ls)
                if hp_match:
                    last_stand_hp = hp_match.group(1)

        specials_from_biome = biome_actions.get(name.lower(), [])
        if specials_from_biome:
            special_actions.extend(specials_from_biome)

        special_actions = [self._strip_markdown(a) for a in special_actions]
        flat_actions: List[str] = []
        for a in actions:
            flat_actions.extend(self._split_action_line(a))
        actions = [self._strip_markdown(a) for a in flat_actions]
        bloodied = self._strip_markdown(bloodied)
        last_stand = self._strip_markdown(last_stand)
        flavor = self._strip_markdown(flavor) if flavor else ""
        size = self._strip_markdown(size)
        armor = self._strip_markdown(armor)
        speed = self._strip_markdown(speed)
        saves = self._strip_markdown(saves)

        return {
            "name": name,
            "file": str(path),
            "legendary": legendary,
            "level": level,
            "hp": hp,
            "armor": armor,
            "speed": speed,
            "size": size,
            "saves": saves,
            "flavor": biome_flavor or flavor,
            "actions": actions,
            "special_actions": special_actions,
            "bloodied": bloodied,
            "last_stand": last_stand,
            "last_stand_hp": last_stand_hp,
            "biome_loot": biome_loot,
        }

    def _collect_vault(self, vault_root: Path) -> Tuple[Dict, List[str], List[Tuple[Path, Dict]], List[Tuple[Path, Dict]]]:
        """Walk vault, return data dict plus debug log and per-file metadata."""
        monsters: List[Dict] = []
        legendary_monsters: List[Dict] = []
        loot_by_biome: Dict[str, List[str]] = {}
        debug_lines: List[str] = []
        file_meta: List[Tuple[Path, Dict]] = []
        biome_file_meta: List[Tuple[Path, Dict]] = []

        for type_dir in sorted([p for p in vault_root.iterdir() if p.is_dir()]):
            is_legend_type = type_dir.name.lower() in {
                "legendary",
                "legendary monsters",
                "legendary-monsters",
                "legendary_monsters",
            }
            if is_legend_type:
                for md in sorted(type_dir.glob("*.md")):
                    meta = self._parse_monster_file(md, {}, "", [], legendary_hint=True)
                    if not meta:
                        debug_lines.append(f"[skip] {md} (empty parse)")
                        continue
                    meta["type"] = type_dir.name
                    meta["biome"] = ""
                    legendary_monsters.append(meta)
                    file_meta.append((md, meta))
                    debug_lines.append(
                        f"[legendary] {md} specials={len(meta.get('special_actions', []))} actions={len(meta.get('actions', []))}"
                    )

            for biome_dir in sorted([p for p in type_dir.iterdir() if p.is_dir()]):
                biome_name = biome_dir.name
                biome_file = biome_dir / f"{biome_name}.md"
                biome_actions: Dict[str, List[str]] = {}
                biome_flavor = ""
                biome_loot: List[str] = []
                if biome_file.exists():
                    biome_actions, biome_flavor, biome_loot = self._parse_biome_summary(biome_file)
                    if biome_loot:
                        loot_by_biome[biome_name] = biome_loot
                    debug_lines.append(
                        f"[biome] {biome_file} actions={len(biome_actions)} flavor={'yes' if biome_flavor else 'no'} loot={len(biome_loot)}"
                    )
                    biome_file_meta.append(
                        (
                            biome_file,
                            {
                                "type": type_dir.name,
                                "biome": biome_name,
                                "file": str(biome_file),
                                "flavor": biome_flavor,
                                "loot": biome_loot,
                                "shared_actions": biome_actions,
                            },
                        )
                    )

                for md in sorted(biome_dir.glob("*.md")):
                    if md.name.lower() == f"{biome_name.lower()}.md":
                        continue
                    meta = self._parse_monster_file(
                        md, biome_actions, biome_flavor, biome_loot, legendary_hint=is_legend_type
                    )
                    if not meta:
                        debug_lines.append(f"[skip] {md} (empty parse)")
                        continue
                    meta["type"] = type_dir.name
                    meta["biome"] = biome_name
                    if "__all__" in biome_actions:
                        merged = list(meta.get("special_actions", [])) + list(
                            biome_actions.get("__all__", [])
                        )
                        meta["special_actions"] = merged
                    if meta.get("legendary"):
                        legendary_monsters.append(meta)
                        file_meta.append((md, meta))
                        debug_lines.append(
                            f"[legendary] {md} specials={len(meta.get('special_actions', []))} actions={len(meta.get('actions', []))}"
                        )
                    else:
                        monsters.append(meta)
                        file_meta.append((md, meta))
                        debug_lines.append(
                            f"[monster] {md} specials={len(meta.get('special_actions', []))} actions={len(meta.get('actions', []))}"
                        )

        return (
            {
                "monsters": monsters,
                "legendary_monsters": legendary_monsters,
                "loot_by_biome": loot_by_biome,
            },
            debug_lines,
            file_meta,
            biome_file_meta,
        )
