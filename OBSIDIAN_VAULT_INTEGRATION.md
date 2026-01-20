# Obsidian Vault Integration


Nimble Encounter Builder is an independent product published under the Nimble 3rd Party Creator License. Nimble © Nimble Co.
The Nimble Encounter Builder now supports using an Obsidian vault as the base directory for all file operations.

## How It Works

When you configure an **Obsidian Vault Path** in the Config tab, all folder paths will be resolved relative to that vault:

- **Combat Logs** → `<Obsidian Vault>/Combat Logs`
- **Encounters** → `<Obsidian Vault>/Encounters`
- **Party Files** → `<Obsidian Vault>/Heroes`

## Automatic Detection

### On First Load
When you load the config for the first time, the app will **automatically detect** your Obsidian vault if:
- Your Monster Vault path contains "Nimble Vault", "TTRPG_Vault", or "Obsidian" in the path
- Example: `C:\TTRPG_Vault\Nimble Vault\Foes\Monsters\bestiary.json` → auto-detects `C:\TTRPG_Vault\Nimble Vault`

### Auto-Inference of Folders
Once the vault is detected or manually set, the app will **automatically look for and set** folder paths:
- Searches for existing folders like "Encounters", "Sessions", "Heroes", "Party", "Combat Logs", "Logs"
- Uses relative paths (e.g., "Encounters" instead of full path)
- Only infers if the folder paths are currently empty

### Manual Setup

1. Go to the **Config** tab
2. Find the **Paths** section
3. Click **Browse** next to **Obsidian Vault Path**
4. Select your vault's root directory (e.g., `C:\TTRPG_Vault\Nimble Vault`)
5. The app will automatically detect existing folders and populate the paths
6. Click **Save Config**

### Folder Behavior

Once the Obsidian Vault Path is set:

#### Default Folders
If you leave the individual folder paths empty, the app will use these defaults within your vault:
- **Encounters** → `<Vault>/Encounters`
- **Heroes/Party** → `<Vault>/Heroes`
- **Combat Logs** → `<Vault>/Combat Logs`

#### Custom Relative Paths
You can specify custom folder names that will be relative to your vault:
- Set **Encounter Folder** to `"Sessions/Encounters"` → resolves to `<Vault>/Sessions/Encounters`
- Set **Party Folder** to `"Characters/Party"` → resolves to `<Vault>/Characters/Party`
- Set **Combat Log Folder** to `"Logs"` → resolves to `<Vault>/Logs`

#### Absolute Paths Override
If you specify an absolute path (starting with `C:\` or `/`), it will be used as-is, ignoring the vault path.

## Example Setup

### Without Obsidian Vault
```
Obsidian Vault Path: (empty)
Encounter Folder: C:\MyGames\Encounters
Party Folder: C:\MyGames\Heroes
Combat Log Folder: C:\MyGames\Logs
```
Result: Uses exactly the paths you specified.

### With Obsidian Vault
```
Obsidian Vault Path: C:\TTRPG_Vault\Nimble Vault
Encounter Folder: (empty)
Party Folder: (empty)
Combat Log Folder: (empty)
```
Result:
- Encounters → `C:\TTRPG_Vault\Nimble Vault\Encounters`
- Heroes → `C:\TTRPG_Vault\Nimble Vault\Heroes`
- Combat Logs → `C:\TTRPG_Vault\Nimble Vault\Combat Logs`

### With Obsidian Vault + Custom Paths
```
Obsidian Vault Path: C:\TTRPG_Vault\Nimble Vault
Encounter Folder: Campaign/Encounters
Party Folder: Campaign/Heroes
Combat Log Folder: Campaign/Logs
```
Result:
- Encounters → `C:\TTRPG_Vault\Nimble Vault\Campaign/Encounters`
- Heroes → `C:\TTRPG_Vault\Nimble Vault\Campaign/Heroes`
- Combat Logs → `C:\TTRPG_Vault\Nimble Vault\Campaign/Logs`

## Benefits

### Organization
- All your campaign data in one place
- Easy to backup (just backup the vault)
- Works seamlessly with Obsidian for note-taking

### Portability
- Move your vault, update one path, everything works
- Share entire campaigns by sharing the vault folder
- No broken file references

### Flexibility
- Can still use absolute paths if needed
- Mix and match relative and absolute paths
- Works with or without Obsidian vault set

## Technical Details

The following config methods handle path resolution:
- `CONFIG.get_encounter_folder()` - Returns encounter folder Path object
- `CONFIG.get_party_folder()` - Returns party folder Path object
- `CONFIG.get_combat_log_folder()` - Returns combat log folder Path object

These methods check if `obsidian_vault_path` is set and exists, then:
1. If a specific folder is configured and it's relative, join it with the vault path
2. If a specific folder is configured and it's absolute, use it as-is
3. If no specific folder is configured, use default folder name within the vault
4. If no vault is configured, fall back to project root folders

## Backwards Compatibility

If you don't set an Obsidian Vault Path, everything works exactly as before. Your existing folder configurations are not affected.

