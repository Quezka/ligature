"""The window, driven headlessly: selecting things must not change them, edits land,
and every page builds in both diagram kinds."""
import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QEventLoop, QTimer  # noqa: E402

from ligature.application.types import DiagramKind, FileFormat  # noqa: E402


@pytest.fixture(scope="module")
def app():
    from ligature.presentation.qt_app import create_application
    return create_application([])


@pytest.fixture
def window(app, tmp_path, monkeypatch):
    from PySide6.QtCore import QSettings
    QSettings().clear()
    from ligature.bootstrap import build_services
    from ligature.presentation.main_window import MainWindow
    w = MainWindow(build_services())
    yield w
    w.editor.settle()
    w.close()


def pump(ms=50):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def test_selecting_items_changes_nothing(window):
    window.open_sample(DiagramKind.ER)
    before = window.editor.diagram()
    for item in (*before.entities, *before.relationships):
        window.diagram.scene.select_only([item.id])
        pump()
    window.diagram.scene.select_only([])
    pump()
    assert window.editor.diagram() == before and not window.editor.can_undo
    window.open_sample(DiagramKind.UML)
    before = window.editor.diagram()
    for item in (*before.classes, *before.links):
        window.diagram.scene.select_only([item.id])
        pump()
    assert window.editor.diagram() == before and not window.editor.can_undo


def test_editing_in_the_panel(window):
    window.new_diagram(DiagramKind.ER)
    from ligature.presentation.canvas import Tool
    window.diagram._add(Tool.ENTITY,
                        0, 0)
    panel = window.diagram.panel.entity
    panel.name.setText("Studente")
    panel.name.textEdited.emit("Studente")
    panel.attributes.add_row()
    row = panel.attributes.rows[0]
    row["name"].setText("matricola")
    row["name"].textEdited.emit("matricola")
    row["key"].setChecked(True)
    e = window.editor.diagram().entities[0]
    assert e.name == "Studente" and e.attributes[0].name == "matricola" and e.attributes[0].key
    assert window.diagram.scene.nodes[e.id].record == e


def test_pages_and_exports(window, tmp_path):
    from ligature.presentation.export import pdf_bytes, png_bytes, svg_bytes
    window.open_sample(DiagramKind.ER)
    window.show_page(window.SQL)
    assert "CREATE TABLE" in window.sql.sql.toPlainText()
    record = window.editor.diagram()
    assert png_bytes(record).startswith(b"\x89PNG")
    assert b"<svg" in svg_bytes(record)
    assert pdf_bytes(record).startswith(b"%PDF")
    path = tmp_path / "registro.png"
    assert window._save_to(str(path))
    window.editor.open(str(path))
    assert window.editor.diagram() == record and window.editor.format is FileFormat.PNG
    window.open_sample(DiagramKind.UML)
    window.show_page(window.SQL)
    assert window.sql.empty.isVisibleTo(window.sql)


def test_mouse_places_connects_and_drags(window):
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest
    from ligature.presentation.canvas import Tool
    window.resize(1300, 800)
    window.show()
    window.new_diagram(DiagramKind.ER)
    pump()
    view = window.diagram.view

    def at(x, y) -> QPoint:
        return view.mapFromScene(x, y)

    window.diagram.set_tool(Tool.ENTITY)
    QTest.mouseClick(view.viewport(), Qt.LeftButton, pos=at(100, 100))
    window.diagram.set_tool(Tool.ENTITY)
    QTest.mouseClick(view.viewport(), Qt.LeftButton, pos=at(400, 100))
    a, b = window.editor.diagram().entities
    assert (a.x, a.y, b.x) == (100, 100, 400)
    window.diagram.set_tool(Tool.RELATIONSHIP)
    QTest.mouseClick(view.viewport(), Qt.LeftButton, pos=at(100, 100))
    QTest.mouseClick(view.viewport(), Qt.LeftButton, pos=at(400, 100))
    (rel,) = window.editor.diagram().relationships
    assert [p.entity_id for p in rel.participants] == [a.id, b.id]
    assert window.diagram.scene.tool is Tool.SELECT
    assert window.diagram.scene.selected_ids() == [rel.id]
    # Drag the first entity down; it snaps to the grid and is one undo step.
    QTest.mousePress(view.viewport(), Qt.LeftButton, pos=at(100, 100))
    for step in range(1, 6):
        QTest.mouseMove(view.viewport(), at(100, 100 + step * 20.3))
    QTest.mouseRelease(view.viewport(), Qt.LeftButton, pos=at(100, 201.5))
    moved = window.editor.diagram().entities[0]
    assert moved.y % 10 == 0 and 190 <= moved.y <= 210
    window.editor.undo()
    assert window.editor.diagram().entities[0].y == 100
    # Double-click on empty space adds an entity.
    QTest.mouseDClick(view.viewport(), Qt.LeftButton, pos=at(250, 350))
    assert len(window.editor.diagram().entities) == 3
