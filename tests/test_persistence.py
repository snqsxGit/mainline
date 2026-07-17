"""Persistence service tests."""

from __future__ import annotations

import chess

from app.database import Database
from app.services import PersistenceService


def test_create_save_and_restore_repertoire_tree(tmp_path):
    service = PersistenceService(Database(tmp_path / "mainline.sqlite3"))
    loaded = service.create_repertoire("White repertoire")

    loaded.tree.add_move(chess.Move.from_uci("e2e4"))
    selected = loaded.tree.add_move(chess.Move.from_uci("e7e5"))
    service.save_repertoire_tree(loaded.id, loaded.tree, selected)

    restored = service.load_last_repertoire()

    assert restored is not None
    assert restored.name == "White repertoire"
    assert restored.selected_node.san == "e5"
    assert restored.tree.root.children[0].san == "e4"
    assert restored.tree.root.children[0].children[0].san == "e5"
    service.close()


def test_repertoire_names_are_made_unique(tmp_path):
    service = PersistenceService(Database(tmp_path / "mainline.sqlite3"))

    first = service.create_repertoire("Black repertoire")
    second = service.create_repertoire("Black repertoire")

    assert first.name == "Black repertoire"
    assert second.name == "Black repertoire (2)"
    service.close()
