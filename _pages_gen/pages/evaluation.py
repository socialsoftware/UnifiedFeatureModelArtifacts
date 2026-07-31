"""The Evaluation pages.

They are kept in one module because they share their shape: the two-level
``sub_nav`` strip, the lookup from a tool to the paper it came from, and the
"Proposed model extension" section that both the per-tool and the union pages
render. Splitting them across files would hide that.

There is no ``/evaluation/`` landing page: it only restated what ``sub_nav``
already links, so the section's top-nav entry lives on the Mono2Micro tool page
instead (see ``NAV_TOOL`` below).
"""

from __future__ import annotations

import html
from typing import Dict, List, Tuple

from ..artifacts import Artifacts
from ..config import (EXCLUDED_TOOLS, MERGED, PAPERS, TOOLS, TOOL_LABEL,
                      TOOL_META)
from ..parse import parse_paper_inventory
from ..render import (collect_images, downloads_block, figure, mapping_figures,
                      profile_downloads, sub_nav, table, tool_images,
                      write_page)

#: The tool page that carries the section's top-nav entry, since there is no
#: ``/evaluation/`` index to carry it. Mono2Micro is the tool the initial model
#: was derived from, so it is the section's natural front door.
NAV_TOOL = "mono2micro"
NAV_ORDER = 6


def render_paper_page(paper: Dict[str, str], assets: Artifacts) -> None:
    """One page per source paper: which tools it contributed."""
    key, slug = paper["key"], paper["slug"]
    tools = [t for t in TOOLS if TOOL_META[t]["source"] == key]

    inventory = parse_paper_inventory(key)

    body = [
        f"# {html.escape(paper['label'])}\n",
        f"<p class=\"meta-line\">{html.escape(paper['venue'])}</p>\n",
        f"The tools this paper contributed to the evaluation. "
        + (f"All <b>{len(tools)}</b> of them were mapped."
           if len(tools) > 1 else
           "It contributes a single tool.") + "\n",
    ]

    rows = []
    for tool in tools:
        href = "{{BASE}}/evaluation/" + slug + "/" + tool.lower() + "/"
        entry = inventory.get(tool.lower(), {})
        rows.append((
            f'<a href="{href}"><b>{html.escape(TOOL_LABEL[tool])}</b></a>',
            html.escape(entry.get("venue", "—")),
            entry.get("availability", "—"),
            f'<code>{TOOL_META[tool]["skill"]}</code>',
        ))
    # Tools this paper lists that were not mappable.
    for name, source, reason in EXCLUDED_TOOLS:
        if source != key:
            continue
        rows.append((html.escape(name),
                     html.escape(inventory.get(name.lower(), {}).get("venue", "—")),
                     "—",
                     f"<i>not mapped — {html.escape(reason.lower())}</i>"))
    body.append(table(["Tool", "Venue", "Availability", "Mapped with"], rows))

    if paper["union"]:
        body.append(
            f"\nA merged profile combining all {len(tools)} of them is on the "
            f'<a href="{{{{BASE}}}}/evaluation/{slug}/all/">'
            f"All {html.escape(paper['label'])} tools</a> page.\n")

    write_page(f"evaluation/{slug}/index.md",
               {"layout": "default", "title": paper["label"],
                "permalink": f"/evaluation/{slug}/"},
               sub_nav(active_paper=key) + "\n".join(body))


def render_eval_tool_page(tool: str, assets: Artifacts) -> None:
    """One page per tool: the mapping images, then the downloads."""
    key = TOOL_META[tool]["source"]
    paper = next(p for p in PAPERS if p["key"] == key)
    label = TOOL_LABEL[tool]
    shots = tool_images(tool, assets)

    body = [
        f"# {html.escape(label)}\n",
        f'<p class="meta-line">Mapped with '
        f'<code>{TOOL_META[tool]["skill"]}</code> · '
        f'from <a href="{{{{BASE}}}}/evaluation/{paper["slug"]}/">'
        f'{html.escape(paper["label"])}</a> · '
        f'<a href="{TOOL_META[tool]["repo"]}">tool repository</a></p>\n',
    ]
    body += mapping_figures(shots, label)

    entries: List[Tuple[str, str]] = []
    for rel, description in (
            (f"analyses/{tool}-analysis.md",
             "The full analysis, every finding citing its evidence"),
            (f"analyses/{tool}-readme.md",
             "How the tool was obtained and run")):
        if rel in assets:
            entries.append((rel, description))
    entries += profile_downloads(assets, tool)
    body.append(downloads_block(assets, entries))

    # The extended model is the authors' proposal, so it gets its own section
    # rather than sitting among the skill's output above.
    extended_xml = f"models/{tool}_feature_model.xml"
    if extended_xml in assets or "extended" in shots:
        body.append("\n## Proposed model extension\n")
        body.append(
            f"{html.escape(label)} exposed features the model did not have. "
            "They were added to a copy of the model, shown below. This is a "
            "proposal by the authors, not skill output.\n")
        if "extended" in shots:
            body.append(figure(
                f"The model extended with {html.escape(label)}'s features.",
                [shots["extended"]]))
        if extended_xml in assets:
            body.append(downloads_block(
                assets,
                [(extended_xml, "The extended feature model (FeatureIDE XML)")],
                heading=""))

    front: Dict[str, object] = {
        "layout": "default", "title": label,
        "permalink": f"/evaluation/{paper['slug']}/{tool.lower()}/",
    }
    # One tool page doubles as the Evaluation section's top-nav entry.
    if tool == NAV_TOOL:
        front["nav_title"] = "Evaluation"
        front["nav_order"] = NAV_ORDER

    write_page(f"evaluation/{paper['slug']}/{tool.lower()}.md", front,
               sub_nav(active_paper=key, active_tool=tool) + "\n".join(body))


def render_union_page(key: str, assets: Artifacts) -> None:
    """A merged mapping: what a set of tools covers together.

    ``all-tools`` sits at the top of the Evaluation strip; ``wang`` sits under
    its paper. The third merged profile, mono2micro+Micro2Micro, has no page of
    its own -- it is offered as a download here, since a two-tool subset is a
    detail of the paper rather than a section of the appendix.
    """
    entry = next(m for m in MERGED if m[0] == key)
    _, prefix, label = entry

    if key == "all-tools":
        slug, active_paper, covered = "evaluation/all-tools", "", TOOLS
        permalink = "/evaluation/all-tools/"
        intro = ("Every one of the seven mapped tools, merged into a single "
                 "profile: what the tools cover <i>together</i>, and — more to "
                 "the point — what none of them covers.")
    else:
        paper = next(p for p in PAPERS if p["union"] == key)
        slug = f"evaluation/{paper['slug']}/all"
        permalink = f"/evaluation/{paper['slug']}/all/"
        active_paper = paper["key"]
        covered = [t for t in TOOLS if TOOL_META[t]["source"] == paper["key"]]
        intro = (f"The {len(covered)} tools from {html.escape(paper['label'])}, "
                 "merged into a single profile.")

    shots = collect_images(assets, [
        ("claude", f"{prefix}_claudeMapping.png", "Automated mapping"),
        ("revised", f"{prefix}_revisedMapping.png", "Revised mapping"),
        ("extended", f"{prefix}_extended.png", "Extended model"),
        ("extendedMapping", f"{prefix}_extendedMapping.png", "Extended model"),
    ], label)
    # all-tools names its extended image _extended.png; every other family uses
    # _extendedMapping.png. Normalise so the page does not care.
    if "extended" not in shots and "extendedMapping" in shots:
        shots["extended"] = shots.pop("extendedMapping")
    shots.pop("extendedMapping", None)

    body = [
        f"# {html.escape(label)}\n",
        f"<p>{intro}</p>\n",
        "<p>Merged with <code>merge-profiles</code> from the individual "
        "mappings of "
        + ", ".join(
            f'<a href="{{{{BASE}}}}/evaluation/'
            f'{next(p["slug"] for p in PAPERS if p["key"] == TOOL_META[t]["source"])}'
            f'/{t.lower()}/">{html.escape(TOOL_LABEL[t])}</a>'
            for t in covered)
        + ".</p>\n",
    ]
    body += mapping_figures(shots, label)

    entries = profile_downloads(assets, key)
    body.append(downloads_block(assets, entries))

    extended_xml = f"models/{key}_feature_model.xml"
    if extended_xml in assets or "extended" in shots:
        body.append("\n## Proposed model extension\n")
        body.append(
            "The union of every feature the tools exposed that the model did "
            "not have, added to a copy of the model. A proposal by the authors, "
            "not skill output.\n")
        if "extended" in shots:
            body.append(figure("The model extended with the union of the "
                               "tools' extra features.", [shots["extended"]]))
        if extended_xml in assets:
            body.append(downloads_block(
                assets,
                [(extended_xml, "The extended feature model (FeatureIDE XML)")],
                heading=""))

    if key == "all-tools":
        subset = "mono2micro+Micro2Micro"
        rows = profile_downloads(
            assets, subset, "mono2micro_user_review+Micro2Micro_user_review")
        if rows:
            body.append("\n## Other merged mappings\n")
            body.append(
                "The paper also discusses Mono2Micro and Micro2Micro together, "
                "as the two tools that share a lineage. That pairing has its own "
                "merged profile.\n")
            body.append(downloads_block(assets, rows, heading=""))

    write_page(f"{slug}.md",
               {"layout": "default", "title": label, "permalink": permalink},
               sub_nav(active_paper=active_paper, active_tool=key)
               + "\n".join(body))
