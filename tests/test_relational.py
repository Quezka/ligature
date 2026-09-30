"""ER schema -> tables -> SQL, following the rules taught at school."""
from ligature.domain import (
    Attribute, Cardinality, Diagram, DiagramKind, Dialect, Entity, IssueKind, Participant, Point,
    Relationship, identifier, to_sql, to_tables,
)

P0 = Point(0, 0)
ONE = Cardinality(1, False)
ZERO_ONE = Cardinality(0, False)
MANY = Cardinality(0, True)
ONE_MANY = Cardinality(1, True)


def er(*items):
    d = Diagram(DiagramKind.ER)
    for item in items:
        d = d.put(item)
    return d


def entity(id, name, *attrs, weak=False):
    return Entity(id, name, P0, tuple(attrs), weak)


def rel(id, name, *parts, attrs=()):
    return Relationship(id, name, P0, tuple(Participant(e, c, *role) for e, c, *role in parts),
                        tuple(attrs))


CLASSE = entity("c", "Classe", Attribute("id", "INT", key=True), Attribute("sezione"))
STUDENTE = entity("s", "Studente", Attribute("matricola", "CHAR(6)", key=True),
                  Attribute("email", optional=True))


def tables(d):
    schema = to_tables(d)
    return {t.name: t for t in schema.tables}, schema.issues


def test_one_to_many_puts_the_foreign_key_on_the_single_side():
    t, issues = tables(er(CLASSE, STUDENTE, rel("r", "Frequenta", ("s", ONE), ("c", ONE_MANY),
                                                attrs=[Attribute("dal", "DATE")])))
    assert not issues and set(t) == {"Classe", "Studente"}
    studente = t["Studente"]
    assert studente.primary_key == ("matricola",)
    fk = {c.name: c for c in studente.columns}["id_classe"]
    assert fk.foreign and not fk.nullable and fk.type == "INT"
    assert {c.name: c for c in studente.columns}["dal"].type == "DATE"  # relationship attribute
    assert {c.name: c for c in studente.columns}["email"].nullable
    assert studente.foreign_keys[0].table == "Classe"


def test_optional_participation_makes_a_nullable_key():
    t, _ = tables(er(CLASSE, STUDENTE, rel("r", "Frequenta", ("s", ZERO_ONE), ("c", MANY))))
    assert {c.name: c for c in t["Studente"].columns}["id_classe"].nullable


def test_many_to_many_gets_its_own_table():
    corso = entity("k", "Corso", Attribute("codice", key=True))
    t, _ = tables(er(STUDENTE, corso, rel("r", "Segue", ("s", MANY), ("k", ONE_MANY),
                                          attrs=[Attribute("voto", "INT")])))
    segue = t["Segue"]
    assert segue.primary_key == ("matricola_studente", "codice_corso")
    assert [c.name for c in segue.columns][-1] == "voto"
    assert {fk.table for fk in segue.foreign_keys} == {"Studente", "Corso"}


def test_one_to_one_goes_on_the_mandatory_side_and_is_unique():
    docente = entity("d", "Docente", Attribute("cf", "CHAR(16)", key=True))
    t, _ = tables(er(CLASSE, docente, rel("r", "Coordina", ("d", ZERO_ONE), ("c", ONE))))
    fk = t["Classe"].foreign_keys[0]
    assert fk.table == "Docente" and fk.unique and fk.columns == ("cf_docente",)
    sql = to_sql(to_tables(er(CLASSE, docente, rel("r", "Coordina", ("d", ZERO_ONE),
                                                    ("c", ONE)))))
    assert "UNIQUE (cf_docente)" in sql


def test_weak_entity_borrows_its_owners_key():
    edificio = entity("e", "Edificio", Attribute("codice", key=True))
    aula = entity("a", "Aula", Attribute("numero", "INT", key=True), weak=True)
    t, issues = tables(er(edificio, aula, rel("r", "Contiene", ("a", ONE), ("e", ONE_MANY))))
    assert not issues
    assert t["Aula"].primary_key == ("numero", "codice_edificio")
    assert len(t["Aula"].foreign_keys) == 1


def test_recursive_relationship_uses_roles():
    persona = entity("p", "Persona", Attribute("id", "INT", key=True))
    t, _ = tables(er(persona, rel("r", "Genitore", ("p", MANY, "figlio"),
                                  ("p", MANY, "genitore"))))
    assert t["Genitore"].primary_key == ("id_figlio", "id_genitore")
    t, _ = tables(er(persona, rel("r", "Capo", ("p", ZERO_ONE, "dipendente"),
                                  ("p", MANY, "capo"))))
    assert "id_capo" in [c.name for c in t["Persona"].columns]


def test_missing_key_is_reported_and_made_up():
    t, issues = tables(er(entity("x", "Nota", Attribute("testo", "TEXT"))))
    assert t["Nota"].primary_key == ("id",)
    assert issues[0].kind is IssueKind.NO_KEY and issues[0].subject == "Nota"


def test_three_way_relationship_is_a_table():
    a, b, c = (entity(i, n, Attribute("id", "INT", key=True)) for i, n in
               (("a", "Docente"), ("b", "Classe"), ("c", "Materia")))
    t, _ = tables(er(a, b, c, rel("r", "Insegna", ("a", MANY), ("b", MANY), ("c", ONE))))
    assert t["Insegna"].primary_key == ("id_docente", "id_classe", "id_materia")


def test_sql_orders_tables_and_quotes_reserved_words():
    order = entity("o", "Order", Attribute("id", "INT", key=True), Attribute("date", "DATETIME"))
    d = er(STUDENTE, order, rel("r", "Fa", ("o", ONE), ("s", MANY)))
    sql = to_sql(to_tables(d), Dialect.MYSQL)
    assert sql.index("CREATE TABLE Studente") < sql.index("CREATE TABLE `Order`")
    assert "ENGINE=InnoDB" in sql
    postgres = to_sql(to_tables(d), Dialect.POSTGRESQL)
    assert '"Order"' in postgres and "TIMESTAMP" in postgres
    assert to_sql(to_tables(d), Dialect.SQLITE).startswith("PRAGMA foreign_keys = ON;")


def test_foreign_keys_in_a_cycle_are_added_afterwards():
    a = entity("a", "A", Attribute("id", "INT", key=True))
    b = entity("b", "B", Attribute("id", "INT", key=True))
    d = er(a, b, rel("r1", "R1", ("a", ONE), ("b", MANY)), rel("r2", "R2", ("b", ONE), ("a", MANY)))
    sql = to_sql(to_tables(d))
    assert "ALTER TABLE A ADD FOREIGN KEY (id_b) REFERENCES B (id);" in sql


def test_identifiers_are_made_safe():
    assert identifier("Città di nascita") == "Citta_di_nascita"
    assert identifier("1° anno") == "_1_anno"
    assert identifier("  ") == "unnamed"


# ---- generalisations ------------------------------------------------------------------------

from ligature.domain import Generalisation, Mapping  # noqa: E402

PERSONA = entity("p", "Persona", Attribute("cf", "CHAR(16)", key=True), Attribute("nome"))
STUD = entity("s", "Studente", Attribute("matricola", "CHAR(6)"))
DOC = entity("d", "Docente", Attribute("materia"))
CORSO = entity("k", "Corso", Attribute("codice", key=True))


def isa(mapping, total=True, exclusive=True):
    return Generalisation("g", "p", ("s", "d"), total, exclusive, mapping)


def test_generalisation_separate_tables_share_the_parents_key():
    t, issues = tables(er(PERSONA, STUD, DOC, isa(Mapping.SEPARATE)))
    assert not issues and set(t) == {"Persona", "Studente", "Docente"}
    assert t["Studente"].primary_key == ("cf",)
    assert t["Studente"].foreign_keys[0].table == "Persona"
    assert [c.name for c in t["Studente"].columns] == ["cf", "matricola"]


def test_generalisation_into_the_parent():
    d = er(PERSONA, STUD, DOC, CORSO, isa(Mapping.INTO_PARENT),
           rel("r", "Segue", ("s", ONE_MANY), ("k", MANY)))
    t, issues = tables(d)
    assert not issues and set(t) == {"Persona", "Corso", "Segue"}
    columns = {c.name: c for c in t["Persona"].columns}
    assert columns["matricola"].nullable and columns["materia"].nullable
    assert not columns["tipo"].nullable  # total: every person is one of them
    assert "cf_persona" in [c.name for c in t["Segue"].columns]  # the relationship moved up
    overlapping, _ = tables(er(PERSONA, STUD, DOC, isa(Mapping.INTO_PARENT, exclusive=False)))
    assert {"is_studente", "is_docente"} <= {c.name for c in overlapping["Persona"].columns}


def test_generalisation_into_the_children():
    t, issues = tables(er(PERSONA, STUD, DOC, isa(Mapping.INTO_CHILDREN)))
    assert not issues and set(t) == {"Studente", "Docente"}
    assert t["Docente"].primary_key == ("cf",)
    assert [c.name for c in t["Docente"].columns] == ["cf", "nome", "materia"]


def test_merging_into_children_needs_a_total_generalisation_without_relationships():
    t, issues = tables(er(PERSONA, STUD, DOC, isa(Mapping.INTO_CHILDREN, total=False)))
    assert issues[0].kind is IssueKind.CHILDREN_NEED_TOTAL and "Persona" in t
    d = er(PERSONA, STUD, DOC, CORSO, isa(Mapping.INTO_CHILDREN),
           rel("r", "Frequenta", ("p", MANY), ("k", MANY)))
    t, issues = tables(d)
    assert issues[0].kind is IssueKind.CHILDREN_NEED_NO_RELATIONSHIPS and "Persona" in t


def test_nested_generalisations():
    ric = entity("x", "Ricercatore", Attribute("area"))
    d = er(PERSONA, STUD, DOC, ric, isa(Mapping.INTO_PARENT),
           Generalisation("g2", "d", ("x",), mapping=Mapping.INTO_PARENT))
    t, _ = tables(d)
    assert set(t) == {"Persona"}
    assert {"area", "materia", "matricola"} <= {c.name for c in t["Persona"].columns}


def test_deleting_entities_keeps_generalisations_consistent():
    d = er(PERSONA, STUD, DOC, isa(Mapping.SEPARATE))
    assert d.without({"s"}).generalisations[0].children == ("d",)
    assert d.without({"s", "d"}).generalisations == ()
    assert d.without({"p"}).generalisations == ()
