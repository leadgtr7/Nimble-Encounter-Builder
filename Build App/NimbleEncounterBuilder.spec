# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Nimble Encounter Builder
# Auto-generated with enhanced PySide6 support

block_cipher = None

a = Analysis(
    ['C:/Users/Jack/Documents/Nimble Initiative Tracker/Nimble-Encounter-Builder/NimbleEncounterBuilder.py'],
    pathex=['C:/Users/Jack/Documents/Nimble Initiative Tracker/Nimble-Encounter-Builder'],
    
    # PySide6 binaries and plugins
    binaries=[
        ('C:/Users/Jack/AppData/Local/Python/pythoncore-3.14-64/Lib/site-packages/PySide6/plugins/platforms', 'PySide6/plugins/platforms'),
        ('C:/Users/Jack/AppData/Local/Python/pythoncore-3.14-64/Lib/site-packages/PySide6/plugins/styles', 'PySide6/plugins/styles'),
    ],
    datas=[
                ('C:/Users/Jack/Documents/Nimble Initiative Tracker/Nimble-Encounter-Builder/uiDesign/addEditHero.ui', 'uiDesign'),
        ('C:/Users/Jack/Documents/Nimble Initiative Tracker/Nimble-Encounter-Builder/uiDesign/addEditMonster.ui', 'uiDesign'),
        ('C:/Users/Jack/Documents/Nimble Initiative Tracker/Nimble-Encounter-Builder/uiDesign/nimbleHandy.ui', 'uiDesign'),
        ('C:/Users/Jack/Documents/Nimble Initiative Tracker/Nimble-Encounter-Builder/uiDesign/numberInput.ui', 'uiDesign'),
        ('C:/Users/Jack/Documents/Nimble Initiative Tracker/Nimble-Encounter-Builder/uiDesign/setMapMarkers.ui', 'uiDesign'),
        ('C:/Users/Jack/Documents/Nimble Initiative Tracker/Nimble-Encounter-Builder/README.html', '.'),
        ('C:/Users/Jack/Documents/Nimble Initiative Tracker/Nimble-Encounter-Builder/EncounterBuilderAppImage.png', '.'),
    ],
    hiddenimports=[
        # PySide6 modules
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtUiTools',
        'shiboken6',
        # Application modules
        'modules.combatManager',
        'modules.combatants',
        'modules.config',
        'modules.persistence',
        'modules.shared_statblock',
        'modules.condition_descriptions',
        'tabs.heroes_tab',
        'tabs.combat_tab',
        'tabs.bestiary_tab',
        'tabs.config_tab',
        'tabs.hero_dialog',
        'tabs.conditions_dialog',
        'tabs.damage_heal_dialog',
        'tabs.add_edit_monster_dialog',
        'tabs.marker_dialog',
        'tabs.random_encounter_dialog',
        'tabs.bulk_marker_dialog',
        'tabs.vault_viewer_controller',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'tkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Nimble Encounter Builder v01192026_202940',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set NIMBLE_BUILD_CONSOLE=1 for debug output
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='C:/Users/Jack/Documents/Nimble Initiative Tracker/Nimble-Encounter-Builder/EncounterBuilderIconImage.png',  # Application icon
)
