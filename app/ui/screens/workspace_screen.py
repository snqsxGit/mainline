"""Main opening editing workspace screen."""

from __future__ import annotations

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QCheckBox, QFrame, QHBoxLayout, QLabel, QPushButton, QSplitter, QToolButton, QVBoxLayout, QWidget

from app.chess import MoveTreeModel, MoveTreeNode
from app.ui.board import ChessBoardWidget
from app.ui.widgets import MoveTreeWidget, PlaceholderPanel
from app.ui.theme import AppTheme, DARK_THEME, LIGHT_THEME, stylesheet


class WorkspaceScreen(QWidget):
    """Opening editor workspace that synchronizes board, tree, and navigation."""

    backHomeRequested = Signal()
    startDrillRequested = Signal()

    def __init__(self, parent: QWidget | None = None, *, theme: AppTheme | None = None) -> None:
        """Create the workspace with board, move tree, and editor actions."""
        super().__init__(parent)
        self.setObjectName("workspace_screen")
        self._theme = theme or DARK_THEME
        self._focus_mode = False
        self._board = ChessBoardWidget(theme=self._theme.board)
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

        self.flip_action = QAction("↻", self)
        self.flip_action.setToolTip("Flip board (F)")
        self.flip_action.setShortcut(QKeySequence("F"))
        self.flip_action.triggered.connect(self._board.flip_orientation)

        self.fullscreen_action = QAction("⛶", self)
        self.fullscreen_action.setToolTip("Toggle fullscreen (F11)")
        self.fullscreen_action.setShortcut(QKeySequence("F11"))
        self.fullscreen_action.triggered.connect(self._toggle_fullscreen)

        self.exit_fullscreen_action = QAction("Exit Fullscreen", self)
        self.exit_fullscreen_action.setShortcut(QKeySequence(Qt.Key.Key_Escape))
        self.exit_fullscreen_action.triggered.connect(self._exit_fullscreen)

        self.focus_action = QAction("Focus", self)
        self.focus_action.setToolTip("Focus mode (Ctrl+Shift+F)")
        self.focus_action.setShortcut(QKeySequence("Ctrl+Shift+F"))
        self.focus_action.setCheckable(True)
        self.focus_action.triggered.connect(self._set_focus_mode)

        self.theme_action = QAction("☾", self)
        self.theme_action.setToolTip("Toggle light/dark theme")
        self.theme_action.triggered.connect(self._toggle_theme)

        self.home_action = QAction("Return Home", self)
        self.home_action.setShortcut(QKeySequence("Ctrl+H"))
        self.home_action.triggered.connect(self.backHomeRequested.emit)

        self.drill_action = QAction("Start Drill", self)
        self.drill_action.setShortcut(QKeySequence("Ctrl+D"))
        self.drill_action.triggered.connect(self.startDrillRequested.emit)

        self.addActions([
            self.first_action, self.previous_action, self.next_action, self.end_action,
            self.previous_variation_action, self.next_variation_action, self.flip_action, self.focus_action, self.theme_action,
            self.fullscreen_action, self.exit_fullscreen_action, self.home_action, self.drill_action,
        ])

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)
        self._header = QLabel(f"Workspace · {self._repertoire_name}")
        self._header.setObjectName("screen_heading")
        top_bar.addWidget(self._header)
        top_bar.addStretch(1)
        for action in [self.home_action, self.drill_action, self.flip_action, self.focus_action, self.fullscreen_action, self.theme_action]:
            button = QToolButton()
            button.setDefaultAction(action)
            button.setAutoRaise(False)
            top_bar.addWidget(button)
        root.addLayout(top_bar)

        self._main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._main_splitter.setChildrenCollapsible(False)

        board_region = QFrame()
        board_region.setObjectName("board_region")
        board_layout = QVBoxLayout(board_region)
        board_layout.setContentsMargins(6, 6, 6, 6)
        board_layout.addWidget(self._board, 1, Qt.AlignmentFlag.AlignCenter)

        self._side_splitter = QSplitter(Qt.Orientation.Vertical)
        self._side_splitter.setChildrenCollapsible(False)
        self._engine_panel = PlaceholderPanel("Engine analysis\nFuture evaluation lines")
        self._side_splitter.addWidget(self._engine_panel)

        move_tree_panel = QFrame()
        move_tree_panel.setObjectName("move_tree_panel")
        move_tree_layout = QVBoxLayout(move_tree_panel)
        move_tree_layout.setContentsMargins(8, 8, 8, 8)
        move_tree_layout.setSpacing(6)
        tree_heading = QLabel("Move tree")
        tree_heading.setObjectName("panel_heading")
        move_tree_layout.addWidget(tree_heading)
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
        self._move_tree_panel = move_tree_panel
        self._side_splitter.addWidget(move_tree_panel)
        self._side_splitter.setSizes([180, 460])

        self._main_splitter.addWidget(board_region)
        self._main_splitter.addWidget(self._side_splitter)
        self._main_splitter.setStretchFactor(0, 8)
        self._main_splitter.setStretchFactor(1, 2)
        self._main_splitter.setSizes([1180, 260])
        root.addWidget(self._main_splitter, 1)

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
        focus_button = QPushButton("Focus Mode")
        focus_button.clicked.connect(lambda: self._set_focus_mode(not self._focus_mode))
        self.focus_action.changed.connect(lambda: focus_button.setText("Exit Focus" if self._focus_mode else "Focus Mode"))
        actions.addWidget(focus_button)
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

    def _set_focus_mode(self, enabled: bool) -> None:
        self._focus_mode = bool(enabled)
        self.focus_action.setChecked(self._focus_mode)
        self._side_splitter.setVisible(not self._focus_mode)
        self._header.setText(("Focus · " if self._focus_mode else "Workspace · ") + self._repertoire_name)
        self._main_splitter.setSizes([1, 0] if self._focus_mode else [1180, 260])

    def _toggle_theme(self) -> None:
        self._theme = LIGHT_THEME if self._theme is DARK_THEME else DARK_THEME
        self._board.set_theme(self._theme.board)
        self.window().setStyleSheet(stylesheet(self._theme))

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
