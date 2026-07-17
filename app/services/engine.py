"""Lightweight Stockfish service boundary."""

from __future__ import annotations

from dataclasses import dataclass

import chess
import chess.engine


@dataclass(frozen=True)
class EngineAnalysis:
    """Small UI-safe analysis result."""

    evaluation: str
    best_move: str
    depth: int | None = None
    pv: str = ""


class EngineService:
    """Manage one optional Stockfish process behind a simple API."""

    def __init__(self, path: str = "stockfish") -> None:
        self.path = path
        self._engine: chess.engine.SimpleEngine | None = None

    @property
    def is_running(self) -> bool:
        return self._engine is not None

    def start(self) -> None:
        if self._engine is None:
            self._engine = chess.engine.SimpleEngine.popen_uci(self.path)

    def stop(self) -> None:
        if self._engine is not None:
            self._engine.quit()
            self._engine = None

    def analyse(self, fen: str, *, depth: int = 10) -> EngineAnalysis:
        self.start()
        assert self._engine is not None
        board = chess.Board(fen)
        result = self._engine.analyse(board, chess.engine.Limit(depth=depth))
        score = result.get("score")
        pov = score.pov(board.turn) if score else None
        evaluation = str(pov) if pov is not None else "—"
        pv_moves = result.get("pv", [])
        best_move = board.san(pv_moves[0]) if pv_moves else "—"
        pv = " ".join(move.uci() for move in pv_moves[:6])
        return EngineAnalysis(evaluation=evaluation, best_move=best_move, depth=result.get("depth"), pv=pv)
