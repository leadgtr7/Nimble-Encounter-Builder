# Release Checklist

## Preflight
- Update version tag used in build output (auto: vYYMMDDNN).
- Review `PRIVACY_CLEANUP.md` exclusions.
- Ensure vault paths are not committed.

## Build
- Run: `python "EncounterBuilder/Build App/_ClickMeToBuild.py"`
- Confirm output exe name: `Nimble Encounter Builder vYYMMDDNN.exe`

## Smoke Test
- Launch the exe from `dist/`.
- Verify:
  - Combat tab: click heal/hurt works.
  - Heroes tab: add/edit hero works.
  - Bestiary: load JSON and add monster.
  - Vault Viewer: scan folder(s) and export JSON.
  - Config: save/load works.

## Packaging
- Bundle exe and any optional folders you want to distribute.
- Include:
  - `README.html`
  - `INSTRUCTION_MANUAL.md`

## Publish
- Create a release note with date and build tag.
- Attach the exe and docs.
