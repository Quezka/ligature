"""Sample diagrams (`ligature --demo`), built through the use cases like a user would."""
from __future__ import annotations

from .application.editor import Editor
from .application.inputs import (
    AttributeInput as A, ClassInput, EntityInput, GeneralisationInput, LinkInput,
    ParticipantInput as P, RelationshipInput,
)
from .application.types import ClassKind, DiagramKind, LinkKind, Mapping


def school_er(editor: Editor):
    """Students, classes, subjects and teachers: the classic register exercise."""
    editor.new(DiagramKind.ER, "Registro scolastico")
    classe = editor.add_entity(100, 140, "Classe")
    studente = editor.add_entity(760, 140, "Studente")
    materia = editor.add_entity(760, 540, "Materia")
    docente = editor.add_entity(100, 540, "Docente")
    editor.update_entity(classe, EntityInput("Classe", (
        A("id_classe", "INT", key=True), A("anno", "INT"), A("sezione", "CHAR(1)"))))
    editor.update_entity(studente, EntityInput("Studente", (
        A("matricola", "CHAR(8)", key=True), A("nome"), A("cognome"),
        A("data_nascita", "DATE"), A("email", optional=True))))
    editor.update_entity(materia, EntityInput("Materia", (
        A("codice", "CHAR(5)", key=True), A("nome"))))
    editor.update_entity(docente, EntityInput("Docente", (
        A("cf", "CHAR(16)", key=True), A("nome"), A("cognome"))))
    frequenta = editor.add_relationship([studente, classe], "Frequenta")
    editor.update_relationship(frequenta, RelationshipInput("Frequenta", (
        P(studente, "(1,1)"), P(classe, "(1,N)"))))
    voto = editor.add_relationship([studente, materia], "Valutazione")
    editor.update_relationship(voto, RelationshipInput("Valutazione", (
        P(studente, "(0,N)"), P(materia, "(0,N)")), (A("voto", "DECIMAL(4,2)"), A("data", "DATE"))))
    insegna = editor.add_relationship([docente, materia], "Insegna")
    editor.update_relationship(insegna, RelationshipInput("Insegna", (
        P(docente, "(1,N)"), P(materia, "(1,N)"))))
    coordina = editor.add_relationship([docente, classe], "Coordina")
    editor.update_relationship(coordina, RelationshipInput("Coordina", (
        P(docente, "(0,1)"), P(classe, "(1,1)"))))
    _settled(editor)


def university_er(editor: Editor):
    """People who are students or teachers (a generalisation), courses and exams."""
    editor.new(DiagramKind.ER, "Università")
    persona = editor.add_entity(400, 100, "Persona")
    studente = editor.add_entity(200, 330, "Studente")
    docente = editor.add_entity(600, 330, "Docente")
    corso = editor.add_entity(400, 580, "Corso")
    editor.update_entity(persona, EntityInput("Persona", (
        A("cf", "CHAR(16)", key=True), A("nome"), A("cognome"), A("email", optional=True))))
    editor.update_entity(studente, EntityInput("Studente", (A("matricola", "CHAR(8)"),
                                                            A("anno_corso", "INT"))))
    editor.update_entity(docente, EntityInput("Docente", (A("ruolo"),)))
    editor.update_entity(corso, EntityInput("Corso", (A("codice", "CHAR(6)", key=True),
                                                      A("titolo"), A("cfu", "INT"))))
    g = editor.add_generalisation(studente, persona)
    editor.add_generalisation(docente, persona)
    editor.update_generalisation(g, GeneralisationInput((studente, docente), total=False,
                                                        exclusive=True, mapping=Mapping.SEPARATE))
    esame = editor.add_relationship([studente, corso], "Esame")
    editor.update_relationship(esame, RelationshipInput("Esame", (
        P(studente, "(0,N)"), P(corso, "(0,N)")), (A("voto", "INT"), A("data", "DATE"))))
    tiene = editor.add_relationship([docente, corso], "Tiene")
    editor.update_relationship(tiene, RelationshipInput("Tiene", (
        P(docente, "(0,N)"), P(corso, "(1,1)"))))
    _settled(editor)


def shapes_uml(editor: Editor):
    """Shapes: inheritance, an interface and a composition."""
    editor.new(DiagramKind.UML, "Figure geometriche")
    figura = editor.add_class(360, 120, "Figura")
    cerchio = editor.add_class(200, 400, "Cerchio")
    rettangolo = editor.add_class(520, 400, "Rettangolo")
    disegnabile = editor.add_class(720, 120, "Disegnabile")
    disegno = editor.add_class(60, 120, "Disegno")
    editor.update_class(figura, ClassInput("Figura", ClassKind.ABSTRACT,
                                           "# nome: String", "+ abstract area(): double\n"
                                           "+ getNome(): String"))
    editor.update_class(cerchio, ClassInput("Cerchio", ClassKind.CLASS, "- raggio: double",
                                            "+ Cerchio(raggio: double)\n+ area(): double"))
    editor.update_class(rettangolo, ClassInput(
        "Rettangolo", ClassKind.CLASS, "- base: double\n- altezza: double",
        "+ area(): double"))
    editor.update_class(disegnabile, ClassInput("Disegnabile", ClassKind.INTERFACE, "",
                                                "+ disegna(): void"))
    editor.update_class(disegno, ClassInput("Disegno", ClassKind.CLASS,
                                            "- titolo: String\n+ static conteggio: int",
                                            "+ aggiungi(f: Figura): void"))
    editor.add_link(LinkKind.INHERITANCE, cerchio, figura)
    editor.add_link(LinkKind.INHERITANCE, rettangolo, figura)
    editor.add_link(LinkKind.REALIZATION, figura, disegnabile)
    composition = editor.add_link(LinkKind.COMPOSITION, disegno, figura)
    editor.update_link(composition, LinkInput(LinkKind.COMPOSITION, "1", "0..*", "contiene"))
    _settled(editor)


def _settled(editor: Editor):
    editor.settle()
