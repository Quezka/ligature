"""The file format, and pictures that carry the diagram inside them."""
import base64
import struct
import zlib

import pytest

from ligature.application.errors import FileAccessError, FileFormatError
from ligature.application.types import DiagramKind, FileFormat
from ligature.demo import school_er
from ligature.infrastructure.files import JsonDiagramFiles, png_source

# A 1x1 PNG.
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
SVG = b'<?xml version="1.0"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="10"><rect/></svg>'


def test_png_keeps_the_diagram_and_stays_a_valid_png(editor, tmp_path):
    school_er(editor)
    data = editor.encode(FileFormat.PNG, PNG)
    assert data.startswith(PNG[:8]) and data.endswith(PNG[-12:])  # IEND still last
    # Every chunk's CRC is right.
    pos = 8
    while pos < len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        assert struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])[0] == \
            zlib.crc32(kind + body) & 0xFFFFFFFF
        pos += 12 + length
    path = tmp_path / "registro.png"
    editor.save(str(path), picture=PNG)
    before = editor.diagram()
    editor.open(str(path))
    assert editor.diagram() == before and editor.format is FileFormat.PNG
    # Saving again replaces the diagram instead of adding a second one.
    again = JsonDiagramFiles().encode(JsonDiagramFiles().read(str(path)), FileFormat.PNG, data)
    assert again.count(b"zTXtligature") == 1


def test_svg_keeps_the_diagram(editor, tmp_path):
    school_er(editor)
    before = editor.diagram()
    path = tmp_path / "registro.svg"
    editor.save(str(path), picture=SVG)
    assert path.read_bytes().count(b"ligature-diagram") == 1
    editor.open(str(path))
    assert editor.diagram() == before


def test_open_bytes_from_the_clipboard(editor):
    school_er(editor)
    data = editor.encode(FileFormat.PNG, PNG)
    before = editor.diagram()
    editor.new(DiagramKind.UML)
    editor.open_bytes(data)
    assert editor.diagram() == before and editor.dirty and editor.path is None


def test_plain_pictures_are_refused(tmp_path):
    for name, data in (("a.png", PNG), ("a.svg", SVG)):
        (tmp_path / name).write_bytes(data)
        with pytest.raises(FileFormatError):
            JsonDiagramFiles().read(str(tmp_path / name))
    assert png_source(PNG) is None


def test_missing_file_and_newer_versions(tmp_path):
    with pytest.raises(FileAccessError):
        JsonDiagramFiles().read(str(tmp_path / "gone.ligature"))
    newer = tmp_path / "new.ligature"
    newer.write_text('{"format": "ligature", "version": 99, "kind": "er"}')
    with pytest.raises(FileFormatError, match="newer"):
        JsonDiagramFiles().read(str(newer))


def test_writing_into_a_missing_folder_fails_clearly(tmp_path):
    with pytest.raises(FileAccessError):
        JsonDiagramFiles().write(str(tmp_path / "no" / "such" / "a.ligature"), b"{}")
