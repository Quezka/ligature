"""Diagram files on disk.

A `.ligature` file is JSON. Exported PNG and SVG pictures carry the same JSON inside
them (a compressed `zTXt` chunk in PNG, a `<metadata>` element in SVG), so a picture
pasted into notes or handed in as homework can be opened in Ligature and edited again.
"""
from __future__ import annotations

import base64
import json
import os
import re
import struct
import tempfile
import zlib
from pathlib import Path

from ..application.errors import FileAccessError, FileFormatError
from ..application.ports import FileFormat
from ..domain import (
    Attribute, Cardinality, ClassKind, Diagram, DiagramKind, Entity, Generalisation, Link,
    LinkKind, Mapping, Member, Notation, Participant, Point, Relationship, UmlClass,
)

FORMAT = "ligature"
VERSION = 1
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PNG_KEYWORD = b"ligature"
SVG_METADATA = re.compile(
    rb'<metadata id="ligature-diagram"[^>]*>\s*([A-Za-z0-9+/=\s]+?)\s*</metadata>')


class JsonDiagramFiles:
    def read(self, path: str) -> Diagram:
        try:
            data = Path(path).read_bytes()
        except FileNotFoundError:
            raise FileAccessError("That file doesn't exist any more.") from None
        except OSError as e:
            raise FileAccessError("Couldn't read the file.") from e
        return self.decode(data)

    def decode(self, data: bytes) -> Diagram:
        if data.startswith(PNG_SIGNATURE):
            source = png_source(data)
            if source is None:
                raise FileFormatError("This picture has no Ligature diagram inside it.")
        elif b"<svg" in data[:4096]:
            match = SVG_METADATA.search(data)
            if not match:
                raise FileFormatError("This picture has no Ligature diagram inside it.")
            source = base64.b64decode(b"".join(match.group(1).split()))
        else:
            source = data
        try:
            return from_json(json.loads(source.decode("utf-8")))
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            raise FileFormatError("This isn't a Ligature diagram, or it's damaged.") from e

    def encode(self, diagram: Diagram, fmt: FileFormat, picture: bytes | None = None) -> bytes:
        source = json.dumps(to_json(diagram), ensure_ascii=False, indent=1).encode("utf-8")
        if fmt is FileFormat.LIGATURE:
            return source
        if picture is None:
            raise ValueError("a picture is needed to save as PNG or SVG")
        if fmt is FileFormat.PNG:
            return png_with_source(picture, source)
        return svg_with_source(picture, source)

    def write(self, path: str, data: bytes) -> None:
        target = Path(path)
        try:
            fd, temp = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.")
            try:
                with os.fdopen(fd, "wb") as out:
                    out.write(data)
                os.replace(temp, target)
            except BaseException:
                Path(temp).unlink(missing_ok=True)
                raise
        except OSError as e:
            raise FileAccessError("Couldn't save the file there.") from e


# ---- JSON -------------------------------------------------------------------------------

def _attributes_json(items):
    return [{"name": a.name, "type": a.type, "key": a.key, "optional": a.optional}
            for a in items]


def to_json(d: Diagram) -> dict:
    out = {"format": FORMAT, "version": VERSION, "kind": d.kind.value, "title": d.title}
    if d.kind is DiagramKind.ER:
        out["notation"] = d.notation.value
        out["entities"] = [
            {"id": e.id, "name": e.name, "x": e.pos.x, "y": e.pos.y, "weak": e.weak,
             "attributes": _attributes_json(e.attributes)} for e in d.entities]
        out["relationships"] = [
            {"id": r.id, "name": r.name, "x": r.pos.x, "y": r.pos.y,
             "participants": [{"entity": p.entity_id, "cardinality": str(p.cardinality),
                               "role": p.role} for p in r.participants],
             "attributes": _attributes_json(r.attributes)} for r in d.relationships]
        out["generalisations"] = [
            {"id": g.id, "parent": g.parent, "children": list(g.children), "total": g.total,
             "exclusive": g.exclusive, "mapping": g.mapping.value}
            for g in d.generalisations]
    else:
        out["classes"] = [
            {"id": c.id, "name": c.name, "x": c.pos.x, "y": c.pos.y, "kind": c.kind.value,
             "attributes": [str(m) for m in c.attributes],
             "operations": [str(m) for m in c.operations]} for c in d.classes]
        out["links"] = [
            {"id": link.id, "kind": link.kind.value, "source": link.source,
             "target": link.target, "source_multiplicity": link.source_multiplicity,
             "target_multiplicity": link.target_multiplicity, "label": link.label}
            for link in d.links]
    return out


def _attributes(items):
    return tuple(Attribute(str(a["name"]), str(a.get("type", "")), bool(a.get("key")),
                           bool(a.get("optional"))) for a in items or ())


def _members(lines):
    return tuple(m for m in (Member.parse(str(line)) for line in lines or ()) if m)


def from_json(data: dict) -> Diagram:
    if data.get("format") != FORMAT:
        raise ValueError("not a Ligature file")
    if int(data.get("version", 1)) > VERSION:
        raise FileFormatError("This diagram was made with a newer Ligature. Update Ligature "
                              "to open it.")
    kind = DiagramKind(data["kind"])
    return Diagram(
        kind, str(data.get("title", "")), Notation(data.get("notation", "chen")),
        tuple(Entity(str(e["id"]), str(e["name"]), Point(float(e["x"]), float(e["y"])),
                     _attributes(e.get("attributes")), bool(e.get("weak")))
              for e in data.get("entities", ())),
        tuple(Relationship(
            str(r["id"]), str(r["name"]), Point(float(r["x"]), float(r["y"])),
            tuple(Participant(str(p["entity"]), Cardinality.parse(p.get("cardinality", "(0,N)")),
                              str(p.get("role", ""))) for p in r.get("participants", ())),
            _attributes(r.get("attributes"))) for r in data.get("relationships", ())),
        tuple(UmlClass(str(c["id"]), str(c["name"]), Point(float(c["x"]), float(c["y"])),
                       ClassKind(c.get("kind", "class")), _members(c.get("attributes")),
                       _members(c.get("operations"))) for c in data.get("classes", ())),
        tuple(Link(str(link["id"]), LinkKind(link["kind"]), str(link["source"]),
                   str(link["target"]), str(link.get("source_multiplicity", "")),
                   str(link.get("target_multiplicity", "")), str(link.get("label", "")))
              for link in data.get("links", ())),
        tuple(Generalisation(str(g["id"]), str(g["parent"]), tuple(str(c) for c in g["children"]),
                             bool(g.get("total")), bool(g.get("exclusive", True)),
                             Mapping(g.get("mapping", "separate")))
              for g in data.get("generalisations", ())),
    )


# ---- pictures that carry the diagram ------------------------------------------------------

def _chunks(data: bytes):
    """(type, body, start, end) for each chunk of a PNG."""
    pos = len(PNG_SIGNATURE)
    while pos + 8 <= len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        end = pos + 12 + length
        yield kind, data[pos + 8:pos + 8 + length], pos, end
        pos = end


def _chunk(kind: bytes, body: bytes) -> bytes:
    return (struct.pack(">I", len(body)) + kind + body
            + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF))


def png_with_source(png: bytes, source: bytes) -> bytes:
    """The PNG with the diagram stored in it (replacing any diagram already there)."""
    if not png.startswith(PNG_SIGNATURE):
        raise ValueError("not a PNG")
    out = [PNG_SIGNATURE]
    for kind, body, start, end in _chunks(png):
        if kind == b"zTXt" and body.startswith(PNG_KEYWORD + b"\0"):
            continue
        if kind == b"IEND":
            out.append(_chunk(b"zTXt", PNG_KEYWORD + b"\0\0" + zlib.compress(source, 9)))
        out.append(png[start:end])
    return b"".join(out)


def png_source(png: bytes) -> bytes | None:
    for kind, body, _start, _end in _chunks(png):
        if kind == b"zTXt" and body.startswith(PNG_KEYWORD + b"\0\0"):
            return zlib.decompress(body[len(PNG_KEYWORD) + 2:])
    return None


def svg_with_source(svg: bytes, source: bytes) -> bytes:
    svg = SVG_METADATA.sub(b"", svg)
    encoded = base64.b64encode(source)
    lines = b"\n".join(encoded[i:i + 76] for i in range(0, len(encoded), 76))
    element = b'<metadata id="ligature-diagram">\n' + lines + b"\n</metadata>\n"
    match = re.search(rb"<svg\b[^>]*>", svg)
    if not match:
        raise ValueError("not an SVG")
    return svg[:match.end()] + b"\n" + element + svg[match.end():]
