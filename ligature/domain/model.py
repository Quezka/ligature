"""What a diagram is: an ER schema (entities and relationships) or a UML class diagram
(classes and the links between them). Plain immutable values; editing makes new ones.

Positions are the centre of each box, in scene units (roughly pixels at 100% zoom).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, replace
from enum import Enum


class DiagramKind(Enum):
    ER = "er"
    UML = "uml"


class Notation(Enum):
    """How an ER diagram is drawn. The model is the same; only the picture changes."""

    CHEN = "chen"  # rectangles, diamonds, attribute lollipops, (min,max) labels
    CROWS_FOOT = "crows_foot"  # entity tables joined by lines with crow's-foot ends


class ClassKind(Enum):
    CLASS = "class"
    ABSTRACT = "abstract"
    INTERFACE = "interface"
    ENUM = "enum"


class LinkKind(Enum):
    ASSOCIATION = "association"
    DIRECTED = "directed"  # navigable association: an open arrow at the target
    AGGREGATION = "aggregation"  # hollow diamond at the source (the whole)
    COMPOSITION = "composition"  # filled diamond at the source (the whole)
    INHERITANCE = "inheritance"  # hollow triangle at the target (the parent)
    REALIZATION = "realization"  # dashed, hollow triangle at the target (the interface)
    DEPENDENCY = "dependency"  # dashed, open arrow at the target


class Visibility(Enum):
    PUBLIC = "+"
    PRIVATE = "-"
    PROTECTED = "#"
    PACKAGE = "~"
    NONE = ""


@dataclass(frozen=True)
class Point:
    x: float
    y: float


# ---- ER --------------------------------------------------------------------------------

DEFAULT_TYPE = "VARCHAR(50)"


@dataclass(frozen=True)
class Attribute:
    name: str
    type: str = DEFAULT_TYPE
    key: bool = False  # part of the entity's identifier (primary key)
    optional: bool = False  # may be left empty: (0,1); becomes a NULL column


@dataclass(frozen=True)
class Entity:
    id: str
    name: str
    pos: Point
    attributes: tuple[Attribute, ...] = ()
    weak: bool = False  # identified through a relationship to another entity as well

    @property
    def key(self) -> tuple[Attribute, ...]:
        return tuple(a for a in self.attributes if a.key)


@dataclass(frozen=True)
class Cardinality:
    """How many times one entity takes part in a relationship: (min, max), max 1 or N."""

    min: int = 0  # 0 or 1
    many: bool = True  # max N (True) or 1 (False)

    def __str__(self) -> str:
        return f"({self.min},{'N' if self.many else '1'})"

    @classmethod
    def parse(cls, text: str) -> "Cardinality":
        m = re.fullmatch(r"\s*\(?\s*([01])\s*,\s*([1nN*])\s*\)?\s*", text)
        if not m:
            raise ValueError(f"not a cardinality: {text!r}")
        return cls(int(m.group(1)), m.group(2) in "nN*")


CARDINALITIES = (Cardinality(0, False), Cardinality(1, False), Cardinality(0, True),
                 Cardinality(1, True))


@dataclass(frozen=True)
class Participant:
    entity_id: str
    cardinality: Cardinality = Cardinality()
    role: str = ""  # needed to tell the two sides apart in a recursive relationship


@dataclass(frozen=True)
class Relationship:
    id: str
    name: str
    pos: Point
    participants: tuple[Participant, ...] = ()
    attributes: tuple[Attribute, ...] = ()

    @property
    def recursive(self) -> bool:
        ids = [p.entity_id for p in self.participants]
        return len(set(ids)) < len(ids)


class Mapping(Enum):
    """How a generalisation becomes tables (the three ways taught at school)."""

    SEPARATE = "separate"  # every entity keeps its table; children borrow the parent's key
    INTO_PARENT = "into_parent"  # one table: the parent's, with the children's attributes
    INTO_CHILDREN = "into_children"  # one table per child, each with the parent's attributes


@dataclass(frozen=True)
class Generalisation:
    """A parent entity and its specialisations (ISA). Total: every parent is one of the
    children; exclusive: never more than one of them."""

    id: str
    parent: str
    children: tuple[str, ...]
    total: bool = False
    exclusive: bool = True
    mapping: Mapping = Mapping.SEPARATE

    @property
    def label(self) -> str:
        return f"({'t' if self.total else 'p'},{'e' if self.exclusive else 's'})"


# ---- UML ---------------------------------------------------------------------------------

@dataclass(frozen=True)
class Member:
    """One line in a class box: an attribute ("nome: String") or an operation
    ("getNome(): String"), with its visibility."""

    text: str
    visibility: Visibility = Visibility.NONE
    static: bool = False  # drawn underlined
    abstract: bool = False  # drawn in italics

    def __str__(self) -> str:
        words = (["static"] if self.static else []) + (["abstract"] if self.abstract else [])
        prefix = self.visibility.value + (" " if self.visibility.value else "")
        return prefix + " ".join(words + [self.text])

    @classmethod
    def parse(cls, line: str) -> "Member | None":
        """Read a member as a student types it: "- nome: String", "+ static conta(): int",
        "# abstract area(): double". Blank lines are None."""
        text = line.strip()
        if not text:
            return None
        visibility = Visibility.NONE
        for v in Visibility:
            if v.value and text.startswith(v.value):
                visibility, text = v, text[1:].lstrip()
                break
        static = abstract = False
        while True:
            if m := re.match(r"(?i)(static|\{static\})\s+", text):
                static, text = True, text[m.end():]
            elif m := re.match(r"(?i)(abstract|\{abstract\})\s+", text):
                abstract, text = True, text[m.end():]
            else:
                break
        return cls(text, visibility, static, abstract) if text else None


@dataclass(frozen=True)
class UmlClass:
    id: str
    name: str
    pos: Point
    kind: ClassKind = ClassKind.CLASS
    attributes: tuple[Member, ...] = ()
    operations: tuple[Member, ...] = ()


@dataclass(frozen=True)
class Link:
    id: str
    kind: LinkKind
    source: str
    target: str
    source_multiplicity: str = ""
    target_multiplicity: str = ""
    label: str = ""


MULTIPLICITIES = ("1", "0..1", "*", "0..*", "1..*")


# ---- the diagram --------------------------------------------------------------------------

@dataclass(frozen=True)
class Diagram:
    kind: DiagramKind
    title: str = ""
    notation: Notation = Notation.CHEN
    entities: tuple[Entity, ...] = ()
    relationships: tuple[Relationship, ...] = ()
    classes: tuple[UmlClass, ...] = ()
    links: tuple[Link, ...] = ()
    generalisations: tuple[Generalisation, ...] = ()

    # ---- lookups --------------------------------------------------------------------

    def entity(self, id: str) -> Entity:
        return _find(self.entities, id)

    def relationship(self, id: str) -> Relationship:
        return _find(self.relationships, id)

    def uml_class(self, id: str) -> UmlClass:
        return _find(self.classes, id)

    def link(self, id: str) -> Link:
        return _find(self.links, id)

    def generalisation(self, id: str) -> Generalisation:
        return _find(self.generalisations, id)

    def ids(self) -> set[str]:
        return {x.id for group in (self.entities, self.relationships, self.classes, self.links,
                                   self.generalisations) for x in group}

    @property
    def empty(self) -> bool:
        return not self.ids()

    # ---- changes (each returns a new diagram) -----------------------------------------

    def put(self, item) -> "Diagram":
        """Add the item, or replace the one with the same id."""
        name = _collection(item)
        items = getattr(self, name)
        if any(x.id == item.id for x in items):
            items = tuple(item if x.id == item.id else x for x in items)
        else:
            items = items + (item,)
        return replace(self, **{name: items})

    def moved(self, positions: dict[str, Point]) -> "Diagram":
        def move(items):
            return tuple(replace(x, pos=positions[x.id]) if x.id in positions else x
                         for x in items)
        return replace(self, entities=move(self.entities),
                       relationships=move(self.relationships), classes=move(self.classes))

    def without(self, ids: set[str]) -> "Diagram":
        """Delete these items and whatever hangs off them: an entity's places in
        relationships (a relationship left with fewer than two goes too), a class's links."""
        entities = tuple(e for e in self.entities if e.id not in ids)
        kept = {e.id for e in entities}
        relationships = []
        for r in self.relationships:
            if r.id in ids:
                continue
            participants = tuple(p for p in r.participants if p.entity_id in kept)
            if len(participants) >= 2 or (participants and len(participants) == len(r.participants)):
                relationships.append(replace(r, participants=participants))
        classes = tuple(c for c in self.classes if c.id not in ids)
        kept_classes = {c.id for c in classes}
        links = tuple(l for l in self.links if l.id not in ids
                      and l.source in kept_classes and l.target in kept_classes)
        generalisations = []
        for g in self.generalisations:
            children = tuple(c for c in g.children if c in kept)
            if g.id not in ids and g.parent in kept and children:
                generalisations.append(replace(g, children=children))
        return replace(self, entities=entities, relationships=tuple(relationships),
                       classes=classes, links=links, generalisations=tuple(generalisations))


def _find(items, id):
    for x in items:
        if x.id == id:
            return x
    raise KeyError(id)


def _collection(item) -> str:
    return {Entity: "entities", Relationship: "relationships", UmlClass: "classes",
            Link: "links", Generalisation: "generalisations"}[type(item)]


def unique_name(base: str, taken) -> str:
    """"Entity", "Entity 2", "Entity 3"… whichever is free (case-insensitively)."""
    taken = {t.casefold() for t in taken}
    if base.casefold() not in taken:
        return base
    n = 2
    while f"{base} {n}".casefold() in taken:
        n += 1
    return f"{base} {n}"


__all__ = [
    "Attribute", "CARDINALITIES", "Cardinality", "ClassKind", "DEFAULT_TYPE", "Diagram",
    "DiagramKind", "Entity", "Generalisation", "Link", "LinkKind", "MULTIPLICITIES", "Mapping",
    "Member", "Notation",
    "Participant", "Point", "Relationship", "UmlClass", "Visibility", "unique_name",
]
