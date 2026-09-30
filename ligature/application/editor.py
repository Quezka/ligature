"""The open diagram and everything you can do to it, with undo and redo."""
from __future__ import annotations

import uuid
from dataclasses import replace
from enum import Enum
from pathlib import Path
from typing import Callable

from ..domain import (
    Attribute, Cardinality, ClassKind, Diagram, DiagramKind, Entity, Link, LinkKind, Member,
    Notation, Participant, Point, Relationship, UmlClass, unique_name,
)
from ..domain import Dialect, to_sql, to_tables
from .errors import NotFound
from .inputs import AttributeInput, ClassInput, EntityInput, LinkInput, RelationshipInput
from .ports import DiagramFiles, FileFormat
from .records import (
    AttributeRecord, ClassRecord, ColumnRecord, DiagramRecord, EntityRecord, IssueRecord,
    LinkRecord, MemberRecord, ParticipantRecord, ReferenceRecord, RelationshipRecord,
    SchemaRecord, TableRecord,
)

HISTORY = 200  # undo steps kept


class Change(Enum):
    DIAGRAM = "diagram"  # what's drawn changed
    DOCUMENT = "document"  # which file is open, or whether it's saved


def file_format(path: str) -> FileFormat:
    suffix = Path(path).suffix.lower()
    return {".png": FileFormat.PNG, ".svg": FileFormat.SVG}.get(suffix, FileFormat.LIGATURE)


class Editor:
    def __init__(self, files: DiagramFiles, new_id: Callable[[], str] | None = None):
        self._files = files
        self._new_id = new_id or (lambda: uuid.uuid4().hex[:10])
        self._listeners: list[Callable[[Change], None]] = []
        self._diagram = Diagram(DiagramKind.ER)
        self._saved: Diagram | None = self._diagram
        self._path: str | None = None
        self._undo: list[tuple[Diagram, str | None]] = []
        self._redo: list[Diagram] = []
        self._open = False

    # ---- notifications ------------------------------------------------------------------

    def subscribe(self, listener: Callable[[Change], None]):
        self._listeners.append(listener)

    def _emit(self, *changes: Change):
        for change in changes:
            for listener in list(self._listeners):
                listener(change)

    # ---- the document -------------------------------------------------------------------

    @property
    def is_open(self) -> bool:
        return self._open

    @property
    def path(self) -> str | None:
        return self._path

    @property
    def format(self) -> FileFormat | None:
        return file_format(self._path) if self._path else None

    @property
    def dirty(self) -> bool:
        return self._diagram is not self._saved

    @property
    def kind(self) -> DiagramKind:
        return self._diagram.kind

    def new(self, kind: DiagramKind, title: str = ""):
        self._load(Diagram(kind, title=title), None, saved=False)

    def open(self, path: str):
        self._load(self._files.read(path), str(path), saved=True)

    def open_bytes(self, data: bytes, title: str = ""):
        """A diagram from a picture (e.g. pasted), as a new unsaved document."""
        diagram = self._files.decode(data)
        self._load(replace(diagram, title=diagram.title or title), None, saved=False)

    def _load(self, diagram: Diagram, path: str | None, saved: bool):
        self._diagram = diagram
        self._saved = diagram if saved else (None if not diagram.empty else diagram)
        self._path = path
        self._undo.clear()
        self._redo.clear()
        self._open = True
        self._emit(Change.DIAGRAM, Change.DOCUMENT)

    def close(self):
        self._open = False
        self._path = None
        self._diagram = Diagram(DiagramKind.ER)
        self._saved = self._diagram
        self._undo.clear()
        self._redo.clear()
        self._emit(Change.DIAGRAM, Change.DOCUMENT)

    def save(self, path: str | None = None, picture: bytes | None = None):
        """Save to `path` (or where it came from). PNG and SVG files need the rendered
        `picture`; the diagram goes inside it so it can be opened and edited again."""
        path = str(path or self._path or "")
        if not path:
            raise NotFound("Choose where to save the diagram.")
        self._files.write(path, self.encode(file_format(path), picture))
        self._path = path
        self._saved = self._diagram
        self._emit(Change.DOCUMENT)

    def encode(self, fmt: FileFormat, picture: bytes | None = None) -> bytes:
        """The diagram as a file's contents (for saving, exporting or the clipboard)."""
        return self._files.encode(self._diagram, fmt, picture)

    def export(self, path: str, data: bytes):
        """Write a finished export (e.g. a PDF) as is; the document stays as it was."""
        self._files.write(str(path), data)

    # ---- undo ----------------------------------------------------------------------------

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def undo(self):
        if self._undo:
            self._redo.append(self._diagram)
            self._diagram, _group = self._undo.pop()
            self._emit(Change.DIAGRAM, Change.DOCUMENT)

    def redo(self):
        if self._redo:
            self._undo.append((self._diagram, None))
            self._diagram = self._redo.pop()
            self._emit(Change.DIAGRAM, Change.DOCUMENT)

    def _commit(self, diagram: Diagram, group: str | None = None):
        """Make `diagram` current as one undo step. Consecutive changes with the same
        `group` (e.g. typing the title) merge into one step."""
        if diagram == self._diagram:
            return
        if not (group and self._undo and self._undo[-1][1] == group):
            self._undo.append((self._diagram, group))
            del self._undo[:-HISTORY]
        self._redo.clear()
        self._diagram = diagram
        self._emit(Change.DIAGRAM, Change.DOCUMENT)

    def settle(self):
        """Treat what's there now as the starting point: nothing to undo, nothing unsaved
        (for samples and templates)."""
        self._undo.clear()
        self._redo.clear()
        self._saved = self._diagram
        self._emit(Change.DOCUMENT)

    def end_group(self):
        """The next change starts a new undo step even if it's of the same group."""
        if self._undo:
            self._undo[-1] = (self._undo[-1][0], None)

    # ---- reading ------------------------------------------------------------------------

    def diagram(self) -> DiagramRecord:
        return diagram_record(self._diagram)

    def schema(self, dialect: Dialect = Dialect.STANDARD) -> SchemaRecord:
        schema = to_tables(self._diagram)
        tables = tuple(
            TableRecord(t.name, tuple(ColumnRecord(c.name, c.type, c.primary, c.nullable,
                                                   c.foreign) for c in t.columns),
                        tuple(ReferenceRecord(fk.columns, fk.table, fk.references)
                              for fk in t.foreign_keys))
            for t in schema.tables)
        return SchemaRecord(tables, tuple(IssueRecord(i.kind, i.subject) for i in schema.issues),
                            to_sql(schema, dialect))

    # ---- the whole diagram ---------------------------------------------------------------

    def set_title(self, title: str):
        self._commit(replace(self._diagram, title=title.strip()), group="title")

    def set_notation(self, notation: Notation):
        self._commit(replace(self._diagram, notation=notation))

    def move(self, positions: dict[str, tuple[float, float]]):
        known = self._diagram.ids()
        self._commit(self._diagram.moved(
            {id: Point(round(x, 1), round(y, 1)) for id, (x, y) in positions.items()
             if id in known}))

    def delete(self, ids):
        self._commit(self._diagram.without(set(ids)))

    def duplicate(self, ids, offset: float = 30) -> list[str]:
        """Copies of the given entities or classes (with what joins only them)."""
        d = self._diagram
        mapping: dict[str, str] = {}
        for e in d.entities:
            if e.id in ids:
                mapping[e.id] = self._new_id()
                d = d.put(replace(e, id=mapping[e.id], name=unique_name(
                    e.name, [x.name for x in d.entities]),
                    pos=Point(e.pos.x + offset, e.pos.y + offset)))
        for c in self._diagram.classes:
            if c.id in ids:
                mapping[c.id] = self._new_id()
                d = d.put(replace(c, id=mapping[c.id], name=unique_name(
                    c.name, [x.name for x in d.classes]),
                    pos=Point(c.pos.x + offset, c.pos.y + offset)))
        for r in self._diagram.relationships:
            if r.id in ids or all(p.entity_id in mapping for p in r.participants):
                if not all(p.entity_id in mapping for p in r.participants):
                    continue
                mapping[r.id] = self._new_id()
                d = d.put(replace(
                    r, id=mapping[r.id],
                    participants=tuple(replace(p, entity_id=mapping[p.entity_id])
                                       for p in r.participants),
                    pos=Point(r.pos.x + offset, r.pos.y + offset)))
        for link in self._diagram.links:
            if link.source in mapping and link.target in mapping:
                mapping[link.id] = self._new_id()
                d = d.put(replace(link, id=mapping[link.id], source=mapping[link.source],
                                  target=mapping[link.target]))
        self._commit(d)
        return list(mapping.values())

    # ---- ER -------------------------------------------------------------------------------

    def add_entity(self, x: float, y: float, name: str = "Entity") -> str:
        id = self._new_id()
        name = unique_name(name, [e.name for e in self._diagram.entities])
        self._commit(self._diagram.put(Entity(id, name, Point(x, y))))
        return id

    def update_entity(self, id: str, data: EntityInput):
        e = self._get(self._diagram.entity, id)
        self._commit(self._diagram.put(replace(
            e, name=data.name.strip() or e.name, weak=data.weak,
            attributes=_attributes(data.attributes))), group=f"edit:{id}")

    def add_relationship(self, entity_ids: list[str], name: str = "Relationship",
                         x: float | None = None, y: float | None = None) -> str:
        entities = [self._get(self._diagram.entity, i) for i in entity_ids]
        if x is None or y is None:
            x = sum(e.pos.x for e in entities) / len(entities)
            y = sum(e.pos.y for e in entities) / len(entities)
            if len(set(entity_ids)) == 1:  # recursive: beside the entity, not on top of it
                x += 190
        id = self._new_id()
        name = unique_name(name, [r.name for r in self._diagram.relationships])
        participants = tuple(Participant(e.id, Cardinality(0, True)) for e in entities)
        self._commit(self._diagram.put(Relationship(id, name, Point(x, y), participants)))
        return id

    def update_relationship(self, id: str, data: RelationshipInput):
        r = self._get(self._diagram.relationship, id)
        known = {e.id for e in self._diagram.entities}
        participants = []
        for p in data.participants:
            if p.entity_id not in known:
                raise NotFound("That entity no longer exists.")
            participants.append(Participant(p.entity_id, Cardinality.parse(p.cardinality),
                                            p.role.strip()))
        self._commit(self._diagram.put(replace(
            r, name=data.name.strip() or r.name, participants=tuple(participants),
            attributes=_attributes(data.attributes))), group=f"edit:{id}")

    # ---- UML ------------------------------------------------------------------------------

    def add_class(self, x: float, y: float, name: str = "Class") -> str:
        id = self._new_id()
        name = unique_name(name, [c.name for c in self._diagram.classes])
        self._commit(self._diagram.put(UmlClass(id, name, Point(x, y))))
        return id

    def update_class(self, id: str, data: ClassInput):
        c = self._get(self._diagram.uml_class, id)
        self._commit(self._diagram.put(replace(
            c, name=data.name.strip() or c.name, kind=data.kind,
            attributes=_members(data.attributes), operations=_members(data.operations))),
            group=f"edit:{id}")

    def add_link(self, kind: LinkKind, source: str, target: str) -> str:
        self._get(self._diagram.uml_class, source)
        self._get(self._diagram.uml_class, target)
        id = self._new_id()
        self._commit(self._diagram.put(Link(id, kind, source, target)))
        return id

    def update_link(self, id: str, data: LinkInput):
        link = self._get(self._diagram.link, id)
        self._commit(self._diagram.put(replace(
            link, kind=data.kind, source_multiplicity=data.source_multiplicity.strip(),
            target_multiplicity=data.target_multiplicity.strip(), label=data.label.strip())),
            group=f"edit:{id}")

    def reverse_link(self, id: str):
        link = self._get(self._diagram.link, id)
        self._commit(self._diagram.put(replace(
            link, source=link.target, target=link.source,
            source_multiplicity=link.target_multiplicity,
            target_multiplicity=link.source_multiplicity)))

    # ---- helpers --------------------------------------------------------------------------

    @staticmethod
    def _get(lookup, id):
        try:
            return lookup(id)
        except KeyError:
            raise NotFound("That item is no longer in the diagram.") from None


def _attributes(items: tuple[AttributeInput, ...]) -> tuple[Attribute, ...]:
    return tuple(Attribute(a.name.strip(), a.type.strip(), a.key, a.optional and not a.key)
                 for a in items if a.name.strip())


def _members(text: str) -> tuple[Member, ...]:
    return tuple(m for m in (Member.parse(line) for line in text.splitlines()) if m)


# ---- domain -> records -----------------------------------------------------------------------

def _attribute_records(items) -> tuple[AttributeRecord, ...]:
    return tuple(AttributeRecord(a.name, a.type, a.key, a.optional) for a in items)


def _member_records(items) -> tuple[MemberRecord, ...]:
    return tuple(MemberRecord(m.text, m.visibility.value, m.static, m.abstract, str(m))
                 for m in items)


def diagram_record(d: Diagram) -> DiagramRecord:
    return DiagramRecord(
        d.kind, d.title, d.notation,
        tuple(EntityRecord(e.id, e.name, e.pos.x, e.pos.y, _attribute_records(e.attributes),
                           e.weak) for e in d.entities),
        tuple(RelationshipRecord(
            r.id, r.name, r.pos.x, r.pos.y,
            tuple(ParticipantRecord(p.entity_id, str(p.cardinality), p.cardinality.min,
                                    p.cardinality.many, p.role) for p in r.participants),
            _attribute_records(r.attributes)) for r in d.relationships),
        tuple(ClassRecord(c.id, c.name, c.pos.x, c.pos.y, c.kind,
                          _member_records(c.attributes), _member_records(c.operations))
              for c in d.classes),
        tuple(LinkRecord(link.id, link.kind, link.source, link.target, link.source_multiplicity,
                         link.target_multiplicity, link.label) for link in d.links),
    )


__all__ = ["Change", "ClassKind", "Editor", "file_format"]
