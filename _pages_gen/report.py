"""The colour-count cross-check printed at the end of every build.

The site no longer renders a coverage page, but these counts are what the
paper's mapping-summary table reports, so they stay worth printing: a silent
change here means the paper and the artifacts have drifted apart.

The profiles are re-read straight from disk rather than through the artifact
registry, because this is a check on the source data, not on what the site
happens to link.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from .config import COLOURS, MERGED, TOOLS
from .parse import parse_profile
from .paths import ARTIFACTS


def colour_counts(colours: Dict[str, str]) -> Dict[str, int]:
    counts = {c: 0 for c in COLOURS}
    for value in colours.values():
        if value in counts:
            counts[value] += 1
    return counts


def tally_profiles() -> Dict[str, Dict[str, Dict[str, int]]]:
    """Per-mapping colour counts, for the cross-check main() prints.

    The site no longer renders a coverage page, but these counts are what the
    paper's mapping-summary table reports, so they stay worth printing on every
    build: a silent change here means the paper and the artifacts have drifted.
    """
    profiles_dir = ARTIFACTS / "feature_model" / ".profiles"
    out: Dict[str, Dict[str, Dict[str, int]]] = {}

    def add(name: str, auto_path: Path, review_path: Path) -> None:
        if not auto_path.is_file():
            return
        entry = {"auto": colour_counts(parse_profile(auto_path))}
        if review_path.is_file():
            entry["review"] = colour_counts(parse_profile(review_path))
        out[name] = entry

    for tool in TOOLS:
        add(tool, profiles_dir / f"{tool}.profile",
            profiles_dir / f"{tool}_user_review.profile")
    for key, _prefix, _label in MERGED:
        review = ("mono2micro_user_review+Micro2Micro_user_review"
                  if key == "mono2micro+Micro2Micro" else f"{key}_user_review")
        add(key, profiles_dir / f"{key}.profile",
            profiles_dir / f"{review}.profile")
    return out
