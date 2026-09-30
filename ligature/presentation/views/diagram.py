"""The drawing page: tools on top, the canvas, and the properties panel beside it."""
from __future__ import annotations

from PySide6.QtCore import QMimeData, Qt, Signal
from PySide6.QtGui import QCursor, QGuiApplication, QKeySequence, QShortcut
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QMenu, QToolButton, QWidget
from shiboken6 import isValid

from ...application.errors import ApplicationError
from ...application.services import Services
from ...application.types import DiagramKind, LinkKind
from .. import theme
from ..canvas import DiagramScene, DiagramView, Tool, style_for
from ..i18n import _
from ..properties import LINK_KINDS, PropertiesPanel
from .common import Card, Page, icon_button, label, primary_button

CLIPBOARD = "application/x-ligature"  # copied diagram items


class DiagramPage(Page):
    saveRequested = Signal()
    exportRequested = Signal(str)  # "png", "svg", "pdf", "copy"
    problem = Signal(str)

    def __init__(self, services: Services, parent=None):
        super().__init__(parent, margins=(24, 18, 24, 20))
        self.services = services
        self.editor = services.editor
        self.link_kind = LinkKind.ASSOCIATION

        self.undo_button = icon_button("undo", _("Undo (Ctrl+Z)"))
        self.redo_button = icon_button("redo", _("Redo (Ctrl+Shift+Z)"))
        self.undo_button.clicked.connect(self.editor.undo)
        self.redo_button.clicked.connect(self.editor.redo)
        export = QToolButton(objectName="icon", toolTip=_("Export"))
        export.setPopupMode(QToolButton.InstantPopup)
        theme.set_icon(export, "download", "muted")
        menu = QMenu(export)
        for text, kind in ((_("PNG picture (editable)…"), "png"),
                           (_("SVG picture (editable)…"), "svg"), (_("PDF…"), "pdf"),
                           (None, None), (_("Copy as picture"), "copy")):
            if text is None:
                menu.addSeparator()
            else:
                menu.addAction(text, lambda k=kind: self.exportRequested.emit(k))
        export.setMenu(menu)
        save = primary_button(_("Save"), "save")
        save.setToolTip(_("Save (Ctrl+S)"))
        save.clicked.connect(self.saveRequested.emit)
        self.add_actions(self.undo_button, self.redo_button, export, save)

        self.scene = DiagramScene(style_for(theme.current()), parent=self)
        self.scene.no_key_warning = _("No key: mark its identifier with the key icon.")
        self.view = DiagramView(self.scene)
        theme.themed(self._restyle)

        # ---- tools --------------------------------------------------------------------
        self.tools = QButtonGroup(self)
        self.tools.setExclusive(True)
        tool_row = QHBoxLayout()
        tool_row.setContentsMargins(10, 8, 10, 8)
        tool_row.setSpacing(4)
        self.tool_buttons: dict[Tool, QToolButton] = {}
        for tool, icon, text, key in (
                (Tool.SELECT, "pointer", _("Select and move"), "V"),
                (Tool.ENTITY, "entity", _("Entity"), "E"),
                (Tool.RELATIONSHIP, "relationship", _("Relationship"), "R"),
                (Tool.GENERALISATION, "inherit", _("Generalisation"), "G"),
                (Tool.CLASS, "class", _("Class"), "C"),
                (Tool.LINK, "link", _("Link"), "L")):
            b = QToolButton(objectName="tool", text=text, checkable=True)
            b.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            b.setToolTip(f"{text}  ({key})")
            b.setCursor(Qt.PointingHandCursor)
            theme.set_icon(b, icon, "muted", "accent", size=16)
            self.tools.addButton(b)
            self.tool_buttons[tool] = b
            tool_row.addWidget(b)
            b.clicked.connect(lambda _c=False, t=tool: self.set_tool(t))
            QShortcut(QKeySequence(key), self.view, activated=lambda t=tool: self._key_tool(t),
                      context=Qt.WidgetShortcut)
        self.link_menu = QMenu(self)
        for kind, text in LINK_KINDS:
            self.link_menu.addAction(_(text), lambda k=kind: self._pick_link(k))
        link_kind = self.tool_buttons[Tool.LINK]
        link_kind.setPopupMode(QToolButton.MenuButtonPopup)
        link_kind.setMenu(self.link_menu)
        self.hint = label("", "hint")
        tool_row.addSpacing(10)
        tool_row.addWidget(self.hint, 1)
        self.zoom_label = label("100%")
        self.zoom_label.setMinimumWidth(42)
        self.zoom_label.setAlignment(Qt.AlignCenter)
        out = icon_button("zoom-out", _("Zoom out (Ctrl+-)"))
        fit = icon_button("fit", _("Fit the diagram (Ctrl+0)"))
        zoom_in = icon_button("zoom-in", _("Zoom in (Ctrl+=, or Ctrl+scroll)"))
        out.clicked.connect(self.view.zoom_out)
        zoom_in.clicked.connect(self.view.zoom_in)
        fit.clicked.connect(self.view.fit)
        self.view.zoomChanged.connect(lambda z: self.zoom_label.setText(f"{round(z * 100)}%"))
        for w in (out, self.zoom_label, zoom_in, fit):
            tool_row.addWidget(w)

        canvas = Card(padding=0)
        canvas.body.setSpacing(0)
        canvas.body.addLayout(tool_row)
        line = QWidget(objectName="rule")
        line.setFixedHeight(1)
        canvas.body.addWidget(line)
        canvas.body.addWidget(self.view, 1)
        self.panel = PropertiesPanel(services)
        body = QHBoxLayout()
        body.setSpacing(14)
        body.addWidget(canvas, 1)
        body.addWidget(self.panel)
        self.root.addLayout(body, 1)

        # ---- wiring ---------------------------------------------------------------------
        self.scene.selectionChanged.connect(self._selection_changed)
        self.scene.addRequested.connect(self._add)
        self.scene.connectRequested.connect(self._connect)
        self.scene.moved.connect(lambda positions: self._try(lambda: self.editor.move(positions)))
        self.scene.editRequested.connect(self._edit)
        self.scene.toolDone.connect(lambda: self.set_tool(Tool.SELECT))
        self.scene.pickedFirst.connect(lambda _id: self.hint.setText(self._second_hint()))
        self.panel.deleteRequested.connect(self.delete_selection)
        self.panel.duplicateRequested.connect(self.duplicate_selection)
        self.view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self._context_menu)
        for keys, slot in ((QKeySequence.Delete, self.delete_selection),
                           (QKeySequence(Qt.Key_Backspace), self.delete_selection),
                           (QKeySequence("Ctrl+D"), self.duplicate_selection),
                           (QKeySequence.Copy, self.copy_selection),
                           (QKeySequence.Cut, self.cut_selection),
                           (QKeySequence.Paste, self.paste),
                           (QKeySequence.SelectAll, self._select_all)):
            QShortcut(keys, self.view, activated=slot, context=Qt.WidgetShortcut)
        for key, dx, dy in ((Qt.Key_Left, -1, 0), (Qt.Key_Right, 1, 0), (Qt.Key_Up, 0, -1),
                            (Qt.Key_Down, 0, 1)):
            for mods, step in ((Qt.NoModifier, 10), (Qt.ShiftModifier, 50)):
                QShortcut(QKeySequence(key | mods), self.view, context=Qt.WidgetShortcut,
                          activated=lambda dx=dx * step, dy=dy * step: self._nudge(dx, dy))
        for keys, slot in (("Ctrl+=", self.view.zoom_in), ("Ctrl++", self.view.zoom_in),
                           ("Ctrl+-", self.view.zoom_out), ("Ctrl+0", self.view.fit)):
            QShortcut(QKeySequence(keys), self, activated=slot,
                      context=Qt.WidgetWithChildrenShortcut)
        self.set_tool(Tool.SELECT)

    # ---- showing the diagram -----------------------------------------------------------

    def _restyle(self, t):
        self.scene.style = style_for(t)
        if self.scene.record is not None:
            self.scene.load(self.scene.record)

    def refresh(self, fit: bool = False):
        record = self.editor.diagram()
        er = record.kind is DiagramKind.ER
        for tool in (Tool.ENTITY, Tool.RELATIONSHIP, Tool.GENERALISATION):
            self.tool_buttons[tool].setVisible(er)
        for tool in (Tool.CLASS, Tool.LINK):
            self.tool_buttons[tool].setVisible(not er)
        self.scene.load(record)
        self.panel.show_selection(self.scene.selected_ids(), record)
        self.undo_button.setEnabled(self.editor.can_undo)
        self.redo_button.setEnabled(self.editor.can_redo)
        if fit:
            self.view.fit()

    def set_heading(self, title: str, subtitle: str):
        self.title.setText(title)
        self.subtitle.setText(subtitle)

    def _selection_changed(self):
        if isValid(self.scene) and isValid(self.panel) and self.scene.record is not None:
            self.panel.show_selection(self.scene.selected_ids(), self.editor.diagram())

    # ---- tools --------------------------------------------------------------------------

    def set_tool(self, tool: Tool):
        self.scene.set_tool(tool)
        self.tool_buttons[tool].setChecked(True)
        self.hint.setText({
            Tool.SELECT: "",
            Tool.ENTITY: _("Click where the entity goes."),
            Tool.CLASS: _("Click where the class goes."),
            Tool.RELATIONSHIP: _("Click the first entity."),
            Tool.GENERALISATION: _("Click the specialised entity (the child)."),
            Tool.LINK: _("Click the first class."),
        }[tool])

    def _key_tool(self, tool: Tool):
        if self.tool_buttons[tool].isVisible():
            self.set_tool(tool)

    def _second_hint(self) -> str:
        if self.scene.tool is Tool.RELATIONSHIP:
            return _("Now click the second entity (the same one again for a recursive "
                     "relationship). Esc cancels.")
        if self.scene.tool is Tool.GENERALISATION:
            return _("Now click the parent entity. Esc cancels.")
        if self.link_kind in (LinkKind.INHERITANCE, LinkKind.REALIZATION):
            return _("Now click the parent class or interface. Esc cancels.")
        return _("Now click the second class. Esc cancels.")

    def _pick_link(self, kind: LinkKind):
        self.link_kind = kind
        button = self.tool_buttons[Tool.LINK]
        button.setText(dict((k, _(t)) for k, t in LINK_KINDS)[kind])
        self.set_tool(Tool.LINK)

    # ---- actions --------------------------------------------------------------------------

    def _try(self, action):
        try:
            return action()
        except ApplicationError as e:
            self.problem.emit(_(str(e)))
            return None

    def _add(self, tool: Tool, x: float, y: float):
        if tool is Tool.ENTITY:
            id = self._try(lambda: self.editor.add_entity(x, y, _("Entity")))
        else:
            id = self._try(lambda: self.editor.add_class(x, y, _("Class")))
        self.set_tool(Tool.SELECT)
        if id:
            self._edit(id)

    def _connect(self, first: str, second: str):
        if self.scene.tool is Tool.RELATIONSHIP:
            id = self._try(lambda: self.editor.add_relationship([first, second],
                                                                 _("Relationship")))
        elif self.scene.tool is Tool.GENERALISATION:
            id = self._try(lambda: self.editor.add_generalisation(first, second))
        else:
            id = self._try(lambda: self.editor.add_link(self.link_kind, first, second))
        self.set_tool(Tool.SELECT)
        if id:
            self._edit(id)

    def _edit(self, id: str):
        self.scene.select_only([id])
        self.panel.focus_name()

    def delete_selection(self):
        ids = self.scene.selected_ids()
        if ids:
            self._try(lambda: self.editor.delete(ids))

    def duplicate_selection(self):
        ids = self.scene.selected_ids()
        if ids:
            new = self._try(lambda: self.editor.duplicate(ids))
            if new:
                self.scene.select_only(new)

    def copy_selection(self) -> bool:
        ids = self.scene.selected_ids()
        if not ids:
            return False
        mime = QMimeData()
        mime.setData(CLIPBOARD, self.editor.copy(ids))
        QGuiApplication.clipboard().setMimeData(mime)
        return True

    def cut_selection(self):
        if self.copy_selection():
            self.delete_selection()

    def paste(self):
        """Items copied here or in another diagram; or the diagram inside a Ligature picture
        (e.g. copied from a note)."""
        mime = QGuiApplication.clipboard().mimeData()
        data = bytes(mime.data(CLIPBOARD)) if mime.hasFormat(CLIPBOARD) else (
            bytes(mime.data("image/png")) if mime.hasFormat("image/png") else b"")
        if not data:
            return
        under = self.view.mapFromGlobal(QCursor.pos())
        if self.view.viewport().rect().contains(under):
            at = self.view.mapToScene(under)
            new = self._try(lambda: self.editor.paste(data, at.x(), at.y()))
        else:
            new = self._try(lambda: self.editor.paste(data))
        if new:
            self.scene.select_only(new)

    def _nudge(self, dx: float, dy: float):
        ids = self.scene.selected_ids()
        if ids:
            self._try(lambda: self.editor.nudge(ids, dx, dy))

    def _select_all(self):
        self.scene.select_only(list(self.scene.nodes) + list(self.scene.links))

    def _context_menu(self, pos):
        scene_pos = self.view.mapToScene(pos)
        menu = QMenu(self)
        item_ids = [i.id for i in self.scene.items(scene_pos) if hasattr(i, "id")]
        if item_ids:
            if item_ids[0] not in self.scene.selected_ids():
                self.scene.select_only(item_ids[:1])
            menu.addAction(_("Copy"), self.copy_selection)
            menu.addAction(_("Cut"), self.cut_selection)
            menu.addAction(_("Duplicate"), self.duplicate_selection)
            menu.addAction(_("Delete"), self.delete_selection)
        else:
            from ..canvas import snap
            x, y = snap(scene_pos.x()), snap(scene_pos.y())
            if self.editor.kind is DiagramKind.ER:
                menu.addAction(_("Add an entity here"), lambda: self._add(Tool.ENTITY, x, y))
            else:
                menu.addAction(_("Add a class here"), lambda: self._add(Tool.CLASS, x, y))
            menu.addAction(_("Paste"), self.paste)
            menu.addSeparator()
            menu.addAction(_("Fit the diagram"), self.view.fit)
        menu.exec(self.view.viewport().mapToGlobal(pos))


