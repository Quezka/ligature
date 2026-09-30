# Changelog

All notable changes to Ligature. Versions follow [Semantic Versioning](https://semver.org):
patch for fixes, minor for new features, major for breaking changes (while below 1.0,
breaking changes bump the minor version).

## [0.1.0] - 2026-09-30

### Added
- **ER diagrams** in Chen notation (entities, relationship diamonds, attribute lollipops
  with the key filled in, (min,max) cardinalities) or crow's foot (entity tables, lines
  with crow's-foot ends). Switch notation at any time; the diagram stays the same.
  Weak entities, recursive relationships with roles, relationships between three or more
  entities, attributes on relationships.
- **SQL**: the logical schema (keys underlined, foreign keys marked) and CREATE TABLE
  statements for MySQL, PostgreSQL, SQLite or standard SQL, following the school rules:
  one-to-many puts the foreign key on the single side, many-to-many gets its own table,
  weak entities borrow their owner's key. Warnings say what's missing (e.g. no key).
- **UML class diagrams**: classes, abstract classes, interfaces and enumerations;
  attributes and operations typed one per line with visibility (+ - # ~), static
  (underlined) and abstract (italics); association, directed association, aggregation,
  composition, inheritance, realisation and dependency, with multiplicities and a label.
- Drawing: double-click to add, pick two items to join them, drag to move (snaps to a
  grid), rubber-band selection, duplicate, delete, undo and redo, pan and zoom.
- Files: `.ligature` files; PNG and SVG pictures that keep the diagram inside them, so
  they open in Ligature again for editing; PDF export; copy as a picture for your notes.
- Samples to start from, recent files, light and dark themes, English and Russian.
