import chess
import pytest

from app.chess.move_tree import MoveTreeModel


def test_add_move_creates_nodes_and_reuses_existing_child():
    model = MoveTreeModel()
    e4 = chess.Move.from_uci("e2e4")

    first = model.add_move(e4)
    model.first()
    second = model.add_move(e4)

    assert first is second
    assert len(model.root.children) == 1
    assert model.current_node.san == "e4"


def test_older_position_move_creates_variation_without_overwriting_main_line():
    model = MoveTreeModel()
    e4 = model.add_move(chess.Move.from_uci("e2e4"))
    model.add_move(chess.Move.from_uci("e7e5"))

    model.select_node(e4)
    c5 = model.add_move(chess.Move.from_uci("c7c5"))

    assert [child.san for child in e4.children] == ["e5", "c5"]
    assert model.current_node is c5


def test_navigation_tracks_main_line_and_sibling_variations():
    model = MoveTreeModel()
    e4 = model.add_move(chess.Move.from_uci("e2e4"))
    e5 = model.add_move(chess.Move.from_uci("e7e5"))
    model.select_node(e4)
    c5 = model.add_move(chess.Move.from_uci("c7c5"))

    assert model.previous_variation() is e5
    assert model.next_variation() is c5
    assert model.first() is model.root
    assert model.next() is e4
    assert model.end() is e5


def test_illegal_move_is_rejected():
    model = MoveTreeModel()

    with pytest.raises(ValueError):
        model.add_move(chess.Move.from_uci("e7e5"))
