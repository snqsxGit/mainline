"""SQLite connection and schema management for Mainline persistence."""

from __future__ import annotations

import sqlite3
from pathlib import Path


APP_DIR = Path.home() / ".mainline"
DEFAULT_DATABASE_PATH = APP_DIR / "mainline.sqlite3"
SCHEMA_VERSION = 1


class Database:
    """Open SQLite connections and initialize the application schema."""

    def __init__(self, path: Path | str | None = None) -> None:
        """Create a database manager for ``path`` or the user data location."""
        self.path = Path(path) if path is not None else DEFAULT_DATABASE_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._initialize_schema()

    @property
    def connection(self) -> sqlite3.Connection:
        """Return the shared SQLite connection."""
        return self._connection

    def close(self) -> None:
        """Close the SQLite connection."""
        self._connection.close()

    def _initialize_schema(self) -> None:
        """Create the current schema if this is a new database file."""
        with self._connection:
            self._connection.execute("PRAGMA user_version = %d" % SCHEMA_VERSION)
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS repertoires (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    side TEXT NOT NULL DEFAULT 'white',
                    root_fen TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_opened_node_id INTEGER,
                    metadata TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS move_nodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repertoire_id INTEGER NOT NULL,
                    parent_id INTEGER,
                    move_uci TEXT,
                    move_san TEXT NOT NULL DEFAULT '',
                    fen_after_move TEXT NOT NULL,
                    move_number INTEGER NOT NULL DEFAULT 1,
                    variation_index INTEGER NOT NULL DEFAULT 0,
                    comments TEXT NOT NULL DEFAULT '[]',
                    nags TEXT NOT NULL DEFAULT '[]',
                    metadata TEXT NOT NULL DEFAULT '{}',
                    FOREIGN KEY (repertoire_id) REFERENCES repertoires(id) ON DELETE CASCADE,
                    FOREIGN KEY (parent_id) REFERENCES move_nodes(id) ON DELETE CASCADE
                )
                """
            )
            self._connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_move_nodes_repertoire_parent
                ON move_nodes(repertoire_id, parent_id, variation_index)
                """
            )
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS app_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
