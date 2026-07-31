"""The meta-review page: a short explanation and the two downloads."""

from __future__ import annotations

import csv
import html

from ..artifacts import Artifacts
from ..paths import BuildError
from ..render import downloads_block, write_page


def render_meta_review(assets: Artifacts) -> int:
    """Tab 3: a short explanation and the two downloads.

    Returns the number of studies, read from the CSV so the count on the page
    cannot drift from the data.
    """
    csv_path = assets.path("data/meta-review.csv")
    with csv_path.open(encoding="utf-8-sig", newline="") as fh:
        records = list(csv.reader(fh))
    if len(records) < 6:
        raise BuildError("meta-review CSV has too few records")

    # Rows 1-4 are the nested header reproducing the model's dimensions, row 5
    # is a vocabulary row; the studies start after them.
    studies = [r[0].strip() for r in records[5:] if r and r[0].strip()]

    body = [
        "# Meta-review\n",
        f"A review of <b>{len(studies)}</b> secondary studies on monolith-to-"
        f"microservice decomposition. Each study is a row; the columns follow "
        f"the dimensions of the feature model, recording the concepts that study "
        f"reports for each one. This is the bottom-up evidence the model was "
        f"generalised from.\n",
        "<p>Studies reviewed: "
        + ", ".join(f"<i>{html.escape(s)}</i>" for s in studies)
        + ".</p>\n",
        '<div class="note"><p>The table is wide and deeply nested — four header '
        'rows — so it is published as data rather than rendered here. The CSV is '
        'the source; the PDF is the same table laid out for reading.</p></div>\n',
    ]

    entries = [("data/meta-review.csv", "The meta-review table (CSV)")]
    if "data/meta-review.pdf" in assets:
        entries.append(("data/meta-review.pdf", "The same table, as a PDF"))
    body.append(downloads_block(assets, entries))

    write_page("meta-review.md",
               {"layout": "default", "title": "Meta-review",
                "nav_title": "Meta-review", "nav_order": 4,
                "permalink": "/meta-review/"},
               "\n".join(body))
    return len(studies)
