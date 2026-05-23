# Architecture

Nimble Encounter Builder is still a PySide6 desktop app, but the core app now
has a small service and extension layer so new capabilities can be added without
rewiring every tab controller.

## Current Layers

- `modules/combatants.py`: domain models and low-level HP/status behavior.
- `modules/combatManager.py`: session state and app use cases used by the UI.
- `modules/persistence.py`: JSON file format helpers.
- `modules/services.py`: app-wide service container and default JSON storage.
- `modules/extensions.py`: plugin contracts and plugin discovery.
- `tabs/`: PySide6 tab/dialog controllers.
- `plugins/`: optional startup-loaded plugins.

## Extension Points

Plugins register capabilities with `ExtensionRegistry`:

- monster library importers
- party importers
- encounter importers
- encounter generators
- rulesets
- UI contributions

Drop a Python module into `plugins/` and expose `register(registry)`.

```python
def register(registry):
    registry.register_encounter_generator(MyGenerator())
```

## Design Direction

Keep `CombatManager` as the stable facade used by Qt controllers. New storage,
import/export, generation, or rules behavior should be added through services or
plugins first, then surfaced in the UI only where needed.
