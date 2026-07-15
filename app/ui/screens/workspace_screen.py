"""Main opening editing workspace screen."""

from __future__ import annotations

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QCheckBox, QFrame, QHBoxLayout, QLabel, QPushButton, QSplitter, QToolButton, QVBoxLayout, QWidget

from app.chess import MoveTreeModel, MoveTreeNode
from app.ui.board import ChessBoardWidget
from app.ui.widgets import MoveTreeWidget, PlaceholderPanel


class WorkspaceScreen(QWidget):
    """Opening editor workspace that synchronizes board, tree, and navigation."""

    backHomeRequested = Signal()
    startDrillRequested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """Create the workspace with board, move tree, and editor actions."""
        super().__init__(parent)
        self.setObjectName("workspace_screen")
        self._board = ChessBoardWidget()
        self._move_tree_model = MoveTreeModel()
        self._move_tree = MoveTreeWidget()
        self._repertoire_name = "Selected repertoire"
        self._build_actions()
        self._build_ui()
        self._connect_synchronization()
        self._move_tree.set_model(self._move_tree_model)
        self._restore_node(self._move_tree_model.root)

    def _build_actions(self) -> None:
        self.first_action = QAction("⏮", self)
        self.first_action.setToolTip("Go to first position")
        self.first_action.setShortcut(QKeySequence(Qt.Key.Key_Home))
        self.first_action.triggered.connect(lambda: self._navigate_to(self._move_tree_model.first()))

        self.previous_action = QAction("◀", self)
        self.previous_action.setToolTip("Previous move")
        self.previous_action.setShortcut(QKeySequence(Qt.Key.Key_Left))
        self.previous_action.triggered.connect(lambda: self._navigate_to(self._move_tree_model.previous()))

        self.next_action = QAction("▶", self)
        self.next_action.setToolTip("Next move")
        self.next_action.setShortcut(QKeySequence(Qt.Key.Key_Right))
        self.next_action.triggered.connect(lambda: self._navigate_to(self._move_tree_model.next()))

        self.end_action = QAction("⏭", self)
        self.end_action.setToolTip("Go to end of current line")
        self.end_action.setShortcut(QKeySequence(Qt.Key.Key_End))
        self.end_action.triggered.connect(lambda: self._navigate_to(self._move_tree_model.end()))

        self.previous_variation_action = QAction("▲", self)
        self.previous_variation_action.setToolTip("Previous variation")
        self.previous_variation_action.setShortcut(QKeySequence(Qt.KeyboardModifier.ShiftModifier | Qt.Key.Key_Left))
        self.previous_variation_action.triggered.connect(lambda: self._navigate_to(self._move_tree_model.previous_variation()))

        self.next_variation_action = QAction("▼", self)
        self.next_variation_action.setToolTip("Next variation")
        self.next_variation_action.setShortcut(QKeySequence(Qt.KeyboardModifier.ShiftModifier | Qt.Key.Key_Right))
        self.next_variation_action.triggered.connect(lambda: self._navigate_to(self._move_tree_model.next_variation()))

        self.flip_action = QAction("Flip Board", self)
        self.flip_action.setShortcut(QKeySequence("F"))
        self.flip_action.triggered.connect(self._board.flip_orientation)

        self.fullscreen_action = QAction("Toggle Fullscreen", self)
        self.fullscreen_action.setShortcut(QKeySequence("F11"))
        self.fullscreen_action.triggered.connect(self._toggle_fullscreen)

        self.exit_fullscreen_action = QAction("Exit Fullscreen", self)
        self.exit_fullscreen_action.setShortcut(QKeySequence(Qt.Key.Key_Escape))
        self.exit_fullscreen_action.triggered.connect(self._exit_fullscreen)

        self.home_action = QAction("Return Home", self)
        self.home_action.setShortcut(QKeySequence("Ctrl+H"))
        self.home_action.triggered.connect(self.backHomeRequested.emit)

        self.drill_action = QAction("Start Drill", self)
        self.drill_action.setShortcut(QKeySequence("Ctrl+D"))
        self.drill_action.triggered.connect(self.startDrillRequested.emit)

        self.addActions([
            self.first_action, self.previous_action, self.next_action, self.end_action,
            self.previous_variation_action, self.next_variation_action, self.flip_action,
            self.fullscreen_action, self.exit_fullscreen_action, self.home_action, self.drill_action,
        ])

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        self._header = QLabel(f"Workspace · {self._repertoire_name}")
        self._header.setObjectName("screen_heading")
        root.addWidget(self._header)

        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setChildrenCollapsible(False)

        board_region = QFrame()
        board_region.setObjectName("board_region")
        board_layout = QVBoxLayout(board_region)
        board_layout.setContentsMargins(4, 4, 4, 4)
        board_layout.addWidget(self._board, 1, Qt.AlignmentFlag.AlignCenter)

        side_splitter = QSplitter(Qt.Orientation.Vertical)
        side_splitter.setChildrenCollapsible(False)
        side_splitter.addWidget(PlaceholderPanel("Engine analysis\nFuture evaluation lines"))

        move_tree_panel = QFrame()
        move_tree_panel.setObjectName("move_tree_panel")
        move_tree_layout = QVBoxLayout(move_tree_panel)
        move_tree_layout.setContentsMargins(8, 8, 8, 8)
        move_tree_layout.setSpacing(6)
        move_tree_layout.addWidget(QLabel("Move tree"))
        toolbar = QHBoxLayout()
        toolbar.setSpacing(3)
        for action in [self.first_action, self.previous_action, self.next_action, self.end_action, self.previous_variation_action, self.next_variation_action]:
            button = QToolButton()
            button.setDefaultAction(action)
            button.setAutoRaise(True)
            toolbar.addWidget(button)
        toolbar.addStretch(1)
        move_tree_layout.addLayout(toolbar)
        move_tree_layout.addWidget(self._move_tree, 1)
        side_splitter.addWidget(move_tree_panel)
        side_splitter.setSizes([210, 430])

        main_splitter.addWidget(board_region)
        main_splitter.addWidget(side_splitter)
        main_splitter.setStretchFactor(0, 7)
        main_splitter.setStretchFactor(1, 2)
        main_splitter.setSizes([1120, 280])
        root.addWidget(main_splitter, 1)

        actions = QHBoxLayout()
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

    def _connect_synchronization(self) -> None:
        self._board.movePlayed.connect(self._add_board_move)
        self._move_tree.nodeSelected.connect(self._restore_node)

    def _add_board_move(self, move: object) -> None:
        node = self._move_tree_model.add_move(move)
        self._move_tree.refresh()
        self._restore_node(node)

    def _restore_node(self, node: MoveTreeNode) -> None:
        self._move_tree_model.select_node(node)
        self._board.set_position(node.fen)
        self._move_tree.set_current_node(node)

    def _navigate_to(self, node: MoveTreeNode) -> None:
        self._restore_node(node)

    def _toggle_fullscreen(self) -> None:
        window = self.window()
        if window.isFullScreen():
            window.showNormal()
        else:
            window.showFullScreen()

    def _exit_fullscreen(self) -> None:
        window = self.window()
        if window.isFullScreen():
            window.showNormal()

    def set_repertoire_name(self, name: str) -> None:
        """Update the workspace heading for the selected repertoire."""
        cleaned_name = name.strip() or "Selected repertoire"
        self._repertoire_name = cleaned_name
        self._header.setText(f"Workspace · {self._repertoire_name}")

    @property
    def board(self) -> ChessBoardWidget:
        """Expose the reusable board for future workspace controllers."""
        return self._board
