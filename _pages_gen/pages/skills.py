"""The Skills page: the six mapping skills that produced the evaluation."""

from __future__ import annotations

import html

from ..artifacts import Artifacts
from ..config import RAW_BASE, SKILL_ORDER, SKILL_SUMMARY
from ..parse import parse_skills
from ..paths import ARTIFACTS, BuildError
from ..render import table, write_page
from ..util import human_size


def render_skills(assets: Artifacts) -> int:
    """Tab 4: the six mapping skills, each downloadable."""
    skills = {s["dir"]: s for s in parse_skills()}
    missing = [d for d in SKILL_ORDER if d not in skills]
    if missing:
        raise BuildError(f"SKILL_ORDER names unknown skills: {missing}")
    extra = [d for d in skills if d not in SKILL_ORDER]

    body = [
        "# Mapping skills\n",
        "The six skills that produced the evaluation. They are Claude Code "
        "skills: each <code>SKILL.md</code> is a written procedure the model "
        "follows, so the mapping process is inspectable and re-runnable rather "
        "than a one-off prompt.\n",
        '<div class="note"><p>The skills are <b>non-deterministic</b>: running '
        'one twice can produce different verdicts. That is why '
        '<code>verify-analysis</code> exists, and why every mapping in the '
        'evaluation is published in both its automated and its reviewed '
        'form.</p></div>\n',
        "\n## The pipeline\n",
        '<pre class="pipeline">'
        "extract-codebases-from-paper   paper  -> tools + codebases\n"
        "         |\n"
        "         v\n"
        "codebase-map / docs-map        tool   -> analysis + colour profile\n"
        "         |\n"
        "         v\n"
        "verify-analysis                reconciles repeated runs\n"
        "         |\n"
        "         v\n"
        "merge-profiles                 per-tool profiles -> union profile"
        "</pre>\n",
        "<p><code>refresh-feature-model-infos</code> sits outside this chain: it "
        "runs whenever the feature model changes, to keep the files that "
        "describe it in step.</p>\n",
        "\n## The skills\n",
        '<ul class="cards skill-cards">',
    ]

    for name in SKILL_ORDER + extra:
        skill = skills[name]
        summary = SKILL_SUMMARY.get(name)
        if summary is None:
            # Fall back to the frontmatter description, which is written as a
            # trigger phrase for the model rather than as prose, but is better
            # than an empty card.
            summary = html.escape(skill["description"])
        tools_used = html.escape(skill["tools"]) if skill["tools"] else "—"
        body.append(
            "<li>"
            f'<h3><a href="{{{{BASE}}}}/artifacts/.claude/skills/{name}/SKILL.html">'
            f"<code>{html.escape(name)}</code></a></h3>"
            f"<p>{summary}</p>"
            f'<p class="card-files">Tools: {tools_used} · '
            f'<a href="{{{{BASE}}}}/artifacts/.claude/skills/{name}/SKILL.html">read</a> · '
            f'<a href="{RAW_BASE}/artifacts/.claude/skills/{name}/SKILL.md" download>'
            "download</a></p>"
            "</li>")
    body.append("</ul>\n")

    body.append("\n## Shared references\n")
    body.append(
        "Two files the mapping skills read. They are identical wherever they "
        "appear, so they are listed once here rather than repeated per skill. "
        "<code>refresh-feature-model-infos</code> is what keeps every copy in "
        "sync with the model.\n")

    ref_rows = []
    for filename, description in (
            ("feature-model-dimensions.md",
             "The feature model's dimensions, as the skills consume them"),
            ("analysis-template.md",
             "The blank analysis document each mapping fills in")):
        # Any copy will do -- they are byte-identical. Pick the first skill
        # that carries one so the link never depends on a specific skill.
        holder = next((d for d in SKILL_ORDER
                       if (ARTIFACTS / ".claude" / "skills" / d / "references"
                           / filename).is_file()), "")
        if not holder:
            continue
        url = ("{{BASE}}/artifacts/.claude/skills/"
               f"{holder}/references/{filename}")
        size = human_size((ARTIFACTS / ".claude" / "skills" / holder /
                           "references" / filename).stat().st_size)
        ref_rows.append((f'<a href="{url}" download><code>{filename}</code></a>',
                         description, size))
    if ref_rows:
        body.append(table(["File", "What it is", "Size"], ref_rows,
                          extra_class="downloads"))

    write_page("skills.md",
               {"layout": "default", "title": "Skills",
                "nav_title": "Skills", "nav_order": 5,
                "permalink": "/skills/"},
               "\n".join(body))
    return len(skills)
