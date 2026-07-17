"""Compact clickable opening move tree widget."""

from __future__ import annotations

import chess
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from app.chess.move_tree import MoveTreeModel, MoveTreeNode


class MoveTreeWidget(QWidget):
    """Display an opening variation tree and emit selected nodes."""

    nodeSelected = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Create the tree view."""
        super().__init__(parent)
        self._model: MoveTreeModel | None = None
        self._node_items: dict[int, QTreeWidgetItem] = {}
        self._tree = QTreeWidget()
        self._tree.setObjectName("move_tree_view")
        self._tree.setHeaderHidden(True)
        self._tree.setIndentation(16)
        self._tree.setUniformRowHeights(True)
        self._tree.setAlternatingRowColors(True)
        self._tree.itemClicked.connect(self._handle_item_clicked)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._tree)

    def set_model(self, model: MoveTreeModel) -> None:
        """Attach a move tree model and rebuild the view."""
        self._model = model
        self.refresh()

    def refresh(self) -> None:
        """Rebuild displayed move items from the current model."""
        self._tree.clear()
        self._node_items.clear()
        if self._model is None:
            return
        root_item = QTreeWidgetItem(["Starting position"])
        root_item.setFont(0, self._item_font(is_mainline=True))
        root_item.setData(0, Qt.ItemDataRole.UserRole, self._model.root)
        self._tree.addTopLevelItem(root_item)
        self._node_items[id(self._model.root)] = root_item
        self._add_children(root_item, self._model.root)
        self._tree.expandAll()
        self.set_current_node(self._model.current_node)

    def set_current_node(self, node: MoveTreeNode) -> None:
        """Highlight ``node`` without emitting a selection signal."""
        item = self._node_items.get(id(node))
        if item is None:
            self.refresh()
            item = self._node_items.get(id(node))
        if item is not None:
            self._tree.setCurrentItem(item)
            self._tree.scrollToItem(item)

    def _add_children(self, parent_item: QTreeWidgetItem, parent_node: MoveTreeNode) -> None:
        for variation_index, child in enumerate(parent_node.children):
            prefix = ""
            if child.move and child.move_number:
                parent_board = chess.Board(parent_node.fen)
                dots = "..." if parent_board.turn == chess.BLACK else "."
                prefix = f"{child.move_number}{dots}"
            label = f"{prefix} {child.san}".strip()
            if variation_index > 0:
                label = f"↳ {label}"
            item = QTreeWidgetItem([label])
            item.setFont(0, self._item_font(is_mainline=variation_index == 0))
            if variation_index > 0:
                item.setForeground(0, QBrush(QColor("#8F9AA3")))
            item.setData(0, Qt.ItemDataRole.UserRole, child)
            parent_item.addChild(item)
            self._node_items[id(child)] = item
            self._add_children(item, child)

    def _item_font(self, *, is_mainline: bool) -> QFont:
        font = QFont("Segoe UI", 10)
        font.setWeight(QFont.Weight.DemiBold if is_mainline else QFont.Weight.Normal)
        return font

    def _handle_item_clicked(self, item: QTreeWidgetItem) -> None:
        node = item.data(0, Qt.ItemDataRole.UserRole)
        if node is not None:
            self.nodeSelected.emit(node)
