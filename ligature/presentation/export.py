"""Pictures of a diagram: PNG, SVG and PDF, always drawn on white in the light style."""
from __future__ import annotations

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QMarginsF, QRectF, QSizeF, Qt
from PySide6.QtGui import QColor, QImage, QPageLayout, QPageSize, QPainter, QPdfWriter
from PySide6.QtSvg import QSvgGenerator

from ..application.records import DiagramRecord
from .canvas import EXPORT_STYLE, DiagramScene

MARGIN = 24


def _scene(record: DiagramRecord) -> tuple[DiagramScene, QRectF]:
    scene = DiagramScene(EXPORT_STYLE, grid=False)
    scene.load(record, keep_selection=False)
    rect = scene.content_rect()
    if rect.isEmpty():
        rect = QRectF(0, 0, 200, 120)
    rect = rect.adjusted(-MARGIN, -MARGIN, MARGIN, MARGIN)
    scene.setSceneRect(rect)
    return scene, rect


def render_image(record: DiagramRecord, scale: float = 2.0) -> QImage:
    scene, rect = _scene(record)
    image = QImage(int(rect.width() * scale), int(rect.height() * scale), QImage.Format_ARGB32)
    image.setDotsPerMeterX(int(3780 * scale))
    image.setDotsPerMeterY(int(3780 * scale))
    image.fill(QColor(EXPORT_STYLE.paper))
    painter = QPainter(image)
    painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
    scene.render(painter, QRectF(image.rect()), rect)
    painter.end()
    return image


def png_bytes(record: DiagramRecord, scale: float = 2.0) -> bytes:
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.WriteOnly)
    render_image(record, scale).save(buffer, "PNG")
    buffer.close()
    return bytes(data)


def svg_bytes(record: DiagramRecord, title: str = "") -> bytes:
    scene, rect = _scene(record)
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.WriteOnly)
    generator = QSvgGenerator()
    generator.setOutputDevice(buffer)
    generator.setSize(rect.size().toSize())
    generator.setViewBox(QRectF(0, 0, rect.width(), rect.height()))
    generator.setTitle(title or record.title or "Ligature")
    painter = QPainter(generator)
    painter.fillRect(QRectF(0, 0, rect.width(), rect.height()), QColor(EXPORT_STYLE.paper))
    scene.render(painter, QRectF(0, 0, rect.width(), rect.height()), rect)
    painter.end()
    buffer.close()
    return bytes(data)


def pdf_bytes(record: DiagramRecord) -> bytes:
    """An A4 page (turned to suit the diagram) with the diagram scaled to fit."""
    scene, rect = _scene(record)
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.WriteOnly)
    writer = QPdfWriter(buffer)
    writer.setTitle(record.title or "Ligature")
    writer.setCreator("Ligature")
    orientation = (QPageLayout.Landscape if rect.width() > rect.height()
                   else QPageLayout.Portrait)
    writer.setPageLayout(QPageLayout(QPageSize(QPageSize.A4), orientation,
                                     QMarginsF(12, 12, 12, 12), QPageLayout.Millimeter))
    writer.setResolution(300)
    painter = QPainter(writer)
    page = QRectF(painter.viewport())
    factor = min(page.width() / rect.width(), page.height() / rect.height(), 300 / 96 * 1.0)
    size = QSizeF(rect.width() * factor, rect.height() * factor)
    target = QRectF(page.left(), page.top(), size.width(), size.height())
    scene.render(painter, target, rect, Qt.KeepAspectRatio)
    painter.end()
    buffer.close()
    return bytes(data)
