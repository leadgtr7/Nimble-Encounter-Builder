"""CSS for the NiceGUI encounter front end."""

APP_CSS = """
:root {
  color-scheme: dark;
  --nimble-bg: #181818;
  --nimble-panel: #242424;
  --nimble-panel-2: #2c2c2c;
  --nimble-border: #464646;
  --nimble-text: #f0eee8;
  --nimble-muted: #b7b0a4;
  --nimble-accent: #b88745;
  --nimble-green: #4b8f5a;
  --nimble-red: #a7473f;
  --parchment: #eee1c5;
  --parchment-line: #b8a17c;
  --ink: #241f18;
}

body {
  background: var(--nimble-bg);
  color: var(--nimble-text);
}

.app-shell {
  width: 100%;
  max-width: 1760px;
  margin: 0 auto;
  padding: 12px;
}

.app-header {
  background: #151515;
  border-bottom: 1px solid var(--nimble-border);
}

.app-logo {
  width: 34px;
  height: 34px;
  object-fit: contain;
}

.app-title {
  font-size: 19px;
  font-weight: 750;
  letter-spacing: 0;
}

.focus-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: stretch;
  min-height: 0;
}

.tools-panel {
  margin-top: 12px;
  padding-top: 0;
}

.tool-tabs {
  background: #1f1f1f;
  border-bottom: 1px solid var(--nimble-border);
  margin: 0 -12px;
  padding: 0 8px;
}

.tool-tabs .q-tab {
  color: var(--nimble-muted);
}

.tool-tabs .q-tab--active {
  color: var(--nimble-text);
}

.tool-tab-panels {
  background: transparent;
}

.tool-tab-panel {
  background: transparent;
  color: var(--nimble-text);
  padding: 10px 0 0;
}

.stat-panel {
  align-items: center;
  display: flex;
  flex-direction: column;
  min-height: 0;
  order: 1;
}

.stat-panel > .nicegui-row {
  align-self: stretch;
}

.setup-panel {
  min-height: 0;
  order: 2;
}

.balance-panel {
  min-height: 0;
  order: 3;
}

.combat-panel {
  min-height: 0;
  order: 4;
}

.panel {
  background: var(--nimble-panel);
  border: 1px solid var(--nimble-border);
  border-radius: 6px;
  padding: 12px;
}

.panel-title {
  font-size: 15px;
  font-weight: 750;
  margin-bottom: 8px;
}

.compact-field {
  min-width: 0;
  width: 150px;
}

.level-field,
.small-number-field {
  min-width: 0;
  width: 96px;
}

.monster-select {
  flex: 1 1 420px;
  min-width: 280px;
}

.library-count {
  color: var(--nimble-muted);
  font-size: 12px;
  min-height: 18px;
}

.setup-row {
  row-gap: 8px;
}

.selected-summary {
  color: var(--nimble-muted);
  font-size: 12px;
  min-height: 20px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.combat-action-bar {
  background: #1f1f1f;
  border: 1px solid #3a3a3a;
  border-radius: 4px;
  margin: 4px 0 8px;
  padding: 6px;
}

.combat-action-row,
.combat-detail-row {
  min-height: 34px;
}

.combat-action-bar .q-btn {
  min-height: 30px;
}

.combat-action-bar .q-btn--round {
  min-height: 30px;
  min-width: 30px;
  width: 30px;
}

.combat-action-bar .q-icon {
  font-size: 18px;
}

.combat-action-bar .q-field--dense .q-field__control,
.combat-action-bar .q-field--dense .q-field__marginal {
  min-height: 32px;
  height: 32px;
}

.mini-switch {
  margin-right: 0;
  min-width: 38px;
}

.conditions-field {
  min-width: 170px;
  flex: 1 1 220px;
}

.marker-field {
  width: 92px;
}

.marker-number-field {
  width: 56px;
}

.group-field {
  min-width: 90px;
  flex: 1 1 110px;
}

.slim-select .q-field__native,
.slim-input input {
  font-size: 12px;
}

.combat-grid {
  height: min(50vh, 520px);
  min-height: 360px;
  width: 100%;
}

.combat-grid .ag-root-wrapper,
.combat-grid .ag-header,
.combat-grid .ag-header-cell,
.combat-grid .ag-row,
.combat-grid .ag-cell {
  background: #242424;
  color: var(--nimble-text);
}

.combat-grid .ag-root-wrapper {
  border-color: var(--nimble-border);
}

.combat-grid .ag-header,
.combat-grid .ag-header-cell {
  background: #303030;
}

.combat-grid .ag-row {
  border-bottom-color: #3a3a3a;
}

.combat-grid .ag-row:hover .ag-cell {
  background: #303030;
}

.combat-grid .ag-header-cell-label,
.combat-grid .ag-cell {
  align-items: center;
  font-size: 12px;
  padding-left: 6px;
  padding-right: 6px;
}

.combat-grid .ag-row.selected-row .ag-cell,
.combat-grid .ag-row.ag-row-selected .ag-cell {
  background: rgba(184, 135, 69, .18) !important;
  border-bottom-color: rgba(184, 135, 69, .38);
}

.combat-difficulty-badge {
  min-width: 112px;
}

.difficulty-pill-mini {
  border-radius: 4px;
  color: white;
  display: inline-block;
  font-size: 12px;
  font-weight: 800;
  line-height: 1;
  padding: 7px 9px;
  white-space: nowrap;
}

.hp-healthy {
  background-color: #205c2d !important;
  color: white !important;
  font-weight: 750;
}

.hp-bloodied {
  background-color: #8c640d !important;
  color: white !important;
  font-weight: 750;
}

.hp-critical,
.hp-dead {
  background-color: #8f2f2b !important;
  color: white !important;
  font-weight: 750;
}

.hp-last-stand {
  background-color: #6f3d99 !important;
  color: white !important;
  font-weight: 750;
}

.difficulty-pill {
  border-radius: 4px;
  color: white;
  font-weight: 800;
  padding: 8px 10px;
  text-align: center;
}

.difficulty-table {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 4px 10px;
  color: var(--nimble-muted);
  font-size: 12px;
}

.stat-card-host {
  align-self: center;
  aspect-ratio: 5 / 7;
  margin: 0 auto;
  width: min(340px, 92vw);
}

.stat-card {
  background:
    linear-gradient(135deg, rgba(255,255,255,.28), rgba(255,255,255,0) 44%),
    var(--parchment);
  border: 1px solid var(--parchment-line);
  border-radius: 4px;
  box-sizing: border-box;
  color: var(--ink);
  font-family: Georgia, "Times New Roman", serif;
  height: 100%;
  min-height: 0;
  overflow: auto;
  padding: 14px;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.32);
}

.stat-card-header {
  align-items: start;
  border-bottom: 2px solid rgba(92, 70, 42, .42);
  display: flex;
  gap: 12px;
  justify-content: space-between;
  padding-bottom: 8px;
}

.stat-card-name {
  font-size: 23px;
  font-style: italic;
  font-variant: small-caps;
  font-weight: 900;
  line-height: 1;
}

.stat-card-meta {
  color: #5d4f3f;
  font-family: Arial, sans-serif;
  font-size: 11px;
  font-weight: 700;
  margin-top: 3px;
  text-transform: uppercase;
}

.stat-card-hp,
.stat-card-tag {
  background: rgba(67, 56, 41, .16);
  border: 1px solid rgba(67, 56, 41, .28);
  border-radius: 999px;
  color: #2a2219;
  font-family: Arial, sans-serif;
  font-size: 12px;
  font-weight: 800;
  padding: 4px 8px;
  white-space: nowrap;
}

.stat-card-tag {
  display: inline-block;
  margin-top: 8px;
}

.stat-card-flavor {
  color: #3a3025;
  font-style: italic;
  margin: 8px 0;
}

.stat-card-strip {
  background: rgba(88, 78, 58, .16);
  display: grid;
  gap: 6px;
  grid-template-columns: repeat(3, 1fr);
  margin: 8px 0 12px;
  padding: 7px 8px;
}

.stat-card-strip span {
  font-family: Arial, sans-serif;
  font-size: 12px;
}

.stat-card h3 {
  border-bottom: 1px solid rgba(92, 70, 42, .25);
  font-family: Arial, sans-serif;
  font-size: 12px;
  letter-spacing: 0;
  margin: 10px 0 4px;
  text-transform: uppercase;
}

.stat-card ul {
  margin: 0;
  padding-left: 17px;
}

.stat-card li,
.stat-card p {
  font-size: 14px;
  line-height: 1.22;
}

.stat-card-callouts p {
  background: rgba(122, 93, 53, .14);
  border-left: 4px solid rgba(122, 93, 53, .46);
  margin: 7px 0 0;
  padding: 6px 8px;
}

.stat-card-empty {
  color: #6b5f4c;
  min-height: 0;
}

.loot-list {
  max-height: 140px;
  overflow: auto;
}

.combat-log {
  font-family: Consolas, "Courier New", monospace;
  min-height: 150px;
}

.monster-edit-dialog {
  background: var(--nimble-panel);
  color: var(--nimble-text);
  max-height: 88vh;
  max-width: 860px;
  overflow: auto;
  width: min(860px, 94vw);
}

.amount-dialog {
  background: var(--nimble-panel);
  color: var(--nimble-text);
  max-width: 420px;
  width: min(420px, 92vw);
}

.amount-hint {
  color: var(--nimble-muted);
  font-size: 12px;
  margin-bottom: 8px;
}

.amount-grid {
  display: grid;
  gap: 6px;
  grid-template-columns: repeat(6, minmax(42px, 1fr));
}

.amount-option {
  border-radius: 4px;
  min-height: 34px;
  min-width: 0 !important;
}

.q-field--outlined .q-field__control {
  background: #171717;
  color: var(--nimble-text);
}

.q-field--outlined .q-field__control:before {
  border-color: #555;
}

.q-field__native,
.q-field__input,
.q-field__label,
.q-field__prefix,
.q-field__suffix,
.q-field__marginal,
.q-select__dropdown-icon,
.q-toggle__label,
.q-checkbox__label {
  color: var(--nimble-text) !important;
}

.q-field--disabled .q-field__native,
.q-field--disabled .q-field__input {
  color: var(--nimble-muted) !important;
}

.q-menu,
.q-menu .q-list,
.q-menu .q-item {
  background: var(--nimble-panel-2);
  color: var(--nimble-text);
}

.q-item--active,
.q-item.q-router-link--active {
  background: rgba(184, 135, 69, .18);
  color: var(--nimble-text);
}

.q-chip {
  background: #353535;
  color: var(--nimble-text);
}

@media (max-width: 1180px) {
  .combat-grid {
    height: 430px;
    min-height: 360px;
  }

  .stat-card {
    height: 100%;
    min-height: 0;
  }
}
"""
