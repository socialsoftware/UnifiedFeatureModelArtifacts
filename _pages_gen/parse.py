"""Readers for the artifact file formats, returning plain Python data.

Each function here takes a path and gives back dicts, lists or a small tree --
nothing in this module knows about HTML, URLs or the site layout.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from .paths import ARTIFACTS, BuildError
from .util import read


def parse_profile(path: Path) -> Dict[str, str]:
    """Parse a FeatureIDE ``.profile`` into ``{feature: Colour}``.

    Line 1 is the "is default profile" flag; the trailing
    ``featureColorMeaning*`` entries are the legend, not features.
    """
    colours: Dict[str, str] = {}
    for line in read(path).splitlines()[1:]:
        line = line.strip()
        if not line or "=" not in line:
            continue
        name, _, value = line.partition("=")
        if name.startswith("featureColorMeaning"):
            continue
        colours[name.strip()] = value.strip()
    if not colours:
        raise BuildError(f"no feature colours in {path.name}")
    return colours


class Node:
    """One node of the feature-model tree.

    ``kind``, ``mandatory``, ``abstract`` and ``depth`` are not read by any
    current page -- only ``name``, ``children`` and ``walk()`` are. They are
    kept because they are a faithful record of what the FeatureIDE XML says,
    and ``__slots__`` makes carrying them almost free.
    """

    __slots__ = ("name", "kind", "mandatory", "abstract", "depth", "children")

    def __init__(self, name: str, kind: str, mandatory: bool,
                 abstract: bool, depth: int) -> None:
        self.name = name
        self.kind = kind              # and | or | alt | feature
        self.mandatory = mandatory
        self.abstract = abstract
        self.depth = depth
        self.children: List["Node"] = []

    def walk(self) -> Iterable["Node"]:
        yield self
        for child in self.children:
            yield from child.walk()


def parse_feature_model(path: Path) -> Tuple[Node, List[str]]:
    """Parse FeatureIDE XML into a tree plus readable constraint strings."""
    root_el = ET.fromstring(read(path))

    struct = root_el.find("struct")
    if struct is None or len(struct) == 0:
        raise BuildError(f"no <struct> in {path.name}")

    def build(el: ET.Element, depth: int) -> Node:
        node = Node(
            name=el.get("name", "?"),
            kind=el.tag,
            mandatory=el.get("mandatory") == "true",
            abstract=el.get("abstract") == "true",
            depth=depth,
        )
        for child in el:
            if child.tag in ("and", "or", "alt", "feature"):
                node.children.append(build(child, depth + 1))
        return node

    tree = build(struct[0], 0)

    def render(el: ET.Element) -> str:
        tag = el.tag
        if tag == "var":
            return (el.text or "").strip()
        parts = [render(c) for c in el]
        if tag == "imp":
            return f"{parts[0]} &rarr; {parts[1]}"
        if tag == "disj":
            return "(" + " &or; ".join(parts) + ")"
        if tag == "conj":
            return "(" + " &and; ".join(parts) + ")"
        if tag == "not":
            return f"&not;{parts[0]}"
        if tag == "eq":
            return f"{parts[0]} &harr; {parts[1]}"
        return " ".join(parts)

    constraints: List[str] = []
    for rule in root_el.findall("./constraints/rule"):
        for child in rule:
            if child.tag != "graphics":
                constraints.append(render(child))
                break

    return tree, constraints


def parse_skills() -> List[Dict[str, str]]:
    """Read name/description from each SKILL.md frontmatter."""
    skills_dir = ARTIFACTS / ".claude" / "skills"
    if not skills_dir.is_dir():
        raise BuildError("missing artifacts/.claude/skills/")

    out: List[Dict[str, str]] = []
    for sub in sorted(skills_dir.iterdir()):
        skill_md = sub / "SKILL.md"
        if not skill_md.is_file():
            continue
        text = read(skill_md)
        match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        if not match:
            raise BuildError(f"no frontmatter in {skill_md}")
        front = match.group(1)

        def field(key: str) -> str:
            m = re.search(rf"^{key}:\s*(.+?)\s*$", front, re.M)
            return m.group(1).strip() if m else ""

        out.append({
            "name": field("name") or sub.name,
            "description": field("description"),
            "tools": field("allowed-tools"),
            "dir": sub.name,
        })
    if not out:
        raise BuildError("no skills found")
    return out


def parse_paper_inventory(key: str) -> Dict[str, Dict[str, str]]:
    """Read the tool table out of ``evaluation/papers/<key>.md``.

    That directory is excluded from the built site because every link in it
    points at a third-party PDF, so the venue and availability columns are
    lifted here and re-rendered instead.
    """
    path = ARTIFACTS / "evaluation" / "papers" / f"{key}.md"
    if not path.is_file():
        return {}

    out: Dict[str, Dict[str, str]] = {}
    for line in read(path).splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4 or cells[0].lower() in ("tool", ""):
            continue
        if set(cells[0]) <= set("-: "):      # the header underline
            continue
        # Availability is a markdown link or plain text; keep any link, since
        # it points at the tool's own repository rather than into papers/.
        availability = re.sub(
            r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', cells[3])
        out[cells[0].lower()] = {"venue": cells[2], "availability": availability}
    return out
