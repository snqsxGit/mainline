"""Repository classes that keep SQL out of UI widgets."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class RepertoireRecord:
    """Stored repertoire project metadata."""

    id: int
    name: str
    side: str
    root_fen: str
    created_at: str
    updated_at: str
    last_opened_node_id: int | None
    metadata: dict[str, object]


@dataclass(frozen=True)
class MoveNodeRecord:
    """Flat database representation of a move-tree node."""

    id: int
    parent_id: int | None
    move_uci: str | None
    move_san: str
    fen_after_move: str
    move_number: int
    variation_index: int
    comments: list[str]
    nags: list[int]
    metadata: dict[str, object]


class RepertoireRepository:
    """CRUD operations for repertoire project records."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def list_all(self) -> list[RepertoireRecord]:
        rows = self._connection.execute(
            "SELECT * FROM repertoires ORDER BY updated_at DESC, name COLLATE NOCASE"
        ).fetchall()
        return [self._to_record(row) for row in rows]

    def get(self, repertoire_id: int) -> RepertoireRecord | None:
        row = self._connection.execute("SELECT * FROM repertoires WHERE id = ?", (repertoire_id,)).fetchone()
        return self._to_record(row) if row else None

    def create(self, name: str, *, side: str, root_fen: str) -> RepertoireRecord:
        unique_name = self.unique_name(name)
        with self._connection:
            cursor = self._connection.execute(
                "INSERT INTO repertoires (name, side, root_fen) VALUES (?, ?, ?)",
                (unique_name, side, root_fen),
            )
        record = self.get(int(cursor.lastrowid))
        if record is None:
            raise RuntimeError("Failed to create repertoire")
        return record

    def rename(self, repertoire_id: int, name: str) -> RepertoireRecord:
        unique_name = self.unique_name(name, exclude_id=repertoire_id)
        with self._connection:
            self._connection.execute(
                "UPDATE repertoires SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (unique_name, repertoire_id),
            )
        record = self.get(repertoire_id)
        if record is None:
            raise ValueError(f"Unknown repertoire id: {repertoire_id}")
        return record

    def delete(self, repertoire_id: int) -> None:
        with self._connection:
            self._connection.execute("DELETE FROM repertoires WHERE id = ?", (repertoire_id,))

    def update_last_node(self, repertoire_id: int, node_id: int | None) -> None:
        with self._connection:
            self._connection.execute(
                "UPDATE repertoires SET last_opened_node_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (node_id, repertoire_id),
            )

    def touch(self, repertoire_id: int) -> None:
        with self._connection:
            self._connection.execute("UPDATE repertoires SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (repertoire_id,))

    def unique_name(self, desired_name: str, *, exclude_id: int | None = None) -> str:
        base = desired_name.strip() or "Untitled repertoire"
        candidate = base
        suffix = 2
        while self._name_exists(candidate, exclude_id=exclude_id):
            candidate = f"{base} ({suffix})"
            suffix += 1
        return candidate

    def _name_exists(self, name: str, *, exclude_id: int | None) -> bool:
        params: tuple[object, ...] = (name,) if exclude_id is None else (name, exclude_id)
        query = "SELECT 1 FROM repertoires WHERE name = ? COLLATE NOCASE"
        if exclude_id is not None:
            query += " AND id != ?"
        return self._connection.execute(query, params).fetchone() is not None

    def _to_record(self, row: sqlite3.Row) -> RepertoireRecord:
        return RepertoireRecord(
            id=int(row["id"]),
            name=str(row["name"]),
            side=str(row["side"]),
            root_fen=str(row["root_fen"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            last_opened_node_id=row["last_opened_node_id"],
            metadata=json.loads(row["metadata"] or "{}"),
        )


class MoveTreeRepository:
    """Store and load flat move-tree node records."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def replace_tree(self, repertoire_id: int, records: list[MoveNodeRecord]) -> dict[int, int]:
        """Replace all nodes for a repertoire and return old-id to new-id mapping."""
        id_map: dict[int, int] = {}
        with self._connection:
            self._connection.execute("DELETE FROM move_nodes WHERE repertoire_id = ?", (repertoire_id,))
            for record in records:
                parent_id = id_map.get(record.parent_id) if record.parent_id is not None else None
                cursor = self._connection.execute(
                    """
                    INSERT INTO move_nodes (
                        repertoire_id, parent_id, move_uci, move_san, fen_after_move,
                        move_number, variation_index, comments, nags, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        repertoire_id,
                        parent_id,
                        record.move_uci,
                        record.move_san,
                        record.fen_after_move,
                        record.move_number,
                        record.variation_index,
                        json.dumps(record.comments),
                        json.dumps(record.nags),
                        json.dumps(record.metadata),
                    ),
                )
                id_map[record.id] = int(cursor.lastrowid)
        return id_map

    def load_tree(self, repertoire_id: int) -> list[MoveNodeRecord]:
        rows = self._connection.execute(
            """
            SELECT * FROM move_nodes
            WHERE repertoire_id = ?
            ORDER BY COALESCE(parent_id, 0), variation_index, id
            """,
            (repertoire_id,),
        ).fetchall()
        return [self._to_record(row) for row in rows]

    def _to_record(self, row: sqlite3.Row) -> MoveNodeRecord:
        return MoveNodeRecord(
            id=int(row["id"]),
            parent_id=row["parent_id"],
            move_uci=row["move_uci"],
            move_san=str(row["move_san"]),
            fen_after_move=str(row["fen_after_move"]),
            move_number=int(row["move_number"]),
            variation_index=int(row["variation_index"]),
            comments=json.loads(row["comments"] or "[]"),
            nags=json.loads(row["nags"] or "[]"),
            metadata=json.loads(row["metadata"] or "{}"),
        )


class AppStateRepository:
    """Persist simple application-level state."""

    LAST_REPERTOIRE_KEY = "last_repertoire_id"

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def get_last_repertoire_id(self) -> int | None:
        row = self._connection.execute("SELECT value FROM app_state WHERE key = ?", (self.LAST_REPERTOIRE_KEY,)).fetchone()
        if row is None:
            return None
        try:
            return int(row["value"])
        except (TypeError, ValueError):
            return None

    def set_last_repertoire_id(self, repertoire_id: int | None) -> None:
        with self._connection:
            if repertoire_id is None:
                self._connection.execute("DELETE FROM app_state WHERE key = ?", (self.LAST_REPERTOIRE_KEY,))
            else:
                self._connection.execute(
                    "INSERT OR REPLACE INTO app_state (key, value) VALUES (?, ?)",
                    (self.LAST_REPERTOIRE_KEY, str(repertoire_id)),
                )
