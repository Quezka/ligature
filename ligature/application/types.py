"""The enums and fixed choices the UI needs, re-exported so it never imports the domain."""
from ..domain import (  # noqa: F401
    CARDINALITIES as _CARDINALITIES, DEFAULT_TYPE, MULTIPLICITIES, ClassKind, Dialect,
    DiagramKind, IssueKind, LinkKind, Mapping, Notation,
)
from .ports import FileFormat  # noqa: F401

CARDINALITIES = tuple(str(c) for c in _CARDINALITIES)  # "(0,1)", "(1,1)", "(0,N)", "(1,N)"

# Offered in the attribute type box; any other type can be typed in.
SQL_TYPES = ("INT", "VARCHAR(50)", "VARCHAR(100)", "CHAR(10)", "TEXT", "DATE", "TIME",
             "DATETIME", "DECIMAL(10,2)", "FLOAT", "BOOLEAN")
