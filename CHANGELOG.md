# Changelog

All notable changes to Ligature. Versions follow [Semantic Versioning](https://semver.org):
patch for fixes, minor for new features, major for breaking changes (while below 1.0,
breaking changes bump the minor version).

## [0.17.0] - 2026-11-09

The suite's new shared look (one design system for every app, `suite-rs/design/tokens.json`):

- **Neutral greys** instead of blue-tinted backgrounds, sidebars and borders; indigo stays as the one accent colour.
- **Bigger, clearer text** on one type scale shared with the phone apps: body text 16 px, nothing smaller than 13 px;
  titles and buttons follow the same sizes everywhere (the Interface size setting still scales it all).
- The same corner radii and spacing in every app.

## [0.16.0] - 2026-11-09

Real transparency and corners that line up (suite-kit 0.10).

- **See-through windows**: where the desktop can blur what's behind a window, the main window and dialogs let it show
  through, like Windows Aero or macOS sidebars; cards stay solid. On Windows it's the system's Acrylic. On GNOME it
  needs the Blur my Shell extension (the app adds itself to its list). Switch it in Settings, Look.
- **Corners line up**: the sidebar, cards and the Settings list share one radius and one gap, and what's inside them is
  rounded to match, so the curves run side by side. The Settings header floats over the cards, as wide as them.
- The glass look's description in Settings says what it really does now.

## [0.15.0] - 2026-11-08

### Changed
- **Liquid glass done properly, the Apple way.** Backgrounds are plain again and content stays solid; the chrome is glass. Menus, drop-down lists and tooltips blur what's really under them, settings headers float over their cards and blur them as they scroll, and the sidebar floats as an inset panel. On Windows 11 the window shows the system's Mica behind the sidebar. The colour wash is gone.

## [0.14.0] - 2026-11-08

### Changed
- **A glass look on top of Material 3, with brighter colours:** frosted, see-through surfaces over a soft wash of colour. Settings turns it off; High contrast stays solid.
- **Settings is redone in the suite's new window:** sections on the left, cards of rows with switches, nothing cut off on a small screen. Every other window gets its title on top and a filled Save button.

## [0.13.0] - 2026-11-04

### Changed
- The icons are Material Symbols now: outlined, and filled for what is selected.

## [0.12.0] - 2026-11-04

### Changed
- A new look: Material 3 shapes and tonal colours, and the Manrope typeface. A flick on a trackpad now keeps gliding; a mouse wheel works as before.

## [0.11.1] - 2026-11-04

Fixed: changing the interface size and pressing Restart now works, and a button's menu opens exactly under the button (kit 0.5.3).

## [0.11.0] - 2026-11-03

### Added
- **Swap cardinalities.** A button in a relationship's properties puts each side's (min,max) on the other side, for
  when they were entered the wrong way round (each entity keeps its role). One undo step.

### Fixed
- **Half a screen works.** The window can now be as narrow as half a laptop screen (683 px): the sidebar shows only
  icons, and the properties panel floats over the right side of the canvas instead of being pushed out of the window.
  It starts closed there; double-click an item or use the panel button to open it.
- The Align button is always clickable and its menu says what to select (two or more items, three to space them
  evenly); before, it was greyed out without saying why.
- The Align and Export buttons show the hand cursor like the other buttons.

## [0.10.4] - 2026-10-27

Fixed: the compact text size now reaches labels, buttons, menus and lists too (the desktop theme was keeping them at the system's larger size), so the whole interface really is smaller.

## [0.10.3] - 2026-10-27

The interface is compact: smaller text (never above 9 pt), tighter spacing and smaller icons and panels, instead of the zoom the size setting used to apply. "Automatic" size is 100% again.

## [0.10.2] - 2026-10-26

The interface size set to Automatic is a compact 85% now (the shared toolkit's new standard; 80% and 90% are new choices). Larger sizes stay in Settings.

## [0.10.1] - 2026-10-26

- The interface size set to Automatic is the system's own size again (100%); the shared toolkit had made it 115%, which was too big. Larger sizes stay one choice away in Settings.

## [0.10.0] - 2026-10-26

- The look now comes from the suite's shared toolkit: darker text and firmer borders, larger captions, and a High contrast option in Settings.

## [0.9.1] - 2026-10-26

- The window can be made much narrower: when the room is short, the tool buttons show only their icons (the tooltips
  still name them) instead of holding the window at 1600 px wide.

## [0.9.0] - 2026-10-26

### Added
- **Align a group.** Select two or more items and use the new Align button: left edges, centres, right edges, tops,
  middles and bottoms, or spread three or more evenly across or down. Boxes of different sizes line up by their edges,
  and the whole thing is one undo step.
- **Notes for the database.** A Notes box on the diagram (DBMS, naming rules, business rules, assumptions), on every
  entity, relationship and class (expected volume, constraints, formats, defaults). They are saved in the file and
  written at the top of the generated SQL as comments, so they travel with the tables.

## [0.8.0] - 2026-10-13

- Alignment guides also snap a box's edges (left/right, top/bottom) to the edges and centres of the other boxes.
- The properties panel can be closed (x) and reopened (button in the toolbar, or by double-clicking an item).
- Enter in an attribute's name or type goes straight to the next attribute's name, adding one after the last (the new field could miss the focus before).

## [0.7.0] - 2026-10-05

- Alignment guides now also snap to the 45° diagonals through other boxes.

## [0.6.0] - 2026-10-05

- Alignment guides: dragging a box snaps its centre to the horizontal or vertical centre line of other boxes, with a dashed line showing the match.

## [0.5.0] - 2026-10-05

- Italian translation of the whole interface (Language in Settings; Italian systems start in Italian).

## [0.4.0] - 2026-10-02

- Pressing Enter in a one-line box now finishes with it: the cursor stops blinking and the box lets go of the focus.

## [0.3.1] - 2026-10-02

- Fixed: opening the app put a second icon on the dock instead of using the pinned one (the screen-size check forgot the app's desktop name).

## [0.3.0] - 2026-10-02
- Interface size in Settings (Automatic, 80%–130%). Automatic makes everything a little smaller on small screens such as 1366x768. Applies after a restart.
- The window never opens bigger than the screen, and Settings scrolls when it is taller than the screen.

## [0.2.2] - 2026-10-01

- Cardinality labels such as (1,N) no longer overlap the entities: they sit beside their line, clear of the entity, the relationship and the line.

## [0.2.1] - 2026-09-30

### Fixed
- Before a diagram is open, the Diagram and SQL pages in the sidebar are clearly greyed
  out (text and icon), and hovering them says to start or open a diagram first.

## [0.2.0] - 2026-09-30

### Added
- **Generalisations (ISA)** in ER diagrams: pick Generalisation in the toolbar (G), click
  the child, then the parent; more children join the same generalisation. Total or
  partial, exclusive or overlapping, drawn with a filled or hollow arrow and its (t,e)
  label, in both notations.
- **Generalisations become tables** the way you choose, as taught at school: a table for
  each entity (the children use the parent's key), everything merged into the parent (with
  a `tipo` column, or one yes/no column per child when they overlap), or merged into the
  children (only when that's possible; otherwise Ligature says why).
- **Copy, cut and paste** (Ctrl+C, Ctrl+X, Ctrl+V): items keep what joins them, and can be
  pasted into another diagram of the same kind. Pasting a Ligature picture (e.g. copied
  from a note) brings in its diagram.
- **Arrow keys** move the selection (Shift for bigger steps).
- An amber **!** on entities that have no key yet, so it's fixed before the SQL.
- **Updates from inside Ligature**: it checks once a day (you can turn it off in Settings)
  and installs new versions for you.
- A third sample: a university, with a generalisation.

### Fixed
- The chosen option in small switches (like the notation) no longer gets cut off.

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
