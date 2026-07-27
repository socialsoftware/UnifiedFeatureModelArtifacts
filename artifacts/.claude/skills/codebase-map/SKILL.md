---
name: codebase-map
description: This skill should be used when the user says "map codebase <path>", "analyse codebase <path>", "run codebase-map on <path>", or provides a path to a local tool codebase and wants it mapped against the feature model. Produces three files per tool: evaluation/analyses/<tool-name>/analysis.md, evaluation/analyses/<tool-name>/README.md, and feature_model/representation/.profiles/<tool-name>.profile. Never modifies my_paper/text.md.
allowed-tools: Read, Write, Bash
---

# codebase-map

Analyse a local tool codebase and map it against the feature model dimensions.

## Inputs

The user provides a path to a local codebase directory, e.g.:

```
../extracted-codebases/Mono2Micro
```

Derive the tool name from the directory name.

## Output files

Three files are produced per tool:

1. `evaluation/analyses/<tool-name>/analysis.md` — filled Analysis Template, feature coverage table, Observations
2. `evaluation/analyses/<tool-name>/README.md` — how to set up and run the tool, gotchas, pointer to the colour profile
3. `feature_model/representation/.profiles/<tool-name>.profile` — FeatureIDE colour profile for the canonical feature model

**Never modify** `my_paper/text.md`, `feature_model/representation/feature_model.xml`, any existing analysis, or any existing profile.

"Existing analysis" and "existing profile" mean files **present in the working tree right now**. Do **not** consult git, `HEAD`, or repository history to decide whether a file exists — judge only by what is on disk. If the user has deleted a tool's analysis/README/profile locally to re-run the skill, those files do not exist and must be regenerated freely (overwrite is expected). Only refuse to modify analysis/profile files for *other* tools that are still present on disk.

## Procedure

### Step 1 — Explore the codebase structure

Get a high-level overview:

```bash
find <path> -maxdepth 3 -type f | head -80
```

Also look for:
- `README.md` or any documentation files at the root
- Build files (`pom.xml`, `build.gradle`, `requirements.txt`, `package.json`, etc.)
- Main entry points (`main.*`, `app.*`, `run.*`)
- Configuration files

Read the README and any top-level documentation.

### Step 2 — Identify feature model coverage

For each feature model dimension, search the codebase for evidence of support. Use `grep`, `find`, and `Read` on relevant files.

Key dimensions to investigate (see `references/feature-model-dimensions.md` for the full schema):

**Granularity:** What unit does the tool decompose? Look for terms like `class`, `method`, `entity`, `service`, `package`, `endpoint`, `file`.

**Representation Collection:**
- What sources does it read? (source code files, DB schemas, logs, configs)
- What technique? (AST parsing → static; log parsing → dynamic; git history → version)

**Representation (Syntax):**
- What graph/model is built? (call graph, dependency graph, co-change graph)
- Is it structural, behavioural, or evolution-based?

**Refactorization:**
- What clustering/decomposition algorithms are used?
- Is there any manual editing support?
- What aggregation criteria drive the clustering?

**Quality Assessment:**
- What metrics are computed? (coupling, cohesion, MoJoFM, etc.)
- Is there any visual comparison support?

Also check for **cross-tree constraint violations** (see `references/feature-model-dimensions.md`). The most common one: `Community detection → NOT Expert knowledge`. Flag any violations in both the analysis and the colour profile. A violation occurs when the tool uses both features together despite the constraint forbidding it, or when the tool uses a feature without the other feature that must co-exist with it (e.g., dynamic analysis requires runtime).

Also look actively for **model gap candidates** — things present in the codebase that have no counterpart in the feature model schema. For each one, note: what it is, where it appears (file:line), whether it would be a leaf or group and under which parent. Pay particular attention to:
- Manual Editing operations beyond Merge/Split/Transfer (e.g., Rename cluster, Form cluster from selection)
- Quality Assessment metrics beyond the listed ones (e.g., silhouette score, performance/response-time, purity against expert)
- Refactorization post-processing steps not covered (e.g., contract generation, CML export)
- Representation sources or collection techniques not in the schema
- Visualisation capabilities not covered by Relations or Visualization Elements

### Step 3 — Fill the Analysis Template

Read `references/analysis-template.md` and fill every section with findings from the codebase. Use bullet points. Every finding must cite at least one `file:line` reference from the actual codebase (e.g., `src/main/Analyzer.java:42`). If the only evidence is in documentation files (README, wiki, etc.), you may cite those, but label them explicitly (e.g., `README.md — "…"`) and keep searching for a corroborating code reference. Never substitute a documentation quote for a code reference when the code contains the evidence.

Citation rules:
- Standard: `` `path/to/file.ext:line` ``
- Documentation only: `` `README.md — "quote"` `` — label it explicitly as documentation.
- Jupyter notebooks: `` `<notebook>.ipynb` Cell N, lines X–Y `` (e.g., `` `1-System_analysis.ipynb` Cell 22, lines 242–260 ``).
- No evidence: write `[evidence not found]`.

### Step 4 — Build the feature coverage table

Produce a table with every leaf feature from the model:

| Feature | Dimension | Supported | Evidence |
|---------|-----------|-----------|----------|
| Method | Granularity | Yes | `src/decompose/MethodGraph.java:12` |
| Class | Granularity | No | [evidence not found] |
| Source code | Repr. Collection > Source > Development | Yes | `src/parser/JavaParser.java:8` |
| Monolith | Representation > Type | Yes | NetworkX DiGraph of the monolith |
| ... | ... | Yes / No / Unclear | file:line or note |

Use `Unclear` when there is indirect evidence but no direct confirmation.

**Evidence format rules (in order of preference):**
1. Actual codebase reference: `` `path/to/file.ext:line` `` — always preferred.
2. Documentation reference: `` `README.md — "quote"` `` — allowed only when no code reference exists; must be labelled as documentation.
3. Both: when documentation and code both support a finding, include the code reference and optionally add the documentation reference in parentheses.
4. `Unclear`: when there is indirect evidence but no direct confirmation — cite the best available reference and note why it is indirect.

Never write a documentation reference in place of a code reference when the code contains the evidence. When a feature is evidenced by both a README claim and an actual code/data artifact (e.g., a CSV file, an AST node, a solver object), cite the artifact — it is more informative and more trustworthy than a documentation quote.

### Step 5 — Write the Observations section

Add a section with the following subsections:

**Model Gap Candidates** — things present in the codebase that have no counterpart in the feature model. For each candidate use this format:
- **Name** — what it would be called as a feature
- **Would be:** leaf or group, and the parent dimension/group it would sit under
- **Evidence:** `file:line`
- **Rationale:** one sentence on why it warrants a place in the model

**Other features outside the model** — features that are present in the codebase but not captured by the feature model and don't meet the criteria to be a model gap candidate (e.g., they are too specific, too low-level, or not relevant to the paper's scope). For each one, note what it is and where it appears.

**Model Vocabulary Fit** — dimensions where the model's vocabulary doesn't quite match the tool's design (concept mismatch, partial overlap, etc.).

**Cross-tree constraint violations** — features that are used together but the model forbids it (or mandatory co-features that are missing).

**Noteworthy design decisions** — interesting patterns, architectural choices, or limitations worth mentioning in the paper's evaluation narrative.

### Step 6 — Write analysis.md

Create `evaluation/analyses/<tool-name>/` and write `analysis.md` with sections:

```
# Analysis — <tool-name>

Codebase path: <path>
Date: <today's date>

---

## Filled Analysis Template
[content from Step 3]

---

## Feature Coverage Table
[table from Step 4]

---

## Observations

### Model Gap Candidates
[candidates from Step 5]

### Other features outside the model
[list from Step 5]

### Model Vocabulary Fit
[vocabulary notes from Step 5]

### Cross-tree constraint violations
[violations from Step 5, or "None found."]

### Noteworthy design decisions
[design notes from Step 5]
```

### Step 7 — Write README.md

Write `evaluation/analyses/<tool-name>/README.md` with the following structure:

```markdown
# <Tool Name>

<one-line description — tool purpose and paper venue/year>

## Relevant Files

| File | Description |
|------|-------------|
| [<Paper title> (<Venue> <Year>)](../../papers/tools/<Tool>.pdf) | Paper PDF |
| [analysis.md](./analysis.md) | Feature model coverage analysis |
| [feature_model/representation/.profiles/<tool-name>.profile](../../feature_model/representation/.profiles/<tool-name>.profile) | FeatureIDE colour profile |
| [../../../../extracted-codebases/<tool-name>](../../../../extracted-codebases/<tool-name>) | Extracted codebase |
| [evaluation/papers/<Survey>.md](../papers/<Survey>.md) | Tool inventory |

---

## Prerequisites
...

## How to Run
...

## Gotchas
...
```

**Tool inventory row:** The tool inventory file (`evaluation/papers/<Survey>.md`) is produced by `extract-codebases-from-paper` before `codebase-map` runs. Locate the correct inventory file by searching `evaluation/papers/` for the `.md` file that lists this tool. Insert the relative link. After writing the README, verify the link resolves to an existing file.

**Paper PDF path:** If the paper PDF is in `papers/tools/`, use `../../papers/tools/<Tool>.pdf`. If it is in a subdirectory like `papers/mono2micro_process/`, adjust accordingly. Check the path exists before writing.

**Multiple repos (e.g. backend + frontend):** Add one codebase row per repository.

### Step 8 — Write the colour profile

Write `feature_model/representation/.profiles/<tool-name>.profile`. If this file is not on disk, write it — do not check git/`HEAD` first; a missing-on-disk profile is meant to be (re)generated.

The profile format is a flat key=value text file. The first line must be `false`. Feature names must match exactly the leaf and group names in `feature_model/representation/feature_model.xml`.

**Colour scheme — leaves:**

| Situation | Colour |
|-----------|--------|
| Leaf exists (confirmed) | `Light_Green` |
| Leaf exists but unclear / indirect evidence only | `Magenta` |
| Leaf absent, optional | `Yellow` |
| Leaf absent, mandatory | `Red` |
| Leaf present but causes a cross-tree constraint violation | `Orange` |

> Note: `Dark_Green` is only valid for group nodes, never for leaves.

**Colour scheme — groups (non-leaf nodes):**

| Situation | Colour |
|-----------|--------|
| All mandatory children **fully satisfied** (a leaf present = `Light_Green`; a group = `Dark_Green`), OR/ALT valid, no mandatory `Magenta` | `Dark_Green` |
| Mandatory child(ren) only `Magenta` (unclear) — or, for an OR group, the only present child(ren) are `Magenta` — with no Red/Orange overriding | `Magenta` |
| OR or AND partially satisfied (≥1 mandatory child **confirmed** Light_Green/Dark_Green, no mandatory child missing or `Magenta`) | `Light_Green` |
| Optional group, no children present | `Yellow` |
| Mandatory group with no children, or any mandatory child missing/Red | `Red` |
| Any child has a cross-tree constraint violation | `Orange` |

**Rules for propagating colour up to groups** (priority: `Red > Orange > Magenta > Light_Green > Yellow`):
1. Evaluate each child first.
2. If the group is mandatory and any mandatory child is `Red` → group is `Red`.
3. Else if any child is `Orange` → group is `Orange`.
4. Else if any mandatory child is `Magenta` — or, for an OR group, the only present child(ren) are `Magenta` (every confirmed branch is absent/Red) → group is `Magenta`. Uncertainty in a required child propagates up; **confirmed sibling leaves do not rescue the group.**
5. Else if ≥1 mandatory child is confirmed present (Light_Green/Dark_Green) — or, for an OR group, ≥1 child is confirmed present — and no mandatory child is missing or `Magenta` → group is `Light_Green` (OR) or continue evaluating (AND).
6. For AND groups: if **all mandatory** children are **fully satisfied** and no violations → `Dark_Green`. A child is *fully satisfied* when it is a **leaf that is present** (`Light_Green` — a leaf's max, since leaves are never `Dark_Green`) **or a group that is itself `Dark_Green`**. A mandatory child **group** that is only `Light_Green` (partially satisfied) caps the AND parent at `Light_Green`. (Optional children that are absent or `Magenta` do not block `Dark_Green`; an optional `Red`/`Orange` child still applies rule 2/3.)
7. Optional group with zero present children → `Yellow`.

Include **every** leaf and group feature name from `feature_model/representation/feature_model.xml`. End the file with the following legend keys:

```
featureColorMeaning0=Leaf/Group: absent or broken (mandatory)
featureColorMeaning1=Constraint violation
featureColorMeaning2=Leaf/Group: absent (optional)
featureColorMeaning3=Group: fully satisfied
featureColorMeaning4=Leaf: exists / Group: partially satisfied
featureColorMeaning5=Extra Feature
featureColorMeaning6=InvalidColor (unused in FeatureIDE)
featureColorMeaning7=InvalidColor (unused in FeatureIDE)
featureColorMeaning8=Leaf: unclear / indirect evidence
featureColorMeaning9=InvalidColor (unused in FeatureIDE)
```

### Step 9 — Report to the user

Summarise:
- Which dimensions had strong coverage vs. gaps
- Any constraint violations found
- Anything particularly noteworthy from the Observations
- Paths to the three output files

## Reference files

- **`references/feature-model-dimensions.md`** — full feature model schema with cross-tree constraints
- **`references/analysis-template.md`** — the template to fill in Step 3
- **`feature_model/representation/feature_model.xml`** — canonical feature model (leaf names for the colour profile)
- **`feature_model/representation/.profiles/`** — existing profiles for reference on format
