"""The five Evaluation pages.

They are kept in one module because they share their shape: the two-level
``sub_nav`` strip, the lookup from a tool to the paper it came from, and the
"Proposed model extension" section that both the per-tool and the union pages
render. Splitting them across files would hide that.
"""

from __future__ import annotations

import html
from typing import Dict, List, Tuple

from ..artifacts import Artifacts
from ..config import (EXCLUDED_TOOLS, MERGED, PAPERS, TOOLS, TOOL_LABEL,
                      TOOL_META)
from ..parse import parse_paper_inventory
from ..render import (collect_images, colour_legend, downloads_block, figure,
                      mapping_figures, profile_downloads, sub_nav, table,
                      tool_images, write_page)


def render_evaluation_index(assets: Artifacts) -> None:
    """Tab 5 landing page: what the evaluation is, and how to read it."""
    body = [
        "# Evaluation\n",
        "Each tool below was mapped onto the feature model, and every mapping "
        "here is the output of the "
        f'<a href="{{{{BASE}}}}/skills/">mapping skills</a> — not a hand-made '
        "assessment. The tools are grouped by the paper they were drawn from.\n",

        "\n## What each tool page shows\n",
        "<dl class=\"provenance\">"
        "<dt>Automated mapping</dt>"
        "<dd>What <code>codebase-map</code> or <code>docs-map</code> produced "
        "from the tool's own code or documentation, unedited.</dd>"
        "<dt>Revised mapping</dt>"
        "<dd>The same mapping after the authors re-checked the cited evidence "
        "and corrected it. Both are published so the corrections are visible.</dd>"
        "<dt>Proposed model extension</dt>"
        "<dd>Where a tool had a feature the model lacked, that feature was added "
        "to a copy of the model. These are the authors' proposals, <b>not</b> "
        "skill output, and only three tools produced one.</dd>"
        "</dl>\n",

        "\n## Colour legend\n",
        colour_legend(),

        "\n## Tools\n",
    ]

    rows = []
    for paper in PAPERS:
        for tool in TOOLS:
            if TOOL_META[tool]["source"] != paper["key"]:
                continue
            href = ("{{BASE}}/evaluation/" + paper["slug"] + "/"
                    + tool.lower() + "/")
            rows.append((
                f'<a href="{href}"><b>{html.escape(TOOL_LABEL[tool])}</b></a>',
                html.escape(paper["label"]),
                f'<code>{TOOL_META[tool]["skill"]}</code>',
            ))
    body.append(table(["Tool", "Source paper", "Mapped with"], rows))

    if EXCLUDED_TOOLS:
        body.append("\n## Tools that could not be mapped\n")
        body.append(
            "These appear in the source papers but have no public codebase or "
            "documentation to map against.\n")
        body.append(table(
            ["Tool", "Source paper", "Reason"],
            [(html.escape(n), html.escape(s), html.escape(r))
             for n, s, r in EXCLUDED_TOOLS]))

    write_page("evaluation/index.md",
               {"layout": "default", "title": "Evaluation",
                "nav_title": "Evaluation", "nav_order": 6,
                "permalink": "/evaluation/"},
               sub_nav() + "\n".join(body))


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

    write_page(f"evaluation/{paper['slug']}/{tool.lower()}.md",
               {"layout": "default", "title": label,
                "permalink": f"/evaluation/{paper['slug']}/{tool.lower()}/"},
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
