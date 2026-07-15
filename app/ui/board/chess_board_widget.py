"""Interactive chessboard widget rendered with Qt and python-chess state."""

from __future__ import annotations

from dataclasses import dataclass

import chess
from PySide6.QtCore import QPoint, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from app.chess import ChessController
from app.ui.board.models import BoardOrientation, BoardTheme, CoordinateStyle
from app.ui.board.renderers import BoardRenderer, PieceRenderer


@dataclass(frozen=True)
class BoardLayout:
    """Calculated rectangles and dimensions for one paint pass."""

    outer_rect: QRectF
    squares_rect: QRectF
    square_size: float


class ChessBoardWidget(QWidget):
    """Reusable square chessboard view with pieces and click-to-move play."""

    BOARD_SIZE = 8
    FILES = tuple("abcdefgh")
    RANKS = tuple(str(rank) for rank in range(1, 9))

    orientationChanged = Signal(BoardOrientation)
    themeChanged = Signal(BoardTheme)
    coordinateVisibilityChanged = Signal(bool)
    coordinateStyleChanged = Signal(CoordinateStyle)
    positionChanged = Signal(str)

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        orientation: BoardOrientation = BoardOrientation.WHITE_AT_BOTTOM,
        theme: BoardTheme | None = None,
        controller: ChessController | None = None,
    ) -> None:
        """Create an interactive chessboard widget."""
        super().__init__(parent)
        self._orientation = orientation
        self._theme = theme or BoardTheme()
        self._coordinates_visible = True
        self._coordinate_style = self._theme.coordinate_style
        self._controller = controller or ChessController()
        self._selected_square: chess.Square | None = None
        self._legal_destinations: set[chess.Square] = set()
        self._board_renderer = BoardRenderer(self._theme)
        self._piece_renderer = PieceRenderer()

        self.setObjectName("chess_board_widget")
        self.setMinimumSize(280, 280)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    @property
    def controller(self) -> ChessController:
        """Return the python-chess-backed board controller."""
        return self._controller

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
        self._board_renderer.set_theme(theme)
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
        return QSize(720, 720)

    def minimumSizeHint(self) -> QSize:  # noqa: N802 - Qt override
        """Suggest the smallest practical board size."""
        return QSize(280, 280)

    def hasHeightForWidth(self) -> bool:  # noqa: N802 - Qt override
        """Tell Qt layouts that the preferred widget shape is square."""
        return True

    def heightForWidth(self, width: int) -> int:  # noqa: N802 - Qt override
        """Keep the preferred height equal to the width."""
        return width

    def square_at(self, point: QPoint) -> chess.Square | None:
        """Return the python-chess square for a widget point, respecting orientation."""
        layout = self._calculate_layout()
        if layout.square_size <= 0 or not layout.squares_rect.contains(point):
            return None

        file_display = int((point.x() - layout.squares_rect.left()) / layout.square_size)
        rank_display = int((point.y() - layout.squares_rect.top()) / layout.square_size)
        file_display = max(0, min(self.BOARD_SIZE - 1, file_display))
        rank_display = max(0, min(self.BOARD_SIZE - 1, rank_display))
        return self._display_to_square(file_display, rank_display)

    def mousePressEvent(self, event) -> None:  # noqa: N802, ANN001 - Qt override
        """Handle click-to-select and click-to-move interaction."""
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return
        square = self.square_at(event.position().toPoint())
        if square is None:
            self._clear_selection()
            return
        self._handle_square_click(square)

    def paintEvent(self, event) -> None:  # noqa: N802, ANN001 - Qt override
        """Render the complete board using Qt painting."""
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        layout = self._calculate_layout()
        rects = self._display_square_rects(layout)
        self._paint_background(painter, layout)
        self._board_renderer.paint_squares(painter, rects)
        self._paint_highlights(painter, layout)
        self._paint_pieces(painter, layout)
        self._paint_coordinates(painter, layout)
        self._paint_border(painter, layout)

    def _handle_square_click(self, square: chess.Square) -> None:
        if self._selected_square is None:
            if self._controller.has_selectable_piece(square):
                self._select_square(square)
            return

        if self._controller.has_selectable_piece(square):
            self._select_square(square)
            return

        if square in self._legal_destinations:
            move = self._controller.legal_move_between(self._selected_square, square)
            if move is not None:
                self._controller.push(move)
                self.positionChanged.emit(self._controller.board.fen())
                self._clear_selection()
                return

        if self._controller.piece_at(square) is None:
            self._clear_selection()

    def _select_square(self, square: chess.Square) -> None:
        self._selected_square = square
        self._legal_destinations = self._controller.legal_destinations_from(square)
        self.update()

    def _clear_selection(self) -> None:
        if self._selected_square is None and not self._legal_destinations:
            return
        self._selected_square = None
        self._legal_destinations = set()
        self.update()

    def _calculate_layout(self) -> BoardLayout:
        side = float(min(self.width(), self.height()))
        x = (self.width() - side) / 2.0
        y = (self.height() - side) / 2.0
        outer_margin = side * self._theme.outer_margin_ratio
        available_side = max(0.0, side - (outer_margin * 2.0))
        outer_rect = QRectF(x + outer_margin, y + outer_margin, available_side, available_side)
        return BoardLayout(
            outer_rect=outer_rect,
            squares_rect=QRectF(outer_rect),
            square_size=available_side / self.BOARD_SIZE if available_side else 0.0,
        )

    def _display_square_rects(self, layout: BoardLayout) -> list[list[QRectF]]:
        return [
            [
                QRectF(
                    layout.squares_rect.left() + file * layout.square_size,
                    layout.squares_rect.top() + rank * layout.square_size,
                    layout.square_size,
                    layout.square_size,
                )
                for file in range(self.BOARD_SIZE)
            ]
            for rank in range(self.BOARD_SIZE)
        ]

    def _paint_background(self, painter: QPainter, layout: BoardLayout) -> None:
        painter.fillRect(layout.outer_rect, self._theme.border_background)

    def _paint_highlights(self, painter: QPainter, layout: BoardLayout) -> None:
        selected_rect = self._square_rect(layout, self._selected_square) if self._selected_square is not None else None
        self._board_renderer.paint_selection(painter, selected_rect)
        self._board_renderer.paint_destinations(
            painter,
            [self._square_rect(layout, square) for square in self._legal_destinations],
        )

    def _paint_pieces(self, painter: QPainter, layout: BoardLayout) -> None:
        for square, piece in self._controller.board.piece_map().items():
            self._piece_renderer.draw_piece(painter, piece, self._square_rect(layout, square))

    def _square_rect(self, layout: BoardLayout, square: chess.Square) -> QRectF:
        display_file, display_rank = self._square_to_display(square)
        return QRectF(
            layout.squares_rect.left() + display_file * layout.square_size,
            layout.squares_rect.top() + display_rank * layout.square_size,
            layout.square_size,
            layout.square_size,
        )

    def _display_to_square(self, display_file: int, display_rank: int) -> chess.Square:
        if self._orientation is BoardOrientation.WHITE_AT_BOTTOM:
            file_index = display_file
            rank_index = self.BOARD_SIZE - 1 - display_rank
        else:
            file_index = self.BOARD_SIZE - 1 - display_file
            rank_index = display_rank
        return chess.square(file_index, rank_index)

    def _square_to_display(self, square: chess.Square) -> tuple[int, int]:
        file_index = chess.square_file(square)
        rank_index = chess.square_rank(square)
        if self._orientation is BoardOrientation.WHITE_AT_BOTTOM:
            return file_index, self.BOARD_SIZE - 1 - rank_index
        return self.BOARD_SIZE - 1 - file_index, rank_index

    def _paint_coordinates(self, painter: QPainter, layout: BoardLayout) -> None:
        if not self._coordinates_visible or layout.square_size <= 0:
            return
        style = self._coordinate_style
        font = QFont(style.font)
        font.setPixelSize(max(9, int(layout.square_size * 0.16)))
        painter.setFont(font)
        inset = max(3.0, layout.square_size * style.edge_inset_ratio)
        for index, file_label in enumerate(self._display_files()):
            x = layout.squares_rect.left() + (index * layout.square_size)
            y = layout.squares_rect.bottom() - layout.square_size
            label_rect = QRectF(
                x + inset,
                y + layout.square_size - (layout.square_size * 0.32) - inset,
                layout.square_size - (inset * 2.0),
                layout.square_size * 0.32,
            )
            painter.setPen(QPen(self._coordinate_color((index + (self.BOARD_SIZE - 1)) % 2 == 0)))
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, file_label)
        for index, rank_label in enumerate(self._display_ranks()):
            x = layout.squares_rect.left()
            y = layout.squares_rect.top() + (index * layout.square_size)
            label_rect = QRectF(
                x + inset,
                y + inset,
                layout.square_size * 0.34,
                layout.square_size * 0.30,
            )
            painter.setPen(QPen(self._coordinate_color(index % 2 == 0)))
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
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(layout.outer_rect)
        painter.drawRect(layout.squares_rect)

    def _display_files(self) -> tuple[str, ...]:
        return self.FILES if self._orientation is BoardOrientation.WHITE_AT_BOTTOM else tuple(reversed(self.FILES))

    def _display_ranks(self) -> tuple[str, ...]:
        return tuple(reversed(self.RANKS)) if self._orientation is BoardOrientation.WHITE_AT_BOTTOM else self.RANKS
