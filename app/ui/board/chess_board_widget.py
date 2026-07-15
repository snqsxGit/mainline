"""Programmatically rendered chessboard widget."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QPoint, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from app.ui.board.models import BoardOrientation, BoardTheme, CoordinateStyle


@dataclass(frozen=True)
class BoardLayout:
    """Calculated rectangles and dimensions for one paint pass."""

    outer_rect: QRectF
    squares_rect: QRectF
    square_size: float


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
    coordinateVisibilityChanged = Signal(bool)
    coordinateStyleChanged = Signal(CoordinateStyle)

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
        self._coordinates_visible = True
        self._coordinate_style = self._theme.coordinate_style

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
        self._coordinate_style = theme.coordinate_style
        self.themeChanged.emit(theme)
        self.updateGeometry()
        self.update()

    @property
    def coordinates_visible(self) -> bool:
        """Return whether file/rank notation is painted on the board."""
        return self._coordinates_visible

    def set_coordinates_visible(self, visible: bool) -> None:
        """Show or hide subtle in-board coordinate notation."""
        if self._coordinates_visible == visible:
            return
        self._coordinates_visible = visible
        self.coordinateVisibilityChanged.emit(visible)
        self.update()

    def toggle_coordinates(self) -> None:
        """Toggle board coordinate notation visibility."""
        self.set_coordinates_visible(not self._coordinates_visible)

    @property
    def coordinate_style(self) -> CoordinateStyle:
        """Return the current coordinate overlay style."""
        return self._coordinate_style

    def set_coordinate_style(self, style: CoordinateStyle) -> None:
        """Replace the coordinate overlay style without changing the theme."""
        if self._coordinate_style == style:
            return
        self._coordinate_style = style
        self.coordinateStyleChanged.emit(style)
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
        squares_side = max(0.0, available_side)

        outer_rect = QRectF(x + outer_margin, y + outer_margin, available_side, available_side)
        squares_rect = QRectF(outer_rect)
        return BoardLayout(
            outer_rect=outer_rect,
            squares_rect=squares_rect,
            square_size=squares_side / self.BOARD_SIZE if squares_side else 0.0,
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
        if not self._coordinates_visible or layout.square_size <= 0:
            return

        style = self._coordinate_style
        font = QFont(style.font)
        font.setPixelSize(max(9, int(layout.square_size * 0.16)))
        painter.setFont(font)

        files = self._display_files()
        ranks = self._display_ranks()
        inset = max(3.0, layout.square_size * style.edge_inset_ratio)

        for index, file_label in enumerate(files):
            x = layout.squares_rect.left() + (index * layout.square_size)
            y = layout.squares_rect.bottom() - layout.square_size
            label_rect = QRectF(
                x + inset,
                y + layout.square_size - (layout.square_size * 0.32) - inset,
                layout.square_size - (inset * 2.0),
                layout.square_size * 0.32,
            )
            square_is_light = (index + (self.BOARD_SIZE - 1)) % 2 == 0
            painter.setPen(QPen(self._coordinate_color(square_is_light)))
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, file_label)

        for index, rank_label in enumerate(ranks):
            x = layout.squares_rect.left()
            y = layout.squares_rect.top() + (index * layout.square_size)
            label_rect = QRectF(
                x + inset,
                y + inset,
                layout.square_size * 0.34,
                layout.square_size * 0.30,
            )
            square_is_light = index % 2 == 0
            painter.setPen(QPen(self._coordinate_color(square_is_light)))
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, rank_label)

    def _coordinate_color(self, square_is_light: bool) -> QColor:
        style = self._coordinate_style
        color = QColor(style.light_square_text if square_is_light else style.dark_square_text)
        color.setAlphaF(max(0.0, min(1.0, style.opacity)))
        return color

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
