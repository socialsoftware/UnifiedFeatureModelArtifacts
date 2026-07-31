#!/usr/bin/env python3
"""Generate the GitHub Pages appendix from the artifacts/ directory.

Run from the repository root:

    python3 generate.py

Reads everything under ``artifacts/`` and writes the derived pages into
``pages/``. Jekyll then only applies the layout and navigation.

Nothing is copied. The Pages source is the repository root, so ``artifacts/``
is inside the Jekyll source tree and is published in place; the build only
resolves artifact paths to URLs (see ``_pages_gen.artifacts.Artifacts``).

The source files under ``artifacts/`` are never modified, and none of them is
inlined into a page: every page shows the images and links the files, so the
artifacts stay the single source of truth and the pages stay short.

This file is only the entry point -- the build itself lives in the
``_pages_gen`` package beside it, laid out bottom-up from ``paths`` to ``cli``
(see its module docstring). Standard library only, so it runs anywhere
Python 3.8+ is available.
"""

import sys

from _pages_gen.cli import main

if __name__ == "__main__":
    sys.exit(main())
