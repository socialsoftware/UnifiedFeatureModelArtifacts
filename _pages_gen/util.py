"""Small pure helpers, with no knowledge of artifacts or configuration."""

from __future__ import annotations

import struct
from pathlib import Path
from typing import Tuple

from .paths import BuildError, REPO


def read(path: Path) -> str:
    if not path.is_file():
        raise BuildError(f"missing required file: {path.relative_to(REPO)}")
    return path.read_text(encoding="utf-8")


def human_size(nbytes: int) -> str:
    if nbytes < 1024:
        return f"{nbytes} B"
    if nbytes < 1024 * 1024:
        return f"{nbytes / 1024:.0f} KB"
    return f"{nbytes / (1024 * 1024):.1f} MB"


def png_size(path: Path) -> Tuple[int, int]:
    """Read width/height straight from the PNG IHDR chunk."""
    with path.open("rb") as fh:
        head = fh.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise BuildError(f"not a PNG: {path}")
    return struct.unpack(">II", head[16:24])
