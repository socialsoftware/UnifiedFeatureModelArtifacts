---
name: refresh-feature-model-infos
description: Check whether all files that depend on the feature model are in sync with feature_model/representation/feature_model.xml, report discrepancies, ask for approval, then update them and the README registry.
allowed-tools: Read, Write, Edit, Bash
---

# refresh-feature-model-infos

Parse the canonical feature model XML and verify that every dependent file accurately reflects its current structure. Report any gaps or stale content, ask for approval, then apply updates and refresh the dependency registry in `feature_model/README.md`.

## Dependent files

| File | Role |
|------|------|
| `.claude/skills/codebase-map/references/feature-model-dimensions.md` | Schema reference — codebase-map skill |
| `.claude/skills/docs-map/references/feature-model-dimensions.md` | Schema reference — docs-map skill |
| `.claude/skills/extract-codebases-from-paper/references/feature-model-dimensions.md` | Schema reference — extract-codebases-from-paper skill |
| `papers/surveys/Analysis - Template.md` | Paper analysis template |
| `.claude/skills/codebase-map/references/analysis-template.md` | Analysis template copy — codebase-map skill |
| `.claude/skills/docs-map/references/analysis-template.md` | Analysis template copy — docs-map skill |

These are also catalogued in `feature_model/README.md` under **Dependent files**.

---

## Procedure

### Step 1 — Parse the feature model

Read `feature_model/representation/feature_model.xml`.

From the `<struct>` block, extract the full feature hierarchy:
- For every `<and>`, `<or>`, `<alt>` group: record its `name`, operator type (AND / OR / ALT), and whether `mandatory="true"`.
- For every `<feature>` leaf: record its `name` and whether `mandatory="true"`.

From the `<constraints>` block, reconstruct each `<rule>` as a plain-English implication: "If X → then Y (OR Z …)".

Build a tree summary, for example:

```
Root: Microservices Decompostion and Refactorization (AND, mandatory)
├── Granularity (OR, mandatory)
│   ├── Method
│   ├── Class
│   └── ...
├── Representation Collection (OR, mandatory)
│   ├── Collector (AND)
│   │   ├── Source (OR, mandatory)
│   │   │   ├── Development (OR): Source Code, Database schema, Version history
│   │   │   ├── Runtime (OR): Runtime Log Traces, User Interactions
│   │   │   ├── Higher-level Models (OR): Business Process Model, Use Case, Data Flow Diagram
│   │   │   └── Documentation (OR): Directly in the Code, Paper Document, Digital Format
│   │   └── Collection Technique (OR, mandatory): Static Analysis, Dynamic Analysis, Version Analysis, Model Analysis
│   └── External
...
```

### Step 2 — Check each dependent file

Read each file and compare against the parsed hierarchy from Step 1.

**For the two `feature-model-dimensions.md` files:**
- `[MISSING]` — feature/group present in XML but absent from the file
- `[OBSOLETE]` — feature/group present in file but removed from XML
- `[MISMATCH]` — wrong operator type (e.g., file says OR but XML has ALT), wrong mandatory flag
- `[TYPO]` — name differs only in capitalisation or spelling
- `[CONSTRAINT_MISSING]` — a cross-tree constraint in the XML is absent from the constraints table
- `[CONSTRAINT_OBSOLETE]` — a constraint in the file no longer exists in XML

**For the two template files (`Analysis - Template.md` and `analysis-template.md`):**
- `[MISSING]` — a model dimension has no corresponding heading section
- `[OBSOLETE]` — a heading section whose dimension was removed from the XML
- `[TYPO]` — heading name differs from the XML name (e.g., "Sintax" instead of "Syntax", "Evolutionp" instead of "Evolution")
- `[HIERARCHY]` — a heading is at the wrong depth relative to its position in the XML tree

Meta-sections (Goals, Phases, Open Issues, Extra notes, Search Query) are not derived from the model — ignore them.

> **User preference:** The `Benchmarks` section under `Quality Assessment > Metrics` in the analysis templates is intentionally kept even though it has no counterpart in the XML. Do **not** flag it as `[OBSOLETE]` and do **not** remove it.

### Step 3 — Report discrepancies

Print a structured report:

```
## Feature Model Refresh Report — <today's date>

### Parsed model summary
<tree from Step 1>

### Discrepancies found

#### .claude/skills/codebase-map/references/feature-model-dimensions.md
- [MISSING] Feature "X" under dimension "Y"
- [TYPO] "Sintax" should be "Syntax"
- ...
- [OK] (if no issues)

#### .claude/skills/extract-codebases-from-paper/references/feature-model-dimensions.md
...

#### papers/surveys/Analysis - Template.md
...

#### .claude/skills/codebase-map/references/analysis-template.md
...
```

If all files are clean, report "All dependent files are up to date." and **skip Steps 4 and 5 — go directly to Step 6** to update the README registry.

### Step 4 — Ask for approval

Before making any edits, show the user the full set of intended changes (which files will be touched and what will change) and ask for confirmation. Only proceed to Step 5 if the user approves.

### Step 5 — Update discrepant files

**Updating `feature-model-dimensions.md` (both copies must end up identical):**
- Rewrite each section to list the correct features with correct operator annotations.
- Keep the same Markdown structure: numbered top-level sections, bold feature names, parenthetical operator notes (OR / AND / ALT — at least one / mandatory / exactly one).
- Update the **Key Cross-Tree Constraints** table at the bottom to match the XML constraints exactly.
- Do not add prose not derivable from the XML.

**Updating `Analysis - Template.md` and `analysis-template.md` (both copies must end up identical):**
- One `##` / `###` / `####` heading per model dimension/group, following the XML hierarchy depth.
- Body of each section: `[TBD]`.
- Rebuild the TOC at the top to match the updated headings.
- Preserve meta-sections (Goals, Phases, Open Issues, Extra notes, Search Query) — do not remove or rename them.
- Fix heading names to match the XML exactly (correct typos, capitalisation).

### Step 6 — Update `feature_model/README.md`

Read the current `feature_model/README.md`. Add or update a `## Dependent files` section (place it after the existing bullet list) with:

```markdown
## Dependent files

The following files derive their structure from `representation/feature_model.xml`.
Last refreshed: <today's date>

| File | Role | Last updated |
|------|------|--------------|
| `.claude/skills/codebase-map/references/feature-model-dimensions.md` | Schema reference — codebase-map skill | <date> |
| `.claude/skills/extract-codebases-from-paper/references/feature-model-dimensions.md` | Schema reference — extract-codebases-from-paper skill | <date> |
| `papers/surveys/Analysis - Template.md` | Paper analysis template | <date> |
| `.claude/skills/codebase-map/references/analysis-template.md` | Analysis template copy — codebase-map skill | <date> |
```

Rules for the **Last updated** column:
- Files changed in Step 5: set to today's date.
- Files already clean (no discrepancies): keep the previous date if the section already existed; if the section is new, write `<today's date> (no update needed)`.

### Step 7 — Report to the user

Summarise:
- How many files were checked.
- How many were already up to date.
- What was changed in each updated file (bullet list of additions, removals, renames, typo fixes).
- Remind the user to commit the changes.
