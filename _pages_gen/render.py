"""Stateless HTML and Markdown fragment builders, plus the page writer.

Everything here returns a string and touches no global state. The only
site-wide knowledge is the ``{{BASE}}`` placeholder convention: URLs are
emitted with that prefix and rewritten into a Liquid ``relative_url`` call by
``postprocess.apply_baseurl`` as the very last step of a build.

``Artifacts`` arrives as a parameter and is only read, so this module sits
above ``artifacts`` in the import graph and is never imported by it.
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .artifacts import Artifacts
from .config import (BANNER, COLOURS, COLOUR_MEANING, COLOUR_SHORT,
                     IMAGE_PREFIX, PAPERS, TOOLS, TOOL_LABEL, TOOL_META)
from .paths import PAGES
from .util import png_size


def chip(colour: Optional[str]) -> str:
    if not colour:
        return '<span class="chip chip-none">not in model</span>'
    cls = colour.lower()
    return f'<span class="chip chip-{cls}">{html.escape(COLOUR_SHORT.get(colour, colour))}</span>'


def write_page(rel: str, front: Dict[str, object], body: str) -> Path:
    """Write a generated page with YAML frontmatter."""
    dest = PAGES / rel
    dest.parent.mkdir(parents=True, exist_ok=True)

    lines = ["---"]
    for key, value in front.items():
        if value is None:
            continue
        if isinstance(value, (int, float)):
            lines.append(f"{key}: {value}")
        else:
            lines.append(f'{key}: "{str(value)}"')
    lines.append("---")
    lines.append(BANNER)
    lines.append("")

    dest.write_text("\n".join(lines) + body.rstrip() + "\n", encoding="utf-8")
    return dest


def table(headers: Sequence[str], rows: Iterable[Sequence[str]],
          extra_class: str = "") -> str:
    """Render an HTML table inside a horizontal-scroll wrapper."""
    cls = f' class="{extra_class}"' if extra_class else ""
    # The class goes on the <table>, not on the scroll wrapper: the CSS targets
    # `.downloads td`, which matches either way.
    parts = ['<div class="table-scroll">', f"<table{cls}>", "<thead><tr>"]
    parts += [f"<th>{h}</th>" for h in headers]
    parts += ["</tr></thead>", "<tbody>"]
    for row in rows:
        parts.append("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>")
    parts += ["</tbody>", "</table>", "</div>"]
    return "\n".join(parts)


def figure(caption: str, shots: Sequence[Dict[str, str]]) -> str:
    """A lightbox figure. Each shot: {file, label, meta, alt}."""
    if not shots:
        return ""
    out = ['<figure class="fm-image">',
           f"<figcaption>{caption}</figcaption>",
           '<div class="fm-shots">']
    for shot in shots:
        out.append(
            '<button type="button" class="fm-shot"'
            f' data-full="{shot["file"]}"'
            f' data-title="{html.escape(shot["label"], quote=True)}"'
            f' data-alt="{html.escape(shot.get("alt", shot["label"]), quote=True)}">'
            f'<img src="{shot["file"]}" alt="{html.escape(shot.get("alt", shot["label"]))}" loading="lazy">'
            '<span class="fm-shot-label">'
            f'<b>{html.escape(shot["label"])}</b>'
            # meta carries an entity (the &times; between the pixel dimensions),
            # so it is already HTML and must not be escaped again.
            f'<span>{shot.get("meta", "")} · click to zoom</span>'
            "</span></button>"
        )
    out += ["</div>", "</figure>"]
    return "\n".join(out)


def colour_legend() -> str:
    items = ['<ul class="legend">']
    for colour in COLOURS:
        items.append(f"<li>{chip(colour)}<span>{html.escape(COLOUR_MEANING[colour])}</span></li>")
    items.append("</ul>")
    return "\n".join(items)


def downloads_block(assets: Artifacts, entries: Sequence[Tuple[str, str]],
                    heading: str = "## Downloads") -> str:
    """A downloads table: (asset-rel-path, description).

    ``heading`` is overridable because a page can carry more than one table --
    a tool page with a proposed model extension keeps that download under its
    own section rather than repeating "Downloads". Pass an empty string to omit
    the heading entirely.
    """
    rows = []
    for rel, description in entries:
        name = rel.rsplit("/", 1)[-1]
        rows.append((
            f'<a href="{assets.url(rel)}" download><code>{html.escape(name)}</code></a>',
            html.escape(description),
            assets.size(rel),
        ))
    prefix = f"\n{heading}\n\n" if heading else "\n"
    return (prefix
            + table(["File", "What it is", "Size"], rows, extra_class="downloads")
            + "\n")


def tool_images(tool: str, assets: Artifacts) -> Dict[str, Dict[str, str]]:
    """The mapping images for one tool, keyed by family.

    Four families exist in exportedImages/, with different provenance, and the
    pages label them as such rather than presenting them as one set:

    ``claude``    the mapping a mapping skill produced, unedited;
    ``revised``   the same mapping after the authors checked the evidence;
    ``extended``  the model with this tool's missing features added -- a manual
                  proposal, not skill output, so pages show it separately;
    ``manual``    a hand-made reference mapping. Only mono2micro has one.
    """
    prefix = IMAGE_PREFIX[tool]
    wanted = [
        ("claude", f"{prefix}_claudeMapping.png", "Automated mapping"),
        ("revised", f"{prefix}_revisedMapping.png", "Revised mapping"),
        ("extended", f"{prefix}_extendedMapping.png", "Extended model"),
        ("manual", f"{prefix}_manualMapping.png", "Manual mapping"),
    ]
    return collect_images(assets, wanted, TOOL_LABEL[tool])


def collect_images(assets: Artifacts,
                   wanted: Sequence[Tuple[str, str, str]],
                   subject: str) -> Dict[str, Dict[str, str]]:
    """Resolve (family, filename, label) triples to lightbox shot dicts.

    Absent files are skipped, not an error: only three tools have an extended
    model and only one has a manual mapping.
    """
    shots: Dict[str, Dict[str, str]] = {}
    for family, filename, label in wanted:
        rel = f"images/{filename}"
        if rel not in assets:
            continue
        width, height = png_size(assets.path(rel))
        shots[family] = {
            "file": assets.url(rel),
            "label": label,
            "meta": f"{width}&times;{height}",
            "alt": f"{subject} {label.lower()} over the feature model",
            "rel": rel,
        }
    return shots


def sub_nav(active_paper: str = "", active_tool: str = "") -> str:
    """The two-level Evaluation navigation strip.

    Rendered as static HTML on every Evaluation page so each tool keeps its own
    URL and stays deep-linkable -- an artifact appendix gets cited by URL, so
    client-side tabs would make the interesting pages unaddressable.

    The second row appears only for the active paper, keeping the strip to a
    readable width.
    """
    rows: List[str] = ['<nav class="sub-nav" aria-label="Evaluation">']

    top: List[str] = ['<ul class="sub-nav-papers">']
    top.append(_sub_nav_item("All tools", "{{BASE}}/evaluation/all-tools/",
                             active_tool == "all-tools"))
    for paper in PAPERS:
        top.append(_sub_nav_item(
            paper["label"], "{{BASE}}/evaluation/" + paper["slug"] + "/",
            paper["key"] == active_paper))
    top.append("</ul>")
    rows.append("".join(top))

    if active_paper:
        paper = next(p for p in PAPERS if p["key"] == active_paper)
        siblings: List[str] = ['<ul class="sub-nav-tools">']
        if paper["union"]:
            siblings.append(_sub_nav_item(
                f"All {paper['label']} tools",
                "{{BASE}}/evaluation/" + paper["slug"] + "/all/",
                active_tool == paper["union"]))
        for tool in TOOLS:
            if TOOL_META[tool]["source"] != active_paper:
                continue
            siblings.append(_sub_nav_item(
                TOOL_LABEL[tool],
                "{{BASE}}/evaluation/" + paper["slug"] + "/" + tool.lower() + "/",
                tool == active_tool))
        siblings.append("</ul>")
        rows.append("".join(siblings))

    rows.append("</nav>")
    return "\n".join(rows) + "\n"


def _sub_nav_item(label: str, href: str, current: bool) -> str:
    mark = ' aria-current="page"' if current else ""
    return f'<li><a href="{href}"{mark}>{html.escape(label)}</a></li>'


def profile_downloads(assets: Artifacts, stem: str,
                      review_stem: str = "") -> List[Tuple[str, str]]:
    """Download entries for a profile pair, skipping whichever is absent.

    ``review_stem`` exists because one merged profile breaks the convention:
    the reviewed twin of ``mono2micro+Micro2Micro`` is filed under
    ``mono2micro_user_review+Micro2Micro_user_review``, not under the plain
    ``_user_review`` suffix every other pair uses.
    """
    entries: List[Tuple[str, str]] = []
    auto = f"profiles/{stem}.profile"
    if auto in assets:
        entries.append((auto, "Colour profile — automated mapping"))
    review = f"profiles/{review_stem or stem + '_user_review'}.profile"
    if review in assets:
        entries.append((review, "Colour profile — after the authors' review"))
    return entries


def mapping_figures(shots: Dict[str, Dict[str, str]], subject: str) -> List[str]:
    """The claude/revised pair plus any manual mapping, with provenance stated."""
    parts: List[str] = []
    pair = [shots[k] for k in ("claude", "revised") if k in shots]
    if pair:
        parts.append(figure(
            f"{subject} mapped onto the feature model. The automated mapping is "
            "the skill's own output; the revised one is the authors' correction "
            "of it after re-checking the cited evidence. Click to open full "
            "screen (drag to pan, scroll to zoom).",
            pair))
    if "manual" in shots:
        parts.append("\n### Manual reference mapping\n")
        parts.append(
            '<div class="note"><p>A mapping done by hand, before the skills '
            'existed. It is kept as a baseline for comparison and is not skill '
            'output.</p></div>\n')
        parts.append(figure("Hand-made reference mapping.", [shots["manual"]]))
    return parts
