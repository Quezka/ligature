"""From an ER schema to tables (the logical model) and on to CREATE TABLE statements.

The usual school rules:
- every entity becomes a table; its identifier becomes the primary key;
- a one-to-many relationship puts a foreign key on the side that takes part at most
  once, with the relationship's attributes; the key may be NULL when that side's
  minimum is 0;
- a one-to-one relationship does the same on the side whose minimum is 1, as a
  UNIQUE foreign key;
- a many-to-many (or three-way) relationship becomes a table of its own, keyed by the
  keys of the entities it joins;
- a weak entity's key also takes in the key of the entity that identifies it (through
  a relationship where the weak entity takes part exactly once, (1,1)).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum

from .model import Diagram, Entity, Participant, Relationship


class Dialect(Enum):
    STANDARD = "standard"
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"


class IssueKind(Enum):
    NO_KEY = "no_key"  # the entity has no identifier: an `id` column was made up
    WEAK_WITHOUT_OWNER = "weak_without_owner"  # weak, but nothing identifies it
    KEY_CYCLE = "key_cycle"  # weak entities that identify each other
    TOO_FEW_PARTICIPANTS = "too_few_participants"
    DUPLICATE_TABLE = "duplicate_table"
    DUPLICATE_COLUMN = "duplicate_column"


@dataclass(frozen=True)
class Issue:
    kind: IssueKind
    subject: str  # the entity, relationship or table it's about


@dataclass(frozen=True)
class Column:
    name: str
    type: str
    primary: bool = False
    nullable: bool = False
    foreign: bool = False


@dataclass(frozen=True)
class ForeignKey:
    columns: tuple[str, ...]
    table: str
    references: tuple[str, ...]
    unique: bool = False  # one-to-one


@dataclass(frozen=True)
class Table:
    name: str
    columns: tuple[Column, ...]
    foreign_keys: tuple[ForeignKey, ...] = ()
    source: str = ""  # id of the entity or relationship it comes from

    @property
    def primary_key(self) -> tuple[str, ...]:
        return tuple(c.name for c in self.columns if c.primary)


@dataclass(frozen=True)
class Schema:
    tables: tuple[Table, ...]
    issues: tuple[Issue, ...] = ()


# ---- names ------------------------------------------------------------------------------

def identifier(name: str) -> str:
    """A safe SQL name: accents dropped, spaces and punctuation turned into underscores."""
    text = unicodedata.normalize("NFKD", name)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^\w]+", "_", text, flags=re.ASCII).strip("_")
    if not text:
        return "unnamed"
    return f"_{text}" if text[0].isdigit() else text


# ---- ER -> tables -------------------------------------------------------------------------

@dataclass
class _Builder:
    name: str
    source: str
    columns: list[Column] = field(default_factory=list)
    foreign_keys: list[ForeignKey] = field(default_factory=list)

    def taken(self) -> set[str]:
        return {c.name.casefold() for c in self.columns}

    def add(self, column: Column, issues: list[Issue]):
        if column.name.casefold() in self.taken():
            issues.append(Issue(IssueKind.DUPLICATE_COLUMN, f"{self.name}.{column.name}"))
            return
        self.columns.append(column)

    def build(self) -> Table:
        # Key columns first, as schemas are usually written.
        ordered = [c for c in self.columns if c.primary] + [c for c in self.columns
                                                            if not c.primary]
        return Table(self.name, tuple(ordered), tuple(self.foreign_keys), self.source)


def _fk_names(target: str, key: list[Column], role: str, taken: set[str]) -> list[str]:
    names = []
    for column in key:
        if role:
            base = f"{column.name}_{identifier(role)}"
        elif target.casefold() in column.name.casefold():
            base = column.name  # "id_classe" stays "id_classe"
        else:
            base = f"{column.name}_{target.lower()}"
        name, n = base, 2
        while name.casefold() in taken:
            name, n = f"{base}_{n}", n + 1
        taken.add(name.casefold())
        names.append(name)
    return names


def _identifying(e: Entity, r: Relationship) -> Participant | None:
    """The other side of a binary relationship that identifies weak entity `e`."""
    if not e.weak or len(r.participants) != 2 or r.recursive:
        return None
    mine = [p for p in r.participants if p.entity_id == e.id]
    if mine and mine[0].cardinality.min == 1 and not mine[0].cardinality.many:
        return next(p for p in r.participants if p.entity_id != e.id)
    return None


def to_tables(diagram: Diagram) -> Schema:
    issues: list[Issue] = []
    entities = {e.id: e for e in diagram.entities}
    builders: dict[str, _Builder] = {}
    names_used: set[str] = set()

    def new_builder(name: str, source: str) -> _Builder:
        table = identifier(name)
        if table.casefold() in names_used:
            issues.append(Issue(IssueKind.DUPLICATE_TABLE, table))
            base, n = table, 2
            while table.casefold() in names_used:
                table, n = f"{base}_{n}", n + 1
        names_used.add(table.casefold())
        return _Builder(table, source)

    for e in diagram.entities:
        builders[e.id] = new_builder(e.name, e.id)

    # Primary keys first, since foreign keys copy them; weak entities borrow their owner's.
    keys: dict[str, list[Column]] = {}
    handled: set[str] = set()  # identifying relationships, already turned into keys
    visiting: set[str] = set()

    def key_of(entity_id: str) -> list[Column]:
        if entity_id in keys:
            return keys[entity_id]
        e, b = entities[entity_id], builders[entity_id]
        if entity_id in visiting:
            issues.append(Issue(IssueKind.KEY_CYCLE, e.name))
            return []
        visiting.add(entity_id)
        own = [Column(identifier(a.name), a.type.strip() or "VARCHAR(50)", primary=True)
               for a in e.key]
        for column in own:
            b.add(column, issues)
        borrowed = []
        for r in diagram.relationships:
            owner = _identifying(e, r)
            if owner is None:
                continue
            owner_key = key_of(owner.entity_id)
            target = builders[owner.entity_id].name
            names = _fk_names(target, owner_key, owner.role, b.taken())
            for name, column in zip(names, owner_key):
                col = Column(name, column.type, primary=True, foreign=True)
                b.add(col, issues)
                borrowed.append(col)
            b.foreign_keys.append(ForeignKey(tuple(names), target,
                                             tuple(c.name for c in owner_key)))
            _add_attributes(b, r, nullable=False, issues=issues)
            handled.add(r.id)
        if e.weak and not borrowed:
            issues.append(Issue(IssueKind.WEAK_WITHOUT_OWNER, e.name))
        key = own + borrowed
        if not key:
            if not e.weak:
                issues.append(Issue(IssueKind.NO_KEY, e.name))
            made_up = Column(_free_name("id", b.taken()), "INT", primary=True)
            b.add(made_up, issues)
            key = [made_up]
        visiting.discard(entity_id)
        keys[entity_id] = key
        return key

    for e in diagram.entities:
        key_of(e.id)

    for e in diagram.entities:
        b = builders[e.id]
        for a in e.attributes:
            if not a.key:
                b.add(Column(identifier(a.name), a.type.strip() or "VARCHAR(50)",
                             nullable=a.optional), issues)

    extra: list[_Builder] = []
    for r in diagram.relationships:
        if r.id in handled:
            continue
        parts = [p for p in r.participants if p.entity_id in entities]
        if len(parts) < 2:
            issues.append(Issue(IssueKind.TOO_FEW_PARTICIPANTS, r.name))
            continue
        holder = _holder(parts)
        if holder is not None:
            other = next(p for p in parts if p is not holder)
            b = builders[holder.entity_id]
            target_key = keys[other.entity_id]
            target = builders[other.entity_id].name
            role = other.role if r.recursive and other.role else (
                identifier(r.name) if r.recursive else "")
            names = _fk_names(target, target_key, role, b.taken())
            nullable = holder.cardinality.min == 0
            for name, column in zip(names, target_key):
                b.add(Column(name, column.type, nullable=nullable, foreign=True), issues)
            one_to_one = not other.cardinality.many
            b.foreign_keys.append(ForeignKey(tuple(names), target,
                                             tuple(c.name for c in target_key), one_to_one))
            _add_attributes(b, r, nullable=nullable, issues=issues)
            continue
        # Many-to-many, or three or more entities: a table of its own.
        b = new_builder(r.name, r.id)
        for index, p in enumerate(parts):
            target_key = keys[p.entity_id]
            target = builders[p.entity_id].name
            role = p.role or (f"{index + 1}" if r.recursive else "")
            names = _fk_names(target, target_key, role, b.taken())
            for name, column in zip(names, target_key):
                b.add(Column(name, column.type, primary=True, foreign=True), issues)
            b.foreign_keys.append(ForeignKey(tuple(names), target,
                                             tuple(c.name for c in target_key)))
        for a in r.attributes:
            b.add(Column(identifier(a.name), a.type.strip() or "VARCHAR(50)", primary=a.key,
                         nullable=a.optional and not a.key), issues)
        extra.append(b)

    tables = [builders[e.id].build() for e in diagram.entities] + [b.build() for b in extra]
    return Schema(tuple(tables), tuple(issues))


def _holder(parts: list[Participant]) -> Participant | None:
    """Which side of a binary relationship gets the foreign key (None: a table of its own)."""
    if len(parts) != 2:
        return None
    a, b = parts
    if not a.cardinality.many and b.cardinality.many:
        return a
    if not b.cardinality.many and a.cardinality.many:
        return b
    if not a.cardinality.many and not b.cardinality.many:
        return b if b.cardinality.min > a.cardinality.min else a
    return None


def _add_attributes(b: _Builder, r: Relationship, nullable: bool, issues: list[Issue]):
    for a in r.attributes:
        b.add(Column(identifier(a.name), a.type.strip() or "VARCHAR(50)",
                     nullable=nullable or a.optional), issues)


def _free_name(base: str, taken: set[str]) -> str:
    name, n = base, 2
    while name.casefold() in taken:
        name, n = f"{base}_{n}", n + 1
    return name


# ---- tables -> SQL ------------------------------------------------------------------------

RESERVED = {
    "add", "all", "alter", "and", "as", "asc", "between", "by", "case", "check", "column",
    "constraint", "create", "cross", "current_date", "database", "default", "delete", "desc",
    "distinct", "drop", "else", "end", "exists", "foreign", "from", "full", "group", "having",
    "in", "index", "inner", "insert", "into", "is", "join", "key", "left", "like", "limit",
    "not", "null", "on", "or", "order", "outer", "primary", "references", "right", "select",
    "set", "table", "then", "to", "union", "unique", "update", "user", "values", "when",
    "where", "with",
}

_POSTGRES_TYPES = {"DATETIME": "TIMESTAMP", "DOUBLE": "DOUBLE PRECISION", "TINYINT": "SMALLINT",
                   "TINYINT(1)": "BOOLEAN"}


def quote(name: str, dialect: Dialect) -> str:
    if name.casefold() not in RESERVED:
        return name
    return f"`{name}`" if dialect is Dialect.MYSQL else f'"{name}"'


def column_type(text: str, dialect: Dialect) -> str:
    text = " ".join(text.split()).upper() if re.fullmatch(r"[\w\s(),]+", text) else text
    if dialect is Dialect.POSTGRESQL:
        return _POSTGRES_TYPES.get(text, text)
    return text


def to_sql(schema: Schema, dialect: Dialect = Dialect.STANDARD) -> str:
    """CREATE TABLE statements, each table after the ones it refers to. Foreign keys that
    go round in a circle are added afterwards with ALTER TABLE."""
    q = lambda name: quote(name, dialect)  # noqa: E731
    by_name = {t.name: t for t in schema.tables}
    ordered, deferred, placed = [], [], set()
    remaining = list(schema.tables)
    while remaining:
        ready = [t for t in remaining
                 if all(fk.table in placed or fk.table == t.name or fk.table not in by_name
                        for fk in t.foreign_keys)]
        if not ready:  # a cycle: place the first and add its forward keys later
            ready = [remaining[0]]
        for t in ready:
            later = [fk for fk in t.foreign_keys
                     if fk.table not in placed and fk.table != t.name and fk.table in by_name]
            deferred.extend((t, fk) for fk in later)
            ordered.append((t, [fk for fk in t.foreign_keys if fk not in later]))
            placed.add(t.name)
            remaining.remove(t)

    out = []
    if dialect is Dialect.SQLITE:
        out.append("PRAGMA foreign_keys = ON;\n")
    for table, fks in ordered:
        lines = []
        for c in table.columns:
            null = " NOT NULL" if c.primary or not c.nullable else ""
            lines.append(f"    {q(c.name)} {column_type(c.type, dialect)}{null}")
        if table.primary_key:
            lines.append(f"    PRIMARY KEY ({', '.join(q(n) for n in table.primary_key)})")
        for fk in fks:
            if fk.unique and tuple(fk.columns) != table.primary_key:
                lines.append(f"    UNIQUE ({', '.join(q(n) for n in fk.columns)})")
            lines.append(_fk_clause(fk, q))
        tail = " ENGINE=InnoDB" if dialect is Dialect.MYSQL else ""
        out.append(f"CREATE TABLE {q(table.name)} (\n" + ",\n".join(lines) + f"\n){tail};\n")
    for table, fk in deferred:
        if fk.unique:
            out.append(f"ALTER TABLE {q(table.name)} ADD UNIQUE "
                       f"({', '.join(q(n) for n in fk.columns)});\n")
        out.append(f"ALTER TABLE {q(table.name)} ADD{_fk_clause(fk, q)[3:]};\n")
    return "\n".join(out)


def _fk_clause(fk: ForeignKey, q) -> str:
    return (f"    FOREIGN KEY ({', '.join(q(n) for n in fk.columns)}) REFERENCES "
            f"{q(fk.table)} ({', '.join(q(n) for n in fk.references)})")
