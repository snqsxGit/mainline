"""Main opening editing workspace screen."""

from __future__ import annotations

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QApplication, QCheckBox, QFrame, QHBoxLayout, QLabel, QPushButton, QSplitter, QToolButton, QVBoxLayout, QWidget

from app.chess import MoveTreeModel, MoveTreeNode
from app.ui.board import ChessBoardWidget
from app.ui.widgets import MoveTreeWidget
from app.services import EngineService
from app.ui.theme import AppTheme, DARK_THEME, LIGHT_THEME, DEFAULT_BOARD_THEME, stylesheet


class WorkspaceScreen(QWidget):
    """Opening editor workspace that synchronizes board, tree, and navigation."""

    backHomeRequested = Signal()
    startDrillRequested = Signal()
    repertoireChanged = Signal()
    currentNodeChanged = Signal(object)

    def __init__(self, parent: QWidget | None = None, *, theme: AppTheme | None = None) -> None:
        """Create the workspace with board, move tree, and editor actions."""
        super().__init__(parent)
        self.setObjectName("workspace_screen")
        self._theme = theme or DARK_THEME
        self._focus_mode = False
        self._board = ChessBoardWidget(theme=DEFAULT_BOARD_THEME)
        self._move_tree_model = MoveTreeModel()
        self._move_tree = MoveTreeWidget()
        self._repertoire_name = "Selected repertoire"
        self._repertoire_side = "white"
        self._undo_stack: list[str] = []
        self._redo_stack: list[str] = []
        self._engine = EngineService()
        self._engine_enabled = False
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

        self.undo_action = QAction("Undo", self)
        self.undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        self.undo_action.triggered.connect(self.undo)

        self.redo_action = QAction("Redo", self)
        self.redo_action.setShortcut(QKeySequence("Ctrl+Shift+Z"))
        self.redo_action.triggered.connect(self.redo)

        self.copy_fen_action = QAction("Copy FEN", self)
        self.copy_fen_action.setShortcut(QKeySequence("Ctrl+Shift+C"))
        self.copy_fen_action.triggered.connect(self.copy_fen)

        self.copy_pgn_action = QAction("Copy PGN", self)
        self.copy_pgn_action.setShortcut(QKeySequence("Ctrl+C"))
        self.copy_pgn_action.triggered.connect(self.copy_pgn)

        self.promote_action = QAction("Promote Variation", self)
        self.promote_action.triggered.connect(lambda: self.promote_variation(self.current_node))

        self.engine_action = QAction("Toggle Engine", self)
        self.engine_action.setCheckable(True)
        self.engine_action.triggered.connect(self.toggle_engine)

        self.addActions([
            self.first_action, self.previous_action, self.next_action, self.end_action,
            self.previous_variation_action, self.next_variation_action, self.flip_action, self.focus_action, self.theme_action,
            self.fullscreen_action, self.exit_fullscreen_action, self.home_action, self.drill_action,
            self.undo_action, self.redo_action, self.copy_fen_action, self.copy_pgn_action, self.promote_action, self.engine_action,
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
        self._engine_panel = QLabel("Engine off · use Study > Toggle Engine")
        self._engine_panel.setObjectName("placeholder_panel")
        self._engine_panel.setWordWrap(True)
        self._engine_panel.setAlignment(Qt.AlignmentFlag.AlignTop)
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
        self._move_tree.copyPgnRequested.connect(lambda _node: self.copy_pgn())
        self._move_tree.copyFenRequested.connect(lambda node: self.copy_fen(node))
        self._move_tree.promoteVariationRequested.connect(self.promote_variation)
        self._move_tree.deleteNodeRequested.connect(self.delete_node)

    def _add_board_move(self, move: object) -> None:
        self._record_undo_snapshot()
        node = self._move_tree_model.add_move(move)
        self._move_tree.refresh()
        self._restore_node(node)
        self.repertoireChanged.emit()

    def _restore_node(self, node: MoveTreeNode) -> None:
        self._move_tree_model.select_node(node)
        self._board.set_position(node.fen)
        self._move_tree.set_current_node(node)
        self._update_metadata()
        self._update_engine_panel()
        self.currentNodeChanged.emit(node)

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

    def load_repertoire(self, name: str, model: MoveTreeModel, selected_node: MoveTreeNode | None = None, *, side: str = "white") -> None:
        """Replace the workspace with a persisted repertoire tree."""
        self._move_tree_model = model
        self._repertoire_side = side
        self._undo_stack.clear(); self._redo_stack.clear()
        self.set_repertoire_name(name)
        self._move_tree.set_model(self._move_tree_model)
        self._restore_node(selected_node or self._move_tree_model.current_node)

    @property
    def move_tree_model(self) -> MoveTreeModel:
        """Return the editable move tree model."""
        return self._move_tree_model

    @property
    def current_node(self) -> MoveTreeNode:
        """Return the currently selected move-tree node."""
        return self._move_tree_model.current_node

    def set_repertoire_name(self, name: str) -> None:
        """Update the workspace heading for the selected repertoire."""
        cleaned_name = name.strip() or "Selected repertoire"
        self._repertoire_name = cleaned_name
        self._update_metadata()

    @property
    def board(self) -> ChessBoardWidget:
        """Expose the reusable board for future workspace controllers."""
        return self._board


    def _record_undo_snapshot(self) -> None:
        self._undo_stack.append(self._move_tree_model.to_pgn())
        self._redo_stack.clear()

    def undo(self) -> None:
        if not self._undo_stack:
            return
        self._redo_stack.append(self._move_tree_model.to_pgn())
        self._move_tree_model = MoveTreeModel.from_pgn(self._undo_stack.pop())
        self._move_tree.set_model(self._move_tree_model)
        self._restore_node(self._move_tree_model.current_node)
        self.repertoireChanged.emit()

    def redo(self) -> None:
        if not self._redo_stack:
            return
        self._undo_stack.append(self._move_tree_model.to_pgn())
        self._move_tree_model = MoveTreeModel.from_pgn(self._redo_stack.pop())
        self._move_tree.set_model(self._move_tree_model)
        self._restore_node(self._move_tree_model.current_node)
        self.repertoireChanged.emit()

    def copy_fen(self, node: MoveTreeNode | None = None) -> None:
        QApplication.clipboard().setText((node or self.current_node).fen)

    def copy_pgn(self) -> None:
        QApplication.clipboard().setText(self._move_tree_model.to_pgn())

    def import_pgn_text(self, pgn_text: str, *, name: str | None = None) -> None:
        self._record_undo_snapshot()
        self._move_tree_model = MoveTreeModel.from_pgn(pgn_text)
        if name:
            self._repertoire_name = name
        self._move_tree.set_model(self._move_tree_model)
        self._restore_node(self._move_tree_model.root)
        self.repertoireChanged.emit()

    def export_pgn_text(self) -> str:
        return self._move_tree_model.to_pgn()

    def promote_variation(self, node: MoveTreeNode | None = None) -> None:
        self._record_undo_snapshot()
        selected = self._move_tree_model.promote_to_mainline(node or self.current_node)
        self._move_tree.refresh()
        self._restore_node(selected)
        self.repertoireChanged.emit()

    def delete_node(self, node: MoveTreeNode | None = None) -> None:
        if (node or self.current_node).is_root:
            return
        self._record_undo_snapshot()
        selected = self._move_tree_model.delete_node(node or self.current_node)
        self._move_tree.refresh()
        self._restore_node(selected)
        self.repertoireChanged.emit()

    def toggle_engine(self, enabled: bool) -> None:
        self._engine_enabled = bool(enabled)
        if not self._engine_enabled:
            self._engine.stop()
        self._update_engine_panel()

    def _update_engine_panel(self) -> None:
        if not hasattr(self, "_engine_panel") or not self._engine_enabled:
            if hasattr(self, "_engine_panel"):
                self._engine_panel.setText("Engine off · use Study > Toggle Engine")
            return
        try:
            analysis = self._engine.analyse(self.current_node.fen, depth=8)
            self._engine_panel.setText(
                f"Engine analysis\nEval: {analysis.evaluation}\nBest: {analysis.best_move}\nDepth: {analysis.depth or '—'}\nPV: {analysis.pv or '—'}"
            )
        except Exception as exc:  # engine availability is environment-dependent
            self._engine_panel.setText(f"Stockfish unavailable\n{exc}")
            self.engine_action.setChecked(False)
            self._engine_enabled = False

    def _update_metadata(self) -> None:
        if not hasattr(self, "_header"):
            return
        side_to_move = "White" if " w " in self.current_node.fen else "Black"
        prefix = "Focus" if self._focus_mode else "Workspace"
        self._header.setText(
            f"{prefix} · {self._repertoire_name} · {self._repertoire_side.title()} · {side_to_move} to move · {self._move_tree_model.node_count()} nodes"
        )
