"""Main application window and screen navigation shell."""

from __future__ import annotations

from enum import IntEnum

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMainWindow, QMessageBox, QStackedWidget

from app.models import LoadedRepertoire
from app.services import PersistenceService
from app.ui.screens import DrillScreen, HomeScreen, WorkspaceScreen
from app.ui.theme import AppTheme, DARK_THEME, LIGHT_THEME, stylesheet


class ScreenIndex(IntEnum):
    """Stable indexes for the main stacked navigation container."""

    HOME = 0
    WORKSPACE = 1
    DRILL = 2


class MainWindow(QMainWindow):
    """Top-level window that composes the Mainline application shell."""

    WINDOW_TITLE = "Mainline"
    DEFAULT_WIDTH = 1400
    DEFAULT_HEIGHT = 900

    def __init__(self) -> None:
        """Initialize menus, screens, persistence, and navigation signal wiring."""
        super().__init__()
        self.setWindowTitle(self.WINDOW_TITLE)
        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)

        self._theme: AppTheme = DARK_THEME
        self._persistence = PersistenceService()
        self._current_repertoire_id: int | None = None
        self._is_loading_workspace = False
        self._create_menu_bar()
        self._create_tool_bar()
        self._create_screens()
        self._apply_style_sheet()
        self._refresh_home_repertoires()
        self._restore_last_repertoire()

    def _create_menu_bar(self) -> None:
        """Create the desktop menu bar and wire practical study actions."""
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        edit_menu = menu_bar.addMenu("Edit")
        view_menu = menu_bar.addMenu("View")
        study_menu = menu_bar.addMenu("Study")
        tools_menu = menu_bar.addMenu("Tools")
        help_menu = menu_bar.addMenu("Help")

        self.new_repertoire_action = QAction("New Repertoire", self)
        self.new_repertoire_action.triggered.connect(self.create_repertoire)
        self.open_repertoire_action = QAction("Open Repertoire", self)
        self.open_repertoire_action.triggered.connect(self.show_home)
        self.import_pgn_action = QAction("Import PGN…", self)
        self.import_pgn_action.triggered.connect(self.import_pgn)
        self.export_pgn_action = QAction("Export PGN…", self)
        self.export_pgn_action.triggered.connect(self.export_pgn)
        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        for action in [self.new_repertoire_action, self.open_repertoire_action, self.import_pgn_action, self.export_pgn_action, quit_action]:
            file_menu.addAction(action)

        # Workspace actions are available after screen construction; placeholders are populated there.
        self._edit_menu = edit_menu
        self._view_menu = view_menu
        self._study_menu = study_menu
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self._show_settings_placeholder)
        themes_action = QAction("Manage Themes", self)
        themes_action.triggered.connect(self._toggle_app_theme)
        tools_menu.addActions([settings_action, themes_action])
        about_action = QAction("About Mainline", self)
        about_action.triggered.connect(lambda: QMessageBox.about(self, "About Mainline", "Mainline chess opening trainer"))
        help_menu.addAction(about_action)

    def _create_tool_bar(self) -> None:
        """Create an empty toolbar that will host common actions later."""
        self.addToolBar("Main Toolbar")

    def _create_screens(self) -> None:
        """Create the central stacked screen container and wire navigation."""
        self._stack = QStackedWidget(self)
        self._stack.setObjectName("main_screen_stack")

        self._home_screen = HomeScreen()
        self._workspace_screen = WorkspaceScreen(theme=self._theme)
        self._drill_screen = DrillScreen()

        self._stack.addWidget(self._home_screen)
        self._stack.addWidget(self._workspace_screen)
        self._stack.addWidget(self._drill_screen)
        self.setCentralWidget(self._stack)

        self._home_screen.continueRequested.connect(self.open_repertoire)
        self._home_screen.createRepertoireRequested.connect(self.create_repertoire)
        self._home_screen.renameRepertoireRequested.connect(self.rename_repertoire)
        self._home_screen.deleteRepertoireRequested.connect(self.delete_repertoire)
        self._home_screen.drillRequested.connect(self.show_drill)
        self._home_screen.settingsRequested.connect(self._show_settings_placeholder)
        self._home_screen.importPgnRequested.connect(self.import_pgn)
        self._workspace_screen.backHomeRequested.connect(self.show_home)
        self._workspace_screen.startDrillRequested.connect(self.show_drill)
        self._workspace_screen.repertoireChanged.connect(self._save_current_workspace)
        self._workspace_screen.currentNodeChanged.connect(self._save_current_position)
        self._drill_screen.backWorkspaceRequested.connect(self.show_workspace)
        self._drill_screen.exitHomeRequested.connect(self.show_home)
        self._drill_screen.showAnswerRequested.connect(self._show_answer_placeholder)
        self._drill_screen.nextRequested.connect(self._next_drill_placeholder)

        self._edit_menu.addActions([self._workspace_screen.undo_action, self._workspace_screen.redo_action])
        self._edit_menu.addSeparator()
        self._edit_menu.addActions([self._workspace_screen.copy_fen_action, self._workspace_screen.copy_pgn_action])
        self._view_menu.addActions([self._workspace_screen.flip_action, self._workspace_screen.focus_action, self._workspace_screen.fullscreen_action, self._workspace_screen.theme_action])
        self._study_menu.addActions([self._workspace_screen.drill_action, self._workspace_screen.engine_action, self._workspace_screen.promote_action])

    def show_home(self) -> None:
        """Navigate to the repertoire manager dashboard."""
        self._refresh_home_repertoires()
        self._stack.setCurrentIndex(ScreenIndex.HOME)
        self.statusBar().showMessage("Home")

    def show_workspace(self) -> None:
        """Navigate to the current repertoire workspace."""
        self._stack.setCurrentIndex(ScreenIndex.WORKSPACE)
        self.statusBar().showMessage("Workspace")

    def show_drill(self) -> None:
        """Navigate to focused drill mode."""
        self._stack.setCurrentIndex(ScreenIndex.DRILL)
        self.statusBar().showMessage("Drill mode")

    def create_repertoire(self) -> None:
        """Prompt for and create a new persisted repertoire."""
        name, accepted = QInputDialog.getText(self, "Create Repertoire", "Repertoire name:")
        if not accepted:
            return
        loaded = self._persistence.create_repertoire(name)
        self._refresh_home_repertoires()
        self._load_workspace(loaded)

    def open_repertoire(self, repertoire_id: int) -> None:
        """Load a persisted repertoire into the workspace."""
        loaded = self._persistence.load_repertoire(repertoire_id)
        if loaded is None:
            QMessageBox.warning(self, "Repertoire Missing", "That repertoire no longer exists.")
            self._refresh_home_repertoires()
            return
        self._load_workspace(loaded)

    def rename_repertoire(self, repertoire_id: int) -> None:
        """Prompt for a new repertoire name and persist it."""
        current = next((rep for rep in self._persistence.list_repertoires() if rep.id == repertoire_id), None)
        if current is None:
            return
        name, accepted = QInputDialog.getText(self, "Rename Repertoire", "Repertoire name:", text=current.name)
        if not accepted:
            return
        renamed = self._persistence.rename_repertoire(repertoire_id, name)
        if self._current_repertoire_id == repertoire_id:
            self._workspace_screen.set_repertoire_name(renamed.name)
        self._refresh_home_repertoires()

    def delete_repertoire(self, repertoire_id: int) -> None:
        """Confirm and delete a repertoire from SQLite."""
        current = next((rep for rep in self._persistence.list_repertoires() if rep.id == repertoire_id), None)
        if current is None:
            return
        reply = QMessageBox.question(
            self,
            "Delete Repertoire",
            f"Delete '{current.name}'? This cannot be undone.",
            QMessageBox.StandardButton.Delete | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if reply != QMessageBox.StandardButton.Delete:
            return
        self._persistence.delete_repertoire(repertoire_id)
        if self._current_repertoire_id == repertoire_id:
            self._current_repertoire_id = None
            self.show_home()
        self._refresh_home_repertoires()

    def closeEvent(self, event: object) -> None:
        """Flush current workspace state and close persistence resources."""
        self._save_current_workspace()
        self._persistence.close()
        super().closeEvent(event)

    def _load_workspace(self, loaded: LoadedRepertoire) -> None:
        self._is_loading_workspace = True
        self._current_repertoire_id = loaded.id
        self._workspace_screen.load_repertoire(loaded.name, loaded.tree, loaded.selected_node, side=loaded.side)
        self._is_loading_workspace = False
        self._stack.setCurrentIndex(ScreenIndex.WORKSPACE)
        self.statusBar().showMessage(f"Workspace · {loaded.name}")

    def _restore_last_repertoire(self) -> None:
        loaded = self._persistence.load_last_repertoire()
        if loaded is None:
            self.show_home()
            return
        self._load_workspace(loaded)

    def _refresh_home_repertoires(self) -> None:
        self._home_screen.set_repertoires(self._persistence.list_repertoires())

    def _save_current_workspace(self) -> None:
        if self._is_loading_workspace or self._current_repertoire_id is None:
            return
        self._persistence.save_repertoire_tree(
            self._current_repertoire_id,
            self._workspace_screen.move_tree_model,
            self._workspace_screen.current_node,
        )
        self._refresh_home_repertoires()

    def _save_current_position(self, _node: object) -> None:
        self._save_current_workspace()

    def _show_settings_placeholder(self) -> None:
        """Reserve a navigation hook for a future settings screen/dialog."""
        self.statusBar().showMessage("Settings will be added later")

    def _show_answer_placeholder(self) -> None:
        """Reserve a hook for future drill answer reveal logic."""
        self.statusBar().showMessage("Answer reveal will be added with drill logic")

    def _next_drill_placeholder(self) -> None:
        """Reserve a hook for future drill progression logic."""
        self.statusBar().showMessage("Next drill position will be added with drill logic")

    def _apply_style_sheet(self) -> None:
        """Apply the active Mainline theme to the full application shell."""
        self.setStyleSheet(stylesheet(self._theme))

    def import_pgn(self) -> None:
        """Import a PGN file into the current or a new workspace."""
        path, _ = QFileDialog.getOpenFileName(self, "Import PGN", "", "PGN files (*.pgn);;All files (*)")
        if not path:
            return
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        if self._current_repertoire_id is None:
            loaded = self._persistence.create_repertoire(path.rsplit("/", 1)[-1].rsplit(".", 1)[0])
            self._current_repertoire_id = loaded.id
        self._workspace_screen.import_pgn_text(text, name=path.rsplit("/", 1)[-1].rsplit(".", 1)[0])
        self._save_current_workspace()
        self.show_workspace()

    def export_pgn(self) -> None:
        """Export the current workspace tree to a PGN file."""
        if self._current_repertoire_id is None:
            self.statusBar().showMessage("Open a repertoire before exporting PGN")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export PGN", f"{self._workspace_screen._repertoire_name}.pgn", "PGN files (*.pgn);;All files (*)")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(self._workspace_screen.export_pgn_text())
        self.statusBar().showMessage(f"Exported PGN to {path}")

    def _toggle_app_theme(self) -> None:
        self._theme = LIGHT_THEME if self._theme is DARK_THEME else DARK_THEME
        self._apply_style_sheet()
