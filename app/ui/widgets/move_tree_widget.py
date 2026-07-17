"""Chess-oriented clickable opening move tree widget."""

from __future__ import annotations

import chess
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import QMenu, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from app.chess.move_tree import MoveTreeModel, MoveTreeNode


class MoveTreeWidget(QWidget):
    """Display an opening tree with mainline alignment and indented variations."""

    nodeSelected = Signal(object)
    copyPgnRequested = Signal(object)
    copyFenRequested = Signal(object)
    promoteVariationRequested = Signal(object)
    deleteNodeRequested = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._model: MoveTreeModel | None = None
        self._node_items: dict[int, QTreeWidgetItem] = {}
        self._tree = QTreeWidget()
        self._tree.setObjectName("move_tree_view")
        self._tree.setHeaderHidden(True)
        self._tree.setIndentation(22)
        self._tree.setRootIsDecorated(False)
        self._tree.setUniformRowHeights(True)
        self._tree.setAlternatingRowColors(False)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.itemClicked.connect(self._handle_item_clicked)
        self._tree.customContextMenuRequested.connect(self._show_context_menu)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._tree)

    def set_model(self, model: MoveTreeModel) -> None:
        self._model = model
        self.refresh()

    def refresh(self) -> None:
        self._tree.clear()
        self._node_items.clear()
        if self._model is None:
            return
        root_item = QTreeWidgetItem(["Starting position"])
        root_item.setFont(0, self._item_font(is_mainline=True))
        root_item.setData(0, Qt.ItemDataRole.UserRole, self._model.root)
        self._tree.addTopLevelItem(root_item)
        self._node_items[id(self._model.root)] = root_item
        self._add_children_aligned(root_item, self._model.root)
        self.set_current_node(self._model.current_node)

    def set_current_node(self, node: MoveTreeNode) -> None:
        item = self._node_items.get(id(node))
        if item is None:
            self.refresh()
            item = self._node_items.get(id(node))
        if item is None:
            return
        parent = item.parent()
        while parent is not None:
            parent.setExpanded(True)
            parent = parent.parent()
        item.setExpanded(True)
        self._tree.setCurrentItem(item)
        self._tree.scrollToItem(item)

    def _add_children_aligned(self, container: QTreeWidgetItem, parent_node: MoveTreeNode) -> None:
        if not parent_node.children:
            return
        main = parent_node.children[0]
        main_item = self._make_item(main, is_mainline=True)
        container.addChild(main_item)
        self._node_items[id(main)] = main_item
        for variation in parent_node.children[1:]:
            variation_item = self._make_item(variation, is_mainline=False)
            variation_item.setText(0, f"↳ {variation_item.text(0)}")
            container.addChild(variation_item)
            self._node_items[id(variation)] = variation_item
            self._add_children_aligned(variation_item, variation)
        self._add_children_aligned(container, main)
        container.setExpanded(True)

    def _make_item(self, node: MoveTreeNode, *, is_mainline: bool) -> QTreeWidgetItem:
        prefix = ""
        if node.move and node.move_number and node.parent is not None:
            parent_board = chess.Board(node.parent.fen)
            dots = "..." if parent_board.turn == chess.BLACK else "."
            prefix = f"{node.move_number}{dots}"
        item = QTreeWidgetItem([f"{prefix} {node.san}".strip()])
        item.setFont(0, self._item_font(is_mainline=is_mainline))
        if not is_mainline:
            item.setForeground(0, QBrush(QColor("#8F9AA3")))
        item.setData(0, Qt.ItemDataRole.UserRole, node)
        return item

    def _item_font(self, *, is_mainline: bool) -> QFont:
        font = QFont("Segoe UI", 10)
        font.setWeight(QFont.Weight.DemiBold if is_mainline else QFont.Weight.Normal)
        return font

    def _handle_item_clicked(self, item: QTreeWidgetItem) -> None:
        node = item.data(0, Qt.ItemDataRole.UserRole)
        if node is not None:
            self.nodeSelected.emit(node)

    def _show_context_menu(self, point) -> None:  # noqa: ANN001
        item = self._tree.itemAt(point)
        if item is None:
            return
        node = item.data(0, Qt.ItemDataRole.UserRole)
        if node is None:
            return
        menu = QMenu(self)
        copy_pgn = menu.addAction("Copy PGN")
        copy_fen = menu.addAction("Copy FEN")
        menu.addSeparator()
        promote = menu.addAction("Promote Variation / Make Main Line")
        delete = menu.addAction("Delete Line")
        menu.addSeparator()
        expand = menu.addAction("Expand")
        collapse = menu.addAction("Collapse")
        chosen = menu.exec(self._tree.viewport().mapToGlobal(point))
        if chosen == copy_pgn:
            self.copyPgnRequested.emit(node)
        elif chosen == copy_fen:
            self.copyFenRequested.emit(node)
        elif chosen == promote:
            self.promoteVariationRequested.emit(node)
        elif chosen == delete:
            self.deleteNodeRequested.emit(node)
        elif chosen == expand:
            item.setExpanded(True)
        elif chosen == collapse:
            item.setExpanded(False)
