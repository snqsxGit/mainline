"""Reusable placeholder panel widget for unfinished application regions."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class PlaceholderPanel(QFrame):
    """A framed placeholder used to reserve space for future features."""

    def __init__(self, title: str) -> None:
        """Create a placeholder panel with centered display text."""
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setObjectName(f"{title.lower().replace(' ', '_')}_panel")

        layout = QVBoxLayout(self)
        label = QLabel(title)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setObjectName("placeholder_label")
        layout.addWidget(label)
