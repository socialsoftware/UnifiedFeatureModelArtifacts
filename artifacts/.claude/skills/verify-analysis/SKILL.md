---
name: verify-analysis
description: This skill should be used when the user says "verify analysis <tool>", "verify all analyses", "reconcile analysis <tool>", "run verify-analysis on <tool>", or wants an existing tool analysis audited and fixed against its cited evidence and prior versions. Reconciles evaluation/analyses/<tool>/analysis.md and re-derives feature_model/representation/.profiles/<tool>.profile. Never modifies my_paper/text.md.
allowed-tools: Read, Write, Bash, WebFetch
---

# verify-analysis

Audit and **reconcile** an existing tool analysis produced by `codebase-map` or `docs-map`,
fixing it against (1) the actual cited evidence and (2) its own prior versions in git.

## Why this skill exists

`codebase-map` and `docs-map` are **non-deterministic**: re-running them on the same tool
produces materially different output, and coverage-table verdicts (Yes / No / Unclear) flip
between runs. This skill is **not another generator** — it does not resample a fresh
analysis. It is a **checker/reconciler** anchored to two stable references: the evidence on
disk/URL, and the set of prior versions in git. Disagreements are resolved by re-reading the
cited evidence, which is deterministic: a given `file:line` either supports a verdict or it
does not. The goal is that repeated runs **converge** instead of diverge.

## Determinism guardrails (apply throughout)

- **Do not generate new verdicts from scratch.** Only confirm or correct existing ones
  against cited evidence.
- **A verdict may only be changed when a specific `file:line`/URL is read and shown to
  contradict it.** Record that evidence in the Reconciliation Log.
- **When evidence is genuinely ambiguous, prefer `Unclear` (leaf colour `Magenta`) and say
  so — never flip a coin.** Ambiguous must stay ambiguous across reruns.
- **The profile is a pure function of the final coverage table.** An identical table must
  yield an identical profile.

## Inputs

- A tool name, e.g. `verify analysis CARGO`. The set of analysed tools lives in
  `evaluation/analyses/`.
- Or `verify all analyses` — iterate the procedure over every directory under
  `evaluation/analyses/` that contains an `analysis.md`.

Resolve `evaluation/analyses/<tool>/analysis.md`. Detect the source type by reading its
header line:
- `Codebase path:` → **codebase-sourced** (ground truth = local files under
  `../extracted-codebases/<tool>`).
- `Documentation:` → **docs-sourced** (ground truth = the cited URLs).

If the analysis does not exist on disk, stop and tell the user to run `codebase-map` /
`docs-map` first — this skill reconciles existing analyses, it does not create them.

## Output files

- `evaluation/analyses/<tool>/analysis.md` — reconciled in place (table + prose + a new
  Reconciliation Log).
- `feature_model/representation/.profiles/<tool>.profile` — re-derived from the corrected
  table.
- `evaluation/analyses/<tool>/README.md` — **left untouched** unless a link is broken
  (see Step 6).

**Never modify** `my_paper/text.md`, `feature_model/representation/feature_model.xml`, or
any *other* tool's analysis/README/profile.

## Procedure

### Step 1 — Gather all versions

List every historical version of the analysis (search all refs, not just current branch):

```bash
git log --oneline --all -- evaluation/analyses/<tool>/analysis.md
```

For each commit, read that version:

```bash
git show <sha>:evaluation/analyses/<tool>/analysis.md
```

Always include the **current on-disk version** too. If there is only one version in
history, the audit reduces to checking that version's claims against evidence (Step 3 still
applies to every feature, not just disagreements).

### Step 2 — Build a per-feature verdict matrix across versions

Read `.claude/skills/codebase-map/references/feature-model-dimensions.md` for the full leaf
list. For every leaf feature, collect each version's verdict (Yes / No / Unclear) and the
evidence it cited. Tabulate them side by side.

**Flag every feature where versions disagree** — these are the non-determinism hotspots that
need adjudication. Features where all versions agree are presumed stable, but spot-check a
representative sample (and any feature whose evidence looks weak or generic) against ground
truth anyway.

### Step 3 — Adjudicate against ground truth (the deterministic core)

For each feature being adjudicated, work **in this order**:

1. **Read the analysis prose / justification first**, across all versions that disagree.
   The justification tells you *what claim* each version is making and *what concept to go
   look for*. Without it you risk misreading a cited `file:line` because you don't know what
   it was meant to support. The prose frames the question.

2. **Open the cited evidence** with that understanding:
   - **Codebase-sourced:** re-open each cited `file:line` in `../extracted-codebases/<tool>`,
     grep/Read around it, and check whether it actually supports the claim the prose
     describes. If a version cited no usable reference, search the codebase for the concept
     before concluding absence.
   - **Docs-sourced:** re-fetch the cited URL with `WebFetch`. If `WebFetch` returns an HTTP
     error (403/401/429/5xx) or an empty/blocked response, fall back to `curl | strip_html`
     (the same pattern as `docs-map` Step 1) and do not retry `WebFetch` for that domain.
     Confirm the quote exists and supports the claim.

3. **Decide.** The evidence answers the question the prose posed. The file/URL only
   *overrides* the prose when the two genuinely conflict — the analysis cannot assert
   something the code/docs contradict. This does **not** replace reading the prose.

Resolve each feature to a single correct verdict plus the strongest evidence reference,
applying the evidence-precedence and confidence rules the existing skills define:
- Code reference > documentation reference; cite the artifact (CSV/AST node/solver object)
  over a README quote when both exist.
- `Unclear` (→ `Magenta`) for indirect/vague evidence; `No` (→ `Yellow`/`Red`) only when you
  are confident the feature is absent.
- Also re-check **cross-tree constraint violations** (see the dimensions reference; the
  common one is `Community detection → NOT Expert knowledge`).

### Step 4 — Rewrite analysis.md so the whole document is consistent

Update the file so prose and table agree on the reconciled verdicts:
- **Coverage Table** — corrected verdicts + strongest evidence per leaf.
- **Filled Analysis Template** — prose adjusted to match (template structure:
  `.claude/skills/codebase-map/references/analysis-template.md`).
- **Observations** — Model Gap Candidates, Other features outside the model, Model
  Vocabulary Fit, Cross-tree constraint violations, Noteworthy design decisions — adjusted
  to match.

Keep section structure intact so diffs stay reviewable. Update the `Date:` header to today.

Append a new section at the end:

```
## Reconciliation Log

Date: <today's date>
Versions compared: <list of commit SHAs + "working tree">

| Feature | From → To | Adjudicating evidence | Which version(s) were wrong |
|---------|-----------|-----------------------|-----------------------------|
| K-means++ | Unclear → Yes | `src/cluster/kmeans.py:31` | run cc53285 marked Unclear |
| ... | ... | `file:line` or `<url> — "quote"` | ... |

Features still genuinely Unclear after adjudication: <list, with why>.
```

If no verdict changed, still write the log with a row-free table and the note
"No verdicts changed; all claims confirmed against evidence." and use the project's
no-change date convention.

### Step 5 — Re-derive the .profile from the corrected table

Rewrite `feature_model/representation/.profiles/<tool>.profile` as a pure function of the
final coverage table. Use the **exact** colour scheme and group-propagation rules from
`codebase-map`/`docs-map` Step 8.

**Leaves:**

| Situation | Colour |
|-----------|--------|
| Leaf exists (confirmed) | `Light_Green` |
| Leaf exists but unclear / indirect evidence | `Magenta` |
| Leaf absent, optional | `Yellow` |
| Leaf absent, mandatory | `Red` |
| Leaf present but causes a cross-tree constraint violation | `Orange` |

`Dark_Green` is valid for **group nodes only**, never leaves.

**Groups** (propagate up, priority `Red > Orange > Magenta > Light_Green > Yellow`):
1. Evaluate each child first.
2. Mandatory group with any mandatory child `Red` → `Red`.
3. Else any child `Orange` → `Orange`.
4. Else if any mandatory child is `Magenta` — or, for an OR group, the only present
   child(ren) are `Magenta` (every confirmed branch is absent/Red) → `Magenta`.
   Uncertainty in a required child propagates up; **confirmed sibling leaves do not
   rescue the group.**
5. Else ≥1 mandatory child confirmed present (Light_Green/Dark_Green) — or, for an OR
   group, ≥1 child confirmed present — and no mandatory child missing or `Magenta` →
   `Light_Green` (OR) or keep evaluating (AND).
6. AND group with **all mandatory** children **fully satisfied** and no violations →
   `Dark_Green`. A child is *fully satisfied* when it is a **leaf that is present**
   (`Light_Green` — a leaf's max, never `Dark_Green`) **or a group that is itself
   `Dark_Green`**. A mandatory child **group** that is only `Light_Green` (partial)
   caps the AND parent at `Light_Green`. (Optional children that are absent or
   `Magenta` do not block `Dark_Green`.)
7. Optional group with zero present children → `Yellow`.

Format: flat `key=value` text; first line is `false`; feature names must match exactly the
leaf and group names in `feature_model/representation/feature_model.xml`. Include **every**
leaf and group. End with the legend:

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

### Step 6 — README.md (touch only if a link breaks)

Leave `evaluation/analyses/<tool>/README.md` untouched. Verify its Relevant-Files /
source links resolve; if one is now broken, fix only that link.

### Step 7 — Report to the user

Summarise:
- How many versions were compared and how many features disagreed.
- Which features' verdicts changed (from → to) with the adjudicating evidence.
- Features still genuinely `Unclear` after adjudication.
- Any cross-tree constraint violations.
- Paths to the modified files.

For `verify all analyses`, report a per-tool summary line plus the totals.

## Reference files

- **`.claude/skills/codebase-map/references/feature-model-dimensions.md`** — full feature
  model schema with cross-tree constraints (reused, not duplicated).
- **`.claude/skills/codebase-map/references/analysis-template.md`** — the analysis template
  structure (reused).
- **`feature_model/representation/feature_model.xml`** — canonical feature model (exact leaf
  and group names for the profile).
- **`feature_model/representation/.profiles/`** — existing profiles for format reference.
