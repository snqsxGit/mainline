"""Configuration models for chessboard rendering."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from PySide6.QtGui import QColor, QFont


class BoardOrientation(Enum):
    """Visual orientation of the board ranks and files."""

    WHITE_AT_BOTTOM = "white_at_bottom"
    BLACK_AT_BOTTOM = "black_at_bottom"

    def flipped(self) -> "BoardOrientation":
        """Return the opposite board orientation."""
        if self is BoardOrientation.WHITE_AT_BOTTOM:
            return BoardOrientation.BLACK_AT_BOTTOM
        return BoardOrientation.WHITE_AT_BOTTOM


@dataclass(frozen=True)
class CoordinateStyle:
    """Style values for in-board coordinate notation.

    Coordinates are painted as an overlay on the playable squares, so they do
    not affect board geometry. The opacity and edge inset keep labels readable
    without competing with future pieces, highlights, arrows, or engine marks.
    """

    light_square_text: QColor = field(default_factory=lambda: QColor("#5F7550"))
    dark_square_text: QColor = field(default_factory=lambda: QColor("#D7DFC0"))
    opacity: float = 0.72
    edge_inset_ratio: float = 0.11
    font: QFont = field(default_factory=lambda: QFont("Sans Serif", 9))


@dataclass(frozen=True)
class BoardTheme:
    """Visual configuration used by :class:`ChessBoardWidget`.

    The values are intentionally data-only so callers can replace the entire
    theme without subclassing the widget. Future overlays can reuse these
    colors or extend this model with their own style objects.
    """

    light_square: QColor = field(default_factory=lambda: QColor("#EEEED2"))
    dark_square: QColor = field(default_factory=lambda: QColor("#769656"))
    border: QColor = field(default_factory=lambda: QColor("#2F3437"))
    border_background: QColor = field(default_factory=lambda: QColor("#F4F1E8"))
    outer_margin_ratio: float = 0.008
    coordinate_style: CoordinateStyle = field(default_factory=CoordinateStyle)
