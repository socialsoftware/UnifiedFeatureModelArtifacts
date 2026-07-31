"""The Skills section: an Explanation tab plus one page per mapping skill.

Shaped like the Evaluation section, and for the same reason: the navigation is
static HTML (``skill_nav``) rather than client-side tabs, so every skill keeps
its own URL and stays deep-linkable in a citation.
"""

from __future__ import annotations

import html
from typing import Dict, List, Tuple

from ..artifacts import Artifacts
from ..config import (RAW_BASE, SKILL_NO_BUNDLE_NOTE, SKILL_ORDER,
                      SKILL_OUTPUT_BLURB, SKILL_REPO_LAYOUT, SKILL_SUMMARY)
from ..parse import parse_skills
from ..paths import REPO, BuildError
from ..render import downloads_block, skill_nav, write_page
from ..util import png_size

#: Where the Skills section sits in the top nav. The Explanation page carries
#: it, since it is the section's front door.
NAV_ORDER = 5


def _skills() -> Dict[str, Dict[str, str]]:
    """Every skill on disk, keyed by directory, validated against SKILL_ORDER."""
    skills = {s["dir"]: s for s in parse_skills()}
    missing = [d for d in SKILL_ORDER if d not in skills]
    if missing:
        raise BuildError(f"SKILL_ORDER names unknown skills: {missing}")
    return skills


def _summary(skill: Dict[str, str]) -> str:
    """Reader-facing prose for a skill, falling back to its frontmatter.

    The fallback is a trigger phrase aimed at the model rather than at a reader,
    so it is escaped and only used when SKILL_SUMMARY has no entry.
    """
    return SKILL_SUMMARY.get(skill["dir"]) or html.escape(skill["description"])


def render_skills(assets: Artifacts) -> int:
    """The Explanation tab: what the skills are, the pipeline, the layout."""
    skills = _skills()

    body = [
        skill_nav(),
        "# Mapping skills\n",
        '<div class="note"><p>The skills are <b>non-deterministic</b>: running '
        "one twice can produce different verdicts. That is why "
        "<code>verify-analysis</code> exists, and why every mapping in the "
        "evaluation is published in both its automated and its reviewed "
        "form.</p></div>\n",
        "\n## The pipeline\n",
    ]

    # A site illustration rather than a research artifact, so it lives in
    # assets/ and is referenced directly -- the Artifacts registry only resolves
    # paths under artifacts/.
    #
    # Plain <img> rather than the shared figure() lightbox: the diagram is small
    # and legible in place, so there is nothing to zoom into, unlike the ~17:1
    # mapping exports that figure() is built for.
    pipeline_png = REPO / "assets" / "images" / "evaluation_pipeline.png"
    if not pipeline_png.is_file():
        raise BuildError(f"missing {pipeline_png.relative_to(REPO)}")
    width, height = png_size(pipeline_png)
    body.append(
        '<figure class="fm-plain">'
        f'<img src="{{{{BASE}}}}/assets/images/evaluation_pipeline.png"'
        f' width="{width}" height="{height}"'
        ' alt="The five mapping skills and the order they run in">'
        "<figcaption>The mapping pipeline. A paper yields tools and codebases; "
        "each tool is mapped from its source or its documentation; the mappings "
        "are reconciled, then merged into a union profile.</figcaption>"
        "</figure>\n")
    body.append(
        "<p><code>refresh-feature-model-infos</code> is absent from the diagram "
        "because it sits outside the chain: it runs whenever the feature model "
        "changes, to keep the files that describe it in step.</p>\n")

    body.append("\n## Expected repository layout\n")
    body.append(
        "The skills read and write fixed paths, so they expect the tree below. "
        "It is <b>not</b> this repository's layout — the skills are archived as "
        "they were run, against an earlier working tree — so reproducing a run "
        "means rebuilding this structure around them.\n")
    body.append(f'<pre class="pipeline">{html.escape(SKILL_REPO_LAYOUT)}</pre>\n')

    body.append("\n## The skills\n")
    body.append('<ul class="cards skill-cards">')
    for name in SKILL_ORDER:
        skill = skills[name]
        page = "{{BASE}}/skills/" + name + "/"
        tools_used = html.escape(skill["tools"]) if skill["tools"] else "—"
        # A skill with no references/ ships no archive, so the card ends at
        # "read the skill" rather than offering a zip that was never built.
        bundle = f"bundles/{name}-skill.zip"
        download = (
            f' · <a href="{assets.url(bundle)}" download>download</a>'
            if bundle in assets else "")
        body.append(
            "<li>"
            f'<h3><a href="{page}"><code>{html.escape(name)}</code></a></h3>'
            f"<p>{_summary(skill)}</p>"
            f'<p class="card-files">Tools: {tools_used} · '
            f'<a href="{page}">open</a> · '
            f'<a href="{{{{BASE}}}}/artifacts/.claude/skills/{name}/SKILL.html">'
            f"read the skill</a>{download}</p>"
            "</li>")
    body.append("</ul>\n")

    write_page("skills.md",
               {"layout": "default", "title": "Skills",
                "nav_title": "Skills", "nav_order": NAV_ORDER,
                "permalink": "/skills/"},
               "\n".join(body))
    return len(skills)


def render_skill_page(name: str, assets: Artifacts) -> None:
    """One page per skill: what it does, its own files, and what it produced."""
    skill = _skills()[name]
    tools_used = html.escape(skill["tools"]) if skill["tools"] else "—"

    body = [
        skill_nav(active=name),
        f"# {html.escape(name)}\n",
        f'<p class="meta-line">Claude Code skill · '
        f"Tools: {tools_used} · "
        f'<a href="{{{{BASE}}}}/artifacts/.claude/skills/{name}/SKILL.html">'
        "read the full procedure</a></p>\n",
        f"{_summary(skill)}\n",
    ]

    # SKILL.md is rendered to SKILL.html by Jekyll (it has frontmatter), so no
    # raw .md is served from the site -- the download has to go to GitHub raw.
    entries: List[Tuple[str, str]] = []
    for key, description in (
            (f"skills/{name}/references/feature-model-dimensions.md",
             "The feature model's dimensions, as the skill consumes them"),
            (f"skills/{name}/references/analysis-template.md",
             "The blank analysis document each mapping fills in")):
        if key in assets:
            entries.append((key, description))
    # Only skills with references/ get an archive -- for the rest it would hold
    # SKILL.md alone, which the paragraph below already links directly.
    bundle = f"bundles/{name}-skill.zip"
    if bundle in assets:
        entries.append(
            (bundle, "The whole skill folder: SKILL.md and its references"))

    body.append("\n## The skill\n")
    body.append(
        f'<p><a href="{RAW_BASE}/artifacts/.claude/skills/{name}/SKILL.md" '
        f"download><code>SKILL.md</code></a> — the procedure itself, as "
        "Markdown.</p>\n")
    if entries:
        body.append(downloads_block(assets, entries, heading=""))

    blurb = SKILL_OUTPUT_BLURB.get(name)
    if blurb:
        body.append("\n## What it produced\n")
        body.append(f"{blurb}\n")
        if name == "extract-codebases-from-paper":
            body.append(
                '<div class="note"><p>The inventories are published as an '
                "example of this skill's output. Their links to the paper PDFs "
                "will not resolve here — those PDFs are third-party and are not "
                "redistributable in this repository — but the availability "
                "links do, and a re-run against a tree laid out as above "
                "produces working links throughout.</p></div>\n")
        body.append(downloads_block(
            assets,
            [(f"bundles/{name}-outputs.zip", "Everything this skill produced")],
            heading=""))
    elif name in SKILL_NO_BUNDLE_NOTE:
        # Ships no archive, but the section still earns its place: the note
        # explains why there is nothing to download. A skill in neither table
        # gets no section at all.
        body.append("\n## What it produced\n")
        body.append(f"{SKILL_NO_BUNDLE_NOTE[name]}\n")

    write_page(f"skills/{name}.md",
               {"layout": "default", "title": name,
                "permalink": f"/skills/{name}/"},
               "\n".join(body))
