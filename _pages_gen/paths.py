"""Where things live, and the one exception the build raises."""

from __future__ import annotations

from pathlib import Path

#: The repository root. This module sits one level down, inside the package,
#: so the root is the *grandparent* of this file rather than its parent.
REPO = Path(__file__).resolve().parent.parent
ARTIFACTS = REPO / "artifacts"
PAGES = REPO / "pages"


class BuildError(RuntimeError):
    """A required input is missing or malformed."""
