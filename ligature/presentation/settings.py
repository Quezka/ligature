"""Settings: appearance and language."""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QProcess
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDialog, QHBoxLayout, QPushButton, QVBoxLayout,
)

from . import i18n, theme
from .i18n import _
from .views.common import Card, Segmented, caption, label


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Settings"))
        self.setMinimumWidth(460)
        manager = theme.manager()
        appearance = Card(_("Appearance"))
        mode = Segmented([("system", _("System")), ("light", _("Light")), ("dark", _("Dark"))])
        mode.set_value(manager.mode)
        mode.changed.connect(manager.set_mode)
        appearance.add(mode)
        appearance.add(label(_("Exported pictures are always drawn on white."), "hint"))

        language = Card(_("Language"))
        self.language = QComboBox()
        for code, name in i18n.LANGUAGES:
            self.language.addItem(_(name) if code == "" else name, code)
        self.language.setCurrentIndex(max(0, self.language.findData(i18n.chosen_language())))
        self.restart = QPushButton(_("Restart Ligature now"))
        self.restart.hide()
        self.restart.clicked.connect(self._restart)
        self.language.currentIndexChanged.connect(self._language_changed)
        language.add(caption(_("Interface language")))
        language.add(self.language)
        language.add(self.restart)

        close = QPushButton(_("Close"))
        close.clicked.connect(self.accept)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(close)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(14)
        layout.addWidget(appearance)
        layout.addWidget(language)
        layout.addLayout(row)

    def _language_changed(self):
        i18n.set_chosen_language(self.language.currentData())
        self.restart.show()

    def _restart(self):
        window = self.parent().window() if self.parent() else None
        if window is not None and not window.close():
            return
        QProcess.startDetached(QCoreApplication.applicationFilePath(),
                               QCoreApplication.arguments()[1:])
        QApplication.quit()
