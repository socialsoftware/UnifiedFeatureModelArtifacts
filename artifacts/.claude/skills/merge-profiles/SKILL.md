---
name: merge-profiles
description: Use when the user says "merge profiles", "run merge-profiles", or wants to produce a union profile that combines tool profiles. With no argument it merges every analysed tool into all-tools.profile. Given a paper name (a file in evaluation/papers/) it merges only that paper's tools into <paper>.profile. Given a list of tool names it merges just those into a custom-named profile. Reads per-tool .profile files in feature_model/representation/.profiles/ and writes a union profile reflecting what the chosen set of tools collectively covers.
allowed-tools: Read, Write, Bash
---

# merge-profiles

Produce a **union profile** — a merge of a chosen set of per-tool profiles in `feature_model/representation/.profiles/`.

The merge **algorithm** (Steps 1–7) is identical in every mode. Only the **source set** and the **output filename** change, both decided in Step 0.

## Source-set rule

The source set is **always per-tool profiles only**. Never feed a derived union profile (`all-tools.profile`, `wang.profile`, a per-paper profile, or a custom-subset profile) back into a merge: a union can carry a leaf color that no single tool has, so re-feeding one inflates the result.

The authoritative list of per-tool profiles is the set of tool directories under `evaluation/analyses/` — each `evaluation/analyses/<tool>/` maps 1:1 (case-sensitively) to `feature_model/representation/.profiles/<tool>.profile`. Any `.profile` with no matching analyses directory (e.g. `all-tools`, `wang`) is a derived union and is excluded automatically.

## Procedure

### Step 0 — Determine mode, source set, and output path

Inspect the skill argument:

**Mode A — No argument → all tools.**
Source set = `<tool>.profile` for every tool directory under `evaluation/analyses/`:

```bash
ls -1 evaluation/analyses/ | while read t; do echo "feature_model/representation/.profiles/$t.profile"; done
```

Output: `feature_model/representation/.profiles/all-tools.profile`.

**Mode B — Argument names a paper** (it matches a file `evaluation/papers/<Name>.md`, e.g. `Wang2024`, `Lopes2023`, `Zhong2025`) → that paper's tools.
Read `evaluation/papers/<Name>.md` and extract the tools from its **Analysis** column — each cell links to `../analyses/<tool>/README.md`. Rows whose Analysis cell is `—` have no analysis and no profile, so they are skipped automatically (they produce no link). Confirm each derived profile file exists before using it.

```bash
grep -oE 'analyses/[^/]+/README\.md' evaluation/papers/<Name>.md | sed -E 's#analyses/([^/]+)/README\.md#\1#' | sort -u
```

Output: `feature_model/representation/.profiles/<Name>.profile` (e.g. `Wang2024.profile`).

**Mode C — Argument is a list of tool names** (e.g. `mono2micro Micro2Micro`) → exactly those tools.
For each name, the source profile is `feature_model/representation/.profiles/<name>.profile`. Match names case-insensitively against the per-tool profiles (the `evaluation/analyses/` directories) and resolve to the real filename; if a name has no matching per-tool profile, stop and tell the user. Require **at least two** tools (a one-tool "merge" is just that tool's own profile).

Output filename: if the user supplied an output name, use it. Otherwise join the resolved tool names with `+` in the order given, e.g. `mono2micro+Micro2Micro.profile`.

In every mode, **list the resolved source set and the output path back to the user and confirm before writing** (project rule: ask before editing). If the argument is ambiguous — a name that is neither a paper file nor a known tool — ask rather than guess.

### Step 1 — Read source profiles

Read each source profile resolved in Step 0. Parse every line of the form `<feature>=<color>` (stop before `featureColorMeaning` lines). Build a map `{ feature → [color, color, ...] }` collecting the color from each profile.

### Step 2 — Identify leaves and groups

Use the feature tree below (derived from `feature_model/representation/feature_model.xml`) to classify each feature as a **leaf** or **group**, and record its mandatory flag and parent group type.

**Leaves** (no children — take merged color directly):

| Feature | Mandatory |
|---------|-----------|
| Method | no |
| Class | no |
| Entity | no |
| Functionality | no |
| Package | no |
| API Endpoint | no |
| Source code | no |
| Database schema | no |
| Version history | no |
| Runtime log traces | no |
| User interactions | no |
| Business process model | no |
| Use case | no |
| Data flow diagram | no |
| Directly in the code | no |
| Paper document | no |
| Digital format | no |
| External | no |
| Static analysis | no |
| Dynamic analysis | no |
| Version analysis | no |
| Model analysis | no |
| Inner structure | no |
| Inheritance | no |
| Association | no |
| Call graph | no |
| Sequence of accesses | no |
| Frequency | no |
| CPU level | no |
| Memory level | no |
| Response time | no |
| By contributor | no |
| By task | no |
| Monolith | no |
| Microservices | no |
| Structural relationship | no |
| Control flow | no |
| Data flow | no |
| Cluster view | no |
| Granularity view | **yes** |
| Task | no |
| Contributor | no |
| Lexical | no |
| Functional | no |
| Adjacency | no |
| Expert knowledge | no |
| Hierarchical clustering | no |
| Community detection | no |
| K-means++ | no |
| Formal concept analysis | no |
| Genetic algorithms | no |
| Hungarian algorithm | no |
| Merge of clusters | no |
| Splitting of clusters | no |
| Transfer of elements between clusters | no |
| Asynchronization | no |
| Granularity refinement | no |
| Coupling | no |
| Cohesion | no |
| Elements size | **yes** |
| Complexity | no |
| Team size | no |
| MoJoFM | **yes** |
| Compare metrics | no |
| Color | no |
| Sizes | no |
| Distance between elements | no |

**Groups** (have children — color is re-derived from children):

| Group | Type | Mandatory | Mandatory children |
|-------|------|-----------|-------------------|
| Microservices Decomposition and Refactoring | AND | yes | Granularity, Representation Collection, Representation, Refactoring, Quality Assessment |
| Granularity | OR | yes | — |
| Representation Collection | OR | yes | — |
| Collector | AND | no | Source, Collection Technique |
| Source | OR | yes | — |
| Development | OR | no | — |
| Runtime | OR | no | — |
| Higher-Level Models | OR | no | — |
| Documentation | OR | no | — |
| Collection Technique | OR | yes | — |
| Representation | AND | yes | Analytical, Type, Visualization |
| Analytical | OR | yes | — |
| Structure | OR | no | — |
| Inter Structure | OR | no | — |
| Behavior | OR | no | — |
| Evolution | OR | no | — |
| Type | AND | yes | Microservices |
| Visualization | AND | yes | Elements, Relations |
| Elements | AND | yes | Granularity view |
| Relations | OR | yes | — |
| Refactoring | AND | yes | Domain Knowledge, Services Refactoring |
| Domain Knowledge | AND | yes | Aggregation Criteria |
| Aggregation Criteria | OR | yes | — |
| Services Refactoring | AND | yes | Algorithms |
| Algorithms | OR | yes | — |
| Manual Editing | OR | no | — |
| Functionality Refactoring | OR | no | — |
| Quality Assessment | AND | yes | Metrics |
| Metrics | OR | yes | — |
| Single Decomposition | AND | no | Elements size |
| Several Decompositions | AND | no | MoJoFM |
| Graphical Comparison | OR | no | — |

### Step 3 — Compute merged color for each leaf

For each leaf feature, look at its color across all source profiles and apply this priority (highest wins):

```
Light_Green > Magenta > Orange > Red > Yellow
```

- If **any** profile has `Light_Green` → assign `Light_Green`
- Else if **any** has `Magenta` → assign `Magenta`
- Else if **any** has `Orange` → assign `Orange`
- Else if **any** has `Red` → assign `Red`
- Else → assign `Yellow`

### Step 4 — Re-derive group colors bottom-up

Starting from the deepest groups, work up to the root. A child counts as **present** if its color is `Light_Green`, `Magenta`, or `Dark_Green` (`Yellow` and `Red` are *not* present). A `Magenta` child is present but **not fully satisfied** (indirect/unclear evidence, `featureColorMeaning8`): uncertainty in a *mandatory* child propagates up and **outranks** `Light_Green` — confirmed sibling leaves do not rescue the group.

**The leaf/group cap principle** (governs when a group reaches full `Dark_Green` satisfaction). `Dark_Green` is only valid for **group** nodes, never for leaves, so a leaf can never be more than `Light_Green`:

- A **leaf** child at `Light_Green` is **fully satisfied** (that is the best a leaf can be) and does **not** cap the parent. If every required child of a group is a leaf at `Light_Green`, the group is `Dark_Green`.
- A **group** child at only `Light_Green` is **partially satisfied** (it could have been `Dark_Green` but isn't) and **does cap** the parent at `Light_Green`. This holds for **both AND and OR** parents.
- An **absent (`Yellow`) optional leaf** in an **AND** group caps the parent at `Light_Green`: an AND group reaches `Dark_Green` only when *all* its leaf children (mandatory and optional) are present. (A leaf that *exists* = `Light_Green` does not cap; only its absence does.)

For each group, evaluate its direct children's merged colors and apply these rules in order (priority: `Red > Orange > Magenta > Light_Green > Yellow`):

1. **Mandatory group with any mandatory child not present** (Red, Yellow, or otherwise absent) → `Red`. This applies to every **mandatory** group with mandatory children, AND or OR, and it **outranks `Orange`**: a broken mandatory child is the most severe state. **Scope: `Red` is reserved for *mandatory* groups.** An **optional** group whose own mandatory child is broken/absent does **not** become `Red` — it degrades to `Yellow` per rule 5 (nothing required it, so its breakage is not a violation). Example: `Several Decompositions` is optional with a mandatory `MoJoFM` leaf; when `MoJoFM` is absent the group is `Yellow`, not `Red`, even if a sibling optional leaf is present.
2. **Any child is `Orange`** (and no mandatory child is missing) → `Orange`
3. **Any mandatory child is `Magenta`** — or, for any group (AND or OR), the only present child(ren) are `Magenta` (every confirmed branch is absent/Red) → `Magenta`. Uncertainty in a required child propagates up; confirmed sibling leaves do not rescue the group.
4. **≥1 child is present** (and no mandatory child missing, `Magenta`, or `Orange`) — apply the leaf/group cap principle above:
   - AND group → `Dark_Green` only if every mandatory child is fully satisfied (leaf = `Light_Green`, group = `Dark_Green`) **and** no optional leaf is absent (`Yellow`); otherwise cap at `Light_Green` (a mandatory child *group* at `Light_Green`, or any absent optional leaf, caps it).
   - OR/ALT group → `Dark_Green` only if **all** children are present **and** every present *group* child is itself `Dark_Green`; if all present but some present group child is only `Light_Green`, cap at `Light_Green`; if only **some** children are present, `Light_Green`.
5. **Zero present children** (all children are `Yellow` or `Red`) → `Yellow` (if optional) or `Red` (if mandatory).

**When the rules are genuinely ambiguous for a feature, ask the user how to resolve it — do NOT consult another merged/derived profile (`all-tools.profile`, a `<paper>.profile`, a custom-subset profile) to settle the question.** Derived profiles may have been produced under older rules and can be stale/wrong; treating them as precedent propagates errors. The per-tool source profiles and `feature_model.xml` are the only authoritative inputs.

**Bottom-up evaluation order** (children before parents):

```
Leaves first, then:
Inter Structure → Structure
Behavior
Evolution
Analytical (from Structure, Behavior, Evolution)
Type (from Monolith, Microservices)
Elements (from Granularity view, Cluster view)
Relations
Visualization (from Elements, Relations)
Representation (from Analytical, Type, Visualization)
Development → Runtime → Higher-Level Models → Documentation → Source
Collection Technique
Collector (from Source, Collection Technique)
Representation Collection (from Collector, External)
Aggregation Criteria
Domain Knowledge (from Aggregation Criteria, Expert knowledge)
Algorithms
Manual Editing
Functionality Refactoring
Services Refactoring (from Algorithms, Manual Editing)
Refactoring (from Domain Knowledge, Services Refactoring, Functionality Refactoring)
Single Decomposition → Several Decompositions → Metrics
Graphical Comparison
Quality Assessment (from Metrics, Graphical Comparison)
Granularity
Microservices Decomposition and Refactoring (root)
```

### Step 5 — Write the output profile

Write the output profile resolved in Step 0 (`all-tools.profile`, `<paper>.profile`, or the custom-subset name).

- First line: `false`
- Lines 2–103: one `feature=color` per line, in the **same order** as the existing profiles (use MOSAIC.profile as the ordering reference)
- Lines 104–112: the standard legend:

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

### Step 6 — Print the verification table

Before the summary, print a **Markdown table** so the merge can be eyeballed for mistakes. Output it directly in chat (do not write it to a file).

- **One row per feature**, in the same profile order used for the output file (the MOSAIC.profile ordering).
- **One column per source tool** (the resolved source set, in the order resolved in Step 0), holding that tool's color for the feature — or `—` if the feature is absent from that tool's profile.
- A leading **Feature** column and, as the **last column**, **Merged** = the final merged color written to the output profile.
- Keep group rows in the table too (their Merged value is the re-derived group color from Step 4); this is what makes bottom-up mistakes visible.

Use the short color names verbatim (`Light_Green`, `Magenta`, `Orange`, `Red`, `Yellow`, `Dark_Green`). Example shape:

```
| Feature | mono2micro | Micro2Micro | Merged |
|---------|------------|-------------|--------|
| Method  | Light_Green | Yellow     | Light_Green |
| ...     | ...         | ...        | ...         |
```

### Step 7 — Report to the user

After the table, summarise:
- Which mode ran and which tools were merged (the resolved source set)
- How many source profiles were merged
- How many leaves ended up Light_Green, Magenta, Orange, Red, Yellow
- Any notable observations (e.g., features that are Red in every profile = universal gap)
- Path to the output file

## Reference files

- **`feature_model/representation/.profiles/`** — source profiles (read) and output location (write)
- **`evaluation/analyses/`** — one directory per analysed tool; defines the authoritative per-tool source set (Mode A and name resolution)
- **`evaluation/papers/<Name>.md`** — paper tool-inventory files; the Analysis column maps a paper to its tools (Mode B)
- **`feature_model/representation/feature_model.xml`** — canonical feature model (leaf/group structure)
