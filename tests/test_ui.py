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
    from ligature.infrastructure.settings import MemorySettings
    from ligature.infrastructure.updates import NoInstaller
    from ligature.presentation.main_window import MainWindow
    from .fakes import FakeReleases
    w = MainWindow(build_services(settings=MemorySettings(), releases=FakeReleases(),
                                  installer=NoInstaller()))
    yield w
    w.editor.settle()
    w.close()


def pump(ms=50):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def test_selecting_items_changes_nothing(window):
    window.open_sample("university")
    before = window.editor.diagram()
    for item in (*before.entities, *before.relationships, *before.generalisations):
        window.diagram.scene.select_only([item.id])
        pump()
    assert window.editor.diagram() == before and not window.editor.can_undo
    window.open_sample("school")
    before = window.editor.diagram()
    for item in (*before.entities, *before.relationships):
        window.diagram.scene.select_only([item.id])
        pump()
    window.diagram.scene.select_only([])
    pump()
    assert window.editor.diagram() == before and not window.editor.can_undo
    window.open_sample("shapes")
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
    window.open_sample("school")
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
    window.open_sample("shapes")
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
    # Dragging near another box's centre line snaps to it and shows guides.
    QTest.mousePress(view.viewport(), Qt.LeftButton, pos=at(400, 100))
    QTest.mouseMove(view.viewport(), at(404, 330))
    assert window.diagram.scene._guides == []  # nothing near
    QTest.mouseMove(view.viewport(), at(404, 104))
    assert len(window.diagram.scene._guides) == 2  # level with the other entity and the diamond
    QTest.mouseRelease(view.viewport(), Qt.LeftButton, pos=at(404, 104))
    assert window.diagram.scene._guides == []
    assert window.editor.diagram().entities[1].y == 100
    window.editor.undo()
    # ...and to a 45° line through another box (the first entity is at 100,100).
    QTest.mousePress(view.viewport(), Qt.LeftButton, pos=at(400, 100))
    QTest.mouseMove(view.viewport(), at(300, 250))
    QTest.mouseMove(view.viewport(), at(303, 303))
    assert len(window.diagram.scene._guides) >= 1
    QTest.mouseRelease(view.viewport(), Qt.LeftButton, pos=at(303, 303))
    moved = window.editor.diagram().entities[1]
    assert (moved.x, moved.y) == (300, 300)
    window.editor.undo()
    # Double-click on empty space adds an entity.
    QTest.mouseDClick(view.viewport(), Qt.LeftButton, pos=at(250, 350))
    assert len(window.editor.diagram().entities) == 3


def test_copy_paste_and_arrow_keys(window):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    window.resize(1300, 800)
    window.show()
    window.open_sample("university")
    pump()
    page = window.diagram
    person = next(e for e in window.editor.diagram().entities if e.name == "Persona")
    page.scene.select_only([person.id])
    window.activateWindow()  # the scene only takes keys when its window is the active one
    page.view.setFocus()
    pump()
    QTest.keyClick(page.view, Qt.Key_Right)
    assert window.editor.diagram().find(person.id).x == person.x + 10
    assert page.copy_selection()
    page.paste()
    names = [e.name for e in window.editor.diagram().entities]
    assert "Persona 2" in names and len(page.scene.selected_ids()) == 1
    page.cut_selection()
    assert "Persona 2" not in [e.name for e in window.editor.diagram().entities]


def test_generalisation_tool_and_panel(window):
    from ligature.presentation.canvas import Tool
    from ligature.application.types import Mapping
    window.new_diagram(DiagramKind.ER)
    parent = window.editor.add_entity(0, 0, "Veicolo")
    child = window.editor.add_entity(0, 200, "Auto")
    window.diagram.set_tool(Tool.GENERALISATION)
    window.diagram._connect(child, parent)
    (g,) = window.editor.diagram().generalisations
    assert window.diagram.scene.selected_ids() == [g.id]
    panel = window.diagram.panel.generalisation
    panel.coverage.group.button(0).click()  # total
    panel.mapping.setCurrentIndex(panel.mapping.findData(Mapping.INTO_PARENT))
    g = window.editor.diagram().generalisations[0]
    assert g.total and g.mapping is Mapping.INTO_PARENT and g.label == "(t,e)"
    assert window.diagram.scene.nodes[parent].warning  # no key yet


def test_cardinality_labels_stay_off_the_entities(app, editor):
    from PySide6.QtCore import QRectF
    from PySide6.QtGui import QPolygonF
    from ligature.application.inputs import ParticipantInput as P, RelationshipInput
    from ligature.presentation import canvas

    editor.new(DiagramKind.ER, "t")
    a, b = editor.add_entity(100, 100, "Studente"), editor.add_entity(330, 130, "Classe")
    d, f = editor.add_entity(100, 330, "Docente"), editor.add_entity(230, 450, "Materia")
    r1, r2 = editor.add_relationship([a, b], "Frequenta"), editor.add_relationship([d, f], "X")
    editor.update_relationship(r1, RelationshipInput("Frequenta", (
        P(a, "(0,N)", "iscritto"), P(b, "(1,N)", "frequentata"))))
    editor.update_relationship(r2, RelationshipInput("X", (
        P(d, "(1,N)", "titolare"), P(f, "(0,N)"))))
    scene = canvas.DiagramScene(canvas.EXPORT_STYLE, grid=False)
    scene.load(editor.diagram(), keep_selection=False)
    edges = [e for e in scene.items() if isinstance(e, canvas.ChenEdge)]
    assert len(edges) == 4
    for edge in edges:
        spot = edge._label_spot(edge.label)
        w, h = canvas._width(canvas.SMALL_FONT, edge.label) + 6, canvas._height(canvas.SMALL_FONT)
        box = QPolygonF(QRectF(spot.x() - w / 2, spot.y() - h / 2, w, h))
        assert box.intersected(edge.entity.scene_outline()).isEmpty(), edge.label
