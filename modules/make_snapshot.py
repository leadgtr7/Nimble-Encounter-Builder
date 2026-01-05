"""
Create a timestamped snapshot of the working tree.

Usage:
    python make_snapshot.py

The snapshot (zip) is written to the snapshots/ folder alongside the project root.
Common build/virtualenv/cache directories are excluded.
"""

from __future__ import annotations

import datetime
import zipfile
from pathlib import Path


EXCLUDED_DIRS = {
    ".git",
    ".idea",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".vs",
    "snapshots",
}


def should_exclude(path: Path) -> bool:
    """Return True if any part of the path is in the excluded set."""
    return any(part in EXCLUDED_DIRS for part in path.parts)


def make_snapshot() -> Path:
    # Snapshot root is the repo root (one level above Nimble-Encounter-Builder).
    root = Path(__file__).resolve().parents[2]
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    snapshot_dir = root / "snapshots"
    snapshot_dir.mkdir(exist_ok=True)
    zip_path = snapshot_dir / f"snapshot-{timestamp}.zip"

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in root.rglob("*"):
            if path.is_dir():
                # Skip excluded directories entirely
                if should_exclude(path):
                    continue
                continue
            if should_exclude(path):
                continue
            # Avoid archiving the snapshot file while it's being written
            if zip_path.exists() and path.samefile(zip_path):
                continue
            zf.write(path, arcname=path.relative_to(root))

    return zip_path


if __name__ == "__main__":
    out = make_snapshot()
    print(f"Created snapshot: {out}")
