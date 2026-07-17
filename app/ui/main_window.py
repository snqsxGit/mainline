"""Main application window and screen navigation shell."""

from __future__ import annotations

from enum import IntEnum

from PySide6.QtWidgets import QMainWindow, QStackedWidget

from app.ui.screens import DrillScreen, HomeScreen, WorkspaceScreen
from app.ui.theme import AppTheme, DARK_THEME, stylesheet


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
        """Initialize menus, screens, and navigation signal wiring."""
        super().__init__()
        self.setWindowTitle(self.WINDOW_TITLE)
        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)

        self._theme: AppTheme = DARK_THEME
        self._create_menu_bar()
        self._create_tool_bar()
        self._create_screens()
        self._apply_style_sheet()
        self.statusBar().showMessage("Home")

    def _create_menu_bar(self) -> None:
        """Create the top-level menu categories for future actions."""
        menu_bar = self.menuBar()
        menu_bar.addMenu("File")
        menu_bar.addMenu("Edit")
        menu_bar.addMenu("View")
        menu_bar.addMenu("Help")

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

        self._home_screen.continueRequested.connect(self.show_workspace)
        self._home_screen.createRepertoireRequested.connect(self.show_workspace)
        self._home_screen.drillRequested.connect(self.show_drill)
        self._home_screen.settingsRequested.connect(self._show_settings_placeholder)
        self._workspace_screen.backHomeRequested.connect(self.show_home)
        self._workspace_screen.startDrillRequested.connect(self.show_drill)
        self._drill_screen.backWorkspaceRequested.connect(self.show_workspace)
        self._drill_screen.exitHomeRequested.connect(self.show_home)
        self._drill_screen.showAnswerRequested.connect(self._show_answer_placeholder)
        self._drill_screen.nextRequested.connect(self._next_drill_placeholder)

    def show_home(self) -> None:
        """Navigate to the launcher dashboard."""
        self._stack.setCurrentIndex(ScreenIndex.HOME)
        self.statusBar().showMessage("Home")

    def show_workspace(self, repertoire_name: str = "Selected repertoire") -> None:
        """Navigate to the selected repertoire workspace."""
        self._workspace_screen.set_repertoire_name(repertoire_name)
        self._stack.setCurrentIndex(ScreenIndex.WORKSPACE)
        self.statusBar().showMessage(f"Workspace · {repertoire_name}")

    def show_drill(self) -> None:
        """Navigate to focused drill mode."""
        self._stack.setCurrentIndex(ScreenIndex.DRILL)
        self.statusBar().showMessage("Drill mode")

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
