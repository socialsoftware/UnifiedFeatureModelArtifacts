"""The registry that maps logical asset keys to real files under ``artifacts/``.

Nothing is copied. The Pages source is the repository root, so Jekyll publishes
``artifacts/`` in place and the site links straight into it; this module only
records where each artifact lives and turns that into a URL.

The one exception is ``build_bundle``, which creates a zip -- a
"download the folder" link needs a real file. Those land in ``bundles/`` at the
repository root, never under ``artifacts/``: that tree holds only the original
research artifacts, and a bundle is derived from it.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, TypedDict

from .config import (BUNDLE_NAME, INITIAL_BUNDLE_NAME, MERGED, SKILL_BUNDLE,
                     SKILL_ORDER, SKILL_OUTPUT_BUNDLE, TOOLS, TOOL_META)
from .paths import ARTIFACTS, BUNDLES, BuildError, REPO
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


def build_bundle(folder: str, bundle_name: str, arc_root: str = "") -> Path:
    """Zip a whole artifacts/ subfolder and return the archive path.

    ``arc_root`` overrides the folder the archive is rooted at. A skill lives at
    ``.claude/skills/<name>/``, and unzipping that path would bury the files
    three levels deep for no reason; the skills pass their bare name instead.

    Everything else on the site is linked in place (see ``Artifacts``), but a
    "download the folder" link needs a real file, so these are the only
    artifacts the script creates rather than merely locating. They are written
    to ``bundles/`` rather than beside what they archive, keeping ``artifacts/``
    to the original research artifacts alone.

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
    root = arc_root or folder
    members = [
        # Rooted at a folder name so unzipping yields the folder, not a scatter
        # of loose files in the reader's download directory.
        (f"{root}/" + p.relative_to(src).as_posix(), p)
        for p in src.rglob("*")
        if p.is_file() and p.name != ".project"]
    if not members:
        raise BuildError(f"nothing to bundle under {src.relative_to(REPO)}/")
    return write_bundle(bundle_name, members)


def write_bundle(bundle_name: str, members: Sequence[Tuple[str, Path]]) -> Path:
    """Zip explicit ``(archive name, source file)`` pairs, deterministically.

    ``build_bundle`` archives a whole folder; this takes a list instead, for the
    per-skill output archives whose members are scattered across
    ``evaluation/analyses/`` and ``feature_model/.profiles/`` and so have no one
    folder to root at.

    ``bundle_name`` is a bare filename: every archive is written flat into
    ``bundles/``, which is created here since it holds nothing but build output
    and so need not exist in a fresh checkout.

    Members are sorted by archive name and written with fixed timestamps and
    modes, so unchanged inputs yield a byte-identical archive.
    """
    if not members:
        raise BuildError(f"nothing to bundle into {bundle_name}")

    BUNDLES.mkdir(exist_ok=True)
    out = BUNDLES / bundle_name
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for arcname, path in sorted(members, key=lambda m: m[0]):
            info = zipfile.ZipInfo(arcname, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, path.read_bytes())
    return out


def skill_output_members(skill: str) -> List[Tuple[str, Path]]:
    """The artifacts one skill produced, as ``(archive name, path)`` pairs.

    Ownership is derived from ``TOOL_META[tool]["skill"]`` and ``MERGED`` rather
    than declared, so adding a tool never means editing a list here.
    ``refresh-feature-model-infos`` edits files in place and owns nothing, so it
    yields an empty list and gets no archive.
    """
    profiles = ARTIFACTS / "feature_model" / ".profiles"
    analyses = ARTIFACTS / "evaluation" / "analyses"
    members: List[Tuple[str, Path]] = []

    if skill == "extract-codebases-from-paper":
        for paper_md in sorted((ARTIFACTS / "evaluation" / "papers").glob("*.md")):
            members.append((f"papers/{paper_md.name}", paper_md))
        return members

    if skill == "merge-profiles":
        # A merged profile is filed under its stem or under its site key, which
        # coincide for `wang` -- hence the dedupe, or the archive would carry
        # the same member twice.
        seen = set()
        for key, stem, _ in MERGED:
            for name in (f"{stem}.profile", f"{key}.profile"):
                path = profiles / name
                if path.is_file() and name not in seen:
                    seen.add(name)
                    members.append((f".profiles/{name}", path))
        return members

    if skill == "verify-analysis":
        # The reviewed twins are this skill's product: one per automated
        # mapping, re-derived after the cited evidence was re-checked.
        for path in sorted(profiles.glob("*_user_review*.profile")):
            members.append((f".profiles/{path.name}", path))
        return members

    # codebase-map and docs-map: the tools each one mapped.
    for tool in TOOLS:
        if TOOL_META[tool]["skill"] != skill:
            continue
        for rel in ("analysis.md", "README.md"):
            path = analyses / tool / rel
            if path.is_file():
                members.append((f"analyses/{tool}/{rel}", path))
        path = profiles / f"{tool}.profile"
        if path.is_file():
            members.append((f".profiles/{tool}.profile", path))
    return members


def register_skill_artifacts(artifacts: Artifacts) -> None:
    """Register each skill's own files and build its two download archives.

    ``SKILL.md`` carries YAML frontmatter, so Jekyll renders it to ``SKILL.html``
    and no raw ``.md`` is served -- the skill pages link GitHub raw for reading
    it directly. The archives are what make the whole folder downloadable, and
    the ``references/*.md`` files have no frontmatter so they are served as-is.
    """
    skills_dir = ARTIFACTS / ".claude" / "skills"
    for skill in SKILL_ORDER:
        base = skills_dir / skill
        artifacts.register(base / "SKILL.md", f"skills/{skill}/SKILL.md")

        for ref in sorted((base / "references").glob("*.md")):
            artifacts.register(ref, f"skills/{skill}/references/{ref.name}")

        artifacts.register(
            build_bundle(f".claude/skills/{skill}",
                         SKILL_BUNDLE.format(skill=skill), arc_root=skill),
            f"bundles/{skill}-skill.zip")

        members = skill_output_members(skill)
        if members:
            artifacts.register(
                write_bundle(SKILL_OUTPUT_BUNDLE.format(skill=skill), members),
                f"bundles/{skill}-outputs.zip")


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

    # The paper inventories. Published as the output of
    # extract-codebases-from-paper -- their relative links to paper PDFs do not
    # resolve here (those PDFs are not redistributable), which the skill page
    # says plainly.
    for paper_md in sorted((ARTIFACTS / "evaluation" / "papers").glob("*.md")):
        artifacts.register(paper_md, f"papers/{paper_md.stem}.md")

    register_skill_artifacts(artifacts)

    return {
        "images": images,
        "profiles": len(profile_files),
        "extended_models": extended_models,
        "has_pdf": pdf_src is not None,
    }
