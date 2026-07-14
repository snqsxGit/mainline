"""Focused training mode screen."""

from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.ui.board import ChessBoardWidget


class DrillScreen(QWidget):
    """Minimal drill mode with only essential controls and a large board."""

    backWorkspaceRequested = Signal()
    exitHomeRequested = Signal()
    showAnswerRequested = Signal()
    nextRequested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """Create a clutter-free drill screen without editor side panels."""
        super().__init__(parent)
        self.setObjectName("drill_screen")
        self._board = ChessBoardWidget()
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Drill Mode")
        title.setObjectName("screen_heading")
        prompt = QLabel("Find the next move in the line.")
        prompt.setObjectName("muted_text")
        prompt.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(prompt)
        root.addLayout(header)

        board_shell = QFrame()
        board_shell.setObjectName("drill_board_shell")
        board_layout = QVBoxLayout(board_shell)
        board_layout.setContentsMargins(0, 0, 0, 0)
        board_layout.addWidget(self._board, 1, Qt.AlignmentFlag.AlignCenter)
        root.addWidget(board_shell, 1)

        actions = QHBoxLayout()
        back_button = QPushButton("Back to Workspace")
        exit_button = QPushButton("Exit to Home")
        answer_button = QPushButton("Show Answer")
        next_button = QPushButton("Next")
        back_button.clicked.connect(self.backWorkspaceRequested.emit)
        exit_button.clicked.connect(self.exitHomeRequested.emit)
        answer_button.clicked.connect(self.showAnswerRequested.emit)
        next_button.clicked.connect(self.nextRequested.emit)
        actions.addWidget(back_button)
        actions.addWidget(exit_button)
        actions.addStretch(1)
        actions.addWidget(answer_button)
        actions.addWidget(next_button)
        root.addLayout(actions)

    @property
    def board(self) -> ChessBoardWidget:
        """Expose the reusable board for future drill controllers."""
        return self._board
