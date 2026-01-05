# Privacy & Personal Data Cleanup

This document explains what to exclude when sharing the project and how to keep
personal vault paths and session data out of the repo.

## What To Exclude

### Build Artifacts
```
build/                      (entire folder)
dist/                       (entire folder)
Build App/*.spec            (spec files can embed absolute paths)
*.exe
```

### App State / Cache
```
autosave_session.json       (session state)
config_location.json        (local pointer to vault config)
config.json                 (if it contains personal paths)
```

### Vault/Data Folders
```
Combat Logs/
Heroes/
Encounters/
data/
```

### Python Cache
```
__pycache__/
*.pyc
*.pyo
```

## Safe to Share

- `modules/*.py`, `tabs/*.py`, `NimbleEncounterBuilder.py`
- `uiDesign/*.ui`
- `Build App/*` build scripts
- Documentation files

## Recommended .gitignore

```gitignore
# Build artifacts
build/
dist/
Build App/*.spec
*.exe

# Python cache
__pycache__/
*.pyc
*.pyo

# Session data / caches
autosave_session.json
config_location.json

# Local config with personal paths
config.json

# Vault data folders
Combat Logs/
Heroes/
Encounters/
data/
```

## Verification

Before pushing, scan for personal paths:

```bash
# Search for usernames or absolute paths
rg -n "C:/" .
rg -n "Users" .
```

If any matches are found, review and clean them manually.

