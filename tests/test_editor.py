"""Editing a diagram through the use cases: adding, changing, deleting, undo and saving."""
import pytest

from ligature.application.errors import FileFormatError, NotFound
from ligature.application.inputs import (
    AttributeInput as A, ClassInput, EntityInput, LinkInput, ParticipantInput as P,
    RelationshipInput,
)
from ligature.application.editor import Change
from ligature.application.types import (
    ClassKind, Dialect, DiagramKind, FileFormat, IssueKind, LinkKind, Notation,
)
from ligature.demo import school_er, shapes_uml


def test_new_diagram_is_clean_and_names_are_unique(editor):
    editor.new(DiagramKind.ER)
    assert editor.is_open and not editor.dirty
    first = editor.add_entity(0, 0, "Studente")
    second = editor.add_entity(100, 0, "Studente")
    names = [e.name for e in editor.diagram().entities]
    assert names == ["Studente", "Studente 2"] and first != second
    assert editor.dirty


def test_entity_edits_undo_and_redo(editor):
    editor.new(DiagramKind.ER)
    e = editor.add_entity(0, 0)
    editor.update_entity(e, EntityInput("Classe", (A("id", "INT", key=True), A("  "),
                                                   A("note", optional=True))))
    record = editor.diagram().entities[0]
    assert record.name == "Classe" and [a.name for a in record.attributes] == ["id", "note"]
    assert record.attributes[1].optional
    # Typing into the same item merges into one undo step.
    editor.update_entity(e, EntityInput("Classi", record_attributes(record)))
    editor.undo()
    assert editor.diagram().entities[0].name == "Entity"
    editor.redo()
    assert editor.diagram().entities[0].name == "Classi"
    editor.undo()
    editor.undo()
    assert editor.diagram().empty and not editor.can_undo


def record_attributes(record):
    return tuple(A(a.name, a.type, a.key, a.optional) for a in record.attributes)


def test_key_attributes_are_never_optional(editor):
    editor.new(DiagramKind.ER)
    e = editor.add_entity(0, 0)
    editor.update_entity(e, EntityInput("X", (A("id", key=True, optional=True),)))
    assert not editor.diagram().entities[0].attributes[0].optional


def test_relationships_and_cascading_delete(editor):
    editor.new(DiagramKind.ER)
    a, b = editor.add_entity(0, 0, "A"), editor.add_entity(200, 0, "B")
    r = editor.add_relationship([a, b])
    rel = editor.diagram().relationships[0]
    assert (rel.x, rel.y) == (100, 0) and [p.cardinality for p in rel.participants] == ["(0,N)"] * 2
    editor.update_relationship(r, RelationshipInput("Ha", (P(a, "(1,1)"), P(b, "(0,N)"))))
    assert editor.diagram().relationships[0].participants[0].many is False
    editor.delete([a])
    assert [e.name for e in editor.diagram().entities] == ["B"]
    assert editor.diagram().relationships == ()  # left with one entity: it goes too
    editor.undo()
    assert len(editor.diagram().relationships) == 1


def test_recursive_relationship_sits_beside_its_entity(editor):
    editor.new(DiagramKind.ER)
    a = editor.add_entity(100, 100)
    editor.add_relationship([a, a])
    rel = editor.diagram().relationships[0]
    assert rel.x == 290 and len(rel.participants) == 2


def test_unknown_items_raise_not_found(editor):
    editor.new(DiagramKind.ER)
    with pytest.raises(NotFound):
        editor.update_entity("nope", EntityInput("X"))
    a = editor.add_entity(0, 0)
    r = editor.add_relationship([a, editor.add_entity(9, 9)])
    with pytest.raises(NotFound):
        editor.update_relationship(r, RelationshipInput("R", (P("gone"), P(a))))


def test_move_is_one_step_and_ignores_unknown_ids(editor):
    editor.new(DiagramKind.ER)
    a, b = editor.add_entity(0, 0), editor.add_entity(10, 10)
    editor.move({a: (50.04, 60), b: (70, 80), "ghost": (1, 1)})
    d = editor.diagram()
    assert (d.entities[0].x, d.entities[1].y) == (50.0, 80)
    editor.undo()
    assert editor.diagram().entities[0].x == 0


def test_duplicate_copies_entities_and_what_joins_them(editor):
    editor.new(DiagramKind.ER)
    a, b = editor.add_entity(0, 0, "A"), editor.add_entity(200, 0, "B")
    editor.add_relationship([a, b], "R")
    new = editor.duplicate([a, b])
    d = editor.diagram()
    assert [e.name for e in d.entities] == ["A", "B", "A 2", "B 2"]
    assert len(d.relationships) == 2 and len(new) == 3
    assert {p.entity_id for p in d.relationships[1].participants} == set(new[:2])


def test_uml_classes_and_links(editor):
    editor.new(DiagramKind.UML)
    shape = editor.add_class(0, 0, "Figura")
    circle = editor.add_class(0, 200, "Cerchio")
    editor.update_class(shape, ClassInput("Figura", ClassKind.ABSTRACT, "# nome: String\n\n",
                                          "+ abstract area(): double\n+ static conta(): int"))
    c = editor.diagram().classes[0]
    assert c.kind is ClassKind.ABSTRACT and [m.line for m in c.attributes] == ["# nome: String"]
    area, count = c.operations
    assert area.abstract and area.text == "area(): double" and area.visibility == "+"
    assert count.static and count.line == "+ static conta(): int"
    link = editor.add_link(LinkKind.INHERITANCE, circle, shape)
    editor.update_link(link, LinkInput(LinkKind.ASSOCIATION, "1", "0..*", " ha "))
    editor.reverse_link(link)
    l = editor.diagram().links[0]
    assert (l.source, l.target, l.source_multiplicity, l.label) == (shape, circle, "0..*", "ha")
    editor.delete([circle])
    assert editor.diagram().links == ()


def test_notifications(editor):
    seen = []
    editor.subscribe(seen.append)
    editor.new(DiagramKind.ER)
    assert seen == [Change.DIAGRAM, Change.DOCUMENT]
    seen.clear()
    editor.set_notation(Notation.CROWS_FOOT)
    editor.set_notation(Notation.CROWS_FOOT)  # no change, no notice
    assert seen == [Change.DIAGRAM, Change.DOCUMENT]


def test_save_and_open_round_trip(editor, tmp_path):
    school_er(editor)
    assert not editor.dirty and not editor.can_undo
    before = editor.diagram()
    path = tmp_path / "registro.ligature"
    editor.save(str(path))
    assert editor.path == str(path) and not editor.dirty
    editor.new(DiagramKind.UML)
    editor.open(str(path))
    assert editor.diagram() == before and editor.format is FileFormat.LIGATURE


def test_uml_round_trip(editor, tmp_path):
    shapes_uml(editor)
    before = editor.diagram()
    path = tmp_path / "figure.ligature"
    editor.save(str(path))
    editor.open(str(path))
    assert editor.diagram() == before


def test_undo_back_to_the_saved_state_is_clean(editor, tmp_path):
    editor.new(DiagramKind.ER)
    editor.add_entity(0, 0)
    editor.save(str(tmp_path / "a.ligature"))
    editor.add_entity(10, 10)
    assert editor.dirty
    editor.undo()
    assert not editor.dirty


def test_saving_needs_a_place(editor):
    editor.new(DiagramKind.ER)
    with pytest.raises(NotFound):
        editor.save()


def test_opening_something_else_fails_clearly(editor, tmp_path):
    bad = tmp_path / "x.ligature"
    bad.write_text("hello")
    with pytest.raises(FileFormatError):
        editor.open(str(bad))


def test_schema_record(editor):
    school_er(editor)
    schema = editor.schema(Dialect.MYSQL)
    names = [t.name for t in schema.tables]
    assert names == ["Classe", "Studente", "Materia", "Docente", "Valutazione", "Insegna"]
    classe = schema.tables[0]
    assert "cf_docente" in [c.name for c in classe.columns]  # Coordina: (1,1) side
    assert schema.issues == () and "CREATE TABLE Valutazione" in schema.sql
    editor.add_entity(0, 0, "Vuota")
    assert editor.schema().issues[0].kind is IssueKind.NO_KEY


# ---- generalisations, copy and paste ----------------------------------------------------------

def test_generalisations_are_built_child_by_child(editor, tmp_path):
    from ligature.application.inputs import GeneralisationInput
    from ligature.application.types import Mapping
    editor.new(DiagramKind.ER)
    person, student, teacher = (editor.add_entity(x, 0, n) for x, n in
                                ((0, "Persona"), (-100, "Studente"), (100, "Docente")))
    g = editor.add_generalisation(student, person)
    assert editor.add_generalisation(teacher, person) == g  # joins the same one
    record = editor.diagram().generalisations[0]
    assert record.children == (student, teacher) and record.label == "(p,e)"
    editor.update_generalisation(g, GeneralisationInput((student, teacher), total=True,
                                                        exclusive=False, mapping=Mapping.INTO_PARENT))
    assert editor.diagram().generalisations[0].label == "(t,s)"
    with pytest.raises(NotFound):
        editor.add_generalisation(person, student)  # a circle
    path = tmp_path / "isa.ligature"
    editor.save(str(path))
    before = editor.diagram()
    editor.open(str(path))
    assert editor.diagram() == before
    editor.delete([student])
    assert editor.diagram().generalisations[0].children == (teacher,)
    editor.update_generalisation(g, GeneralisationInput(()))
    assert editor.diagram().generalisations == ()


def test_copy_and_paste_between_diagrams(editor):
    school_er(editor)
    d = editor.diagram()
    student = next(e.id for e in d.entities if e.name == "Studente")
    classe = next(e.id for e in d.entities if e.name == "Classe")
    data = editor.copy([student, classe])
    new = editor.paste(data)
    after = editor.diagram()
    assert len(after.entities) == 6 and len(after.relationships) == 5  # Frequenta came too
    assert {e.name for e in after.entities} >= {"Studente 2", "Classe 2"}
    editor.undo()
    editor.new(DiagramKind.ER)
    ids = editor.paste(data, 500, 500)
    pasted = editor.diagram()
    assert len(ids) == 3 and {e.name for e in pasted.entities} == {"Studente", "Classe"}
    xs = [e.x for e in pasted.entities] + [r.x for r in pasted.relationships]
    assert abs(sum(xs) / len(xs) - 500) <= 10
    editor.new(DiagramKind.UML)
    with pytest.raises(NotFound):
        editor.paste(data)
    assert new


def test_nudging_is_one_undo_step(editor):
    editor.new(DiagramKind.ER)
    a = editor.add_entity(0, 0)
    for _i in range(3):
        editor.nudge([a], 10, 0)
    assert editor.diagram().entities[0].x == 30
    editor.undo()
    assert editor.diagram().entities[0].x == 0
