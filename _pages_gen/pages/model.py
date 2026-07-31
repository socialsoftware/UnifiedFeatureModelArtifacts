"""The two pages about the feature model itself.

``feature-model`` is the canonical model plus the table of every downloadable
colour profile; ``initial-model`` is the pre-generalisation version, published
so the two can be compared.
"""

from __future__ import annotations

import html
from typing import Tuple

from ..artifacts import Artifacts
from ..config import MAPPING_BLURB, MERGED, PAPERS, TOOLS, TOOL_LABEL, TOOL_META
from ..render import downloads_block, figure, table, write_page
from ..util import png_size


def render_feature_model(assets: Artifacts) -> None:
    """Tab 1: the proposed model -- the image, and the model itself."""
    width, height = png_size(assets.path("images/feature_model.png"))

    body = [
        "# The unified feature model\n",
        figure("The complete feature model, rendered from FeatureIDE.",
               [{"file": assets.url("images/feature_model.png"),
                 "label": "Unified feature model",
                 "meta": f"{width}&times;{height}",
                 "alt": "The complete unified feature model as a horizontal tree"}]),
    ]

    body.append("\n## Colour profiles\n")
    body.append(
        "Every colour profile available for download: one per tool, plus the "
        "merged profiles. \nEach is a FeatureIDE colour profile that paints the "
        "model with that tool's mapping. The <i>reviewed</i> column is the "
        "authors' revised version of the automated mapping.\n")

    rows = []
    for tool in TOOLS:
        paper = next(p for p in PAPERS if p["key"] == TOOL_META[tool]["source"])
        rows.append(_profile_row(
            assets, TOOL_LABEL[tool], tool,
            page=f"{{{{BASE}}}}/evaluation/{paper['slug']}/{tool.lower()}/"))
    for key, _prefix, label in MERGED:
        review = ("mono2micro_user_review+Micro2Micro_user_review"
                  if key == "mono2micro+Micro2Micro" else "")
        # mono2micro+Micro2Micro is deliberately pageless (see
        # render_union_page), so its row is plain text and the blurb carries it.
        page = ""
        if key == "all-tools":
            page = "{{BASE}}/evaluation/all-tools/"
        elif key == "wang":
            paper = next(p for p in PAPERS if p["union"] == key)
            page = f"{{{{BASE}}}}/evaluation/{paper['slug']}/all/"
        rows.append(_profile_row(assets, label, key, review, page=page))
    body.append(table(["Mapping", "What it is", "Automated", "Reviewed"], rows))

    entries = [
        ("bundles/feature_model.zip",
         "Everything below in one archive: the model, every colour profile, "
         "and the configuration"),
        ("models/feature_model.xml", "The feature model (FeatureIDE XML)"),
        ("images/feature_model.png", "The rendered model, as shown above"),
    ]
    if "models/feature_model_config.xml" in assets:
        entries.append(("models/feature_model_config.xml",
                        "FeatureIDE configuration listing every feature"))
    body.append(downloads_block(assets, entries))

    write_page("feature-model.md",
               {"layout": "default", "title": "Feature model",
                "nav_title": "Feature Model", "nav_order": 2,
                "permalink": "/feature-model/"},
               "\n".join(body))


def _profile_row(assets: Artifacts, label: str, stem: str,
                 review_stem: str = "",
                 page: str = "") -> Tuple[str, str, str, str]:
    """One row of the Colour profiles table.

    ``page`` is the mapping's own page, where it has one. It is optional
    because mono2micro+Micro2Micro deliberately has none, and that row then
    renders as plain text rather than a dead link.
    """
    def link(rel: str) -> str:
        if rel not in assets:
            return "—"
        name = rel.rsplit("/", 1)[-1]
        return f'<a href="{assets.url(rel)}" download><code>{html.escape(name)}</code></a>'

    name = html.escape(label)
    return (f'<a href="{page}">{name}</a>' if page else name,
            html.escape(MAPPING_BLURB.get(stem, "")),
            link(f"profiles/{stem}.profile"),
            link(f"profiles/{review_stem or stem + '_user_review'}.profile"))


def render_initial_model(assets: Artifacts) -> None:
    """Tab 2: the model that preceded generalisation."""
    width, height = png_size(assets.path("images/initial_feature_model.png"))

    body = [
        "# The initial feature model\n",
        figure("The initial feature model, before the bottom-up generalisation.",
               [{"file": assets.url("images/initial_feature_model.png"),
                 "label": "Initial feature model",
                 "meta": f"{width}&times;{height}",
                 "alt": "The initial feature model derived from Mono2Micro"}]),
    ]

    entries = [
        ("bundles/initial_feature_model.zip",
         "Everything below in one archive: the model, the rendered image, "
         "and the configuration"),
        ("models/initial_feature_model.xml",
         "The initial feature model (FeatureIDE XML)"),
        ("images/initial_feature_model.png", "The rendered model, as shown above"),
    ]
    body.append(downloads_block(assets, entries))

    write_page("initial-model.md",
               {"layout": "default", "title": "Initial model",
                "nav_title": "Initial Model", "nav_order": 3,
                "permalink": "/initial-model/"},
               "\n".join(body))
