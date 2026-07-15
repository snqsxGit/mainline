"""Thin python-chess backed controller for board state and legal moves."""

from __future__ import annotations

import chess


class ChessController:
    """Own chess state while delegating all rules to :mod:`python-chess`."""

    def __init__(self, fen: str | None = None) -> None:
        """Create a controller at the standard starting position or ``fen``."""
        self._board = chess.Board(fen) if fen else chess.Board()

    @property
    def board(self) -> chess.Board:
        """Return the mutable python-chess board used as the rule engine."""
        return self._board

    def piece_at(self, square: chess.Square) -> chess.Piece | None:
        """Return the piece on ``square``, if any."""
        return self._board.piece_at(square)

    def legal_destinations_from(self, square: chess.Square) -> set[chess.Square]:
        """Return legal target squares for the piece on ``square``."""
        return {move.to_square for move in self._board.legal_moves if move.from_square == square}

    def has_selectable_piece(self, square: chess.Square) -> bool:
        """Return whether ``square`` contains the side-to-move's piece."""
        piece = self.piece_at(square)
        return piece is not None and piece.color == self._board.turn

    def legal_move_between(self, from_square: chess.Square, to_square: chess.Square) -> chess.Move | None:
        """Return a legal move between squares, including simple promotion handling."""
        candidates = [move for move in self._board.legal_moves if move.from_square == from_square and move.to_square == to_square]
        if not candidates:
            return None
        queen_promotions = [move for move in candidates if move.promotion == chess.QUEEN]
        return queen_promotions[0] if queen_promotions else candidates[0]

    def push(self, move: chess.Move) -> None:
        """Execute ``move`` through python-chess validation."""
        self._board.push(move)

    def reset(self) -> None:
        """Reset to the initial chess position."""
        self._board.reset()

    def set_fen(self, fen: str) -> None:
        """Replace board state from FEN."""
        self._board.set_fen(fen)
