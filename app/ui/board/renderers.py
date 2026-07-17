"""Rendering helpers for board squares, highlights, and piece images."""

from __future__ import annotations

from pathlib import Path

import chess
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainter, QPainterPath, QPixmap

from app.ui.board.models import BoardTheme


class BoardRenderer:
    """Paint board squares and interaction highlights."""

    def __init__(self, theme: BoardTheme) -> None:
        self._theme = theme

    def set_theme(self, theme: BoardTheme) -> None:
        """Update theme colors used for square painting."""
        self._theme = theme

    def rounded_path(self, rect: QRectF) -> QPainterPath:
        """Return the rounded board clipping path for ``rect``."""
        radius = rect.width() * self._theme.corner_radius_ratio
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        return path

    def paint_squares(self, painter: QPainter, square_rects: list[list[QRectF]], clip_rect: QRectF) -> None:
        """Paint all checkerboard squares from display-space rectangles."""
        painter.save()
        painter.setClipPath(self.rounded_path(clip_rect))
        for display_rank, row in enumerate(square_rects):
            for display_file, square_rect in enumerate(row):
                is_light = (display_file + display_rank) % 2 == 0
                painter.fillRect(square_rect, self._theme.light_square if is_light else self._theme.dark_square)
        painter.restore()

    def paint_overlay(self, painter: QPainter, rect: QRectF | None, color) -> None:
        """Paint a square overlay when a target rectangle exists."""
        if rect is not None:
            painter.fillRect(rect, color)

    def paint_destinations(self, painter: QPainter, rects: list[QRectF]) -> None:
        """Paint refined legal-destination dots and capture rings."""
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._theme.destination_color)
        for rect in rects:
            radius = rect.width() * 0.145
            painter.drawEllipse(rect.center(), radius, radius)


class PieceRenderer:
    """Load and draw chess piece PNG assets independently of chess rules."""

    def __init__(self, pieces_path: Path | None = None) -> None:
        self._pieces_path = pieces_path or Path(__file__).resolve().parents[2] / "resources" / "pieces" / "chesscom"
        self._pixmaps: dict[str, QPixmap] = {}
        self._load_pixmaps()

    def draw_piece(self, painter: QPainter, piece: chess.Piece, rect: QRectF, *, opacity: float = 1.0) -> None:
        """Draw ``piece`` scaled to ``rect`` while preserving smooth edges."""
        pixmap = self._pixmaps.get(self._asset_key(piece))
        if pixmap is None or pixmap.isNull():
            return
        painter.save()
        painter.setOpacity(opacity)
        padding = rect.width() * 0.035
        target = rect.adjusted(padding, padding, -padding, -padding)
        painter.drawPixmap(target, pixmap, pixmap.rect())
        painter.restore()

    def _load_pixmaps(self) -> None:
        for color_prefix in ("w", "b"):
            for piece_code in ("k", "q", "r", "b", "n", "p"):
                key = f"{color_prefix}{piece_code}"
                self._pixmaps[key] = QPixmap(str(self._pieces_path / f"{key}.png"))

    def _asset_key(self, piece: chess.Piece) -> str:
        color_prefix = "w" if piece.color == chess.WHITE else "b"
        return f"{color_prefix}{piece.symbol().lower()}"
