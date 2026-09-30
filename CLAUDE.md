# Ligature

Python 3.10+ / PySide6 desktop app (Linux + Windows): ER (Chen / crow's foot) and UML class
diagrams, with SQL generation. Sibling of Quire (`../quire`): same look, same toolkit, same
release process.

- Layers: `ligature/domain` → `ligature/application` → `ligature/infrastructure` + `ligature/presentation`; wired in `ligature/bootstrap.py`. `tests/test_architecture.py` enforces it; the UI never imports the domain (enums come through `application/types.py`).
- Run: `.venv/bin/ligature --demo`. Test: `.venv/bin/python -m pytest -q`. Headless UI checks: `QT_QPA_PLATFORM=offscreen`.
- All edits go through `application/editor.Editor` (immutable `Diagram` snapshots → undo/redo; edits to one item merge into one undo step until `end_group()`).
- The canvas (`presentation/canvas.py`) is rebuilt from the `DiagramRecord` after every change; fonts are pixel-sized so exports measure the same as the screen.
- The properties panel sends edits as you type; `set_attributes`/`load` must never emit edits (a UI test selects every item and checks nothing changed).
- Exported PNG/SVG carry the diagram (`infrastructure/files.py`); Quire's "Edit in Ligature" relies on `ligature <file.png>` opening it and Save writing the PNG back in place. Keep that working.
- Generalisations: `domain.Generalisation` (+ `Mapping`); `relational.without_generalisations` rewrites them into plain ER (weak children with an `isa:` identifying relationship, merge into parent, or merge into children) before the table rules run.
- Self-update: ported from Quire (`application/updates.py`, `infrastructure/updates.py`, `presentation/updates_ui.py`); asset names must stay `ligature_<v>_<arch>.deb` and `Ligature-<v>-windows-x64-setup.exe`. Small settings live in `infrastructure/settings.JsonSettings` (~/.config/Ligature/settings.json). Tests use `tests/fakes.py`, never GitHub.
- UI text: wrap in `_()`/`N_()`, add Russian to `presentation/locales/ru.py` (`tests/test_i18n.py`).
- Releases: bump `__version__`, add a CHANGELOG section and a metainfo `<release>`, tag `vX.Y.Z`; CI publishes the .deb and setup .exe.
