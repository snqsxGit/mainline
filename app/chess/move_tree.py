"""UI-independent chess opening variation tree."""

from __future__ import annotations

from dataclasses import dataclass, field
from io import StringIO

import chess
import chess.pgn


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

    def promote_to_mainline(self, node: MoveTreeNode | None = None) -> MoveTreeNode:
        """Move ``node`` to the first child slot under its parent."""
        node = node or self.current_node
        parent = node.parent
        if parent is None or parent.children[0] is node:
            return node
        parent.children.remove(node)
        parent.children.insert(0, node)
        self.current_node = node
        return node

    def delete_node(self, node: MoveTreeNode | None = None) -> MoveTreeNode:
        """Delete ``node`` and its descendants, selecting the parent position."""
        node = node or self.current_node
        parent = node.parent
        if parent is None:
            return node
        parent.children.remove(node)
        self.current_node = parent
        return parent

    def node_count(self) -> int:
        """Return the number of positions in the tree, including the root."""
        count = 0
        stack = [self.root]
        while stack:
            current = stack.pop()
            count += 1
            stack.extend(current.children)
        return count

    def to_pgn(self) -> str:
        """Serialize the full tree, including variations and comments, as PGN."""
        game = chess.pgn.Game()
        game.headers["Event"] = "Mainline repertoire"
        game.setup(chess.Board(self.root.fen))

        def copy_children(source: MoveTreeNode, target: chess.pgn.GameNode) -> None:
            for child in source.children:
                variation = target.add_variation(child.move) if child.move else target
                variation.comment = "\n".join(child.comments)
                for nag in child.nags:
                    variation.nags.add(nag)
                copy_children(child, variation)

        copy_children(self.root, game)
        exporter = chess.pgn.StringExporter(headers=True, variations=True, comments=True)
        return game.accept(exporter)

    @classmethod
    def from_pgn(cls, pgn_text: str) -> "MoveTreeModel":
        """Create a move tree from the first game in ``pgn_text`` using python-chess."""
        game = chess.pgn.read_game(StringIO(pgn_text))
        if game is None:
            raise ValueError("No PGN game found")
        board = game.board()
        tree = cls(board.fen())

        def import_children(pgn_node: chess.pgn.GameNode, tree_node: MoveTreeNode, board: chess.Board) -> None:
            for variation in pgn_node.variations:
                move = variation.move
                san = board.san(move)
                move_number = board.fullmove_number
                next_board = board.copy(stack=False)
                next_board.push(move)
                child = MoveTreeNode(
                    fen=next_board.fen(),
                    parent=tree_node,
                    move=move,
                    san=san,
                    move_number=move_number,
                    comments=[variation.comment] if variation.comment else [],
                    nags=set(variation.nags),
                )
                tree_node.children.append(child)
                import_children(variation, child, next_board)

        import_children(game, tree.root, board)
        tree.current_node = tree.root
        return tree
