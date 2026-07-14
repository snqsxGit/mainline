"""Main opening editing workspace screen."""

from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSplitter, QVBoxLayout, QWidget

from app.ui.board import ChessBoardWidget
from app.ui.widgets.placeholder_panel import PlaceholderPanel


class WorkspaceScreen(QWidget):
    """Default repertoire workspace layout prepared for future docking panels."""

    backHomeRequested = Signal()
    startDrillRequested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """Create the workspace with board, analysis, tree, and action regions."""
        super().__init__(parent)
        self.setObjectName("workspace_screen")
        self._board = ChessBoardWidget()
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        header = QLabel("Workspace · Selected repertoire")
        header.setObjectName("screen_heading")
        root.addWidget(header)

        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setObjectName("workspace_splitter")

        board_region = QFrame()
        board_region.setObjectName("board_region")
        board_layout = QVBoxLayout(board_region)
        board_layout.setContentsMargins(0, 0, 0, 0)
        board_layout.addWidget(self._board, 1, Qt.AlignmentFlag.AlignCenter)

        side_splitter = QSplitter(Qt.Orientation.Vertical)
        side_splitter.setObjectName("workspace_side_splitter")
        side_splitter.addWidget(PlaceholderPanel("Engine analysis\nFuture evaluation lines"))
        side_splitter.addWidget(PlaceholderPanel("Move / variation tree\nFuture repertoire editor"))
        side_splitter.setSizes([320, 360])

        main_splitter.addWidget(board_region)
        main_splitter.addWidget(side_splitter)
        main_splitter.setStretchFactor(0, 3)
        main_splitter.setStretchFactor(1, 1)
        main_splitter.setSizes([920, 380])
        root.addWidget(main_splitter, 1)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        back_button = QPushButton("Back to Home")
        drill_button = QPushButton("Start Drill")
        flip_button = QPushButton("Flip Board")
        back_button.clicked.connect(self.backHomeRequested.emit)
        drill_button.clicked.connect(self.startDrillRequested.emit)
        flip_button.clicked.connect(self._board.flip_orientation)
        actions.addWidget(back_button)
        actions.addWidget(drill_button)
        actions.addStretch(1)
        actions.addWidget(flip_button)
        root.addLayout(actions)

    @property
    def board(self) -> ChessBoardWidget:
        """Expose the reusable board for future workspace controllers."""
        return self._board
