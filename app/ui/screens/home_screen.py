"""Home launcher screen for choosing how to enter Mainline."""

from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class HomeScreen(QWidget):
    """Launcher-style start screen for repertoire and training entry points."""

    continueRequested = Signal(int)
    repertoireSelected = Signal(int)
    createRepertoireRequested = Signal()
    renameRepertoireRequested = Signal(int)
    deleteRepertoireRequested = Signal(int)
    drillRequested = Signal()
    settingsRequested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """Create the home dashboard without workspace/editor chrome."""
        super().__init__(parent)
        self.setObjectName("home_screen")
        self._repertoires = []
        self._build_ui()
        self._refresh_repertoire_list()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(48, 40, 48, 40)
        root.setSpacing(24)

        title = QLabel("Mainline")
        title.setObjectName("home_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("Choose a repertoire to prepare, or start a focused training session.")
        subtitle.setObjectName("home_subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        root.addWidget(title)
        root.addWidget(subtitle)

        content = QHBoxLayout()
        content.setSpacing(28)
        root.addLayout(content, 1)

        repertoire_panel = self._create_repertoire_panel()
        actions_panel = self._create_actions_panel()
        content.addWidget(repertoire_panel, 3)
        content.addWidget(actions_panel, 2)

    def _create_repertoire_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("home_card")
        panel.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        heading = QLabel("Repertoires")
        heading.setObjectName("section_heading")
        helper = QLabel("Double-click a repertoire to open it in the workspace.")
        helper.setObjectName("muted_text")
        helper.setWordWrap(True)

        self._search_box = QLineEdit()
        self._search_box.setObjectName("repertoire_search")
        self._search_box.setPlaceholderText("Search repertoires")
        self._search_box.textChanged.connect(self._refresh_repertoire_list)

        self._repertoire_list = QListWidget()
        self._repertoire_list.setObjectName("recent_repertoire_list")
        self._repertoire_list.itemDoubleClicked.connect(self._open_repertoire_item)
        self._repertoire_list.currentItemChanged.connect(self._update_continue_button)

        self._empty_state = QLabel("No repertoires yet. Create one to start building your opening files.")
        self._empty_state.setObjectName("muted_text")
        self._empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_state.setWordWrap(True)

        self._continue_button = QPushButton("Continue Selected Repertoire")
        self._continue_button.clicked.connect(self._continue_selected_repertoire)

        layout.addWidget(heading)
        layout.addWidget(helper)
        layout.addWidget(self._search_box)
        layout.addWidget(self._repertoire_list, 1)
        layout.addWidget(self._empty_state, 1)
        layout.addWidget(self._continue_button)
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
            ("Create New Repertoire", self.createRepertoireRequested),
            ("Rename Selected", self._rename_selected_repertoire),
            ("Delete Selected", self._delete_selected_repertoire),
            ("Enter Drill Mode", self.drillRequested),
            ("Settings", self.settingsRequested),
        ]
        for text, signal in buttons:
            button = QPushButton(text)
            button.setMinimumHeight(42)
            button.clicked.connect(signal.emit if hasattr(signal, "emit") else signal)
            layout.addWidget(button)

        layout.addStretch(1)
        note = QLabel("The repertoire list is the open action: select a file, then double-click or continue.")
        note.setObjectName("muted_text")
        note.setWordWrap(True)
        layout.addWidget(note)
        return panel

    def _refresh_repertoire_list(self) -> None:
        query = self._search_box.text().strip().lower() if hasattr(self, "_search_box") else ""
        visible_repertoires = [rep for rep in self._repertoires if query in rep.name.lower()]

        self._repertoire_list.clear()
        for rep in visible_repertoires:
            item = QListWidgetItem(f"{rep.name} · {rep.side.title()}")
            item.setData(Qt.ItemDataRole.UserRole, rep.id)
            self._repertoire_list.addItem(item)

        has_items = self._repertoire_list.count() > 0
        self._repertoire_list.setVisible(has_items)
        self._empty_state.setVisible(not has_items)
        if has_items:
            self._repertoire_list.setCurrentRow(0)
        self._update_continue_button()

    def _update_continue_button(self, *args: object) -> None:
        self._continue_button.setEnabled(self._repertoire_list.currentItem() is not None)

    def _continue_selected_repertoire(self) -> None:
        current_item = self._repertoire_list.currentItem()
        if current_item is None:
            return
        self._open_repertoire_item(current_item)

    def _open_repertoire_item(self, item: QListWidgetItem) -> None:
        repertoire_id = int(item.data(Qt.ItemDataRole.UserRole))
        self.repertoireSelected.emit(repertoire_id)
        self.continueRequested.emit(repertoire_id)

    def set_repertoires(self, repertoires: list[object]) -> None:
        """Replace the displayed repertoire list with persisted summaries."""
        self._repertoires = list(repertoires)
        self._refresh_repertoire_list()

    def selected_repertoire_id(self) -> int | None:
        """Return the selected repertoire id, if any."""
        current_item = self._repertoire_list.currentItem()
        if current_item is None:
            return None
        return int(current_item.data(Qt.ItemDataRole.UserRole))

    def _rename_selected_repertoire(self) -> None:
        repertoire_id = self.selected_repertoire_id()
        if repertoire_id is not None:
            self.renameRepertoireRequested.emit(repertoire_id)

    def _delete_selected_repertoire(self) -> None:
        repertoire_id = self.selected_repertoire_id()
        if repertoire_id is not None:
            self.deleteRepertoireRequested.emit(repertoire_id)
