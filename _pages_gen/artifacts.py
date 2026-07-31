"""The registry that maps logical asset keys to real files under ``artifacts/``.

Nothing is copied. The Pages source is the repository root, so Jekyll publishes
``artifacts/`` in place and the site links straight into it; this module only
records where each artifact lives and turns that into a URL.

The one exception is ``build_bundle``, which creates a zip -- a
"download the folder" link needs a real file.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Dict, List, Optional, TypedDict

from .config import BUNDLE_NAME, BUNDLE_NAMES, INITIAL_BUNDLE_NAME, TOOLS
from .paths import ARTIFACTS, BuildError, REPO
from .util import human_size


class Artifacts:
    """Maps logical asset keys to the real files under ``artifacts/``.

    Nothing is copied. The Pages source is the repository root, so Jekyll
    publishes ``artifacts/`` in place and the site links straight into it; this
    class only records where each artifact lives and turns that into a URL.

    ``paths`` doubles as the existence registry the page renderers query
    (``if key not in artifacts: ...``) to decide whether an optional artifact
    was shipped.
    """

    def __init__(self) -> None:
        self.paths: Dict[str, Path] = {}

    def register(self, src: Path, key: str, *, required: bool = True) -> Optional[str]:
        """Record a logical key for a real artifact file.

        Returns the key, or None when an optional file is absent. Raises for a
        missing required file, matching the old copy() contract.
        """
        if not src.is_file():
            if required:
                raise BuildError(f"missing artifact: {src.relative_to(REPO)}")
            return None
        self.paths[key] = src
        return key

    def __contains__(self, key: str) -> bool:
        return key in self.paths

    def path(self, key: str) -> Path:
        """The real artifact path, for png_size() and the CSV read."""
        try:
            return self.paths[key]
        except KeyError:
            raise BuildError(f"unregistered artifact key: {key}") from None

    def size(self, key: str) -> str:
        return human_size(self.paths[key].stat().st_size) if key in self.paths else ""

    def url(self, key: str) -> str:
        """Site URL of the artifact, addressed in place under artifacts/.

        Spaces are percent-encoded here rather than left to Liquid's
        ``relative_url``. That filter would encode them correctly, but the
        {{BASE}} placeholder never survives long enough to reach it: the
        substitution in apply_baseurl matches a run of non-whitespace, so a
        raw space truncates the URL mid-path. The meta-review CSV and PDF are
        the files this affects.

        Only the space is encoded, so the result stays readable and
        Addressable's later normalise() is a no-op rather than a double-encode.
        """
        rel = self.path(key).relative_to(REPO).as_posix()
        return "{{BASE}}/" + rel.replace(" ", "%20")


def build_bundle(folder: str, bundle_name: str) -> Path:
    """Zip a whole artifacts/ subfolder and return the archive path.

    Everything else on the site is linked in place (see ``Artifacts``), but a
    "download the folder" link needs a real file, so these are the only
    artifacts the script creates rather than merely locating.

    That makes each a committed binary: GitHub Pages builds the committed tree
    and never runs this script, so re-run generate.py and commit the result
    after changing anything under the bundled folder, or the download silently
    serves stale contents.

    Written deterministically -- sorted members, fixed timestamps and modes --
    so an unchanged folder yields a byte-identical archive. Otherwise checkout
    mtimes would leak into the zip and every build would show a spurious diff on
    a binary.
    """
    src = ARTIFACTS / folder
    if not src.is_dir():
        raise BuildError(f"missing {src.relative_to(REPO)}/")

    # .project is FeatureIDE's Eclipse metadata: it names a local workspace
    # project and means nothing outside it, so it stays out of the download.
    # Every bundle name is skipped, not just this folder's, so an archive can
    # never end up nested inside another.
    skip = (*BUNDLE_NAMES, ".project")
    members = sorted(
        (p for p in src.rglob("*") if p.is_file() and p.name not in skip),
        key=lambda p: p.relative_to(src).as_posix())
    if not members:
        raise BuildError(f"nothing to bundle under {src.relative_to(REPO)}/")

    out = src / bundle_name
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in members:
            # Rooted at the folder name so unzipping yields the folder, not a
            # scatter of loose files in the reader's download directory.
            info = zipfile.ZipInfo(
                f"{folder}/" + path.relative_to(src).as_posix(),
                date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, path.read_bytes())
    return out


class BuildSummary(TypedDict):
    """What register_artifacts reports back to main() for the closing print.

    Spelled out rather than Dict[str, object] so ``extended_models`` stays a
    list of names: as ``object`` it cannot be passed to str.join().
    """
    images: int
    profiles: int
    extended_models: List[str]
    has_pdf: bool


def register_artifacts(artifacts: Artifacts) -> BuildSummary:
    """Register every artifact the site links to. Returns a small summary."""
    # Only the count is ever reported, and every registration below is required
    # -- register() either returns the key or raises -- so counting avoids
    # collecting an Optional[str] into a List[str].
    images = 0

    exported = ARTIFACTS / "evaluation" / "exportedImages"
    if not exported.is_dir():
        raise BuildError("missing artifacts/evaluation/exportedImages/")
    for png in sorted(exported.glob("*.png")):
        artifacts.register(png, f"images/{png.name}")
        images += 1

    # The two rendered feature models.
    artifacts.register(
        ARTIFACTS / "feature_model" / "extended.png", "images/feature_model.png")
    artifacts.register(
        ARTIFACTS / "initialFeatureModelFromMono2Micro" / "initial_extended.png",
        "images/initial_feature_model.png")
    images += 2

    # Colour profiles. A dotfolder, so it only reaches the built site because
    # _config.yml lists `.profiles` under `include:`.
    profiles = ARTIFACTS / "feature_model" / ".profiles"
    profile_files = sorted(profiles.glob("*.profile"))
    if not profile_files:
        raise BuildError("no .profile files found")
    for prof in profile_files:
        artifacts.register(prof, f"profiles/{prof.name}")

    # Built, not located -- and built here, once the profiles above are known
    # to exist, so the download can never ship a folder missing them.
    artifacts.register(build_bundle("feature_model", BUNDLE_NAME),
                       "bundles/feature_model.zip")

    # FeatureIDE models: the canonical one, the initial one, and the
    # tool-specific extended ones.
    artifacts.register(ARTIFACTS / "feature_model" / "feature_model.xml",
                       "models/feature_model.xml")
    artifacts.register(ARTIFACTS / "initialFeatureModelFromMono2Micro" / "model.xml",
                       "models/initial_feature_model.xml")

    # The initial model's whole-folder download, built after the two files
    # above are known to exist, for the same reason as the bundle above.
    artifacts.register(
        build_bundle("initialFeatureModelFromMono2Micro", INITIAL_BUNDLE_NAME),
        "bundles/initial_feature_model.zip")

    extended_models: List[str] = []
    eval_models = ARTIFACTS / "evaluation" / "feature_models"
    if eval_models.is_dir():
        for sub in sorted(eval_models.iterdir()):
            xml = sub / "feature_model.xml"
            if xml.is_file():
                artifacts.register(xml, f"models/{sub.name}_feature_model.xml")
                extended_models.append(sub.name)

    # Meta-review. The source filenames contain spaces; they are served as-is
    # and percent-encoded by Liquid's relative_url (see Artifacts.url).
    meta_dir = ARTIFACTS / "meta-review"
    csv_src = next(meta_dir.glob("*.csv"), None)
    pdf_src = next(meta_dir.glob("*.pdf"), None)
    if csv_src is None:
        raise BuildError("missing meta-review CSV")
    artifacts.register(csv_src, "data/meta-review.csv")
    if pdf_src is not None:
        artifacts.register(pdf_src, "data/meta-review.pdf")

    # The FeatureIDE configuration beside the canonical model. Optional: it is
    # a selected product rather than the model itself.
    artifacts.register(ARTIFACTS / "feature_model" / "configs" / "default.xml",
                       "models/feature_model_config.xml", required=False)

    # Per-tool analyses and run notes, so each page can offer the raw markdown.
    # Neither file carries a YAML header, so Jekyll copies them verbatim and
    # they are downloadable as-is -- unlike SKILL.md, which it renders.
    for tool in TOOLS:
        base = ARTIFACTS / "evaluation" / "analyses" / tool
        artifacts.register(base / "analysis.md", f"analyses/{tool}-analysis.md")
        artifacts.register(base / "README.md", f"analyses/{tool}-readme.md",
                           required=False)

    return {
        "images": images,
        "profiles": len(profile_files),
        "extended_models": extended_models,
        "has_pdf": pdf_src is not None,
    }
