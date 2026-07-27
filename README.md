# A Unified Feature Model for Microservice Identification and Refactoring — Artifacts

This repository is the companion artifact package for the paper:

> **A Unified Feature Model for Microservice Identification and Refactoring**
> Ana Margarida Almeida ([0000-0002-5946-3064](https://orcid.org/0000-0002-5946-3064)) and
> António Rito Silva ([0000-0001-9840-457X](https://orcid.org/0000-0001-9840-457X)), 2026.

It contains all the artifacts needed to inspect and reproduce the paper's
results: the unified feature model, the per-tool mappings used in the
evaluation, the images and figures, the meta-review data, and the LLM-based
mapping tooling.

A browsable version of this appendix is published via GitHub Pages:
<https://socialsoftware.github.io/UnifiedFeatureModelArtifacts/> (enable it under
*Settings → Pages → Source: `/` on `main`*).

The site is served from the repository root, so `artifacts/` is published in
place: every image, profile, and model on the site is the file in `artifacts/`
itself, never a copy.

The site's derived pages (per-tool pages, coverage matrix, meta-review table) are
generated from `artifacts/` by a script. GitHub Pages builds from the committed
tree and does not run it, so **re-run it whenever `artifacts/` changes** and
commit the regenerated `pages/`, or the published site goes stale:

```sh
python3 generate.py    # from the repository root; standard library only
```

It prints a per-tool colour-count summary that should match the mapping summary
table in the paper, and fails loudly if an expected analysis, profile, or image
is missing.

## Repository structure

```
README.md                     This file.
LICENSE                       MIT license (covers the code/skills).
LICENSE-DATA                  CC BY 4.0 license (covers the model, data, images).
CITATION.cff                  Machine-readable citation metadata.
artifacts/
  feature_model/              The unified feature model (FeatureIDE XML + PNG)
                              and the per-tool `.profiles/`.
  initialFeatureModelFromMono2Micro/
                              The initial model derived from mono2micro, before
                              generalisation.
  evaluation/
    analyses/<tool>/          Per-tool analysis.md and README.md.
    feature_models/<tool>/    Per-tool FeatureIDE projects.
    exportedImages/           Exported mapping images (claude / revised /
                              extended mappings).
    papers/                   Per-paper extractions behind the evaluated tools.
  meta-review/                Study selection and meta-review data.
  .claude/skills/             The mapping tooling (Claude skills).
generate.py                   Regenerates pages/ from artifacts/.
_config.yml                   Jekyll configuration for the Pages site.
_layouts/                     The page layout.
assets/                       Stylesheet and the image lightbox. Website source
                              only — research artifacts live in artifacts/.
pages/
  index.md                    Hand-written home page.
  methodology.md, feature-model.md, coverage.md, meta-review.md, tools/
                              Generated — do not edit by hand.
```

## Artifacts

| Artifact | Location | Description |
| -------- | -------- | ----------- |
| Unified feature model | [`artifacts/feature_model/`](artifacts/feature_model/) | The feature model in a machine-readable format plus a rendered image. |
| Tool mappings | [`artifacts/evaluation/analyses/<tool>/`](artifacts/evaluation/analyses/) | For each evaluated tool: the generated analysis and a README. |
| Colour profiles | [`artifacts/feature_model/.profiles/`](artifacts/feature_model/.profiles/) | The `.profile` mapping of each tool onto the feature model, plus the merged and user-reviewed profiles. |
| Mapping images | [`artifacts/evaluation/exportedImages/`](artifacts/evaluation/exportedImages/) | Exported figures showing each tool's mapping (`*_claudeMapping.png`), the manually revised mapping (`*_revisedMapping.png`), and the extended mapping (`*_extendedMapping.png`). |
| Meta-review data | [`artifacts/meta-review/`](artifacts/meta-review/) | The study-selection and meta-review material behind the state-of-the-art analysis. |
| Mapping skills | [`artifacts/.claude/skills/`](artifacts/.claude/skills/) | The LLM-based skills used to produce the mappings (`codebase-map`, `docs-map`, `verify-analysis`, `extract-codebases-from-paper`, `merge-profiles`, `refresh-feature-model-infos`). |

### Evaluated tools

The feature model was evaluated by mapping the following tools onto it:
mono2micro, IBM Mono2Micro, Micro2Micro, CARGO, HyDec, MEM, and MOSAIC.
See [`artifacts/evaluation/analyses/`](artifacts/evaluation/analyses/) for each
tool's mapping, and
[`artifacts/feature_model/.profiles/`](artifacts/feature_model/.profiles/) for
the individual and merged profiles.

## Reproducing the results

The evaluation mappings were produced with LLM-based skills and are therefore
**non-deterministic**. To keep the artifact inspectable and reproducible we
distinguish two levels:

1. **Inspect the results (deterministic).** The primary artifacts are the
   already-generated `analysis.md` files under
   [`artifacts/evaluation/analyses/`](artifacts/evaluation/analyses/) and the
   `.profile` mappings under
   [`artifacts/feature_model/.profiles/`](artifacts/feature_model/.profiles/).
   Every finding cites concrete evidence (a `file:line` reference or a
   documentation link) that can be checked directly against the tool's source.

2. **Re-run the mappings (optional).** The skills under
   [`artifacts/.claude/skills/`](artifacts/.claude/skills/) can
   regenerate the mappings. Because they rely on large language models, output
   will vary between runs; each mapping is meant to be validated against its
   cited evidence rather than taken at face value. We ran each mapping several
   times and reconciled results with `verify-analysis` before manual review.

**TODO:** add exact commands / environment for re-running the skills.

## Mapping paper claims to artifacts

**TODO:** fill in once table/figure numbers are final.

| Paper reference | Artifact |
| --------------- | -------- |
| Feature model overview (Fig. TODO) | [`artifacts/feature_model/`](artifacts/feature_model/) |
| Coverage table (Table TODO) | [`artifacts/evaluation/analyses/`](artifacts/evaluation/analyses/) |
| Per-tool mappings | [`artifacts/evaluation/analyses/<tool>/`](artifacts/evaluation/analyses/) |

## License

This repository uses two licenses:

- **Code** — the mapping tooling under
  [`artifacts/.claude/skills/`](artifacts/.claude/skills/) is licensed under the
  **MIT License** (see [`LICENSE`](LICENSE)).
- **Research artifacts** — the feature model, tool mappings (`.profile`),
  images, generated analysis, and meta-review data are licensed under
  **Creative Commons Attribution 4.0 International (CC BY 4.0)** (see
  [`LICENSE-DATA`](LICENSE-DATA)).

## Citation

If you use these artifacts, please cite the paper. See [`CITATION.cff`](CITATION.cff)
or use the "Cite this repository" button on GitHub.

## Status

- [x] Licenses (MIT + CC BY 4.0)
- [x] README
- [x] GitHub Pages site scaffold (repository root)
- [x] Feature model in machine-readable format
- [x] Per-tool analysis and `.profile` files
- [x] Meta-review data
- [x] Mapping skills
- [x] GitHub Pages appendix site (`pages/`, built by `generate.py`)
- [ ] Archive a release on Zenodo and add the DOI
- [ ] Enable GitHub Pages (Settings → Pages → Source: `/` on `main`)
- [ ] Add the paper DOI to `pages/index.md` (currently a placeholder)
