"""High-level persistence orchestration for repertoires and move trees."""

from __future__ import annotations

import chess

from app.chess import MoveTreeModel, MoveTreeNode
from app.database import AppStateRepository, Database, MoveNodeRecord, MoveTreeRepository, RepertoireRecord, RepertoireRepository
from app.models import LoadedRepertoire, RepertoireSummary


class PersistenceService:
    """Coordinate repository operations and chess move-tree serialization."""

    def __init__(self, database: Database | None = None) -> None:
        self._database = database or Database()
        connection = self._database.connection
        self._repertoires = RepertoireRepository(connection)
        self._move_trees = MoveTreeRepository(connection)
        self._app_state = AppStateRepository(connection)

    def close(self) -> None:
        """Close the underlying database connection."""
        self._database.close()

    def list_repertoires(self) -> list[RepertoireSummary]:
        return [self._summary(record) for record in self._repertoires.list_all()]

    def create_repertoire(self, name: str, *, side: str = "white") -> LoadedRepertoire:
        tree = MoveTreeModel()
        record = self._repertoires.create(name, side=side, root_fen=tree.root.fen)
        self.save_repertoire_tree(record.id, tree, tree.root)
        return self.load_repertoire(record.id)  # type: ignore[return-value]

    def rename_repertoire(self, repertoire_id: int, name: str) -> RepertoireSummary:
        return self._summary(self._repertoires.rename(repertoire_id, name))

    def delete_repertoire(self, repertoire_id: int) -> None:
        if self._app_state.get_last_repertoire_id() == repertoire_id:
            self._app_state.set_last_repertoire_id(None)
        self._repertoires.delete(repertoire_id)

    def load_repertoire(self, repertoire_id: int) -> LoadedRepertoire | None:
        record = self._repertoires.get(repertoire_id)
        if record is None:
            return None
        tree, nodes_by_id = self._deserialize_tree(record)
        selected = nodes_by_id.get(record.last_opened_node_id, tree.root)
        tree.select_node(selected)
        self._app_state.set_last_repertoire_id(repertoire_id)
        self._repertoires.touch(repertoire_id)
        return LoadedRepertoire(record.id, record.name, record.side, tree, selected)

    def load_last_repertoire(self) -> LoadedRepertoire | None:
        repertoire_id = self._app_state.get_last_repertoire_id()
        if repertoire_id is None:
            return None
        loaded = self.load_repertoire(repertoire_id)
        if loaded is None:
            self._app_state.set_last_repertoire_id(None)
        return loaded

    def save_repertoire_tree(self, repertoire_id: int, tree: MoveTreeModel, selected_node: MoveTreeNode) -> None:
        node_ids = self._assign_transient_ids(tree.root)
        records = self._serialize_tree(tree.root, node_ids)
        id_map = self._move_trees.replace_tree(repertoire_id, records)
        selected_id = id_map.get(node_ids[id(selected_node)])
        self._repertoires.update_last_node(repertoire_id, selected_id)
        self._app_state.set_last_repertoire_id(repertoire_id)

    def _deserialize_tree(self, record: RepertoireRecord) -> tuple[MoveTreeModel, dict[int | None, MoveTreeNode]]:
        rows = self._move_trees.load_tree(record.id)
        tree = MoveTreeModel(record.root_fen)
        nodes_by_id: dict[int | None, MoveTreeNode] = {None: tree.root}
        root_rows = [row for row in rows if row.parent_id is None]
        if root_rows:
            root = root_rows[0]
            tree.root.fen = root.fen_after_move
            tree.root.move_number = root.move_number
            tree.root.comments = root.comments
            tree.root.nags = set(root.nags)
            tree.root.metadata = root.metadata
            nodes_by_id[root.id] = tree.root
        for row in rows:
            if row.parent_id is None:
                continue
            parent = nodes_by_id.get(row.parent_id)
            if parent is None:
                continue
            node = MoveTreeNode(
                fen=row.fen_after_move,
                parent=parent,
                move=chess.Move.from_uci(row.move_uci) if row.move_uci else None,
                san=row.move_san,
                move_number=row.move_number,
                comments=row.comments,
                nags=set(row.nags),
                metadata=row.metadata,
            )
            parent.children.append(node)
            nodes_by_id[row.id] = node
        return tree, nodes_by_id

    def _assign_transient_ids(self, root: MoveTreeNode) -> dict[int, int]:
        mapping: dict[int, int] = {}
        next_id = 1
        stack = [root]
        while stack:
            node = stack.pop(0)
            mapping[id(node)] = next_id
            next_id += 1
            stack.extend(node.children)
        return mapping

    def _serialize_tree(self, root: MoveTreeNode, node_ids: dict[int, int]) -> list[MoveNodeRecord]:
        records: list[MoveNodeRecord] = []

        def visit(node: MoveTreeNode, parent: MoveTreeNode | None, variation_index: int) -> None:
            records.append(
                MoveNodeRecord(
                    id=node_ids[id(node)],
                    parent_id=node_ids[id(parent)] if parent is not None else None,
                    move_uci=node.move.uci() if node.move else None,
                    move_san=node.san,
                    fen_after_move=node.fen,
                    move_number=node.move_number,
                    variation_index=variation_index,
                    comments=node.comments,
                    nags=sorted(node.nags),
                    metadata=node.metadata,
                )
            )
            for child_index, child in enumerate(node.children):
                visit(child, node, child_index)

        visit(root, None, 0)
        return records

    def _summary(self, record: RepertoireRecord) -> RepertoireSummary:
        return RepertoireSummary(record.id, record.name, record.side, record.updated_at, record.created_at)
