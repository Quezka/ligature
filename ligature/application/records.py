"""Read-only views of a diagram handed to the UI (so it never touches domain objects)."""
from __future__ import annotations

from dataclasses import dataclass

from .types import ClassKind, DiagramKind, IssueKind, LinkKind, Notation


@dataclass(frozen=True)
class AttributeRecord:
    name: str
    type: str
    key: bool
    optional: bool


@dataclass(frozen=True)
class EntityRecord:
    id: str
    name: str
    x: float
    y: float
    attributes: tuple[AttributeRecord, ...]
    weak: bool


@dataclass(frozen=True)
class ParticipantRecord:
    entity_id: str
    cardinality: str  # "(1,N)"
    min: int
    many: bool
    role: str


@dataclass(frozen=True)
class RelationshipRecord:
    id: str
    name: str
    x: float
    y: float
    participants: tuple[ParticipantRecord, ...]
    attributes: tuple[AttributeRecord, ...]


@dataclass(frozen=True)
class MemberRecord:
    text: str  # without visibility or modifiers: "nome: String"
    visibility: str  # "+", "-", "#", "~" or ""
    static: bool
    abstract: bool
    line: str  # as typed back into the editor: "+ static conta(): int"


@dataclass(frozen=True)
class ClassRecord:
    id: str
    name: str
    x: float
    y: float
    kind: ClassKind
    attributes: tuple[MemberRecord, ...]
    operations: tuple[MemberRecord, ...]


@dataclass(frozen=True)
class LinkRecord:
    id: str
    kind: LinkKind
    source: str
    target: str
    source_multiplicity: str
    target_multiplicity: str
    label: str


@dataclass(frozen=True)
class DiagramRecord:
    kind: DiagramKind
    title: str
    notation: Notation
    entities: tuple[EntityRecord, ...] = ()
    relationships: tuple[RelationshipRecord, ...] = ()
    classes: tuple[ClassRecord, ...] = ()
    links: tuple[LinkRecord, ...] = ()

    def find(self, id: str):
        for group in (self.entities, self.relationships, self.classes, self.links):
            for item in group:
                if item.id == id:
                    return item
        return None

    @property
    def empty(self) -> bool:
        return not (self.entities or self.relationships or self.classes or self.links)


@dataclass(frozen=True)
class ColumnRecord:
    name: str
    type: str
    primary: bool
    nullable: bool
    foreign: bool


@dataclass(frozen=True)
class ReferenceRecord:
    columns: tuple[str, ...]
    table: str
    references: tuple[str, ...]


@dataclass(frozen=True)
class TableRecord:
    name: str
    columns: tuple[ColumnRecord, ...]
    references: tuple[ReferenceRecord, ...]


@dataclass(frozen=True)
class IssueRecord:
    kind: IssueKind
    subject: str


@dataclass(frozen=True)
class SchemaRecord:
    tables: tuple[TableRecord, ...]
    issues: tuple[IssueRecord, ...]
    sql: str
