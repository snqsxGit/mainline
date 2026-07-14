"""Home launcher screen for choosing how to enter Mainline."""

from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class HomeScreen(QWidget):
    """Launcher-style start screen for repertoire and training entry points."""

    continueRequested = Signal()
    openRepertoireRequested = Signal()
    createRepertoireRequested = Signal()
    drillRequested = Signal()
    settingsRequested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """Create the home dashboard without workspace/editor chrome."""
        super().__init__(parent)
        self.setObjectName("home_screen")
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(48, 40, 48, 40)
        root.setSpacing(28)

        title = QLabel("Mainline")
        title.setObjectName("home_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("Choose a repertoire or start a focused training session.")
        subtitle.setObjectName("home_subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        root.addWidget(title)
        root.addWidget(subtitle)

        content = QHBoxLayout()
        content.setSpacing(28)
        root.addLayout(content, 1)

        recent_panel = self._create_recent_panel()
        actions_panel = self._create_actions_panel()
        content.addWidget(recent_panel, 3)
        content.addWidget(actions_panel, 2)

    def _create_recent_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("home_card")
        panel.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        heading = QLabel("Recent repertoires")
        heading.setObjectName("section_heading")
        helper = QLabel("Placeholder list for repertoire selection and quick continue.")
        helper.setObjectName("muted_text")
        helper.setWordWrap(True)

        recent_list = QListWidget()
        recent_list.setObjectName("recent_repertoire_list")
        recent_list.addItems(["White repertoire", "Black repertoire", "Endgame sparring lines"])
        recent_list.setCurrentRow(0)
        recent_list.itemDoubleClicked.connect(self.continueRequested.emit)

        continue_button = QPushButton("Continue Selected Repertoire")
        continue_button.clicked.connect(self.continueRequested.emit)

        layout.addWidget(heading)
        layout.addWidget(helper)
        layout.addWidget(recent_list, 1)
        layout.addWidget(continue_button)
        return panel

    def _create_actions_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("home_card")
        panel.setFrameShape(QFrame.Shape.StyledPanel)
        panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        heading = QLabel("Actions")
        heading.setObjectName("section_heading")
        layout.addWidget(heading)

        buttons = [
            ("Open Existing Repertoire", self.openRepertoireRequested),
            ("Create New Repertoire", self.createRepertoireRequested),
            ("Enter Drill Mode", self.drillRequested),
            ("Settings", self.settingsRequested),
        ]
        for text, signal in buttons:
            button = QPushButton(text)
            button.setMinimumHeight(42)
            button.clicked.connect(signal.emit)
            layout.addWidget(button)

        layout.addStretch(1)
        note = QLabel("Workspace panels appear only after a repertoire is opened.")
        note.setObjectName("muted_text")
        note.setWordWrap(True)
        layout.addWidget(note)
        return panel
