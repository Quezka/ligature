# Ligature

ER and UML class diagrams for school, with the SQL they make. Free software (GPL-3.0-or-later)
for Linux and Windows.

- **ER diagrams** in Chen or crow's foot notation, switchable at any time.
- **SQL** from your ER diagram: the logical schema and `CREATE TABLE` statements for MySQL,
  PostgreSQL, SQLite or standard SQL.
- **UML class diagrams** with visibility, static and abstract members, interfaces,
  inheritance, aggregation and composition.
- **Editable pictures**: exported PNG and SVG files carry the diagram inside them. Paste one
  into your notes (e.g. in [Quire](https://github.com/Quezka/quire)) and open it in Ligature
  again to change it.

## Install

Download the latest release from the [releases page](https://github.com/Quezka/ligature/releases):
the `.deb` for Debian/Ubuntu (`sudo apt install ./ligature_*_amd64.deb`), or the setup `.exe`
for Windows.

## Run from source

```sh
python3 -m venv .venv && .venv/bin/pip install -e . pytest
.venv/bin/ligature --demo      # opens a sample ER diagram
.venv/bin/python -m pytest -q  # tests (QT_QPA_PLATFORM=offscreen without a display)
```

## Architecture

Clean Architecture, enforced by `tests/test_architecture.py`:

- `ligature/domain`: the diagram model and the ER → tables → SQL rules. No Qt, no I/O.
- `ligature/application`: the editor use case (every edit, undo/redo, saving), ports, and the
  read-only records and inputs the UI exchanges with it.
- `ligature/infrastructure`: the file format (JSON, and pictures with the diagram inside).
- `ligature/presentation`: the Qt interface. Wired together in `ligature/bootstrap.py`.

### File format

A `.ligature` file is JSON (`"format": "ligature", "version": 1`). PNG exports store the same
JSON compressed in a `zTXt` chunk with the keyword `ligature`; SVG exports store it base64
encoded in `<metadata id="ligature-diagram">`.
