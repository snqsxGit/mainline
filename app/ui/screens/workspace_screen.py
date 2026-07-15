"""Main opening editing workspace screen."""

from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QCheckBox, QFrame, QHBoxLayout, QLabel, QPushButton, QSplitter, QVBoxLayout, QWidget

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
        self._repertoire_name = "Selected repertoire"
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        self._header = QLabel(f"Workspace · {self._repertoire_name}")
        self._header.setObjectName("screen_heading")
        root.addWidget(self._header)

        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setObjectName("workspace_splitter")
        main_splitter.setChildrenCollapsible(False)

        board_region = QFrame()
        board_region.setObjectName("board_region")
        board_layout = QVBoxLayout(board_region)
        board_layout.setContentsMargins(4, 4, 4, 4)
        board_layout.setSpacing(0)
        board_layout.addWidget(self._board, 1, Qt.AlignmentFlag.AlignCenter)

        side_splitter = QSplitter(Qt.Orientation.Vertical)
        side_splitter.setObjectName("workspace_side_splitter")
        side_splitter.setChildrenCollapsible(False)
        side_splitter.addWidget(PlaceholderPanel("Engine analysis\nFuture evaluation lines"))
        side_splitter.addWidget(PlaceholderPanel("Move / variation tree\nFuture repertoire editor"))
        side_splitter.setSizes([260, 360])

        main_splitter.addWidget(board_region)
        main_splitter.addWidget(side_splitter)
        main_splitter.setStretchFactor(0, 5)
        main_splitter.setStretchFactor(1, 2)
        main_splitter.setSizes([1040, 300])
        root.addWidget(main_splitter, 1)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        back_button = QPushButton("Back to Home")
        drill_button = QPushButton("Start Drill")
        flip_button = QPushButton("Flip Board")
        notation_toggle = QCheckBox("Show notation")
        notation_toggle.setChecked(self._board.coordinates_visible)
        back_button.clicked.connect(self.backHomeRequested.emit)
        drill_button.clicked.connect(self.startDrillRequested.emit)
        flip_button.clicked.connect(self._board.flip_orientation)
        notation_toggle.toggled.connect(self._board.set_coordinates_visible)
        self._board.coordinateVisibilityChanged.connect(notation_toggle.setChecked)
        actions.addWidget(back_button)
        actions.addWidget(drill_button)
        actions.addStretch(1)
        actions.addWidget(notation_toggle)
        actions.addWidget(flip_button)
        root.addLayout(actions)

    def set_repertoire_name(self, name: str) -> None:
        """Update the workspace heading for the selected repertoire."""
        cleaned_name = name.strip() or "Selected repertoire"
        self._repertoire_name = cleaned_name
        self._header.setText(f"Workspace · {self._repertoire_name}")

    @property
    def board(self) -> ChessBoardWidget:
        """Expose the reusable board for future workspace controllers."""
        return self._board
