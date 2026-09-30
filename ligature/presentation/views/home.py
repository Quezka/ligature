"""The start page: new diagrams, samples, and the files you opened lately."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout, QListWidget, QListWidgetItem, QSizePolicy, QToolButton, QVBoxLayout,
)

from ...application.types import DiagramKind
from .. import theme
from ..i18n import _
from .common import Card, Page, button, label


class HomePage(Page):
    newRequested = Signal(object)  # DiagramKind
    openRequested = Signal(str)  # a path, or "" to choose one
    sampleRequested = Signal(object)  # DiagramKind

    def __init__(self, parent=None):
        super().__init__(parent)
        self.title.setText(_("Ligature"))
        self.subtitle.setText(_("ER and UML class diagrams for school, with the SQL they make."))

        start = Card(_("Start"))
        grid = QGridLayout()
        grid.setSpacing(10)
        for column, (icon, text, detail, action) in enumerate((
                ("entity", _("New ER diagram"), _("Entities, relationships, keys → SQL"),
                 lambda: self.newRequested.emit(DiagramKind.ER)),
                ("class", _("New UML class diagram"), _("Classes, inheritance, associations"),
                 lambda: self.newRequested.emit(DiagramKind.UML)),
                ("folder", _("Open…"), _("A .ligature file, or a picture Ligature made"),
                 lambda: self.openRequested.emit("")))):
            tile = QToolButton(objectName="startTile")
            tile.setText(f"{text}\n{detail}")
            tile.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            tile.setIconSize(QSize(30, 30))
            tile.setMinimumSize(210, 120)
            tile.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            tile.setCursor(Qt.PointingHandCursor)
            theme.set_icon(tile, icon, "accent", size=30)
            tile.clicked.connect(action)
            grid.addWidget(tile, 0, column)
        start.body.addLayout(grid)
        samples = label(_("Or look around a sample first:"), "hint")
        start.add(samples)
        row = QGridLayout()
        er = button(_("School register (ER)"), "database")
        uml = button(_("Geometric shapes (UML)"), "class")
        er.clicked.connect(lambda: self.sampleRequested.emit(DiagramKind.ER))
        uml.clicked.connect(lambda: self.sampleRequested.emit(DiagramKind.UML))
        row.addWidget(er, 0, 0)
        row.addWidget(uml, 0, 1)
        row.setColumnStretch(2, 1)
        start.body.addLayout(row)

        recent = Card(_("Recent"))
        self.recent = QListWidget(objectName="recent")
        self.recent.itemActivated.connect(
            lambda item: self.openRequested.emit(item.data(Qt.UserRole)))
        self.empty = label(_("Diagrams you open or save show up here."), "hint")
        recent.add(self.recent, 1)
        recent.add(self.empty)
        self.filler = recent.body.addStretch(1)

        column = QVBoxLayout()
        column.setSpacing(16)
        column.addWidget(start)
        column.addWidget(recent, 1)
        self.root.addLayout(column, 1)

    def set_recent(self, paths: list[str]):
        self.recent.clear()
        for path in paths:
            p = Path(path)
            item = QListWidgetItem(f"{p.name}\n{p.parent}")
            item.setData(Qt.UserRole, path)
            item.setToolTip(path)
            self.recent.addItem(item)
        self.empty.setVisible(not paths)
        self.recent.setVisible(bool(paths))
