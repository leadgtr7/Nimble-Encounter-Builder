# Instruction Manual - Nimble Encounter Builder


Nimble Encounter Builder is an independent product published under the Nimble 3rd Party Creator License. Nimble © Nimble Co.
This manual walks through setup and the main workflows.

## Getting Started
1) Launch:
```bash
python EncounterBuilder/NimbleEncounterBuilder.py
```
2) If prompted, choose a config file location (recommended: in your vault). If you skip, the app will create a `data/` folder with:
- `Encounters/`
- `Heroes/`
- `Combat Logs/`
3) Open the Config tab to adjust thresholds, colors, and paths.

## Combat Tab
- **Heal/Damage**: single-click the Heal (heart) or Hurt (swords) columns.
- **Edit Monster**: double-click a monster name.
- **Markers**: double-click the marker column.
- **Conditions**: double-click conditions to edit.
- **Difficulty**: shown in the left status label; updates automatically.
- **Loot**: defeated monsters show loot info in the bottom panel.

## Heroes Tab
- **Add/Edit**: double-click hero name to edit.
- **Conditions**: double-click conditions to edit.
- **Import/Export**: use party JSON files to save/load heroes.

## Bestiary Tab
- **Monster Vault**: load one or more JSON bestiary files.
- **Filters**: name, biome, level, legendary.
- **Add to Encounter**: select and add monsters to combat.
- **Random Encounter**: generate encounters based on filters.

## Vault Viewer (Config Tab)
- **Browse Vault**: pick a root folder or add multiple folders.
- **Add Folder**: append more vault roots; paths are stored separated by `;`.
- **Scan Vault**: parses markdown monsters and builds an internal bestiary list.
- **Export Bestiary**: writes a JSON bestiary to the configured bestiary folder (or `Bestiary/` if not set).

## Config Tab
- **HP Thresholds**: bloodied/critical values per hero/monster.
- **Marker Palette**: configure and manage marker colors.
- **Autosave**: enable/disable session autosave and set location.
- **Paths**: set vault, encounter, party, and combat log folders.

## Conditions
Conditions are shared across the app for heroes and monsters. Double-click the conditions column to edit. You can also add or remove condition types in Config.

## Keyboard Shortcuts
- **Double-click**: edit names, markers, or conditions.
- **Ctrl + click**: multi-select rows for bulk marker assignment.

## Troubleshooting
- **Bestiary not loading**: verify the JSON path(s) in Config; multiple files are separated by `;`.
- **Vault scan empty**: ensure your vault uses supported markdown format and folders are selected.
- **Build missing assets**: rebuild with `Build App/_ClickMeToBuild.py` to include UI and images.

## File Formats
- **Bestiary JSON**: list or `{ "monsters": [...] }`.
- **Encounter JSON**: `{ "name": "...", "monsters": [...] }`.
- **Party JSON**: `{ "name": "...", "heroes": [...] }`.

## Support
Use the in-app Help tab (README.html) for the full reference guide.
