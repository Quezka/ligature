from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMimeData, QSettings, QSize, Qt
from PySide6.QtGui import QAction, QGuiApplication, QIcon, QImage, QKeySequence
from PySide6.QtWidgets import (
    QButtonGroup, QFileDialog, QFrame, QHBoxLayout, QLabel, QMainWindow, QMenu, QMessageBox,
    QSizePolicy, QStackedWidget, QToolButton, QVBoxLayout, QWidget,
)

from .. import FILE_EXTENSION, HOMEPAGE, __version__
from ..application.errors import ApplicationError
from ..application.services import Services
from ..application.types import DiagramKind, FileFormat
from . import theme
from .bridge import ChangeRelay
from .fit import clamp_window
from .export import pdf_bytes, png_bytes, svg_bytes
from .i18n import N_, _
from .icons import APP_ICON
from .settings import SettingsDialog
from .updates_ui import UpdateChecker
from .views.diagram import DiagramPage
from .views.home import HomePage
from .views.sql import SqlPage

RECENT = 12
OPEN_FILTER = N_("Diagrams")
PNG_MIME = "image/png"


def _filters(*pairs) -> str:
    return ";;".join(f"{_(name)} ({pattern})" for name, pattern in pairs)


class Sidebar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(206)
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        brand_icon = QLabel()
        brand_icon.setPixmap(QIcon(str(APP_ICON)).pixmap(28, 28))
        brand = QHBoxLayout()
        brand.setContentsMargins(12, 4, 12, 0)
        brand.setSpacing(10)
        brand.addWidget(brand_icon)
        brand.addWidget(QLabel(_("Ligature"), objectName="brand"))
        brand.addStretch()
        self.nav = QVBoxLayout()
        self.nav.setSpacing(2)
        self.footer = QVBoxLayout()
        self.footer.setSpacing(2)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 20, 12, 14)
        layout.setSpacing(6)
        layout.addLayout(brand)
        layout.addSpacing(18)
        layout.addLayout(self.nav)
        layout.addStretch()
        layout.addLayout(self.footer)

    def nav_button(self, icon_name: str, text: str, checkable: bool = True) -> QToolButton:
        button = QToolButton(objectName="nav", text=f"  {text}", checkable=checkable)
        button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.setIconSize(QSize(18, 18))
        button.setCursor(Qt.PointingHandCursor)
        theme.set_icon(button, icon_name, "muted", "accent" if checkable else None)
        return button

    def add_page(self, icon_name: str, text: str, shortcut: str) -> QToolButton:
        button = self.nav_button(icon_name, text)
        button.setToolTip(f"{text}  ({shortcut})")
        self.group.addButton(button, len(self.group.buttons()))
        self.nav.addWidget(button)
        return button


class MainWindow(QMainWindow):
    HOME, DIAGRAM, SQL = range(3)
    PAGES = [("home", N_("Home")), ("diagram", N_("Diagram")), ("database", N_("SQL"))]

    def __init__(self, services: Services):
        super().__init__()
        self.services = services
        self.editor = services.editor
        clamp_window(self, 1320, 840, 1000, 640)
        self.setAcceptDrops(True)

        self.relay = ChangeRelay(self.editor, self)
        self.home = HomePage()
        self.diagram = DiagramPage(services)
        self.sql = SqlPage(services)
        self.sidebar = Sidebar()
        self.stack = QStackedWidget()
        for i, (page, (icon, text)) in enumerate(zip((self.home, self.diagram, self.sql),
                                                     self.PAGES)):
            self.stack.addWidget(page)
            self.sidebar.add_page(icon, _(text), f"Ctrl+{i + 1}")
        self.sidebar.group.idClicked.connect(self.show_page)
        more = self.sidebar.nav_button("more", _("More"), checkable=False)
        more.setPopupMode(QToolButton.InstantPopup)
        more.setMenu(self._more_menu())
        self.sidebar.footer.addWidget(more)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        self.relay.diagramChanged.connect(self._diagram_changed)
        self.relay.documentChanged.connect(self._document_changed)
        self.home.newRequested.connect(self.new_diagram)
        self.home.openRequested.connect(lambda path: self.open_file(path or None))
        self.home.sampleRequested.connect(self.open_sample)
        self.diagram.saveRequested.connect(self.save)
        self.diagram.exportRequested.connect(self.export)
        self.diagram.problem.connect(lambda text: QMessageBox.warning(self, _("Ligature"), text))
        self.sql.saveRequested.connect(self.save_sql)
        self.updater = UpdateChecker(services, self)  # not `update`: that's QWidget's
        self._shortcuts()

        settings = QSettings()
        geometry = settings.value("window/geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        self.home.set_recent(self.recent_files())
        self._document_changed()
        self.show_page(self.HOME)

    # ---- pages ------------------------------------------------------------------------

    def show_page(self, index: int):
        if index != self.HOME and not self.editor.is_open:
            index = self.HOME
        self.stack.setCurrentIndex(index)
        self.sidebar.group.button(index).setChecked(True)
        if index == self.SQL:
            self.sql.refresh()
        if index == self.DIAGRAM:
            self.diagram.view.setFocus()

    def _diagram_changed(self):
        if self.editor.is_open:
            self.diagram.refresh()
            if self.stack.currentIndex() == self.SQL:
                self.sql.refresh()

    def _document_changed(self):
        editor = self.editor
        open_ = editor.is_open
        for page in (self.DIAGRAM, self.SQL):
            button = self.sidebar.group.button(page)
            button.setEnabled(open_)
            text = _(self.PAGES[page][1])
            button.setToolTip(f"{text}  (Ctrl+{page + 1})" if open_ else
                              _("{page}: start or open a diagram first").format(page=text))
        self.sidebar.group.button(self.SQL).setVisible(not open_ or editor.kind is DiagramKind.ER)
        if not open_:
            self.setWindowTitle(_("Ligature"))
            return
        record = editor.diagram()
        name = Path(editor.path).name if editor.path else _("Not saved yet")
        title = record.title or (Path(editor.path).stem if editor.path else _("Untitled diagram"))
        kind = _("ER diagram") if editor.kind is DiagramKind.ER else _("UML class diagram")
        state = _("unsaved changes") if editor.dirty else _("saved")
        subtitle = f"{kind} · {name}" + (f" · {state}" if editor.path else "")
        self.diagram.set_heading(title, subtitle)
        self.diagram.undo_button.setEnabled(editor.can_undo)
        self.diagram.redo_button.setEnabled(editor.can_redo)
        self.setWindowTitle(("• " if editor.dirty else "") + f"{title} — Ligature")

    # ---- documents ---------------------------------------------------------------------

    def _run(self, action) -> bool:
        try:
            action()
            return True
        except ApplicationError as e:
            QMessageBox.warning(self, _("Ligature"), _(str(e)))
            return False

    def maybe_keep_changes(self) -> bool:
        """Before closing or replacing the diagram: False means stay (the user cancelled)."""
        if not (self.editor.is_open and self.editor.dirty):
            return True
        box = QMessageBox(QMessageBox.Warning, _("Unsaved changes"),
                          _("Save the changes to this diagram first?"),
                          QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, self)
        box.setDefaultButton(QMessageBox.Save)
        answer = box.exec()
        if answer == QMessageBox.Save:
            return self.save()
        return answer == QMessageBox.Discard

    def new_diagram(self, kind: DiagramKind):
        if self.maybe_keep_changes():
            self.editor.new(kind)
            self.diagram.refresh(fit=True)
            self.diagram.view.set_zoom(1.0)
            self.diagram.view.centerOn(300, 250)
            self.show_page(self.DIAGRAM)

    def open_sample(self, name: str):
        from ..demo import school_er, shapes_uml, university_er
        if self.maybe_keep_changes():
            {"school": school_er, "university": university_er,
             "shapes": shapes_uml}[name](self.editor)
            self.diagram.refresh(fit=True)
            self.show_page(self.DIAGRAM)

    def open_file(self, path: str | None = None):
        if not self.maybe_keep_changes():
            return
        if not path:
            path, _chosen = QFileDialog.getOpenFileName(
                self, _("Open a diagram"), self._folder(),
                _filters((OPEN_FILTER, f"*{FILE_EXTENSION} *.png *.svg"),
                         (N_("All files"), "*")))
            if not path:
                return
        if self._run(lambda: self.editor.open(path)):
            self._remember(path)
            self.diagram.refresh(fit=True)
            self.show_page(self.DIAGRAM)
        else:
            self._forget(path)

    def open_clipboard(self):
        data = QGuiApplication.clipboard().mimeData()
        raw = bytes(data.data(PNG_MIME)) if data.hasFormat(PNG_MIME) else b""
        if not raw:
            QMessageBox.information(self, _("Ligature"), _(
                "Copy a Ligature picture first (e.g. from a note), then try again."))
            return
        if self.maybe_keep_changes() and self._run(lambda: self.editor.open_bytes(raw)):
            self.diagram.refresh(fit=True)
            self.show_page(self.DIAGRAM)

    def save(self) -> bool:
        if not self.editor.is_open:
            return False
        if not self.editor.path:
            return self.save_as()
        return self._save_to(self.editor.path)

    def save_as(self) -> bool:
        if not self.editor.is_open:
            return False
        name = (self.editor.diagram().title or _("Diagram")) + FILE_EXTENSION
        path, chosen = QFileDialog.getSaveFileName(
            self, _("Save the diagram"), str(Path(self._folder()) / name),
            _filters((N_("Ligature diagram"), f"*{FILE_EXTENSION}"),
                     (N_("Editable PNG picture"), "*.png"),
                     (N_("Editable SVG picture"), "*.svg")))
        if not path:
            return False
        if not Path(path).suffix:
            path += ".png" if "png" in chosen else ".svg" if "svg" in chosen else FILE_EXTENSION
        return self._save_to(path)

    def _save_to(self, path: str) -> bool:
        suffix = Path(path).suffix.lower()
        record = self.editor.diagram()
        picture = (png_bytes(record) if suffix == ".png"
                   else svg_bytes(record) if suffix == ".svg" else None)
        if self._run(lambda: self.editor.save(path, picture)):
            self._remember(path)
            return True
        return False

    def export(self, kind: str):
        if not self.editor.is_open:
            return
        record = self.editor.diagram()
        if kind == "copy":
            png = png_bytes(record)
            mime = QMimeData()
            mime.setData(PNG_MIME, self.editor.encode(FileFormat.PNG, png))
            mime.setImageData(QImage.fromData(png))
            QGuiApplication.clipboard().setMimeData(mime)
            return
        names = {"png": (N_("PNG picture"), ".png"), "svg": (N_("SVG picture"), ".svg"),
                 "pdf": (N_("PDF document"), ".pdf")}
        label, suffix = names[kind]
        stem = record.title or (Path(self.editor.path).stem if self.editor.path else _("Diagram"))
        path, _chosen = QFileDialog.getSaveFileName(
            self, _("Export"), str(Path(self._folder()) / (stem + suffix)),
            _filters((label, f"*{suffix}")))
        if not path:
            return
        if not path.lower().endswith(suffix):
            path += suffix
        if kind == "png":
            data = self.editor.encode(FileFormat.PNG, png_bytes(record))
        elif kind == "svg":
            data = self.editor.encode(FileFormat.SVG, svg_bytes(record))
        else:
            data = pdf_bytes(record)
        self._run(lambda: self.editor.export(path, data))

    def save_sql(self, text: str):
        stem = self.editor.diagram().title or "schema"
        path, _chosen = QFileDialog.getSaveFileName(
            self, _("Save the SQL"), str(Path(self._folder()) / f"{stem}.sql"),
            _filters((N_("SQL script"), "*.sql")))
        if path:
            self._run(lambda: self.editor.export(path, text.encode("utf-8")))

    # ---- recent files -----------------------------------------------------------------

    def recent_files(self) -> list[str]:
        value = QSettings().value("recent", [])
        paths = [value] if isinstance(value, str) else list(value or [])
        return [p for p in paths if Path(p).exists()][:RECENT]

    def _remember(self, path: str):
        path = str(Path(path).resolve())
        paths = [path] + [p for p in self.recent_files() if p != path]
        QSettings().setValue("recent", paths[:RECENT])
        QSettings().setValue("folder", str(Path(path).parent))
        self.home.set_recent(paths[:RECENT])

    def _forget(self, path: str):
        paths = [p for p in self.recent_files() if p != str(path)]
        QSettings().setValue("recent", paths)
        self.home.set_recent(paths)

    def _folder(self) -> str:
        folder = QSettings().value("folder", "")
        return folder if folder and Path(folder).is_dir() else str(Path.home())

    # ---- menus and shortcuts ---------------------------------------------------------------

    def _shortcut(self, keys, slot):
        action = QAction(self)
        action.setShortcut(QKeySequence(keys))
        action.setShortcutContext(Qt.ApplicationShortcut)
        action.triggered.connect(slot)
        self.addAction(action)

    def _shortcuts(self):
        for i in range(len(self.PAGES)):
            self._shortcut(f"Ctrl+{i + 1}", lambda _c=False, i=i: self.show_page(i))
        self._shortcut(QKeySequence.New, lambda: self.new_diagram(DiagramKind.ER))
        self._shortcut("Ctrl+Shift+N", lambda: self.new_diagram(DiagramKind.UML))
        self._shortcut(QKeySequence.Open, lambda: self.open_file())
        self._shortcut(QKeySequence.Save, self.save)
        self._shortcut("Ctrl+Shift+S", self.save_as)
        self._shortcut("Ctrl+Shift+C", lambda: self.export("copy"))
        self._shortcut("Ctrl+E", lambda: self.export("png"))
        self._shortcut("Ctrl+P", lambda: self.export("pdf"))
        self._shortcut(QKeySequence.Undo, self.editor.undo)
        self._shortcut("Ctrl+Shift+Z", self.editor.redo)
        self._shortcut("Ctrl+Y", self.editor.redo)
        self._shortcut("Ctrl+,", self.open_settings)
        self._shortcut(QKeySequence.Quit, self.close)
        self._shortcut("Ctrl+Q", self.close)

    def _more_menu(self) -> QMenu:
        menu = QMenu(self)
        entries = [
            (_("New ER diagram"), "Ctrl+N", lambda: self.new_diagram(DiagramKind.ER)),
            (_("New UML class diagram"), "Ctrl+Shift+N",
             lambda: self.new_diagram(DiagramKind.UML)),
            (_("Open…"), "Ctrl+O", lambda: self.open_file()),
            (_("Open a picture from the clipboard"), None, self.open_clipboard),
            None,
            (_("Save"), "Ctrl+S", self.save),
            (_("Save as…"), "Ctrl+Shift+S", self.save_as),
            (_("Export as PNG…"), "Ctrl+E", lambda: self.export("png")),
            (_("Export as SVG…"), None, lambda: self.export("svg")),
            (_("Export as PDF…"), "Ctrl+P", lambda: self.export("pdf")),
            (_("Copy as picture"), "Ctrl+Shift+C", lambda: self.export("copy")),
            None,
            (_("Settings…"), "Ctrl+,", self.open_settings),
            (_("Check for updates…"), None, lambda: self.updater.check_now()),
            (_("Keyboard shortcuts"), None, self.show_shortcuts),
            (_("About Ligature"), None, self.about),
            None,
            (_("Quit Ligature"), "Ctrl+Q", self.close),
        ]
        for entry in entries:
            if entry is None:
                menu.addSeparator()
                continue
            text, keys, slot = entry
            action = menu.addAction(text, slot)
            if keys:
                action.setShortcut(QKeySequence(keys))
                action.setShortcutVisibleInContextMenu(True)
                action.setShortcutContext(Qt.WidgetShortcut)  # the window-level ones fire
        return menu

    def open_settings(self):
        SettingsDialog(self.services, self.updater, self).exec()

    def show_shortcuts(self):
        rows = [("Ctrl+1 / 2 / 3", " / ".join(_(t) for _i, t in self.PAGES)),
                ("Ctrl+N / Ctrl+Shift+N", _("New ER / UML diagram")),
                ("Ctrl+O, Ctrl+S, Ctrl+Shift+S", _("Open, save, save as")),
                ("V, E, R, G, C, L", _("Tools: select, entity, relationship, generalisation, "
                                       "class, link")),
                ("Ctrl+C / Ctrl+X / Ctrl+V", _("Copy, cut, paste (also into another diagram)")),
                (_("Arrow keys"), _("Move the selection (with Shift, further)")),
                (_("Double-click"), _("Add an entity or class, or edit the one clicked")),
                ("Delete", _("Delete the selection")), ("Ctrl+D", _("Duplicate")),
                ("Ctrl+Z / Ctrl+Shift+Z", _("Undo / redo")), ("Esc", _("Cancel the tool")),
                (_("Space + drag, middle button"), _("Move around")),
                ("Ctrl+scroll, Ctrl+= / Ctrl+-", _("Zoom")), ("Ctrl+0", _("Fit the diagram")),
                ("Ctrl+E, Ctrl+P", _("Export as PNG, PDF")),
                ("Ctrl+Shift+C", _("Copy as picture (paste it into notes)"))]
        table = "".join(f"<tr><td style='padding:3px 18px 3px 0'><b>{k}</b></td><td>{v}</td></tr>"
                        for k, v in rows)
        QMessageBox.information(self, _("Keyboard shortcuts"), f"<table>{table}</table>")

    def about(self):
        QMessageBox.about(
            self, _("About Ligature"),
            f"<h3>Ligature {__version__}</h3>"
            f"<p>{_('ER and UML class diagrams for school, with the SQL they make.')}</p>"
            f"<p><a href='{HOMEPAGE}'>{HOMEPAGE}</a></p>"
            f"<p>{_('Free software under the GNU General Public License, version 3 or later.')}"
            "</p>")

    # ---- window ----------------------------------------------------------------------------

    def dragEnterEvent(self, event):
        if any(url.isLocalFile() for url in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile():
                self.open_file(url.toLocalFile())
                break

    def closeEvent(self, event):
        if not self.maybe_keep_changes():
            event.ignore()
            return
        QSettings().setValue("window/geometry", self.saveGeometry())
        super().closeEvent(event)
