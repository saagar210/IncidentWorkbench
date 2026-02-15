"""Database connection and migration management."""

import sqlite3
from pathlib import Path
from typing import Any
from threading import Lock

from config import settings


class Database:
    """SQLite database manager with migration support."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or settings.db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # Lock to protect connection creation (note: individual connections still need
        # their own synchronization, but this is better than no protection)
        self._lock = Lock()

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with WAL mode enabled.

        Note: Returns a connection with check_same_thread=False. Each connection
        should be used within a single request/context and properly closed.
        WAL mode allows concurrent reads with single writer.
        """
        with self._lock:
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def run_migrations(self) -> None:
        """Run all pending migrations."""
        conn = self.get_connection()
        try:
            # Create migrations table if it doesn't exist
            conn.execute("""
                CREATE TABLE IF NOT EXISTS _migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

            # Get already applied migrations
            cursor = conn.execute("SELECT name FROM _migrations")
            applied = {row["name"] for row in cursor.fetchall()}

            # Find and apply pending migrations
            migrations_dir = Path(__file__).parent / "migrations"
            if not migrations_dir.exists():
                return

            migration_files = sorted(migrations_dir.glob("*.sql"))
            for migration_file in migration_files:
                migration_name = migration_file.name
                if migration_name in applied:
                    continue

                print(f"Applying migration: {migration_name}")
                sql = migration_file.read_text()

                # Execute migration SQL
                conn.executescript(sql)

                # Record migration
                conn.execute(
                    "INSERT INTO _migrations (name) VALUES (?)",
                    (migration_name,)
                )
                conn.commit()
                print(f"Migration applied: {migration_name}")

        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Migration failed: {e}") from e
        finally:
            conn.close()


db = Database()
