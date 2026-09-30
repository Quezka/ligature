"""Entry script for frozen builds (PyInstaller needs a file, not a module)."""
from ligature.app import main

raise SystemExit(main())
