"""UI-safe repertoire data models."""

from __future__ import annotations

from dataclasses import dataclass

from app.chess import MoveTreeModel, MoveTreeNode


@dataclass(frozen=True)
class RepertoireSummary:
    """Lightweight repertoire metadata for lists and launch flows."""

    id: int
    name: str
    side: str
    updated_at: str
    created_at: str


@dataclass
class LoadedRepertoire:
    """A repertoire plus its editable move tree and restored position."""

    id: int
    name: str
    side: str
    tree: MoveTreeModel
    selected_node: MoveTreeNode
