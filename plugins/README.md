# Plugins

Plugins are optional Python modules loaded at startup. A plugin can expose either
`register(registry)` or a `PLUGIN` object with a `register(registry)` method.

Example:

```python
class MyEncounterGenerator:
    id = "my.generator"
    label = "My Encounter Generator"

    def generate(self, context, options):
        ...


def register(registry):
    registry.register_encounter_generator(MyEncounterGenerator())
```

Available registry methods:

- `register_monster_library_importer(importer)`
- `register_party_importer(importer)`
- `register_encounter_importer(importer)`
- `register_encounter_generator(generator)`
- `register_ruleset(ruleset)`
- `register_ui_contribution(contribution)`

UI contributions receive the running `NimbleMainApp` instance through
`attach(app)` after the core tabs are initialized.
