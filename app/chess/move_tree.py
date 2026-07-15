"""UI-independent chess opening variation tree."""

from __future__ import annotations

from dataclasses import dataclass, field

import chess


@dataclass
class MoveTreeNode:
    """One position in an opening tree, reached by an optional played move."""

    fen: str
    parent: "MoveTreeNode | None" = None
    move: chess.Move | None = None
    san: str = ""
    move_number: int = 1
    children: list["MoveTreeNode"] = field(default_factory=list)
    comments: list[str] = field(default_factory=list)
    nags: set[int] = field(default_factory=set)
    metadata: dict[str, object] = field(default_factory=dict)

    @property
    def is_root(self) -> bool:
        """Return whether this node is the tree root."""
        return self.parent is None

    @property
    def ply(self) -> int:
        """Return the half-move depth from the root."""
        depth = 0
        node = self
        while node.parent is not None:
            depth += 1
            node = node.parent
        return depth

    def child_for_move(self, move: chess.Move) -> "MoveTreeNode | None":
        """Return the existing child reached by ``move``, if present."""
        for child in self.children:
            if child.move == move:
                return child
        return None


class MoveTreeModel:
    """Opening variation tree backed by python-chess positions and moves."""

    def __init__(self, starting_fen: str | None = None) -> None:
        """Create a tree rooted at the standard start position or ``starting_fen``."""
        board = chess.Board(starting_fen) if starting_fen else chess.Board()
        self.root = MoveTreeNode(fen=board.fen(), move_number=board.fullmove_number)
        self.current_node = self.root

    def add_move(self, move: chess.Move) -> MoveTreeNode:
        """Add or select the child produced by playing ``move`` from the current node."""
        board = chess.Board(self.current_node.fen)
        if move not in board.legal_moves:
            raise ValueError(f"Illegal move for current position: {move.uci()}")

        existing = self.current_node.child_for_move(move)
        if existing is not None:
            self.current_node = existing
            return existing

        san = board.san(move)
        move_number = board.fullmove_number
        board.push(move)
        node = MoveTreeNode(
            parent=self.current_node,
            children=[],
            move=move,
            san=san,
            fen=board.fen(),
            move_number=move_number,
        )
        self.current_node.children.append(node)
        self.current_node = node
        return node

    def select_node(self, node: MoveTreeNode) -> MoveTreeNode:
        """Make ``node`` current and return it."""
        self.current_node = node
        return node

    def first(self) -> MoveTreeNode:
        """Navigate to the root position."""
        return self.select_node(self.root)

    def previous(self) -> MoveTreeNode:
        """Navigate to the parent position when possible."""
        if self.current_node.parent is not None:
            self.current_node = self.current_node.parent
        return self.current_node

    def next(self) -> MoveTreeNode:
        """Navigate to the main child variation when possible."""
        if self.current_node.children:
            self.current_node = self.current_node.children[0]
        return self.current_node

    def end(self) -> MoveTreeNode:
        """Navigate to the end of the current main line."""
        while self.current_node.children:
            self.current_node = self.current_node.children[0]
        return self.current_node

    def previous_variation(self) -> MoveTreeNode:
        """Select the previous sibling variation when one exists."""
        parent = self.current_node.parent
        if parent is None:
            return self.current_node
        index = parent.children.index(self.current_node)
        if index > 0:
            self.current_node = parent.children[index - 1]
        return self.current_node

    def next_variation(self) -> MoveTreeNode:
        """Select the next sibling variation when one exists."""
        parent = self.current_node.parent
        if parent is None:
            return self.current_node
        index = parent.children.index(self.current_node)
        if index < len(parent.children) - 1:
            self.current_node = parent.children[index + 1]
        return self.current_node
