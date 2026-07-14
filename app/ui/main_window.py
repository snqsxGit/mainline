"""Main application window layout."""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QWidget

from app.ui.board import ChessBoardWidget
from app.ui.widgets.placeholder_panel import PlaceholderPanel


class MainWindow(QMainWindow):
    """Top-level window that composes the main application shell."""

    WINDOW_TITLE = "Mainline"
    DEFAULT_WIDTH = 1400
    DEFAULT_HEIGHT = 900

    def __init__(self) -> None:
        """Initialize the main window and its static UI regions."""
        super().__init__()
        self.setWindowTitle(self.WINDOW_TITLE)
        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)

        self._create_menu_bar()
        self._create_tool_bar()
        self._create_central_layout()
        self.statusBar().showMessage("Ready")

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

    def _create_central_layout(self) -> None:
        """Create the placeholder three-column application layout."""
        central_widget = QWidget(self)
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        debuts_panel = PlaceholderPanel("Debuts")
        board_panel = ChessBoardWidget()
        inspector_panel = PlaceholderPanel("Inspector")

        layout.addWidget(debuts_panel, 1)
        layout.addWidget(board_panel, 3)
        layout.addWidget(inspector_panel, 1)

        self.setCentralWidget(central_widget)
