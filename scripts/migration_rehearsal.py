#!/usr/bin/env python3
"""Rehearse migrations against a fresh temporary database."""

from __future__ import annotations

import tempfile
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import Database  # noqa: E402


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="migration-rehearsal-") as tmp_dir:
        db_path = Path(tmp_dir) / "rehearsal.db"
        rehearsal_db = Database(db_path=db_path)

        # First run must apply all migrations on empty schema.
        rehearsal_db.run_migrations()

        # Second run must be a no-op (idempotent migration runner behavior).
        rehearsal_db.run_migrations()

        conn = rehearsal_db.get_connection()
        try:
            count = conn.execute("SELECT COUNT(*) FROM _migrations").fetchone()[0]
            if count <= 0:
                raise RuntimeError("Expected at least one applied migration")
        finally:
            conn.close()

    print("Migration rehearsal passed.")


if __name__ == "__main__":
    main()
