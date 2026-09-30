"""What the use cases need from the outside world, as interfaces. Adapters live in
`infrastructure`; `bootstrap` plugs them in."""
from __future__ import annotations

from enum import Enum
from typing import Protocol

from ..domain import Diagram


class FileFormat(Enum):
    LIGATURE = "ligature"  # the diagram itself (JSON)
    PNG = "png"  # a picture with the diagram inside it, so it can be edited again
    SVG = "svg"  # the same, as a vector picture


class DiagramFiles(Protocol):
    def read(self, path: str) -> Diagram:
        """Load a diagram from a .ligature file, or from a PNG/SVG Ligature exported.
        Raises FileFormatError or FileAccessError."""
        ...

    def encode(self, diagram: Diagram, fmt: FileFormat, picture: bytes | None = None) -> bytes:
        """The file's bytes: the diagram as JSON, or `picture` with the diagram inside."""
        ...

    def decode(self, data: bytes) -> Diagram:
        """The diagram inside a file's bytes (e.g. an image pasted from the clipboard)."""
        ...

    def write(self, path: str, data: bytes) -> None:
        """Write the whole file safely (never leaves half a file behind)."""
        ...
