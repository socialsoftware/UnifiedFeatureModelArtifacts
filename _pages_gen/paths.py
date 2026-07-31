"""Where things live, and the one exception the build raises."""

from __future__ import annotations

from pathlib import Path

#: The repository root. This module sits one level down, inside the package,
#: so the root is the *grandparent* of this file rather than its parent.
REPO = Path(__file__).resolve().parent.parent
ARTIFACTS = REPO / "artifacts"
PAGES = REPO / "pages"

#: Where the generated zip downloads are written. Deliberately *outside*
#: ``artifacts/``: that tree holds only the original research artifacts, whereas
#: every file here is derived and rebuilt from it by generate.py. Keeping the
#: two apart also means the bundler never has to skip its own output when
#: collecting members.
BUNDLES = REPO / "bundles"


class BuildError(RuntimeError):
    """A required input is missing or malformed."""
