---
name: docs-map
description: This skill should be used when the user says "map docs <url>", "analyse docs <url>", "run docs-map on <url>", or provides a documentation URL and wants a tool mapped against the feature model without a local codebase. Produces three files per tool: evaluation/analyses/<tool-name>/analysis.md, evaluation/analyses/<tool-name>/README.md, and feature_model/representation/.profiles/<tool-name>.profile. Never modifies my_paper/text.md.
allowed-tools: Read, Write, WebFetch, Bash
---

# docs-map

Analyse a tool's online documentation and map it against the feature model dimensions. This is the documentation-only counterpart of `codebase-map` — use it when the tool is closed-source or proprietary and only online docs are available.

## Inputs

The user provides:
1. A single entry-point URL to the tool's documentation (e.g., `https://www.ibm.com/docs/en/mono2micro`).
2. A tool name (derive from context or ask the user if not obvious).

## Output files

Three files are produced per tool:

1. `evaluation/analyses/<tool-name>/analysis.md` — filled Analysis Template, feature coverage table, Observations
2. `evaluation/analyses/<tool-name>/README.md` — documentation sources log, how to set up and run the tool, gotchas, pointer to the colour profile
3. `feature_model/representation/.profiles/<tool-name>.profile` — FeatureIDE colour profile for the canonical feature model

**Never modify** `my_paper/text.md`, `feature_model/representation/feature_model.xml`, any existing analysis, or any existing profile.

"Existing analysis" and "existing profile" mean files **present in the working tree right now**. Do **not** consult git, `HEAD`, or repository history to decide whether a file exists — judge only by what is on disk. If the user has deleted a tool's analysis/README/profile locally to re-run the skill, those files do not exist and must be regenerated freely (overwrite is expected). Only refuse to modify analysis/profile files for *other* tools that are still present on disk.

## Procedure

### Step 1 — Fetch and explore the documentation entry point

Fetch the landing page using `WebFetch(<entry-point URL>)`. If `WebFetch` returns an HTTP error (403, 401, 429, 5xx) or an empty/blocked response, fall back immediately to `curl` via Bash:

```bash
strip_html() {
  python3 -c "
import sys, re, html
text = sys.stdin.read()
text = re.sub(r'<[^>]+>', ' ', text)
text = html.unescape(text)
text = re.sub(r'\s+', ' ', text).strip()
print(text)
"
}
curl -s "<url>" -H "Accept: text/html" | strip_html
```

Use the same `curl | strip_html` pattern for every subsequent sub-page fetch whenever `WebFetch` has already failed once for the same domain. Do not retry `WebFetch` after confirming the domain blocks it.

From the landing page, identify and fetch relevant sub-pages. Prioritise pages that describe:
- What the tool does (overview, architecture, features)
- What inputs it takes (getting started, prerequisites, configuration)
- What algorithms or techniques it uses (how it works, technical overview)
- What outputs and metrics it produces (results, evaluation, API reference)
- Known limitations or caveats (FAQ, known issues, release notes)

Fetch each relevant sub-page individually. **Keep a running list of every URL visited** (entry-point + all sub-pages fetched), in the order they were fetched. This list will go into the README.

### Step 2 — Identify feature model coverage

For each feature model dimension, search the fetched documentation for evidence of support.

Key dimensions to investigate (see `references/feature-model-dimensions.md` for the full schema):

**Granularity:** What unit does the tool decompose? Look for terms like `class`, `method`, `entity`, `service`, `package`, `endpoint`, `file`.

**Representation Collection:**
- What sources does it read? (source code files, DB schemas, logs, configs)
- What technique? (AST parsing → static; log/trace analysis → dynamic; git history → version)

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

Also look actively for **model gap candidates** — capabilities described in the docs that have no counterpart in the feature model schema. For each one, note: what it is, where it appears (URL + quote), whether it would be a leaf or group and under which parent. Pay particular attention to:
- Manual Editing operations beyond Merge/Split/Transfer (e.g., Rename cluster, Form cluster from selection)
- Quality Assessment metrics beyond the listed ones (e.g., silhouette score, purity against expert)
- Refactorization post-processing steps not covered (e.g., contract generation, export)
- Representation sources or collection techniques not in the schema
- Visualisation capabilities not covered by Relations or Visualization Elements

### Step 3 — Fill the Analysis Template

Read `references/analysis-template.md` and fill every section with findings from the documentation. Use bullet points. Every finding must cite at least one URL reference.

**Evidence format for docs-map (in order of preference):**
1. Direct quote: `` `<url> — "exact quote from the page"` `` — always preferred when the documentation contains explicit technical detail.
2. Paraphrase: `` `<url> — paraphrase: summary of what the page says` `` — use only when no quotable sentence exists; label explicitly as paraphrase.
3. No evidence: write `[evidence not found]`.

**Confidence rule:** Prefer `Unclear` over `Yes` when the only evidence is a vague marketing claim (e.g., "supports X" with no technical detail). Reserve `Yes` for documentation that includes technical specifics (algorithm names, config keys, data structures, step-by-step descriptions, screenshots of UI).

Never invent evidence. If a feature is not mentioned in the documentation, mark it absent.

### Step 4 — Build the feature coverage table

Produce a table with every leaf feature from the model:

| Feature | Dimension | Supported | Evidence |
|---------|-----------|-----------|----------|
| Method | Granularity | Yes | `https://... — "the tool decomposes at the method level"` |
| Class | Granularity | No | [evidence not found] |
| Source code | Repr. Collection > Source > Development | Yes | `https://... — "analyses Java source files"` |
| ... | ... | Yes / No / Unclear | url — quote or paraphrase |

Use `Unclear` when there is indirect or vague evidence but no direct technical confirmation.

### Step 5 — Write the Observations section

Add a section with the following subsections:

**Model Gap Candidates** — capabilities present in the documentation that have no counterpart in the feature model. For each candidate use this format:
- **Name** — what it would be called as a feature
- **Would be:** leaf or group, and the parent dimension/group it would sit under
- **Evidence:** `<url> — "quote"`
- **Rationale:** one sentence on why it warrants a place in the model

**Other features outside the model** — features present in the documentation but not captured by the feature model and not meeting the criteria to be a model gap candidate (too specific, too low-level, or out of scope). For each one, note what it is and where it appears.

**Model Vocabulary Fit** — dimensions where the model's vocabulary doesn't quite match the tool's design (concept mismatch, partial overlap, etc.).

**Cross-tree constraint violations** — features that are used together but the model forbids it (or mandatory co-features that are missing).

**Noteworthy design decisions** — interesting patterns, architectural choices, or limitations worth mentioning in the paper's evaluation narrative.

### Step 6 — Write analysis.md

Create `evaluation/analyses/<tool-name>/` and write `analysis.md` with sections:

```
# Analysis — <tool-name>

Documentation: <entry-point URL>
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

<one-line description — tool purpose, URL, year if known>

## Relevant Files

| File | Description |
|------|-------------|
| [analysis.md](./analysis.md) | Feature model coverage analysis |
| [feature_model/representation/.profiles/<tool-name>.profile](../../feature_model/representation/.profiles/<tool-name>.profile) | FeatureIDE colour profile |

---

## Documentation Sources

- **Entry point:** <entry-point URL>
- **Fetched:** <today's date>
- **Pages visited:** <total count>

| # | URL | Purpose |
|---|-----|---------|
| 1 | <url> | Entry point / overview |
| 2 | <url> | Getting started / prerequisites |
| 3 | <url> | ... |

---

## Prerequisites
...

## How to Run
...

## Gotchas
...
```

**Relevant Files notes:**
- No codebase row (docs-map is used for closed-source/proprietary tools with no local codebase).
- No tool inventory row (docs-map tools are not typically included in survey inventory files — omit unless one exists).
- If a paper PDF is available locally, add a row: `| [<Paper title>](../../papers/.../<file>.pdf) | Paper PDF |`.

**Documentation Sources:** List every URL fetched during Step 1, in the order they were visited, with a one-line description of what each page covers.

### Step 8 — Write the colour profile

Write `feature_model/representation/.profiles/<tool-name>.profile`. If this file is not on disk, write it — do not check git/`HEAD` first; a missing-on-disk profile is meant to be (re)generated.

The profile format is a flat key=value text file. The first line must be `false`. Feature names must match exactly the leaf and group names in `feature_model/representation/feature_model.xml`.

**Colour scheme — leaves:**

| Situation | Colour |
|-----------|--------|
| Leaf exists — confirmed with technical detail in docs | `Light_Green` |
| Leaf exists but vague claim only / indirect evidence | `Magenta` |
| Leaf absent, optional | `Yellow` |
| Leaf absent, mandatory | `Red` |
| Leaf present but causes a cross-tree constraint violation | `Orange` |

> Note: `Dark_Green` is only valid for group nodes, never for leaves.
>
> **Documentation-specific rule:** Prefer `Magenta` over `Light_Green` whenever the only evidence is a high-level marketing claim with no technical detail. Reserve `Light_Green` for documentation that includes specifics (algorithm names, config keys, data structures, step-by-step descriptions).
>
> **Uncertainty rule:** When you are unsure whether a piece of documentation refers to the feature at all (ambiguous scope, overlapping terminology, indirect reference), prefer `Magenta` over `Yellow`. Use `Yellow` only when you are confident the feature is absent.

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
- How many documentation pages were fetched and which entry point was used
- Which dimensions had strong coverage vs. gaps
- Any constraint violations found
- Anything particularly noteworthy from the Observations
- Paths to the three output files

## Key differences from `codebase-map`

| Aspect | `codebase-map` | `docs-map` |
|--------|---------------|------------|
| Evidence source | `file.ext:line` | `<url> — "quote"` |
| Tools used | `Read`, `Bash` (grep/find) | `WebFetch` |
| Confidence default | High (code is ground truth) | Medium — `Magenta` for vague claims |
| README "How to run" | Derived from code/build files | Derived from official install/quickstart docs |
| README extra section | — | Documentation Sources (entry point, page count, full URL list) |

## Reference files

- **`references/feature-model-dimensions.md`** — full feature model schema with cross-tree constraints
- **`references/analysis-template.md`** — the template to fill in Step 3
- **`feature_model/representation/feature_model.xml`** — canonical feature model (leaf names for the colour profile)
- **`feature_model/representation/.profiles/`** — existing profiles for reference on format
