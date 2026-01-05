# Nimble Encounter Builder

## Note
This app was built with heavy use of AI tools. I won't pretend that I know exactly how everything works, but I do understand the structure. With that said, if you create a pull request I may struggle with reviewing and approving. Please be patient with me.

Nimble Encounter Builder is a fast, table-first combat tracker and encounter builder for TTRPGs. It focuses on quick in-session edits, clear status visibility, and light data management.

## Highlights
- Combat table with single-click heal/damage and double-click edits.
- Heroes management with party import/export.
- Bestiary-backed encounter building with difficulty readouts.
- Configurable HP thresholds, colors, markers, and autosave.
- Vault Viewer for scanning Obsidian-style vaults and exporting JSON bestiaries.
- Multi-folder Vault Viewer input and multi-file monster vault support.
- Always-dark UI for consistent appearance across system themes.

## Quick Start
1) Run the app:
```bash
python NimbleEncounterBuilder.py
```
2) On first run, choose a config location (vault JSON). If you skip, the app prompts for a base folder and creates `data/Encounters`, `data/Heroes`, and `data/Combat Logs`.
3) Open the Config tab to set paths and preferences.

## Build
The build output name is auto-versioned as:
`Nimble Encounter Builder vYYMMDDNN.exe`

Build from the repo root:
```bash
python "Build App/_ClickMeToBuild.py"
```

## Data Locations
- Config pointer: `config_location.json` (local pointer to your vault config file).
- Autosave: `autosave_session.json` (session state).
- Vault data: stored wherever you point the app (often in your Obsidian vault).

## Notes
- Monster vault path supports multiple JSON files. Use multi-select in the file picker or separate paths with `;`.
- Vault Viewer supports multiple input folders via the "Add Folder" button.

## Folder Structure
```
Nimble-Encounter-Builder/
  NimbleEncounterBuilder.py
  modules/
  tabs/
  uiDesign/
  Build App/
  README.html
  README.md
  INSTRUCTION_MANUAL.md
snapshots/
```

## License
Add your license here.
