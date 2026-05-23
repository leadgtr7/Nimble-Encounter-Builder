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

.app-grid {
  display: grid;
  grid-template-columns: minmax(260px, 320px) minmax(520px, 1fr) minmax(360px, 500px);
  gap: 12px;
  align-items: start;
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
}

.combat-grid {
  height: 590px;
  width: 100%;
}

.combat-grid .ag-theme-balham-dark {
  --ag-background-color: #202020;
  --ag-odd-row-background-color: #252525;
  --ag-header-background-color: #303030;
  --ag-border-color: #454545;
  --ag-row-hover-color: #38342c;
  --ag-selected-row-background-color: #4b3924;
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
  width: 100%;
}

.stat-card {
  background:
    linear-gradient(135deg, rgba(255,255,255,.28), rgba(255,255,255,0) 44%),
    var(--parchment);
  border: 1px solid var(--parchment-line);
  border-radius: 4px;
  color: var(--ink);
  font-family: Georgia, "Times New Roman", serif;
  min-height: 260px;
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
  min-height: 180px;
}

.loot-list {
  max-height: 140px;
  overflow: auto;
}

.combat-log {
  font-family: Consolas, "Courier New", monospace;
  min-height: 150px;
}

@media (max-width: 1180px) {
  .app-grid {
    grid-template-columns: 1fr;
  }

  .combat-grid {
    height: 460px;
  }
}
"""

