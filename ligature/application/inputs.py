"""What the UI sends to the use cases when something is edited."""
from __future__ import annotations

from dataclasses import dataclass

from .types import DEFAULT_TYPE, ClassKind, LinkKind, Mapping


@dataclass(frozen=True)
class AttributeInput:
    name: str
    type: str = DEFAULT_TYPE
    key: bool = False
    optional: bool = False


@dataclass(frozen=True)
class EntityInput:
    name: str
    attributes: tuple[AttributeInput, ...] = ()
    weak: bool = False


@dataclass(frozen=True)
class ParticipantInput:
    entity_id: str
    cardinality: str = "(0,N)"
    role: str = ""


@dataclass(frozen=True)
class RelationshipInput:
    name: str
    participants: tuple[ParticipantInput, ...] = ()
    attributes: tuple[AttributeInput, ...] = ()


@dataclass(frozen=True)
class ClassInput:
    name: str
    kind: ClassKind = ClassKind.CLASS
    attributes: str = ""  # one per line: "- nome: String"
    operations: str = ""  # one per line: "+ getNome(): String"


@dataclass(frozen=True)
class LinkInput:
    kind: LinkKind
    source_multiplicity: str = ""
    target_multiplicity: str = ""
    label: str = ""


@dataclass(frozen=True)
class GeneralisationInput:
    children: tuple[str, ...]
    total: bool = False
    exclusive: bool = True
    mapping: Mapping = Mapping.SEPARATE
