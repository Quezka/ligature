"""The drawing: a QGraphicsScene built from a DiagramRecord, and the view you pan and zoom.

Each entity, relationship or class is a node you can drag; the lines between them
follow. The scene is rebuilt from the record after every change, keeping the selection.
ER diagrams are drawn in Chen notation (rectangles, diamonds, attribute lollipops,
(min,max) labels) or crow's foot (entity tables, lines with crow's-foot ends).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import QEvent, QLineF, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QColor, QFont, QFontMetricsF, QPainter, QPainterPath, QPainterPathStroker, QPen, QPolygonF,
)
from PySide6.QtWidgets import QGraphicsItem, QGraphicsScene, QGraphicsView

from ..application.records import (
    ClassRecord, DiagramRecord, EntityRecord, GeneralisationRecord, LinkRecord, RelationshipRecord,
)
from ..application.types import ClassKind, DiagramKind, LinkKind, Notation
from . import theme

GRID = 10  # positions snap to this
STICK = 16  # attribute lollipop length
DOT = 4.5  # attribute lollipop radius


# ---- colours and fonts ----------------------------------------------------------------------

@dataclass(frozen=True)
class Style:
    paper: str
    grid: str
    fill: str
    header: str
    border: str
    text: str
    muted: str
    line: str
    accent: str
    accent_soft: str
    relationship: str
    amber: str


def style_for(t: theme.Theme) -> Style:
    if t.dark:
        return Style(paper=t.bg, grid="#24262b", fill=t.surface, header="#23243a",
                     border="#50535c", text=t.text, muted=t.muted, line="#8a8f99",
                     accent=t.accent, accent_soft=t.accent_soft, relationship="#2b2a1f",
                     amber="#f5a524")
    return Style(paper="#ffffff", grid="#e4e6eb", fill="#ffffff", header="#eeeefc",
                 border="#3a3f4a", text=t.text, muted=t.muted, line="#3a3f4a",
                 accent=t.accent, accent_soft=t.accent_soft, relationship="#fff6e5",
                 amber="#f5a524")


EXPORT_STYLE = style_for(theme.LIGHT)  # pictures always come out on white


def _font(size: float, bold: bool = False, italic: bool = False) -> QFont:
    """Sized in pixels (scene units), so text measures the same on screen and in exports
    of any resolution; `size` is in points at 96 dpi."""
    font = QFont()
    font.setPixelSize(round(size * 4 / 3))
    font.setBold(bold)
    font.setItalic(italic)
    return font


NAME_FONT = _font(10, bold=True)
TEXT_FONT = _font(9)
SMALL_FONT = _font(8.5)


def _width(font: QFont, text: str) -> float:
    return QFontMetricsF(font).horizontalAdvance(text)


def _height(font: QFont) -> float:
    return QFontMetricsF(font).height()


def pen(color: str, width: float = 1.4, dashed: bool = False) -> QPen:
    p = QPen(QColor(color), width)
    p.setJoinStyle(Qt.RoundJoin)
    p.setCapStyle(Qt.RoundCap)
    if dashed:
        p.setDashPattern([5, 4])
    return p


# ---- geometry ---------------------------------------------------------------------------------

def exit_point(polygon: QPolygonF, inside: QPointF, outside: QPointF) -> QPointF:
    """Where the segment from `inside` to `outside` crosses the polygon's edge."""
    segment = QLineF(inside, outside)
    best, best_t = None, None
    for i in range(polygon.size()):
        edge = QLineF(polygon.at(i), polygon.at((i + 1) % polygon.size()))
        kind, point = segment.intersects(edge)
        if kind == QLineF.BoundedIntersection:
            t = QLineF(inside, point).length()
            if best_t is None or t > best_t:
                best, best_t = point, t
    return best if best is not None else inside


def _unit(a: QPointF, b: QPointF) -> QPointF:
    dx, dy = b.x() - a.x(), b.y() - a.y()
    length = math.hypot(dx, dy) or 1.0
    return QPointF(dx / length, dy / length)


def _normal(u: QPointF) -> QPointF:
    return QPointF(-u.y(), u.x())


# ---- nodes ----------------------------------------------------------------------------------

class Node(QGraphicsItem):
    """Something you can drag: an entity, a relationship or a class."""

    def __init__(self, record, style: Style, blocked: tuple[bool, bool] = (False, False)):
        super().__init__()
        self.record = record
        self.id = record.id
        self.style = style
        # Whether lines leave from the top / bottom: Chen attributes go elsewhere.
        self.blocked = blocked
        self.warning = ""  # set by the scene: something to fix (shown as a badge)
        self.edges: list[Edge] = []
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable
                      | QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self.setZValue(2)
        self.setPos(record.x, record.y)
        self.layout()

    def layout(self):
        """Work out the sizes (in item coordinates, centred on 0,0)."""
        self.body = QRectF(-60, -24, 120, 48)
        self.bounds = self.body

    def outline(self) -> QPolygonF:
        """The edge lines stop at, in item coordinates."""
        return QPolygonF(self.body)

    def scene_outline(self) -> QPolygonF:
        return self.mapToScene(self.outline())

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        path.addPolygon(self.outline())
        path.closeSubpath()
        return path

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            scene = self.scene()
            if scene is not None and scene.mouseGrabberItem() is self and hasattr(scene, "align"):
                return scene.align(self, value)
        if change == QGraphicsItem.ItemPositionHasChanged:
            for edge in self.edges:
                edge.refresh()
        return super().itemChange(change, value)

    def set_warning(self, text: str):
        self.warning = text
        self.setToolTip(text)

    def _badge(self, painter: QPainter):
        """A small amber "!" on the corner of something that needs fixing (never exported)."""
        scene = self.scene()
        if not self.warning or scene is None or not getattr(scene, "grid", False):
            return
        centre = QPointF(self.body.right() - 2, self.body.top() + 2)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(self.style.amber))
        painter.drawEllipse(centre, 8, 8)
        painter.setPen(QColor("#ffffff"))
        painter.setFont(_font(9, bold=True))
        painter.drawText(QRectF(centre.x() - 8, centre.y() - 8, 16, 16), Qt.AlignCenter, "!")

    def boundingRect(self) -> QRectF:  # room for the warning badge
        return self.bounds.adjusted(-3, -11, 11, 3)

    def _border(self, painter: QPainter, width: float = 1.4):
        if self.isSelected():
            painter.setPen(pen(self.style.accent, 2.4))
        else:
            painter.setPen(pen(self.style.border, width))

    def _lollipops(self, painter: QPainter, attributes, top_edge, bottom_edge):
        """Chen attributes: a stick with a dot (filled for the key) and the name, in a row
        above the shape and, when there are many, a row below."""
        for attribute, x, top in self._attribute_slots(attributes):
            edge_y = top_edge(x) if top else bottom_edge(x)
            direction = -1 if top else 1
            end = edge_y + direction * STICK
            painter.setPen(pen(self.style.line, 1.2))
            painter.drawLine(QPointF(x, edge_y), QPointF(x, end))
            centre = QPointF(x, end + direction * DOT)
            painter.setBrush(QColor(self.style.text if attribute.key else self.style.fill))
            painter.drawEllipse(centre, DOT, DOT)
            label = _attribute_label(attribute)
            painter.setFont(SMALL_FONT)
            painter.setPen(QColor(self.style.text))
            h = _height(SMALL_FONT)
            w = _width(SMALL_FONT, label) + 4
            y = centre.y() - DOT - h if top else centre.y() + DOT
            painter.drawText(QRectF(x - w / 2, y, w, h), Qt.AlignCenter, label)
            if attribute.key:  # underlined, as the identifier is written
                painter.drawLine(QPointF(x - w / 2 + 2, y + h - 1.5),
                                 QPointF(x + w / 2 - 2, y + h - 1.5))

    def _attribute_slots(self, attributes):
        top_count = _top_count(attributes, self.blocked)
        rows = [attributes[:top_count], attributes[top_count:]]
        for row, top in zip(rows, (True, False)):
            if not row:
                continue
            spacing = _row_spacing(row)
            start = -spacing * (len(row) - 1) / 2
            for i, attribute in enumerate(row):
                yield attribute, start + i * spacing, top


def _attribute_label(attribute) -> str:
    return f"{attribute.name} (0,1)" if attribute.optional else attribute.name


def _row_spacing(row) -> float:
    return max(38.0, max(_width(SMALL_FONT, _attribute_label(a)) for a in row) + 14)


def _top_count(attributes, blocked: tuple[bool, bool]) -> int:
    """How many attributes go in the row above (the rest go below): all of them on the
    side no line leaves from, else split in two when there are more than two."""
    n = len(attributes)
    top_blocked, bottom_blocked = blocked
    if top_blocked and not bottom_blocked:
        return 0
    if bottom_blocked and not top_blocked:
        return n
    return math.ceil(n / 2) if n > 2 else n


def _rows_width(attributes, blocked=(False, False)) -> float:
    top_count = _top_count(attributes, blocked)
    rows = [r for r in (attributes[:top_count], attributes[top_count:]) if r]
    return max((len(r) * _row_spacing(r) for r in rows), default=0.0)


def _lollipop_extent(attributes, blocked=(False, False)) -> tuple[float, float]:
    """How far the attribute rows reach above and below the shape."""
    reach = STICK + 2 * DOT + _height(SMALL_FONT)
    top_count = _top_count(attributes, blocked)
    return ((reach if top_count else 0.0),
            (reach if len(attributes) > top_count else 0.0))


class ChenEntity(Node):
    record: EntityRecord

    def layout(self):
        r = self.record
        rows = _rows_width(r.attributes, self.blocked)
        w = max(110.0, _width(NAME_FONT, r.name) + 36, rows + 12)
        self.body = QRectF(-w / 2, -24, w, 48)
        above, below = _lollipop_extent(r.attributes, self.blocked)
        wide = max(w, rows)
        self.bounds = QRectF(-wide / 2, -24 - above, wide, 48 + above + below)

    def paint(self, painter, option, widget=None):
        s, r = self.style, self.record
        painter.setRenderHint(QPainter.Antialiasing)
        self._lollipops(painter, r.attributes, lambda x: self.body.top(),
                        lambda x: self.body.bottom())
        painter.setBrush(QColor(s.fill))
        self._border(painter)
        painter.drawRoundedRect(self.body, 3, 3)
        if r.weak:
            painter.drawRoundedRect(self.body.adjusted(4, 4, -4, -4), 2, 2)
        painter.setPen(QColor(s.text))
        painter.setFont(NAME_FONT)
        painter.drawText(self.body, Qt.AlignCenter, r.name)
        self._badge(painter)


class ChenRelationship(Node):
    record: RelationshipRecord

    def layout(self):
        r = self.record
        rows = _rows_width(r.attributes, self.blocked)
        w = max(104.0, _width(NAME_FONT, r.name) * 1.5 + 30, rows * 1.4)
        h = max(56.0, min(w * 0.5, 72.0))
        self.half = (w / 2, h / 2)
        self.body = QRectF(-w / 2, -h / 2, w, h)
        above, below = _lollipop_extent(r.attributes, self.blocked)
        wide = max(w, rows)
        self.bounds = QRectF(-wide / 2, -h / 2 - above, wide, h + above + below)

    def outline(self) -> QPolygonF:
        w, h = self.half
        return QPolygonF([QPointF(0, -h), QPointF(w, 0), QPointF(0, h), QPointF(-w, 0)])

    def paint(self, painter, option, widget=None):
        s, r = self.style, self.record
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.half
        edge = lambda x: h * (1 - min(abs(x) / w, 1.0))  # noqa: E731
        self._lollipops(painter, r.attributes, lambda x: -edge(x), edge)
        painter.setBrush(QColor(s.relationship))
        self._border(painter)
        painter.drawPolygon(self.outline())
        painter.setPen(QColor(s.text))
        painter.setFont(NAME_FONT)
        painter.drawText(self.body, Qt.AlignCenter, r.name)


class TableEntity(Node):
    """Crow's foot: the entity as a table of its attributes, key first."""

    record: EntityRecord
    HEADER = 30.0
    ROW = 22.0

    def layout(self):
        r = self.record
        rows = self._rows()
        widths = [_width(NAME_FONT, r.name) + 32]
        for key, name, kind in rows:
            widths.append(26 + _width(TEXT_FONT, name) + 18 + _width(SMALL_FONT, kind) + 12)
        w = max(140.0, *widths)
        h = self.HEADER + max(1, len(rows)) * self.ROW + 6
        self.body = QRectF(-w / 2, -h / 2, w, h)
        self.bounds = self.body

    def _rows(self):
        attributes = sorted(self.record.attributes, key=lambda a: not a.key)
        return [(a.key, a.name + ("?" if a.optional else ""), a.type) for a in attributes]

    def paint(self, painter, option, widget=None):
        s, r, b = self.style, self.record, self.body
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(s.fill))
        self._border(painter)
        painter.drawRoundedRect(b, 6, 6)
        header = QRectF(b.left(), b.top(), b.width(), self.HEADER)
        clip = QPainterPath()
        clip.addRoundedRect(b, 6, 6)
        painter.save()
        painter.setClipPath(clip)
        painter.fillRect(header, QColor(s.header))
        painter.restore()
        self._border(painter)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(b, 6, 6)
        if r.weak:
            painter.drawRoundedRect(b.adjusted(3, 3, -3, -3), 4, 4)
        painter.setPen(pen(s.border, 1))
        painter.drawLine(QPointF(b.left(), header.bottom()), QPointF(b.right(), header.bottom()))
        painter.setPen(QColor(s.text))
        painter.setFont(NAME_FONT)
        painter.drawText(header, Qt.AlignCenter, r.name)
        y = header.bottom() + 3
        for key, name, kind in self._rows():
            row = QRectF(b.left() + 10, y, b.width() - 20, self.ROW)
            if key:
                painter.setPen(QColor(s.accent))
                painter.setFont(_font(7.5, bold=True))
                painter.drawText(QRectF(row.left(), y, 22, self.ROW), Qt.AlignVCenter, "PK")
            painter.setPen(QColor(s.text))
            font = _font(9, bold=key)
            font.setUnderline(key)
            painter.setFont(font)
            painter.drawText(row.adjusted(22, 0, 0, 0), Qt.AlignVCenter | Qt.AlignLeft, name)
            painter.setPen(QColor(s.muted))
            painter.setFont(SMALL_FONT)
            painter.drawText(row, Qt.AlignVCenter | Qt.AlignRight, kind)
            y += self.ROW
        self._badge(painter)


class CrowRelationship(Node):
    """Crow's foot: the relationship is a label on the line (a small diamond when it joins
    three or more entities); drag it to bend the line."""

    record: RelationshipRecord

    def layout(self):
        r = self.record
        lines = [a.name + (f": {a.type}" if a.type else "") for a in r.attributes]
        w = max([_width(_font(9, bold=True, italic=True), r.name)]
                + [_width(SMALL_FONT, line) for line in lines]) + 16
        h = _height(TEXT_FONT) + len(lines) * _height(SMALL_FONT) + 8
        self.lines = lines
        self.nary = len(r.participants) > 2
        if self.nary:
            self.diamond = QRectF(-18, -14, 36, 28)
            self.label = QRectF(22, -h / 2, w, h)
            self.body = self.diamond
            self.bounds = self.diamond.united(self.label)
        else:
            self.label = QRectF(-w / 2, -h / 2, w, h)
            self.body = self.label
            self.bounds = self.label

    def outline(self) -> QPolygonF:
        if self.nary:
            d = self.diamond
            return QPolygonF([QPointF(0, d.top()), QPointF(d.right(), 0), QPointF(0, d.bottom()),
                              QPointF(d.left(), 0)])
        return QPolygonF(self.body)

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        path.addRect(self.bounds)
        return path

    def paint(self, painter, option, widget=None):
        s, r = self.style, self.record
        painter.setRenderHint(QPainter.Antialiasing)
        if self.nary:
            painter.setBrush(QColor(s.relationship))
            self._border(painter)
            painter.drawPolygon(self.outline())
        painter.setBrush(QColor(s.paper))
        if self.isSelected():
            painter.setPen(pen(s.accent, 1.6))
        else:
            painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.label, 6, 6)
        painter.setPen(QColor(s.text))
        painter.setFont(_font(9, bold=True, italic=True))
        h = _height(TEXT_FONT)
        painter.drawText(QRectF(self.label.left(), self.label.top() + 4, self.label.width(), h),
                         Qt.AlignCenter, r.name)
        painter.setPen(QColor(s.muted))
        painter.setFont(SMALL_FONT)
        y = self.label.top() + 4 + h
        for line in self.lines:
            painter.drawText(QRectF(self.label.left(), y, self.label.width(),
                                    _height(SMALL_FONT)), Qt.AlignCenter, line)
            y += _height(SMALL_FONT)


class ClassBox(Node):
    """UML class: name, attributes and operations in three compartments."""

    record: ClassRecord
    LINE = 19.0

    def layout(self):
        r = self.record
        self.stereotype = {ClassKind.INTERFACE: "«interface»",
                           ClassKind.ENUM: "«enumeration»"}.get(r.kind, "")
        header = 30.0 + (14.0 if self.stereotype else 0.0)
        texts = [_member_text(m) for m in (*r.attributes, *r.operations)]
        w = max([150.0, _width(NAME_FONT, r.name) + 32]
                + [_width(TEXT_FONT, t) + 22 for t in texts])
        attrs = max(1, len(r.attributes)) * self.LINE + 8
        ops = max(1, len(r.operations)) * self.LINE + 8
        h = header + attrs + ops
        self.header_h, self.attrs_h = header, attrs
        self.body = QRectF(-w / 2, -h / 2, w, h)
        self.bounds = self.body

    def paint(self, painter, option, widget=None):
        s, r, b = self.style, self.record, self.body
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(s.fill))
        self._border(painter)
        painter.drawRect(b)
        head = QRectF(b.left(), b.top(), b.width(), self.header_h)
        painter.fillRect(head.adjusted(1, 1, -1, 0), QColor(s.header))
        painter.setPen(pen(s.border, 1))
        y1 = b.top() + self.header_h
        y2 = y1 + self.attrs_h
        painter.drawLine(QPointF(b.left(), y1), QPointF(b.right(), y1))
        painter.drawLine(QPointF(b.left(), y2), QPointF(b.right(), y2))
        painter.setPen(QColor(s.text))
        if self.stereotype:
            painter.setFont(SMALL_FONT)
            painter.drawText(QRectF(b.left(), b.top() + 5, b.width(), 14), Qt.AlignCenter,
                             self.stereotype)
            name_rect = QRectF(b.left(), b.top() + 17, b.width(), self.header_h - 17)
        else:
            name_rect = head
        painter.setFont(_font(10, bold=True, italic=r.kind is ClassKind.ABSTRACT))
        painter.drawText(name_rect, Qt.AlignCenter, r.name)
        for members, top in ((r.attributes, y1), (r.operations, y2)):
            y = top + 4
            for m in members:
                font = _font(9, italic=m.abstract)
                font.setUnderline(m.static)
                painter.setFont(font)
                painter.drawText(QRectF(b.left() + 10, y, b.width() - 16, self.LINE),
                                 Qt.AlignVCenter | Qt.AlignLeft, _member_text(m))
                y += self.LINE
        if self.isSelected():  # the border again on top of the header fill
            self._border(painter)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(b)


def _member_text(m) -> str:
    return f"{m.visibility} {m.text}" if m.visibility else m.text


# ---- lines -----------------------------------------------------------------------------------

class Edge(QGraphicsItem):
    def __init__(self, style: Style):
        super().__init__()
        self.style = style
        self.setZValue(1)
        self.path = QPainterPath()

    def attach(self, *nodes: Node):
        for node in nodes:
            node.edges.append(self)
        self.refresh()

    def refresh(self):
        self.prepareGeometryChange()
        self.compute()

    def compute(self):
        pass

    def boundingRect(self) -> QRectF:
        return self.path.boundingRect().adjusted(-40, -30, 40, 30)

    def _text(self, painter, anchor: QPointF, text: str, font=SMALL_FONT, color=None,
              background=True):
        w, h = _width(font, text) + 6, _height(font)
        rect = QRectF(anchor.x() - w / 2, anchor.y() - h / 2, w, h)
        if background:
            painter.fillRect(rect, QColor(self.style.paper))
        painter.setFont(font)
        painter.setPen(QColor(color or self.style.text))
        painter.drawText(rect, Qt.AlignCenter, text)

    def _label_spot(self, text: str, font=SMALL_FONT) -> QPointF:
        """Where to write a cardinality beside the entity end: next to the line, as near
        the entity as it gets without touching the entity, the relationship or the line.
        When it can't fit anywhere (a very short line), the least crowded spot wins."""
        u = _unit(self.b, self.a)  # from the entity towards the relationship
        n = _normal(u)
        w, h = _width(font, text) + 6, _height(font)
        # How far the label's centre must sit from the line for its box to clear it.
        away = abs(n.x()) * w / 2 + abs(n.y()) * h / 2 + 3
        thin = QPolygonF([self.a + QPointF(n.x(), n.y()), self.b + QPointF(n.x(), n.y()),
                          self.b - QPointF(n.x(), n.y()), self.a - QPointF(n.x(), n.y())])
        avoid = [self.entity.scene_outline(), self.relationship.scene_outline(), thin]
        reach = math.hypot(self.a.x() - self.b.x(), self.a.y() - self.b.y())
        above = 1 if n.y() <= 0 else -1
        best, fewest = None, 99
        for side in (above, -above):
            d = 12.0
            while d <= max(reach, 24.0):
                at = self.b + QPointF(u.x() * d + n.x() * away * side,
                                      u.y() * d + n.y() * away * side)
                box = QPolygonF(QRectF(at.x() - w / 2 - 1, at.y() - h / 2 - 1, w + 2, h + 2))
                hits = sum(not box.intersected(shape).isEmpty() for shape in avoid)
                if hits == 0:
                    return at
                if hits < fewest:
                    best, fewest = at, hits
                d += 4
        # No room along the line: take the nearest free spot around where it meets the entity.
        for radius in range(24, 121, 8):
            for step in range(16):
                angle = 2 * math.pi * step / 16 + math.atan2(u.y(), u.x())
                at = self.b + QPointF(math.cos(angle) * radius, math.sin(angle) * radius)
                box = QPolygonF(QRectF(at.x() - w / 2 - 1, at.y() - h / 2 - 1, w + 2, h + 2))
                if all(box.intersected(shape).isEmpty() for shape in avoid[:2]):
                    return at
        return best


def _ends(a: Node, b: Node, offset: float = 0.0) -> tuple[QPointF, QPointF]:
    """Where a straight line between two nodes leaves each of them, optionally moved
    sideways (to keep parallel lines apart)."""
    ca, cb = a.scenePos(), b.scenePos()
    if offset:
        n = _normal(_unit(ca, cb))
        shift = QPointF(n.x() * offset, n.y() * offset)
        sa, sb = ca + shift, cb + shift
        pa, pb = a.scene_outline(), b.scene_outline()
        if pa.containsPoint(sa, Qt.OddEvenFill) and pb.containsPoint(sb, Qt.OddEvenFill):
            ca, cb = sa, sb
    return exit_point(a.scene_outline(), ca, cb), exit_point(b.scene_outline(), cb, ca)


class ChenEdge(Edge):
    """Relationship diamond to entity, with the entity's (min,max) near the entity."""

    def __init__(self, style, relationship: Node, entity: Node, label: str, offset: float):
        super().__init__(style)
        self.relationship, self.entity, self.label, self.offset = (
            relationship, entity, label, offset)
        self.attach(relationship, entity)

    def compute(self):
        self.a, self.b = _ends(self.relationship, self.entity, self.offset)
        self.path = QPainterPath(self.a)
        self.path.lineTo(self.b)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(pen(self.style.line))
        painter.drawPath(self.path)
        self._text(painter, self._label_spot(self.label), self.label, background=False)


class CrowEdge(Edge):
    """Entity to relationship label. At the entity end: how many of this entity match one
    of the other (the other side's Chen cardinality): a crow's foot for many, a bar for
    one, and a circle (optional) or bar (mandatory) for the minimum."""

    def __init__(self, style, relationship: Node, entity: Node, min_: int | None,
                 many: bool | None, label: str = "", offset: float = 0.0):
        super().__init__(style)
        self.relationship, self.entity = relationship, entity
        self.min, self.many, self.label, self.offset = min_, many, label, offset
        self.attach(relationship, entity)

    def compute(self):
        self.a, self.b = _ends(self.relationship, self.entity, self.offset)
        self.path = QPainterPath(self.a)
        self.path.lineTo(self.b)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        p = pen(self.style.line)
        painter.setPen(p)
        painter.drawPath(self.path)
        if self.many is None:
            if self.label:
                self._text(painter, self._label_spot(self.label), self.label,
                           background=False)
            return
        tip = self.b
        u = _unit(tip, self.a)  # from the entity towards the relationship
        n = _normal(u)

        def at(d: float, side: float = 0.0) -> QPointF:
            return tip + QPointF(u.x() * d + n.x() * side, u.y() * d + n.y() * side)

        if self.many:
            painter.drawLine(at(13), at(0, 8))
            painter.drawLine(at(13), at(0, -8))
            painter.drawLine(at(13), at(0))
        else:
            painter.drawLine(at(9, 7), at(9, -7))
        if self.min == 0:
            painter.setBrush(QColor(self.style.paper))
            painter.drawEllipse(at(20), 4.5, 4.5)
        else:
            painter.drawLine(at(19, 7), at(19, -7))


class LinkEdge(Edge):
    """A UML link between two classes (or a class and itself)."""

    def __init__(self, style, record: LinkRecord, source: Node, target: Node, offset: float):
        super().__init__(style)
        self.record = record
        self.id = record.id
        self.source, self.target, self.offset = source, target, offset
        self.setFlags(QGraphicsItem.ItemIsSelectable)
        self.attach(source, target)

    def compute(self):
        if self.source is self.target:
            b = self.source.sceneBoundingRect().adjusted(3, 3, -3, -3)
            k = 26 + abs(self.offset)
            self.a = QPointF(b.right(), b.top() + 22)
            self.b = QPointF(b.right() - 30, b.top())
            path = QPainterPath(self.a)
            path.lineTo(b.right() + k, self.a.y())
            path.lineTo(b.right() + k, b.top() - k)
            path.lineTo(self.b.x(), b.top() - k)
            path.lineTo(self.b)
            self.path = path
            self.start_dir = QPointF(1, 0)
            self.end_dir = QPointF(0, -1)  # pointing out of the target at the arrow
        else:
            self.a, self.b = _ends(self.source, self.target, self.offset)
            self.path = QPainterPath(self.a)
            self.path.lineTo(self.b)
            self.start_dir = _unit(self.a, self.b)
            self.end_dir = _unit(self.b, self.a)

    def shape(self) -> QPainterPath:
        stroker = QPainterPathStroker()
        stroker.setWidth(10)
        return stroker.createStroke(self.path)

    def paint(self, painter, option, widget=None):
        s, r = self.style, self.record
        painter.setRenderHint(QPainter.Antialiasing)
        color = s.accent if self.isSelected() else s.line
        dashed = r.kind in (LinkKind.REALIZATION, LinkKind.DEPENDENCY)
        painter.setPen(pen(color, 2.2 if self.isSelected() else 1.4, dashed))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.path)
        painter.setPen(pen(color, 2.2 if self.isSelected() else 1.4))

        def point(origin, u, d, side=0.0):
            n = _normal(u)
            return origin + QPointF(u.x() * d + n.x() * side, u.y() * d + n.y() * side)

        tip, u = self.b, self.end_dir
        if r.kind in (LinkKind.INHERITANCE, LinkKind.REALIZATION):
            painter.setBrush(QColor(s.paper))
            painter.drawPolygon(QPolygonF([tip, point(tip, u, 15, 9), point(tip, u, 15, -9)]))
        elif r.kind in (LinkKind.DIRECTED, LinkKind.DEPENDENCY):
            painter.drawLine(tip, point(tip, u, 12, 7))
            painter.drawLine(tip, point(tip, u, 12, -7))
        if r.kind in (LinkKind.AGGREGATION, LinkKind.COMPOSITION):
            start, v = self.a, self.start_dir
            painter.setBrush(QColor(color if r.kind is LinkKind.COMPOSITION else s.paper))
            painter.drawPolygon(QPolygonF([start, point(start, v, 9, 6), point(start, v, 18),
                                           point(start, v, 9, -6)]))
        for text, origin, v in ((r.source_multiplicity, self.a, self.start_dir),
                                (r.target_multiplicity, self.b, self.end_dir)):
            if text:
                n = _normal(v)
                side = 11 if n.y() <= 0 else -11
                self._text(painter, point(origin, v, 26, side), text, background=False)
        if r.label:
            mid = self.path.pointAtPercent(0.5)
            self._text(painter, mid + QPointF(0, -10), r.label, font=_font(9, italic=True))


class GeneralisationEdge(Edge):
    """Specialisations joined to their parent by an arrow: filled when total, hollow when
    partial, with (t,e) / (p,s) beside it."""

    def __init__(self, style, record: GeneralisationRecord, parent: Node, children: list[Node]):
        super().__init__(style)
        self.record = record
        self.id = record.id
        self.parent_node, self.children = parent, children
        self.setFlags(QGraphicsItem.ItemIsSelectable)
        self.attach(parent, *children)

    def compute(self):
        p = self.parent_node.scenePos()
        if len(self.children) == 1:
            junction = self.children[0].scenePos()
        else:
            cx = sum(c.scenePos().x() for c in self.children) / len(self.children)
            cy = sum(c.scenePos().y() for c in self.children) / len(self.children)
            junction = QPointF(p.x() + (cx - p.x()) * 0.5, p.y() + (cy - p.y()) * 0.5)
        self.tip = exit_point(self.parent_node.scene_outline(), p, junction)
        if len(self.children) == 1:
            junction = exit_point(self.children[0].scene_outline(), junction, p)
        self.junction = junction
        path = QPainterPath(self.junction)
        path.lineTo(self.tip)
        if len(self.children) > 1:
            for c in self.children:
                start = exit_point(c.scene_outline(), c.scenePos(), self.junction)
                path.moveTo(start)
                path.lineTo(self.junction)
        self.path = path

    def shape(self) -> QPainterPath:
        stroker = QPainterPathStroker()
        stroker.setWidth(10)
        return stroker.createStroke(self.path)

    def paint(self, painter, option, widget=None):
        s = self.style
        painter.setRenderHint(QPainter.Antialiasing)
        color = s.accent if self.isSelected() else s.line
        painter.setPen(pen(color, 2.2 if self.isSelected() else 1.4))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.path)
        u = _unit(self.tip, self.junction)
        n = _normal(u)
        base = self.tip + QPointF(u.x() * 14, u.y() * 14)
        head = QPolygonF([self.tip, base + QPointF(n.x() * 7, n.y() * 7),
                          base - QPointF(n.x() * 7, n.y() * 7)])
        painter.setBrush(QColor(color if self.record.total else s.paper))
        painter.drawPolygon(head)
        at = self.junction + QPointF(n.x() * 22, n.y() * 22) if len(self.children) > 1 else \
            (self.tip + self.junction) / 2 + QPointF(n.x() * 22, n.y() * 22)
        self._text(painter, at, self.record.label, background=False)


# ---- the scene --------------------------------------------------------------------------------

class Tool(Enum):
    SELECT = "select"
    ENTITY = "entity"
    RELATIONSHIP = "relationship"
    CLASS = "class"
    LINK = "link"
    GENERALISATION = "generalisation"


class DiagramScene(QGraphicsScene):
    moved = Signal(dict)  # {id: (x, y)}
    addRequested = Signal(object, float, float)  # Tool, x, y
    connectRequested = Signal(str, str)  # first node id, second node id
    editRequested = Signal(str)  # id (double-click)
    toolDone = Signal()
    pickedFirst = Signal(str)  # the first end of a new relationship or link was chosen

    def __init__(self, style: Style, grid: bool = True, parent=None):
        super().__init__(parent)
        self.style = style
        self.grid = grid
        self.tool = Tool.SELECT
        self.nodes: dict[str, Node] = {}
        self.links: dict[str, LinkEdge] = {}
        self.record: DiagramRecord | None = None
        self.no_key_warning = "No key: mark its identifier with the key icon."
        self._first: Node | None = None
        self._rubber = None
        self._press_positions: dict[str, QPointF] = {}
        self._aligned: dict[str, tuple[float | None, float | None]] = {}
        self._guides: list = []
        self.zoom_hint = 1.0  # set by the view, so the snap distance is the same on screen

    # ---- alignment guides -------------------------------------------------------------

    def align(self, node: Node, pos: QPointF) -> QPointF:
        """While one node is dragged: snap its centre to the centre lines of the others, and
        show the line. (With several selected they move together, untouched.)"""
        if not self.grid or len(self.selectedItems()) > 1:
            return pos
        reach = 7 / max(self.zoom_hint, 0.01)
        best_x = best_y = None
        for other in self.nodes.values():
            if other is node:
                continue
            p = other.pos()
            if abs(p.x() - pos.x()) <= reach and (
                    best_x is None or abs(p.x() - pos.x()) < abs(best_x - pos.x())):
                best_x = p.x()
            if abs(p.y() - pos.y()) <= reach and (
                    best_y is None or abs(p.y() - pos.y()) < abs(best_y - pos.y())):
                best_y = p.y()
        x = pos.x() if best_x is None else best_x
        y = pos.y() if best_y is None else best_y
        if best_x is None or best_y is None:  # still free on one axis: try the 45° lines
            found = None
            for other in self.nodes.values():
                if other is node:
                    continue
                p = other.pos()
                for sign in (1, -1):
                    if best_x is None and best_y is None:
                        gx = snap(pos.x())
                        cand = (gx, p.y() + sign * (gx - p.x()))
                    elif best_x is not None:
                        cand = (x, p.y() + sign * (x - p.x()))
                    else:
                        cand = (p.x() + sign * (y - p.y()), y)
                    miss = abs(cand[0] - pos.x()) + abs(cand[1] - pos.y())
                    if miss <= reach and (found is None or miss < found[0]):
                        found = (miss, cand)
            if found is not None:
                x, y = found[1]
                best_x = x if best_x is None else best_x
                best_y = y if best_y is None else best_y
        self._aligned[node.id] = (best_x, best_y)
        self._clear_guides()
        for other in self.nodes.values():
            if other is node:
                continue
            p = other.pos()
            if best_x is not None and p.x() == best_x:
                self._guide(QLineF(best_x, min(y, p.y()) - 40, best_x, max(y, p.y()) + 40))
            if best_y is not None and p.y() == best_y:
                self._guide(QLineF(min(x, p.x()) - 70, best_y, max(x, p.x()) + 70, best_y))
            dx, dy = x - p.x(), y - p.y()
            if dx and abs(dx) == abs(dy):  # on a 45° line through the other box
                k = 60 if dx > 0 else -60
                j = k if dy > 0 else -k
                self._guide(QLineF(p.x() - k, p.y() - j, x + k, y + j))
        return QPointF(x, y)

    def _guide(self, line: QLineF):
        item = self.addLine(line, pen(self.style.accent, 1.2, dashed=True))
        item.setZValue(1)
        self._guides.append(item)

    def _clear_guides(self):
        for item in self._guides:
            try:
                self.removeItem(item)
            except RuntimeError:
                pass
        self._guides = []

    # ---- building ---------------------------------------------------------------------

    def load(self, record: DiagramRecord, keep_selection: bool = True):
        selected = set(self.selected_ids()) if keep_selection else set()
        self.blockSignals(True)
        self._cancel_pick()
        self.clear()
        self._guides = []
        self.nodes.clear()
        self.links.clear()
        self.record = record
        s = self.style
        if record.kind is DiagramKind.ER:
            chen = record.notation is Notation.CHEN
            blocked = _blocked_sides(record) if chen else {}
            for e in record.entities:
                self._add_node(ChenEntity(e, s, blocked.get(e.id, (False, False))) if chen
                               else TableEntity(e, s))
            for r in record.relationships:
                node = self._add_node(ChenRelationship(r, s, blocked.get(r.id, (False, False)))
                                      if chen else CrowRelationship(r, s))
                self._relationship_edges(r, node, chen)
            for g in record.generalisations:
                children = [self.nodes[c] for c in g.children if c in self.nodes]
                if g.parent in self.nodes and children:
                    edge = GeneralisationEdge(s, g, self.nodes[g.parent], children)
                    self.addItem(edge)
                    self.links[g.id] = edge
            specialised = {c for g in record.generalisations for c in g.children}
            for e in record.entities:
                if not e.weak and e.id not in specialised and not any(a.key for a in e.attributes):
                    self.nodes[e.id].set_warning(self.no_key_warning)
        else:
            for c in record.classes:
                self._add_node(ClassBox(c, s))
            pairs: dict[frozenset, int] = {}
            for link in record.links:
                if link.source not in self.nodes or link.target not in self.nodes:
                    continue
                key = frozenset((link.source, link.target))
                index = pairs.get(key, 0)
                pairs[key] = index + 1
                # Several links between the same two classes sit side by side.
                offset = index * 14 if link.source == link.target else (
                    (index + 1) // 2 * 18 * (1 if index % 2 else -1))
                edge = LinkEdge(s, link, self.nodes[link.source], self.nodes[link.target],
                                offset)
                self.addItem(edge)
                self.links[link.id] = edge
        for id in selected:
            item = self.nodes.get(id) or self.links.get(id)
            if item is not None:
                item.setSelected(True)
        self.blockSignals(False)
        self.selectionChanged.emit()
        self.update()

    def _add_node(self, node: Node) -> Node:
        self.addItem(node)
        self.nodes[node.id] = node
        return node

    def _relationship_edges(self, r: RelationshipRecord, node: Node, chen: bool):
        parts = [p for p in r.participants if p.entity_id in self.nodes]
        counts: dict[str, int] = {}
        for p in parts:
            counts[p.entity_id] = counts.get(p.entity_id, 0) + 1
        seen: dict[str, int] = {}
        binary = len(parts) == 2
        for index, p in enumerate(parts):
            entity = self.nodes[p.entity_id]
            k = seen.get(p.entity_id, 0)
            seen[p.entity_id] = k + 1
            offset = (k - (counts[p.entity_id] - 1) / 2) * 22 if counts[p.entity_id] > 1 else 0
            label = p.cardinality + (f" {p.role}" if p.role else "")
            if chen:
                edge = ChenEdge(self.style, node, entity, label, offset)
            elif binary:
                other = parts[1 - index]
                edge = CrowEdge(self.style, node, entity, other.min, other.many,
                                offset=offset)
            else:
                edge = CrowEdge(self.style, node, entity, None, None, label, offset)
            self.addItem(edge)

    # ---- reading ----------------------------------------------------------------------

    def selected_ids(self) -> list[str]:
        ids = []
        for item in self.selectedItems():
            if isinstance(item, (Node, LinkEdge, GeneralisationEdge)):
                ids.append(item.id)
        return ids

    def select_only(self, ids):
        self.blockSignals(True)
        self.clearSelection()
        for id in ids:
            item = self.nodes.get(id) or self.links.get(id)
            if item is not None:
                item.setSelected(True)
        self.blockSignals(False)
        self.selectionChanged.emit()

    def content_rect(self) -> QRectF:
        rect = QRectF()
        for item in self.items():
            if isinstance(item, (Node, Edge)):
                rect = rect.united(item.sceneBoundingRect())
        return rect

    # ---- tools ------------------------------------------------------------------------

    def set_tool(self, tool: Tool):
        self._cancel_pick()
        self.tool = tool
        for view in self.views():
            view.setDragMode(QGraphicsView.RubberBandDrag if tool is Tool.SELECT
                             else QGraphicsView.NoDrag)
            view.viewport().setCursor(Qt.ArrowCursor if tool is Tool.SELECT
                                      else Qt.CrossCursor)

    def _node_at(self, pos: QPointF) -> Node | None:
        for item in self.items(pos):
            if isinstance(item, Node):
                return item
        return None

    def _cancel_pick(self):
        if self._rubber is not None:
            try:
                self.removeItem(self._rubber)
            except RuntimeError:
                pass
        self._rubber = None
        self._first = None

    def cancel(self):
        self._cancel_pick()
        if self.tool is not Tool.SELECT:
            self.set_tool(Tool.SELECT)
            self.toolDone.emit()

    def mousePressEvent(self, event):
        pos = event.scenePos()
        if event.button() != Qt.LeftButton or self.tool is Tool.SELECT:
            if self.tool is Tool.SELECT and event.button() == Qt.LeftButton:
                self._press_positions = {id: n.pos() for id, n in self.nodes.items()}
            super().mousePressEvent(event)
            return
        if self.tool in (Tool.ENTITY, Tool.CLASS):
            self.addRequested.emit(self.tool, snap(pos.x()), snap(pos.y()))
            event.accept()
            return
        # Relationship or link: pick two nodes.
        node = self._node_at(pos)
        if node is None or isinstance(node, (ChenRelationship, CrowRelationship)):
            event.accept()
            return
        if self._first is None:
            self._first = node
            self._rubber = self.addLine(QLineF(node.scenePos(), pos),
                                        pen(self.style.accent, 1.6, dashed=True))
            self._rubber.setZValue(5)
            self.pickedFirst.emit(node.id)
        else:
            first = self._first
            self._cancel_pick()
            self.connectRequested.emit(first.id, node.id)
        event.accept()

    def mouseMoveEvent(self, event):
        if self._rubber is not None and self._first is not None:
            self._rubber.setLine(QLineF(self._first.scenePos(), event.scenePos()))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self._clear_guides()
        if self.tool is not Tool.SELECT or not self._press_positions:
            self._aligned = {}
            return
        moved = {}
        for id, node in self.nodes.items():
            before = self._press_positions.get(id)
            if before is not None and node.pos() != before:
                ax, ay = self._aligned.get(id, (None, None))
                x = ax if ax is not None else snap(node.pos().x())
                y = ay if ay is not None else snap(node.pos().y())
                moved[id] = (x, y)
        self._press_positions = {}
        self._aligned = {}
        if moved:
            self.moved.emit(moved)

    def mouseDoubleClickEvent(self, event):
        if self.tool is not Tool.SELECT:
            return
        pos = event.scenePos()
        for item in self.items(pos):
            if isinstance(item, (Node, LinkEdge, GeneralisationEdge)):
                self.editRequested.emit(item.id)
                return
        if self.record is not None:
            tool = Tool.ENTITY if self.record.kind is DiagramKind.ER else Tool.CLASS
            self.addRequested.emit(tool, snap(pos.x()), snap(pos.y()))

    # ---- background -------------------------------------------------------------------

    def drawBackground(self, painter: QPainter, rect: QRectF):
        painter.fillRect(rect, QColor(self.style.paper))
        if not self.grid:
            return
        step = GRID * 2
        painter.setPen(QPen(QColor(self.style.grid), 1.6))
        left = int(math.floor(rect.left() / step)) * step
        top = int(math.floor(rect.top() / step)) * step
        points = []
        x = left
        while x < rect.right():
            y = top
            while y < rect.bottom():
                points.append(QPointF(x, y))
                y += step
            x += step
        if len(points) < 40000:  # skip the dots when zoomed far out
            painter.drawPoints(points)


def _blocked_sides(record: DiagramRecord) -> dict[str, tuple[bool, bool]]:
    """For each entity and relationship: does a line leave it upwards, downwards?"""
    where = {e.id: (e.x, e.y) for e in record.entities}
    where.update({r.id: (r.x, r.y) for r in record.relationships})
    sides: dict[str, list[bool]] = {id: [False, False] for id in where}

    def mark(a: str, b: str):
        (ax, ay), (bx, by) = where[a], where[b]
        dx, dy = bx - ax, by - ay
        if abs(dy) > abs(dx) * 0.5:
            sides[a][0 if dy < 0 else 1] = True

    for r in record.relationships:
        for p in r.participants:
            if p.entity_id in where:
                mark(r.id, p.entity_id)
                mark(p.entity_id, r.id)
    for g in record.generalisations:
        for c in g.children:
            if c in where and g.parent in where:
                mark(c, g.parent)
                mark(g.parent, c)
    return {id: (top, bottom) for id, (top, bottom) in sides.items()}


def snap(value: float) -> float:
    return round(value / GRID) * GRID


# ---- the view ------------------------------------------------------------------------------------

class DiagramView(QGraphicsView):
    zoomChanged = Signal(float)
    MIN, MAX = 0.2, 4.0

    def __init__(self, scene: DiagramScene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setFrameShape(QGraphicsView.NoFrame)
        self.setFocusPolicy(Qt.StrongFocus)
        self._panning = None
        self._space = False
        self.setSceneRect(QRectF(-5000, -5000, 10000, 10000))

    def drawForeground(self, painter, rect):
        scene = self.scene()
        if scene is not None:
            scene.zoom_hint = self.zoom

    @property
    def zoom(self) -> float:
        return self.transform().m11()

    def set_zoom(self, factor: float):
        factor = max(self.MIN, min(self.MAX, factor))
        self.setTransformationAnchor(QGraphicsView.AnchorViewCenter)
        self.resetTransform()
        self.scale(factor, factor)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.zoomChanged.emit(factor)

    def zoom_in(self):
        self.set_zoom(self.zoom * 1.2)

    def zoom_out(self):
        self.set_zoom(self.zoom / 1.2)

    def fit(self):
        rect = self.scene().content_rect()
        if rect.isEmpty():
            self.set_zoom(1.0)
            self.centerOn(0, 0)
            return
        rect = rect.adjusted(-40, -40, 40, 40)
        view = self.viewport().rect()
        factor = min(view.width() / rect.width(), view.height() / rect.height(), 1.5)
        self.set_zoom(factor)
        self.centerOn(rect.center())

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            steps = event.angleDelta().y() / 120
            factor = max(self.MIN, min(self.MAX, self.zoom * (1.15 ** steps)))
            self.scale(factor / self.zoom, factor / self.zoom)
            self.zoomChanged.emit(self.zoom)
            event.accept()
            return
        super().wheelEvent(event)

    def event(self, event):
        if event.type() == QEvent.NativeGesture:
            if event.gestureType() == Qt.ZoomNativeGesture:
                factor = max(self.MIN, min(self.MAX, self.zoom * (1 + event.value())))
                self.scale(factor / self.zoom, factor / self.zoom)
                self.zoomChanged.emit(self.zoom)
                return True
        return super().event(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space and not event.isAutoRepeat():
            self._space = True
            self.viewport().setCursor(Qt.OpenHandCursor)
            return
        if event.key() == Qt.Key_Escape:
            self.scene().cancel()
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Space and not event.isAutoRepeat():
            self._space = False
            self.viewport().setCursor(Qt.ArrowCursor if self.scene().tool is Tool.SELECT
                                      else Qt.CrossCursor)
            return
        super().keyReleaseEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton or (self._space and event.button() == Qt.LeftButton):
            self._panning = event.position()
            self.viewport().setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning is not None:
            delta = event.position() - self._panning
            self._panning = event.position()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._panning is not None:
            self._panning = None
            self.viewport().setCursor(Qt.OpenHandCursor if self._space else Qt.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)


__all__ = ["DiagramScene", "DiagramView", "EXPORT_STYLE", "Style", "Tool",
           "snap", "style_for"]
