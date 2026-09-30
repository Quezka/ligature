"""The panel beside the drawing: edit whatever is selected (or the diagram itself).

Edits go to the editor as you type, so the drawing follows live; a run of edits to one
item is one undo step, ended when you leave a field. While the panel is sending an edit
it doesn't reload itself, so fields keep their focus and half-typed rows."""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit,
    QScrollArea, QStackedWidget, QVBoxLayout, QWidget,
)

from ..application.errors import ApplicationError
from ..application.inputs import (
    AttributeInput, ClassInput, EntityInput, GeneralisationInput, LinkInput, ParticipantInput,
    RelationshipInput,
)
from ..application.records import (
    ClassRecord, DiagramRecord, EntityRecord, GeneralisationRecord, LinkRecord, RelationshipRecord,
)
from ..application.services import Services
from ..application.types import (
    CARDINALITIES, DEFAULT_TYPE, MULTIPLICITIES, SQL_TYPES, ClassKind, DiagramKind, LinkKind,
    Mapping, Notation,
)
from .i18n import N_, _, plural
from .views.common import Segmented, button, caption, icon_button, label

MAPPINGS = [(Mapping.SEPARATE, N_("A table for each (children use the parent's key)")),
            (Mapping.INTO_PARENT, N_("One table: children merged into the parent")),
            (Mapping.INTO_CHILDREN, N_("A table per child: parent merged into them"))]
CLASS_KINDS = [(ClassKind.CLASS, N_("Class")), (ClassKind.ABSTRACT, N_("Abstract class")),
               (ClassKind.INTERFACE, N_("Interface")), (ClassKind.ENUM, N_("Enumeration"))]
LINK_KINDS = [(LinkKind.ASSOCIATION, N_("Association")),
              (LinkKind.DIRECTED, N_("Directed association")),
              (LinkKind.AGGREGATION, N_("Aggregation")),
              (LinkKind.COMPOSITION, N_("Composition")),
              (LinkKind.INHERITANCE, N_("Inheritance (generalisation)")),
              (LinkKind.REALIZATION, N_("Realisation (implements)")),
              (LinkKind.DEPENDENCY, N_("Dependency"))]


def _set_text(edit, text: str):
    """Update a field unless the user is typing in it."""
    if edit.hasFocus():
        return
    if isinstance(edit, QPlainTextEdit):
        if edit.toPlainText() != text:
            edit.setPlainText(text)
    elif edit.text() != text:
        edit.setText(text)


def _combo(options, editable=False) -> QComboBox:
    combo = QComboBox()
    combo.setEditable(editable)
    for value, text in options:
        combo.addItem(_(text), value)
    return combo


def _select(combo: QComboBox, value):
    index = combo.findData(value)
    if index >= 0 and combo.currentIndex() != index:
        combo.blockSignals(True)
        combo.setCurrentIndex(index)
        combo.blockSignals(False)


class SectionPanel(QWidget):
    """One kind of thing's editor. `send` runs a use case with errors shown in the panel."""

    def __init__(self, services: Services, parent=None):
        super().__init__(parent)
        self.services = services
        self.editor = services.editor
        self.id: str | None = None
        self.sending = False
        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.setSpacing(10)
        self.error = label("", "danger")
        self.error.setWordWrap(True)
        self.error.hide()

    def send(self, action):
        self.sending = True
        try:
            action()
            self.error.hide()
        except (ApplicationError, ValueError) as e:
            self.error.setText(_(str(e)))
            self.error.show()
        finally:
            self.sending = False

    def done_editing(self):
        """Leaving a field: the next edit is a new undo step."""
        self.editor.end_group()


class AttributeList(QWidget):
    """Rows of name, type, key and optional, for an entity or a relationship."""

    changed = Signal()
    finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows: list[dict] = []
        self._loading = False
        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(6)
        self.grid.setVerticalSpacing(6)
        self.grid.setColumnStretch(0, 3)
        self.grid.setColumnStretch(1, 2)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addLayout(self.grid)
        self.empty = label(_("No attributes yet."), "hint")
        layout.addWidget(self.empty)
        self.add_button = button(_("Add attribute"), "plus")
        self.add_button.clicked.connect(lambda: self.add_row(focus=True))
        layout.addWidget(self.add_button, 0, Qt.AlignLeft)

    def set_attributes(self, attributes):
        self._loading = True
        try:
            self._set_attributes(attributes)
        finally:
            self._loading = False

    def _emit(self, signal):
        if not self._loading:
            signal.emit()

    def _set_attributes(self, attributes):
        if len(attributes) != len(self.rows):
            while self.rows:
                self._remove_widgets(self.rows.pop())
            for _a in attributes:
                self.add_row(emit=False)
        for row, a in zip(self.rows, attributes):
            _set_text(row["name"], a.name)
            if not row["type"].lineEdit().hasFocus() and row["type"].currentText() != a.type:
                row["type"].setEditText(a.type)
            for key, value in (("key", a.key), ("optional", a.optional)):
                row[key].blockSignals(True)
                row[key].setChecked(value)
                row[key].blockSignals(False)
            row["optional"].setEnabled(not a.key)
        self.empty.setVisible(not self.rows)

    def attributes(self) -> tuple[AttributeInput, ...]:
        return tuple(AttributeInput(r["name"].text(), r["type"].currentText() or DEFAULT_TYPE,
                                    r["key"].isChecked(), r["optional"].isChecked())
                     for r in self.rows)

    def add_row(self, focus=False, emit=True):
        index = len(self.rows)
        name = QLineEdit(placeholderText=_("name"))
        kind = QComboBox()
        kind.setEditable(True)
        kind.addItems(SQL_TYPES)
        kind.setEditText(DEFAULT_TYPE)
        kind.setToolTip(_("Column type in SQL"))
        kind.setFixedWidth(128)
        name.setMinimumWidth(90)
        key = icon_button("key", _("Part of the key (identifier)"), checkable=True)
        optional = QCheckBox("0,1")
        optional.setToolTip(_("Optional: may be left empty"))
        remove = icon_button("x", _("Remove attribute"))
        row = {"name": name, "type": kind, "key": key, "optional": optional, "remove": remove}
        self.rows.append(row)
        for column, widget in enumerate((name, kind, key, optional, remove)):
            self.grid.addWidget(widget, index, column)
        name.textEdited.connect(lambda _t: self._emit(self.changed))
        name.editingFinished.connect(lambda: self._emit(self.finished))
        name.returnPressed.connect(lambda r=row: self._next(r))
        kind.currentTextChanged.connect(lambda _t: self._emit(self.changed))
        key.toggled.connect(lambda on, r=row: (r["optional"].setEnabled(not on),
                                               self._emit(self.changed),
                                               self._emit(self.finished)))
        optional.toggled.connect(lambda _on: (self._emit(self.changed),
                                              self._emit(self.finished)))
        remove.clicked.connect(lambda _c=False, r=row: self._remove(r))
        self.empty.hide()
        if focus:
            name.setFocus()
        if emit:
            self._emit(self.changed)

    def _next(self, row):
        """Enter in the last name adds another row: quick to type a list of attributes."""
        if row is self.rows[-1] and row["name"].text().strip():
            self.add_row(focus=True)
        else:
            index = self.rows.index(row)
            if index + 1 < len(self.rows):
                self.rows[index + 1]["name"].setFocus()

    def _remove(self, row):
        self.rows.remove(row)
        self._remove_widgets(row)
        # Re-lay the remaining rows so there are no gaps.
        for index, r in enumerate(self.rows):
            for column, key in enumerate(("name", "type", "key", "optional", "remove")):
                self.grid.addWidget(r[key], index, column)
        self.empty.setVisible(not self.rows)
        self.changed.emit()
        self.finished.emit()

    def _remove_widgets(self, row):
        for widget in row.values():
            self.grid.removeWidget(widget)
            widget.deleteLater()


class DiagramPanel(SectionPanel):
    """Nothing selected: the diagram's own settings, and how to get started."""

    def __init__(self, services, parent=None):
        super().__init__(services, parent)
        self.title = QLineEdit(objectName="titleEdit", placeholderText=_("Untitled diagram"))
        self.title.textEdited.connect(lambda t: self.send(lambda: self.editor.set_title(t)))
        self.title.editingFinished.connect(self.done_editing)
        self.notation_caption = caption(_("Notation"))
        self.notation = Segmented([(Notation.CHEN, _("Chen")),
                                   (Notation.CROWS_FOOT, _("Crow's foot"))])
        self.notation.changed.connect(lambda n: self.send(lambda: self.editor.set_notation(n)))
        self.counts = label()
        self.help = label("", "hint")
        self.help.setWordWrap(True)
        for w in (caption(_("Title")), self.title, self.notation_caption, self.notation,
                  self.counts, self.help, self.error):
            self.layout_.addWidget(w)
        self.layout_.addStretch()

    def load(self, d: DiagramRecord):
        _set_text(self.title, d.title)
        er = d.kind is DiagramKind.ER
        self.notation_caption.setVisible(er)
        self.notation.setVisible(er)
        self.notation.set_value(d.notation)
        if er:
            self.counts.setText(f"{plural(len(d.entities), 'entity', 'entities')}, "
                                f"{plural(len(d.relationships), 'relationship')}")
            self.help.setText(_(
                "Double-click empty space to add an entity. To join entities, pick "
                "Relationship in the toolbar and click one entity, then the other (the same "
                "one twice for a recursive relationship). Drag to move; Delete removes."))
        else:
            self.counts.setText(f"{plural(len(d.classes), 'class', 'classes')}, "
                                f"{plural(len(d.links), 'link')}")
            self.help.setText(_(
                "Double-click empty space to add a class. To link classes, pick a link type "
                "in the toolbar and click one class, then the other: for inheritance, click "
                "the child first, then the parent."))


class EntityPanel(SectionPanel):
    def __init__(self, services, parent=None):
        super().__init__(services, parent)
        self.name = QLineEdit(objectName="titleEdit", placeholderText=_("Entity name"))
        self.weak = QCheckBox(_("Weak entity (identified through a relationship)"))
        self.attributes = AttributeList()
        self.name.textEdited.connect(lambda _t: self.commit())
        self.name.editingFinished.connect(self.done_editing)
        self.weak.toggled.connect(lambda _on: (self.commit(), self.done_editing()))
        self.attributes.changed.connect(self.commit)
        self.attributes.finished.connect(self.done_editing)
        hint = label(_("The key icon marks the identifier (the primary key). “0,1” marks an "
                       "optional attribute."), "hint")
        hint.setWordWrap(True)
        for w in (caption(_("Entity")), self.name, self.weak, caption(_("Attributes")),
                  self.attributes, hint, self.error):
            self.layout_.addWidget(w)
        self.layout_.addStretch()

    def load(self, e: EntityRecord):
        self.id = e.id
        _set_text(self.name, e.name)
        self.weak.blockSignals(True)
        self.weak.setChecked(e.weak)
        self.weak.blockSignals(False)
        self.attributes.set_attributes(e.attributes)

    def commit(self):
        if self.id:
            data = EntityInput(self.name.text(), self.attributes.attributes(),
                               self.weak.isChecked())
            self.send(lambda: self.editor.update_entity(self.id, data))


class RelationshipPanel(SectionPanel):
    def __init__(self, services, parent=None):
        super().__init__(services, parent)
        self.name = QLineEdit(objectName="titleEdit", placeholderText=_("Relationship name"))
        self.name.textEdited.connect(lambda _t: self.commit())
        self.name.editingFinished.connect(self.done_editing)
        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(6)
        self.grid.setVerticalSpacing(6)
        self.grid.setColumnStretch(0, 3)
        self.rows: list[dict] = []
        self.add_participant = button(_("Add an entity"), "plus")
        self.add_participant.setToolTip(_("For relationships between three or more entities"))
        self.add_participant.clicked.connect(self._add_participant)
        self.attributes = AttributeList()
        self.attributes.changed.connect(self.commit)
        self.attributes.finished.connect(self.done_editing)
        hint = label(_("(min,max) is how many times each entity takes part: (1,1) exactly "
                       "once, (0,N) any number of times. A role tells the two sides of a "
                       "recursive relationship apart."), "hint")
        hint.setWordWrap(True)
        grid_box = QWidget()
        grid_box.setLayout(self.grid)
        for w in (caption(_("Relationship")), self.name, caption(_("Entities")), grid_box,
                  self.add_participant, hint, caption(_("Attributes")), self.attributes,
                  self.error):
            self.layout_.addWidget(w, 0, Qt.AlignLeft if w is self.add_participant else Qt.Alignment())
        self.layout_.addStretch()
        self.entities: list[tuple[str, str]] = []

    def load(self, r: RelationshipRecord, entities):
        self.id = r.id
        self.entities = [(e.id, e.name) for e in entities]
        _set_text(self.name, r.name)
        if len(r.participants) != len(self.rows) or any(
                row["entity"].count() != len(self.entities) for row in self.rows):
            while self.rows:
                for w in self.rows.pop().values():
                    self.grid.removeWidget(w)
                    w.deleteLater()
            for _p in r.participants:
                self._row()
        for row, p in zip(self.rows, r.participants):
            _select(row["entity"], p.entity_id)
            _select(row["card"], p.cardinality)
            _set_text(row["role"], p.role)
            row["remove"].setEnabled(len(r.participants) > 2)
        self.attributes.set_attributes(r.attributes)

    def _row(self):
        index = len(self.rows)
        entity = QComboBox()
        for id, name in self.entities:
            entity.addItem(name, id)
        card = QComboBox()
        for c in CARDINALITIES:
            card.addItem(c, c)
        card.setToolTip(_("How many times this entity takes part: (min,max)"))
        role = QLineEdit(placeholderText=_("role"))
        role.setFixedWidth(84)
        card.setFixedWidth(84)
        remove = icon_button("x", _("Remove this entity from the relationship"))
        row = {"entity": entity, "card": card, "role": role, "remove": remove}
        self.rows.append(row)
        for column, w in enumerate(row.values()):
            self.grid.addWidget(w, index, column)
        entity.currentIndexChanged.connect(lambda _i: (self.commit(), self.done_editing()))
        card.currentIndexChanged.connect(lambda _i: (self.commit(), self.done_editing()))
        role.textEdited.connect(lambda _t: self.commit())
        role.editingFinished.connect(self.done_editing)
        remove.clicked.connect(lambda _c=False, r=row: self._remove(r))
        return row

    def _add_participant(self):
        if self.entities:
            self._row()
            self.commit()
            self.done_editing()

    def _remove(self, row):
        if len(self.rows) <= 2:
            return
        self.rows.remove(row)
        for w in row.values():
            self.grid.removeWidget(w)
            w.deleteLater()
        for index, r in enumerate(self.rows):
            for column, w in enumerate(r.values()):
                self.grid.addWidget(w, index, column)
        self.commit()
        self.done_editing()

    def commit(self):
        if not self.id:
            return
        participants = tuple(ParticipantInput(r["entity"].currentData(), r["card"].currentData(),
                                              r["role"].text()) for r in self.rows
                             if r["entity"].currentData())
        data = RelationshipInput(self.name.text(), participants, self.attributes.attributes())
        self.send(lambda: self.editor.update_relationship(self.id, data))


class ClassPanel(SectionPanel):
    def __init__(self, services, parent=None):
        super().__init__(services, parent)
        self.name = QLineEdit(objectName="titleEdit", placeholderText=_("Class name"))
        self.kind = _combo(CLASS_KINDS)
        self.attributes = QPlainTextEdit(placeholderText=_("- nome: String\n- eta: int"))
        self.operations = QPlainTextEdit(placeholderText=_("+ getNome(): String"))
        for edit in (self.attributes, self.operations):
            edit.setTabChangesFocus(True)
            edit.setMinimumHeight(110)
            edit.setFont(_mono())
            edit.textChanged.connect(self._typed)
        self.name.textEdited.connect(lambda _t: self.commit())
        self.name.editingFinished.connect(self.done_editing)
        self.kind.currentIndexChanged.connect(lambda _i: (self.commit(), self.done_editing()))
        hint = label(_("One per line. Start with + public, - private, # protected or ~ package; "
                       "write “static” or “abstract” before the name to underline it or put it "
                       "in italics."), "hint")
        hint.setWordWrap(True)
        for w in (caption(_("Class")), self.name, self.kind, caption(_("Attributes")),
                  self.attributes, caption(_("Operations")), self.operations, hint, self.error):
            self.layout_.addWidget(w)
        self.layout_.addStretch()
        self._loading = False

    def load(self, c: ClassRecord):
        self.id = c.id
        self._loading = True
        _set_text(self.name, c.name)
        _select(self.kind, c.kind)
        _set_text(self.attributes, "\n".join(m.line for m in c.attributes))
        _set_text(self.operations, "\n".join(m.line for m in c.operations))
        self._loading = False

    def _typed(self):
        if not self._loading:
            self.commit()

    def commit(self):
        if self.id:
            data = ClassInput(self.name.text(), self.kind.currentData(),
                              self.attributes.toPlainText(), self.operations.toPlainText())
            self.send(lambda: self.editor.update_class(self.id, data))

    def focusOutEvent(self, event):
        self.done_editing()
        super().focusOutEvent(event)


def _mono():
    from PySide6.QtGui import QFont
    font = QFont()
    font.setFamilies(["JetBrains Mono", "DejaVu Sans Mono", "Consolas", "monospace"])
    font.setPointSizeF(9.5)
    return font


class LinkPanel(SectionPanel):
    def __init__(self, services, parent=None):
        super().__init__(services, parent)
        self.ends = QLabel(objectName="sheetTitle", wordWrap=True)
        self.kind = _combo(LINK_KINDS)
        self.source = QComboBox()
        self.target = QComboBox()
        for combo in (self.source, self.target):
            combo.setEditable(True)
            combo.addItems(["", *MULTIPLICITIES])
            combo.currentTextChanged.connect(lambda _t: self.commit())
            combo.lineEdit().editingFinished.connect(self.done_editing)
        self.label_edit = QLineEdit(placeholderText=_("e.g. contiene"))
        self.kind.currentIndexChanged.connect(lambda _i: (self.commit(), self.done_editing()))
        self.label_edit.textEdited.connect(lambda _t: self.commit())
        self.label_edit.editingFinished.connect(self.done_editing)
        reverse = button(_("Reverse direction"), "swap")
        reverse.clicked.connect(lambda: self.send(lambda: self.editor.reverse_link(self.id)))
        self.source_caption = caption(_("Multiplicity at the start"))
        self.target_caption = caption(_("Multiplicity at the end"))
        for w in (self.ends, caption(_("Type")), self.kind, self.source_caption, self.source,
                  self.target_caption, self.target, caption(_("Label")), self.label_edit,
                  reverse, self.error):
            self.layout_.addWidget(w, 0, Qt.AlignLeft if w is reverse else Qt.Alignment())
        self.layout_.addStretch()
        self._loading = False

    def load(self, link: LinkRecord, names: dict[str, str]):
        self.id = link.id
        self._loading = True
        self.ends.setText(f"{names.get(link.source, '?')}  →  {names.get(link.target, '?')}")
        _select(self.kind, link.kind)
        for combo, text in ((self.source, link.source_multiplicity),
                            (self.target, link.target_multiplicity)):
            if not combo.lineEdit().hasFocus() and combo.currentText() != text:
                combo.setEditText(text)
        _set_text(self.label_edit, link.label)
        self._loading = False

    def commit(self):
        if self.id and not self._loading:
            data = LinkInput(self.kind.currentData(), self.source.currentText(),
                             self.target.currentText(), self.label_edit.text())
            self.send(lambda: self.editor.update_link(self.id, data))


class GeneralisationPanel(SectionPanel):
    def __init__(self, services, parent=None):
        super().__init__(services, parent)
        self.parent_label = QLabel(objectName="sheetTitle", wordWrap=True)
        self.children_box = QVBoxLayout()
        self.children_box.setSpacing(4)
        self.coverage = Segmented([(True, _("Total")), (False, _("Partial"))])
        self.overlap = Segmented([(True, _("Exclusive")), (False, _("Overlapping"))])
        self.mapping = _combo(MAPPINGS)
        self.coverage.changed.connect(lambda _v: self.commit())
        self.overlap.changed.connect(lambda _v: self.commit())
        self.mapping.currentIndexChanged.connect(lambda _i: self.commit())
        hint = label(_("Total (t): every parent is also one of the children; partial (p): not "
                       "necessarily. Exclusive (e): at most one child; overlapping (s): maybe "
                       "several. To add a child, pick Generalisation in the toolbar and click "
                       "the child, then the parent."), "hint")
        hint.setWordWrap(True)
        mapping_hint = label(_("Merging into the children needs a total generalisation whose "
                               "parent takes part in no relationship."), "hint")
        mapping_hint.setWordWrap(True)
        holder = QWidget()
        holder.setLayout(self.children_box)
        for w in (caption(_("Generalisation")), self.parent_label, caption(_("Specialisations")),
                  holder, self.coverage, self.overlap, hint, caption(_("As tables")),
                  self.mapping, mapping_hint, self.error):
            self.layout_.addWidget(w)
        self.layout_.addStretch()
        self._loading = False
        self.children: tuple[str, ...] = ()

    def load(self, g: GeneralisationRecord, names: dict[str, str]):
        self._loading = True
        self.id = g.id
        self.children = g.children
        self.parent_label.setText(_("Specialisations of {parent}").format(
            parent=names.get(g.parent, "?")))
        while self.children_box.count():
            item = self.children_box.takeAt(0)
            if item.layout():
                while item.layout().count():
                    w = item.layout().takeAt(0).widget()
                    if w:
                        w.deleteLater()
            elif item.widget():
                item.widget().deleteLater()
        for child in g.children:
            row = QHBoxLayout()
            row.addWidget(QLabel(names.get(child, "?")), 1)
            remove = icon_button("x", _("No longer a specialisation"))
            remove.clicked.connect(lambda _c=False, c=child: self._remove(c))
            row.addWidget(remove)
            self.children_box.addLayout(row)
        self.coverage.set_value(g.total)
        self.overlap.set_value(g.exclusive)
        _select(self.mapping, g.mapping)
        self._loading = False

    def _remove(self, child: str):
        self.children = tuple(c for c in self.children if c != child)
        self.commit()

    def commit(self):
        if self.id and not self._loading:
            data = GeneralisationInput(self.children, bool(self.coverage.value()),
                                       bool(self.overlap.value()), self.mapping.currentData())
            self.send(lambda: self.editor.update_generalisation(self.id, data))
            self.done_editing()


class ManyPanel(SectionPanel):
    deleteRequested = Signal()
    duplicateRequested = Signal()

    def __init__(self, services, parent=None):
        super().__init__(services, parent)
        self.count = QLabel(objectName="sheetTitle")
        duplicate = button(_("Duplicate"), "copy")
        delete = button(_("Delete"), "trash")
        delete.setObjectName("danger")
        duplicate.clicked.connect(self.duplicateRequested.emit)
        delete.clicked.connect(self.deleteRequested.emit)
        row = QHBoxLayout()
        row.addWidget(duplicate)
        row.addWidget(delete)
        row.addStretch()
        self.layout_.addWidget(self.count)
        self.layout_.addLayout(row)
        self.layout_.addStretch()

    def load(self, n: int):
        self.count.setText(_("{count} selected").format(count=n))


class PropertiesPanel(QScrollArea):
    """Shows the editor that fits the selection."""

    deleteRequested = Signal()
    duplicateRequested = Signal()

    def __init__(self, services: Services, parent=None):
        super().__init__(parent)
        self.services = services
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFixedWidth(410)
        self.stack = QStackedWidget()
        self.stack.setObjectName("card")
        self.stack.setAttribute(Qt.WA_StyledBackground, True)
        self.diagram_panel = DiagramPanel(services)
        self.entity = EntityPanel(services)
        self.relationship = RelationshipPanel(services)
        self.uml_class = ClassPanel(services)
        self.link = LinkPanel(services)
        self.generalisation = GeneralisationPanel(services)
        self.many = ManyPanel(services)
        self.many.deleteRequested.connect(self.deleteRequested.emit)
        self.many.duplicateRequested.connect(self.duplicateRequested.emit)
        self.panels = (self.diagram_panel, self.entity, self.relationship, self.uml_class,
                       self.link, self.generalisation, self.many)
        for panel in self.panels:
            holder = QWidget()
            box = QVBoxLayout(holder)
            box.setContentsMargins(18, 18, 18, 18)
            box.addWidget(panel)
            self.stack.addWidget(holder)
        self.setWidget(self.stack)
        self._shown = None

    @property
    def busy(self) -> bool:
        """An edit from this panel is on its way: don't reload it under the user's cursor."""
        return any(p.sending for p in self.panels)

    def show_selection(self, ids: list[str], d: DiagramRecord):
        if self.busy:
            return
        if len(ids) > 1:
            self._show(self.many)
            self.many.load(len(ids))
            return
        item = d.find(ids[0]) if ids else None
        if isinstance(item, EntityRecord):
            self._show(self.entity, item.id)
            self.entity.load(item)
        elif isinstance(item, RelationshipRecord):
            self._show(self.relationship, item.id)
            self.relationship.load(item, d.entities)
        elif isinstance(item, ClassRecord):
            self._show(self.uml_class, item.id)
            self.uml_class.load(item)
        elif isinstance(item, LinkRecord):
            self._show(self.link, item.id)
            self.link.load(item, {c.id: c.name for c in d.classes})
        elif isinstance(item, GeneralisationRecord):
            self._show(self.generalisation, item.id)
            self.generalisation.load(item, {e.id: e.name for e in d.entities})
        else:
            self._show(self.diagram_panel)
            self.diagram_panel.load(d)

    def _show(self, panel: SectionPanel, id: str | None = None):
        key = (panel, id)
        if self._shown != key:
            self.services.editor.end_group()
            panel.error.hide()
            self._shown = key
        index = self.panels.index(panel)
        if self.stack.currentIndex() != index:
            self.stack.setCurrentIndex(index)

    def focus_name(self):
        """Double-click on an item: jump to its name, ready to type."""
        panel = self.panels[self.stack.currentIndex()]
        name = getattr(panel, "name", None) or getattr(panel, "title", None)
        if isinstance(name, QLineEdit):
            QTimer.singleShot(0, lambda: (name.setFocus(), name.selectAll()))


