"""Programmatically rendered chessboard widget."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QPoint, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QFont, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from app.ui.board.models import BoardOrientation, BoardTheme


@dataclass(frozen=True)
class BoardLayout:
    """Calculated rectangles and dimensions for one paint pass."""

    outer_rect: QRectF
    squares_rect: QRectF
    square_size: float
    coordinate_margin: float


class ChessBoardWidget(QWidget):
    """Reusable square chessboard view with orientation and coordinates.

    The widget currently renders only the board foundation. It deliberately
    separates configuration, geometry calculation, and paint phases so future
    piece, highlight, arrow, animation, and drag layers can be added without
    changing the public board API.
    """

    BOARD_SIZE = 8
    FILES = tuple("abcdefgh")
    RANKS = tuple(str(rank) for rank in range(1, 9))

    orientationChanged = Signal(BoardOrientation)
    themeChanged = Signal(BoardTheme)

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        orientation: BoardOrientation = BoardOrientation.WHITE_AT_BOTTOM,
        theme: BoardTheme | None = None,
    ) -> None:
        """Create a chessboard widget."""
        super().__init__(parent)
        self._orientation = orientation
        self._theme = theme or BoardTheme()

        self.setObjectName("chess_board_widget")
        self.setMinimumSize(280, 280)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    @property
    def orientation(self) -> BoardOrientation:
        """Return the current visual board orientation."""
        return self._orientation

    def set_orientation(self, orientation: BoardOrientation) -> None:
        """Set whether white or black is displayed at the bottom."""
        if self._orientation == orientation:
            return
        self._orientation = orientation
        self.orientationChanged.emit(orientation)
        self.update()

    def flip_orientation(self) -> None:
        """Swap between white-at-bottom and black-at-bottom orientation."""
        self.set_orientation(self._orientation.flipped())

    @property
    def theme(self) -> BoardTheme:
        """Return the current board theme."""
        return self._theme

    def set_theme(self, theme: BoardTheme) -> None:
        """Replace the board theme and repaint."""
        if self._theme == theme:
            return
        self._theme = theme
        self.themeChanged.emit(theme)
        self.updateGeometry()
        self.update()

    def sizeHint(self) -> QSize:  # noqa: N802 - Qt override
        """Suggest a comfortable square default size."""
        return QSize(640, 640)

    def minimumSizeHint(self) -> QSize:  # noqa: N802 - Qt override
        """Suggest the smallest practical board size."""
        return QSize(280, 280)

    def hasHeightForWidth(self) -> bool:  # noqa: N802 - Qt override
        """Tell Qt layouts that the preferred widget shape is square."""
        return True

    def heightForWidth(self, width: int) -> int:  # noqa: N802 - Qt override
        """Keep the preferred height equal to the width."""
        return width

    def square_at(self, point: QPoint) -> tuple[int, int] | None:
        """Return the logical ``(file_index, rank_index)`` for a widget point.

        Indices are zero-based from White's perspective: ``(0, 0)`` is a1 and
        ``(7, 7)`` is h8. ``None`` is returned for points outside the playable
        8×8 square area. This is a future-friendly hook for selection and drag
        handling without introducing chess rules now.
        """
        layout = self._calculate_layout()
        if not layout.squares_rect.contains(point):
            return None

        file_display = int((point.x() - layout.squares_rect.left()) / layout.square_size)
        rank_display = int((point.y() - layout.squares_rect.top()) / layout.square_size)
        file_display = max(0, min(self.BOARD_SIZE - 1, file_display))
        rank_display = max(0, min(self.BOARD_SIZE - 1, rank_display))

        if self._orientation is BoardOrientation.WHITE_AT_BOTTOM:
            return file_display, self.BOARD_SIZE - 1 - rank_display
        return self.BOARD_SIZE - 1 - file_display, rank_display

    def paintEvent(self, event) -> None:  # noqa: N802, ANN001 - Qt override
        """Render the complete board using Qt painting."""
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        layout = self._calculate_layout()
        self._paint_background(painter, layout)
        self._paint_squares(painter, layout)
        self._paint_coordinates(painter, layout)
        self._paint_border(painter, layout)

    def _calculate_layout(self) -> BoardLayout:
        """Calculate a centered square board layout for the current widget size."""
        side = float(min(self.width(), self.height()))
        x = (self.width() - side) / 2.0
        y = (self.height() - side) / 2.0

        outer_margin = side * self._theme.outer_margin_ratio
        available_side = max(0.0, side - (outer_margin * 2.0))
        coordinate_margin = max(
            float(self._theme.minimum_coordinate_margin),
            available_side * self._theme.coordinate_margin_ratio,
        )
        coordinate_margin = min(coordinate_margin, available_side * 0.18)
        squares_side = max(0.0, available_side - (coordinate_margin * 2.0))

        outer_rect = QRectF(x + outer_margin, y + outer_margin, available_side, available_side)
        squares_rect = QRectF(
            outer_rect.left() + coordinate_margin,
            outer_rect.top() + coordinate_margin,
            squares_side,
            squares_side,
        )
        return BoardLayout(
            outer_rect=outer_rect,
            squares_rect=squares_rect,
            square_size=squares_side / self.BOARD_SIZE if squares_side else 0.0,
            coordinate_margin=coordinate_margin,
        )

    def _paint_background(self, painter: QPainter, layout: BoardLayout) -> None:
        painter.fillRect(layout.outer_rect, self._theme.border_background)

    def _paint_squares(self, painter: QPainter, layout: BoardLayout) -> None:
        for display_rank in range(self.BOARD_SIZE):
            for display_file in range(self.BOARD_SIZE):
                square_rect = QRectF(
                    layout.squares_rect.left() + (display_file * layout.square_size),
                    layout.squares_rect.top() + (display_rank * layout.square_size),
                    layout.square_size,
                    layout.square_size,
                )
                is_light = (display_file + display_rank) % 2 == 0
                color = self._theme.light_square if is_light else self._theme.dark_square
                painter.fillRect(square_rect, color)

    def _paint_coordinates(self, painter: QPainter, layout: BoardLayout) -> None:
        font = QFont(self._theme.coordinate_font)
        font.setPixelSize(max(10, int(layout.coordinate_margin * 0.48)))
        painter.setFont(font)
        painter.setPen(QPen(self._theme.coordinate_text))

        files = self._display_files()
        ranks = self._display_ranks()
        for index, file_label in enumerate(files):
            x = layout.squares_rect.left() + (index * layout.square_size)
            label_rect = QRectF(
                x,
                layout.squares_rect.bottom(),
                layout.square_size,
                layout.coordinate_margin,
            )
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, file_label)

        for index, rank_label in enumerate(ranks):
            y = layout.squares_rect.top() + (index * layout.square_size)
            label_rect = QRectF(
                layout.outer_rect.left(),
                y,
                layout.coordinate_margin,
                layout.square_size,
            )
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, rank_label)

    def _paint_border(self, painter: QPainter, layout: BoardLayout) -> None:
        pen = QPen(self._theme.border)
        pen.setWidthF(max(1.0, layout.outer_rect.width() * 0.004))
        painter.setPen(pen)
        painter.drawRect(layout.outer_rect)
        painter.drawRect(layout.squares_rect)

    def _display_files(self) -> tuple[str, ...]:
        if self._orientation is BoardOrientation.WHITE_AT_BOTTOM:
            return self.FILES
        return tuple(reversed(self.FILES))

    def _display_ranks(self) -> tuple[str, ...]:
        if self._orientation is BoardOrientation.WHITE_AT_BOTTOM:
            return tuple(reversed(self.RANKS))
        return self.RANKS
