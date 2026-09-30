"""The SQL page: the tables an ER diagram becomes, and the CREATE TABLE statements."""
from __future__ import annotations

import html

from PySide6.QtCore import QRegularExpression, Qt, Signal
from PySide6.QtGui import QColor, QFont, QGuiApplication, QSyntaxHighlighter, QTextCharFormat
from PySide6.QtWidgets import QHBoxLayout, QPlainTextEdit, QTextBrowser

from ...application.records import SchemaRecord
from ...application.services import Services
from ...application.types import Dialect, DiagramKind, IssueKind
from .. import theme
from ..i18n import N_, _
from .common import Card, Page, Segmented, button, label

DIALECTS = [(Dialect.STANDARD, N_("Standard")), (Dialect.MYSQL, "MySQL"),
            (Dialect.POSTGRESQL, "PostgreSQL"), (Dialect.SQLITE, "SQLite")]

ISSUES = {
    IssueKind.NO_KEY: N_("“{subject}” has no key, so an “id” column was added. Mark its "
                         "identifier with the key icon."),
    IssueKind.WEAK_WITHOUT_OWNER: N_("“{subject}” is weak but no relationship identifies it: "
                                     "give it a (1,1) relationship to its owner."),
    IssueKind.KEY_CYCLE: N_("“{subject}” is identified through a circle of weak entities."),
    IssueKind.TOO_FEW_PARTICIPANTS: N_("“{subject}” joins fewer than two entities, so it was "
                                       "left out."),
    IssueKind.DUPLICATE_TABLE: N_("Two tables are called “{subject}”; one was renamed."),
    IssueKind.DUPLICATE_COLUMN: N_("“{subject}” appears twice; the second was left out."),
}

KEYWORDS = ("CREATE TABLE", "PRIMARY KEY", "FOREIGN KEY", "REFERENCES", "NOT NULL", "UNIQUE",
            "ALTER TABLE", "ADD", "ENGINE", "PRAGMA")


def mono() -> QFont:
    font = QFont()
    font.setFamilies(["JetBrains Mono", "DejaVu Sans Mono", "Consolas", "monospace"])
    font.setPointSizeF(10)
    return font


class SqlHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.patterns = [QRegularExpression(r"\b" + k.replace(" ", r"\s+") + r"\b")
                         for k in KEYWORDS]
        theme.themed(lambda _t: self.rehighlight())

    def highlightBlock(self, text: str):
        t = theme.current()
        keyword = QTextCharFormat()
        keyword.setForeground(QColor(t.accent))
        keyword.setFontWeight(QFont.Bold)
        for pattern in self.patterns:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), keyword)


class SqlPage(Page):
    saveRequested = Signal(str)  # the SQL text

    def __init__(self, services: Services, parent=None):
        super().__init__(parent)
        self.services = services
        self.title.setText(_("SQL"))
        self.subtitle.setText(_("The tables your ER diagram becomes, ready to paste into "
                                "a database."))
        self.dialect = Segmented([(d, _(text)) for d, text in DIALECTS])
        self.dialect.set_value(Dialect.MYSQL)
        self.dialect.changed.connect(lambda _d: self.refresh())
        copy = button(_("Copy"), "copy")
        copy.clicked.connect(lambda: QGuiApplication.clipboard().setText(self.sql.toPlainText()))
        save = button(_("Save as .sql…"), "save")
        save.clicked.connect(lambda: self.saveRequested.emit(self.sql.toPlainText()))
        self.add_actions(self.dialect, copy, save)

        logical = Card(_("Logical schema"))
        self.schema = QTextBrowser(objectName="code")
        self.schema.setOpenLinks(False)
        logical.add(self.schema, 1)
        key = label(_("Underlined: primary key. Italics with *: foreign key. ? may be empty."),
                    "hint")
        key.setWordWrap(True)
        logical.add(key)
        self.issues = label("", "danger")
        self.issues.setWordWrap(True)
        logical.add(self.issues)
        statements = Card(_("CREATE TABLE statements"))
        self.sql = QPlainTextEdit(objectName="code", readOnly=True)
        self.sql.setFont(mono())
        self.sql.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.highlighter = SqlHighlighter(self.sql.document())
        statements.add(self.sql, 1)
        row = QHBoxLayout()
        row.setSpacing(14)
        row.addWidget(logical, 2)
        row.addWidget(statements, 3)
        self.root.addLayout(row, 1)
        self.empty = label(_("SQL comes from ER diagrams. Open or start an ER diagram to "
                             "see its tables here."), "hint")
        self.empty.setAlignment(Qt.AlignCenter)
        self.root.addWidget(self.empty, 1)
        self.cards = (logical, statements, self.dialect, copy, save)

    def refresh(self):
        editor = self.services.editor
        er = editor.is_open and editor.kind is DiagramKind.ER
        for w in self.cards:
            w.setVisible(er)
        self.empty.setVisible(not er)
        if not er:
            return
        schema = editor.schema(self.dialect.value())
        self.sql.setPlainText(schema.sql or "")
        self.schema.setHtml(logical_html(schema))
        self.issues.setText("\n".join("• " + _(ISSUES[i.kind]).format(subject=i.subject)
                                      for i in schema.issues))
        self.issues.setVisible(bool(schema.issues))


def logical_html(schema: SchemaRecord) -> str:
    """Studente(<u>matricola</u>, nome, <i>id_classe*</i>) — as written in class."""
    t = theme.current()
    if not schema.tables:
        return f"<p style='color:{t.faint}'>{html.escape(_('No entities yet.'))}</p>"
    lines = []
    for table in schema.tables:
        columns = []
        for c in table.columns:
            name = html.escape(c.name)
            if c.foreign:
                name = f"<i>{name}*</i>"
            if c.primary:
                name = f"<u>{name}</u>"
            if c.nullable:
                name += "?"
            columns.append(name)
        lines.append(f"<p style='margin:0 0 8px 0'><b>{html.escape(table.name)}</b>"
                     f"({', '.join(columns)})</p>")
    refs = []
    for table in schema.tables:
        for ref in table.references:
            refs.append(f"{html.escape(table.name)}.{html.escape(', '.join(ref.columns))} → "
                        f"{html.escape(ref.table)}.{html.escape(', '.join(ref.references))}")
    if refs:
        lines.append(f"<p style='color:{t.muted};margin-top:14px'>"
                     + "<br>".join(refs) + "</p>")
    return "".join(lines)
