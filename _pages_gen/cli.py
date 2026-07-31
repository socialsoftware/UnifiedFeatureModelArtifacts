"""Orchestration: register the artifacts, render every page, report.

The order below matters in two places only. ``prune_pages`` must run before
anything is written, so a renamed page cannot leave an orphan behind, and
``apply_baseurl`` must run after every page exists, since it rewrites the
``{{BASE}}`` placeholder wherever it finds one. The renderers in between are
independent of each other.
"""

from __future__ import annotations

import sys
from typing import Dict

from .artifacts import Artifacts, BuildSummary, register_artifacts
from .config import COLOURS, COLOUR_SHORT, PAPERS, SKILL_ORDER, TOOLS
from .pages import (render_eval_tool_page, render_feature_model,
                    render_initial_model, render_meta_review, render_paper_page,
                    render_skill_page, render_skills, render_union_page)
from .paths import ARTIFACTS, BuildError
from .postprocess import apply_baseurl, prune_pages
from .report import tally_profiles


def build() -> Dict[str, object]:
    """Run the whole build. Returns what the closing report needs."""
    assets = Artifacts()
    summary: BuildSummary = register_artifacts(assets)

    prune_pages()

    render_feature_model(assets)
    render_initial_model(assets)
    studies = render_meta_review(assets)
    skills = render_skills(assets)
    for skill in SKILL_ORDER:
        render_skill_page(skill, assets)

    render_union_page("all-tools", assets)
    for paper in PAPERS:
        render_paper_page(paper, assets)
        if paper["union"]:
            render_union_page(paper["union"], assets)
    for tool in TOOLS:
        render_eval_tool_page(tool, assets)

    counts = tally_profiles()

    apply_baseurl()

    return {"summary": summary, "studies": studies, "skills": skills,
            "counts": counts}


def _print_summary(result: Dict[str, object]) -> None:
    """The build report, including the colour-count cross-check.

    The counts are printed on every build because they are what the paper's
    mapping-summary table reports: if they change silently, the paper and the
    artifacts have drifted apart.
    """
    summary = result["summary"]
    assert isinstance(summary, dict)
    counts = result["counts"]
    assert isinstance(counts, dict)

    print(f"{len(TOOLS)} tools, {summary['profiles']} profiles, "
          f"{summary['images']} images, {result['studies']} studies, "
          f"{result['skills']} skills")
    print(f"extended models: {', '.join(summary['extended_models']) or 'none'}")

    print("\nper-tool colour counts (automated / reviewed) — "
          "cross-check against the paper's mapping summary table:")
    print("  {:<24}".format("tool")
          + "".join(f"{COLOUR_SHORT[c][:11]:>13}" for c in COLOURS))
    for key, value in counts.items():
        auto = value["auto"]
        review = value.get("review")
        cells = "".join(
            "{:>13}".format(f"{auto[c]}" + (f" ({review[c]})" if review else ""))
            for c in COLOURS)
        print(f"  {key:<24}{cells}")


def main() -> int:
    if not ARTIFACTS.is_dir():
        print(f"error: {ARTIFACTS} not found — run from the repository root",
              file=sys.stderr)
        return 2

    try:
        result = build()
    except BuildError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    _print_summary(result)
    return 0
