# Analysis — HyDec

Codebase path: ../extracted-codebases/HyDec
Date: 2026-06-28

---

## Filled Analysis Template

### Goals

- Implements two decomposition approaches: **HierDec** (static-only) and **HyDec** (static + dynamic hybrid), recommending a target microservice for each class/method of a monolithic Java application (`README.md — "suggests the recommended microservices for each class in the system"`, `hydec/hydec.py:12-15`).
- The shipped implementation is a *generalization* of the paper: an extensible analysis pipeline where each "representation" (structural, semantic, dynamic) is an `AbstractAnalysis` plugged into a hierarchical DBSCAN clustering loop (`hydec/analysis/abstractAnalysis.py:7`, `hydec/hybridDecomp.py:10`).

### Phases

1. **Data collection** — structural call matrix, semantic TF-IDF vectors, and dynamic call matrix are loaded from disk, a gRPC parsing service, or the `decparsing` module (`hydec/dataHandler.py:47-152`).
2. **Analysis construction** — each representation becomes an analysis object; `hyDec` pipeline = `["dynamic", ["structural", "semantic"]]`, `hierDec` = `[["structural", "semantic"]]` (`hydec/hydec.py:12-15`).
3. **Hierarchical clustering** — alternating / alternating_epsilon / sequential strategies run DBSCAN layer by layer, aggregating clusters between layers (`hydec/hybridDecomp.py:59-127`).
4. **Output** — per-layer cluster assignments written to `layers.csv` plus metadata JSON (`hydec/experiment.py:112-124`).

### Granularity

- **Class** and **Method** are both supported and validated by the CLI/API (`hydec/hydec.py:26` `assert granularity in ["class", "method"]`, `cli.py:41-42`).
- The unit being clustered is an "atom" = class or method name (`hydec/hybridDecomp.py:18`, `hydec/dataHandler.py:154-171`).

## Representation Collection

### Collector

#### Source

##### Development

- **Source code** — structural call graph and semantic TF-IDF are derived from parsing the Java source via external analysis/parsing services (`README.md — "analyzes the source code of a monolithic Java application through static analysis and a TFIDF based pipeline"`, `hydec/clients/parsingClient.py:46-63`).
- No database-schema or version-history collection.

##### Runtime

- **Runtime log traces** — the dynamic representation is an MxM class-call matrix built from execution traces (`README.md — "class_calls.npy ... the calls from each class to the others in the execution traces"`, `hydec/dataHandler.py:47-67`). The README notes generating this is manual and not automated (`README.md — "generating dynamic analysis results is required and is not automated"`).

##### Higher-Level Models

- [evidence not found]

##### Documentation

- [evidence not found]

#### Collection Technique

- **Static analysis** — structural calls and TF-IDF semantics come from static source-code parsing (`hydec/clients/parsingClient.py:46-63`, `hydec/dataHandler.py:69-125`).
- **Dynamic analysis** — the dynamic call matrix is collected from runtime execution traces (`hydec/dataHandler.py:47-67`, `hydec/hydec.py:13`).
- No version or model analysis.

## Representation

### Analytical

#### Structure

- **Association (calls)** — both the static and dynamic representations are class-to-class *call* matrices; similarity is computed from incoming-call overlap (`hydec/analysis/dependencyAnalysis.py:11-39`, `hydec/analysis/similarity.py:4-16`).
- Inner structure / inheritance: not represented; the matrices capture call relations only.

#### Behavior

- **Call graph** — the dynamic representation is a runtime call matrix (`README.md — "the calls from each class to the others in the execution traces"`, `hydec/dataHandler.py:47-67`); the static representation is also a call matrix (`hydec/dataHandler.py:69-93`).
- No frequency / CPU / memory / response-time signals are used (the matrix is treated as call presence/weight, not profiled metrics).

#### Evolution

- [evidence not found] — no version history or co-change.

### Type

- **Monolith** — the input atoms and call/TF-IDF matrices represent the monolith (`hydec/hybridDecomp.py:46-49`).
- **Microservices** — the output layers assign each atom to a recommended microservice cluster (`hydec/experiment.py:112-119`, `README.md — "suggests the recommended microservices"`).

### Visualization

#### Elements

- [evidence not found] — output is CSV/JSON only (`hydec/experiment.py:116-122`); no granularity or cluster view.

#### Relations

- [evidence not found]

## Refactoring

### Domain Knowledge

#### Aggregation Criteria

- **Adjacency** — structural and dynamic clustering is driven by call coupling between atoms (`hydec/analysis/dependencyAnalysis.py:38-39`, `hydec/analysis/similarity.py:4-16`).
- **Lexical** — semantic clustering uses cosine similarity over TF-IDF vectors (`hydec/analysis/tfidfAnalysis.py:40-42`).
- **Functional** — partial/indirect: call-graph adjacency drives grouping, but there is no explicit use-case / functional-cohesion criterion. Treated as Unclear.
  - not really used to calculate similarity

#### Expert knowledge

- [evidence not found] — clustering is fully automatic; the only human inputs are hyperparameters (epsilons, strategy), not domain rules.

### Services Refactoring

#### Algorithms

- **Hierarchical clustering** — a hierarchical DBSCAN: clusters are aggregated layer by layer, re-running DBSCAN on the aggregated representation with incrementing epsilon (`hydec/hybridDecomp.py:59-127`, `README.md — "a hierarchical version of the DBSCAN algorithm"`).
- DBSCAN itself is from scikit-learn with `metric="precomputed"` on a 1−similarity distance matrix (`hydec/hybridDecomp.py:71-72`).
- No community detection, k-means++, FCA, genetic, or Hungarian algorithms.

#### Manual Editing

- [evidence not found] — no merge/split/transfer operations exposed.

### Functionality Refactoring

- [evidence not found] — no asynchronization or granularity-refinement post-processing.

## Quality Assessment

### Metrics

#### Single Decomposition

- **Not active.** An `EvaluationHandler` with coupling/cohesion-style metrics existed but is entirely commented out (`hydec/experiment.py:79-93`, `126-153`). No metric is computed in the shipped pipeline.

#### Several Decompositions

- [evidence not found] — no MoJoFM or comparative metric in the code (evaluation block disabled).

#### Benchmarks

- [evidence not found]

### Graphical Comparison

- [evidence not found]

## Open Issues

- Evaluation/metrics code is fully commented out; quality assessment is performed externally (in the papers' experiments), not by the tool.
- Dynamic data generation is out of scope of this repo and manual.

## Extra notes

- The hybrid combination of representations is itself a design dimension (alternating / sequential strategies, plus a weighted `SumAnalysis`) not captured by the model — see Model Gap Candidates.

---

## Feature Coverage Table

| Feature | Dimension | Supported | Evidence |
|---------|-----------|-----------|----------|
| Method | Granularity | Yes | `hydec/hydec.py:26`; `cli.py:41-42` |
| Class | Granularity | Yes | `hydec/hydec.py:26`; `cli.py:41-42` |
| Entity | Granularity | No | [evidence not found] |
| Functionality | Granularity | No | [evidence not found] |
| Package | Granularity | No | [evidence not found] |
| API endpoint | Granularity | No | [evidence not found] |
| Source code | Repr. Collection > Source > Development | Yes | `hydec/clients/parsingClient.py:46-63` |
| Database schema | Repr. Collection > Source > Development | No | [evidence not found] |
| Version history | Repr. Collection > Source > Development | No | [evidence not found] |
| Runtime log traces | Repr. Collection > Source > Runtime | Yes | `hydec/dataHandler.py:47-67` (`README.md — "calls ... in the execution traces"`) |
| User interactions | Repr. Collection > Source > Runtime | No | [evidence not found] |
| Business process model | Repr. Collection > Source > Higher-Level Models | No | [evidence not found] |
| Use case | Repr. Collection > Source > Higher-Level Models | No | [evidence not found] |
| Data flow diagram | Repr. Collection > Source > Higher-Level Models | No | [evidence not found] |
| Directly in the code | Repr. Collection > Source > Documentation | No | [evidence not found] |
| Paper document | Repr. Collection > Source > Documentation | No | [evidence not found] |
| Digital format | Repr. Collection > Source > Documentation | No | [evidence not found] |
| Static analysis | Repr. Collection > Collection Technique | Yes | `hydec/dataHandler.py:69-125`; `hydec/clients/parsingClient.py:46-63` |
| Dynamic analysis | Repr. Collection > Collection Technique | Yes | `hydec/dataHandler.py:47-67`; `hydec/hydec.py:13` |
| Version analysis | Repr. Collection > Collection Technique | No | [evidence not found] |
| Model analysis | Repr. Collection > Collection Technique | No | [evidence not found] |
| External | Repr. Collection | No | [evidence not found] |
| Inner structure | Representation > Analytical > Structure | No | [evidence not found] |
| Inheritance | Representation > Analytical > Structure > Inter Structure | No | [evidence not found] |
| Association | Representation > Analytical > Structure > Inter Structure | Yes | `hydec/analysis/dependencyAnalysis.py:38-39`; `hydec/analysis/similarity.py:4-16` |
| Call graph | Representation > Analytical > Behavior | Yes | `hydec/dataHandler.py:47-67` (`README.md — "calls ... in the execution traces"`) |
| Sequence of accesses | Representation > Analytical > Behavior | No | [evidence not found] |
| Frequency | Representation > Analytical > Behavior | No | [evidence not found] |
| CPU level | Representation > Analytical > Behavior | No | [evidence not found] |
| Memory level | Representation > Analytical > Behavior | No | [evidence not found] |
| Response time | Representation > Analytical > Behavior | No | [evidence not found] |
| By contributor | Representation > Analytical > Evolution | No | [evidence not found] |
| By task | Representation > Analytical > Evolution | No | [evidence not found] |
| Monolith | Representation > Type | Yes | `hydec/hybridDecomp.py:46-49` |
| Microservices | Representation > Type | Yes | `hydec/experiment.py:112-119` (`README.md — "suggests the recommended microservices"`) |
| Granularity view | Representation > Visualization > Elements | No | [evidence not found] |
| Cluster view | Representation > Visualization > Elements | No | [evidence not found] |
| Structural relationship | Representation > Visualization > Relations | No | [evidence not found] |
| Control flow | Representation > Visualization > Relations | No | [evidence not found] |
| Data flow | Representation > Visualization > Relations | No | [evidence not found] |
| Task | Refactoring > Aggregation Criteria | No | [evidence not found] |
| Contributor | Refactoring > Aggregation Criteria | No | [evidence not found] |
| Lexical | Refactoring > Aggregation Criteria | Yes | `hydec/analysis/tfidfAnalysis.py:40-42` |
| Functional | Refactoring > Aggregation Criteria | Unclear | call-graph adjacency drives grouping but no explicit functional-cohesion criterion (`hydec/analysis/similarity.py:4-16`) |
| Adjacency | Refactoring > Aggregation Criteria | Yes | `hydec/analysis/dependencyAnalysis.py:38-39` |
| Expert knowledge | Refactoring > Domain Knowledge | No | [evidence not found] |
| Hierarchical clustering | Refactoring > Services Refactoring > Algorithms | Yes | `hydec/hybridDecomp.py:59-127` (`README.md — "a hierarchical version of the DBSCAN algorithm"`) |
| Community detection | Refactoring > Services Refactoring > Algorithms | No | [evidence not found] |
| K-means++ | Refactoring > Services Refactoring > Algorithms | No | [evidence not found] |
| Formal concept analysis | Refactoring > Services Refactoring > Algorithms | No | [evidence not found] |
| Genetic algorithms | Refactoring > Services Refactoring > Algorithms | No | [evidence not found] |
| Hungarian algorithm | Refactoring > Services Refactoring > Algorithms | No | [evidence not found] |
| Merge of clusters | Refactoring > Services Refactoring > Manual Editing | No | [evidence not found] |
| Splitting of clusters | Refactoring > Services Refactoring > Manual Editing | No | [evidence not found] |
| Transfer of elements between clusters | Refactoring > Services Refactoring > Manual Editing | No | [evidence not found] |
| Asynchronization | Refactoring > Functionality Refactoring | No | [evidence not found] |
| Granularity refinement | Refactoring > Functionality Refactoring | No | [evidence not found] |
| Coupling | Quality Assessment > Metrics > Single Decomposition | No | evaluation code commented out (`hydec/experiment.py:79-93`) |
| Cohesion | Quality Assessment > Metrics > Single Decomposition | No | evaluation code commented out (`hydec/experiment.py:79-93`) |
| Elements size | Quality Assessment > Metrics > Single Decomposition | No | [evidence not found] |
| Complexity | Quality Assessment > Metrics > Single Decomposition | No | [evidence not found] |
| Team size | Quality Assessment > Metrics > Single Decomposition | No | [evidence not found] |
| MoJoFM | Quality Assessment > Metrics > Several Decompositions | No | [evidence not found] |
| Compare metrics | Quality Assessment > Metrics > Several Decompositions | No | [evidence not found] |
| Color | Quality Assessment > Graphical Comparison | No | [evidence not found] |
| Sizes | Quality Assessment > Graphical Comparison | No | [evidence not found] |
| Distance between elements | Quality Assessment > Graphical Comparison | No | [evidence not found] |

---

## Observations

### Model Gap Candidates

- **Hybrid representation combination strategy**
  - **Would be:** group (with leaf children like *Alternating*, *Sequential*, *Weighted sum*) under Refactoring, near Services Refactoring / Aggregation Criteria.
  - **Evidence:** `hydec/hybridDecomp.py:27` (`ALLOWED_STRATEGIES = ["alternating", "alternating_epsilon", "sequential"]`), `hydec/analysis/sumAnalysis.py:30-45`.
  - **Rationale:** the core HyDec contribution is *how* multiple aggregation criteria (adjacency + lexical + dynamic) are combined into one clustering; the model captures *which* criteria are used but not the combination policy.

- **Hierarchical / layered output (decomposition layers)**
  - **Would be:** leaf under Representation > Type or a new "Output" facet, distinct from a single flat decomposition.
  - **Evidence:** `hydec/hybridDecomp.py:65-79`, `hydec/experiment.py:116-119` (`layers.csv` with one row per layer).
  - **Rationale:** the tool emits a *hierarchy* of decompositions at increasing granularity, not a single partition; the model assumes a single target decomposition.

- **Outlier handling**
  - **Would be:** leaf under Refactoring > Services Refactoring.
  - **Evidence:** `hydec/hybridDecomp.py:146-159` (`tag_outliers`), `min_samples` parameter.
  - **Rationale:** DBSCAN-based methods explicitly model atoms that belong to no service (outliers tagged −1), a decision dimension absent from the model.

### Other features outside the model

- **Epsilon / epsilon-step hyperparameters** controlling cluster granularity per layer (`hydec/hybridDecomp.py:26`, `hydec/utils/default_hyperparams.py:56-62`) — too tool-specific (DBSCAN tuning).
- **gRPC service architecture / `decparsing` module integration** for sourcing parsed data (`hydec/clients/parsingClient.py`, `hydec/clients/decParsingClient.py`) — a deployment concern, not a decomposition feature.
- **Two similarity functions for call matrices** (`call` vs `cousage`) (`hydec/analysis/similarity.py:4-30`) — implementation detail of the Adjacency criterion.

### Model Vocabulary Fit

- **Static vs dynamic call graph:** the model's *Call graph* lives under Behavior, but HyDec's *structural* call matrix is collected by static analysis (a structural association). The same data structure (call matrix) serves both a static-structural and a dynamic-behavioural role here, which the model's split between Structure (Association) and Behavior (Call graph) does not cleanly express. Mapped both Association (structural) and Call graph (dynamic) as Yes.
- **Aggregation Criteria > Functional:** ambiguous — call-graph coupling is the basis for grouping, but there is no explicit functional/use-case notion, so it is marked Unclear rather than Yes.
- **Hierarchical clustering:** the model lists "Hierarchical clustering" as an algorithm; HyDec's is a hierarchical *DBSCAN* (density-based), which fits the label but is a specific variant the vocabulary does not distinguish.

### Cross-tree constraint violations

None found.
- Static analysis → requires Source code: satisfied (`hydec/dataHandler.py:69-125`).
- Dynamic analysis → requires Runtime (Runtime log traces): satisfied (`hydec/dataHandler.py:47-67`).
- Call graph → requires Static OR Dynamic analysis: satisfied.
- Lexical → requires Structure OR Call graph OR Sequence of accesses: satisfied (TF-IDF over source structure + call graph present).
- Adjacency → requires Behavior OR Structure: satisfied.
- No Expert knowledge is used, so no Community-detection / FCA conflict arises.

### Noteworthy design decisions

- **Generalized, pluggable pipeline.** Each representation is an `AbstractAnalysis` subclass implementing `aggregate` + `calculate_similarity`, so new representations can be added without touching the clustering core (`hydec/analysis/abstractAnalysis.py:7-71`, `README.md — "implement your own Analysis class"`). This makes HyDec a *framework* for hybrid clustering, not just a fixed algorithm.
- **Density-based, parameter-light boundaries.** Using DBSCAN (vs k or cut-count) means the number of services emerges from epsilon/density rather than being fixed up front, and atoms with too few neighbours are flagged as outliers (`hydec/hybridDecomp.py:146-159`).
- **Quality assessment deliberately external.** The metric/evaluation machinery is present but commented out (`hydec/experiment.py:79-153`); the tool produces decompositions and leaves scoring to the paper's experimental harness — a notable gap for a standalone tool.
- **Dynamic data is a hard dependency for HyDec but not automated** (`README.md — "not possible with HyDec because generating dynamic analysis results is required and is not automated"`), so in practice HierDec (static-only) is the turnkey path.

---

## Reconciliation Log

Date: 2026-06-28
Versions compared: 7f30d44, 29f7dfc, cc53285, d9b7b1c (working tree)

No coverage-table verdicts changed; all claims confirmed against the codebase under `../extracted-codebases/HyDec`. The two oldest versions (7f30d44, 29f7dfc) used the pre-rename model vocabulary and had disagreed on three features, but those were already corrected in cc53285/d9b7b1c, which the current table matches:

| Feature | Stale verdict (old versions) | Reconciled verdict | Adjudicating evidence |
|---------|------------------------------|--------------------|-----------------------|
| Microservices | No (7f30d44, 29f7dfc) | Yes | `hydec/experiment.py:120` (`layers` cluster output); `hydec/hybridDecomp.py:129-144` |
| Hierarchical clustering | No (7f30d44, 29f7dfc) | Yes | `hydec/hybridDecomp.py:59-150` — DBSCAN run layer by layer (layered/hierarchical aggregation) |
| Community detection | Yes — "DBSCAN" (7f30d44, 29f7dfc) | No | DBSCAN is density-based, not graph-modularity community detection; the layered structure makes Hierarchical clustering the correct label |

Spot-checks confirmed against ground truth this run: `Frequency`/`CPU`/`Memory`/`Response time` = No (grep for those signals in `hydec/` is empty; matrices hold call presence/weights only); `Sequence of accesses` = No (aggregated M×M matrix, no ordering); `Inner structure` = No (TF-IDF is bag-of-tokens, not class-internal composition); `Functional` = Unclear (call-graph coupling drives grouping but there is no explicit use-case/functional-cohesion criterion); `Lexical` = Yes (`hydec/analysis/tfidfAnalysis.py:41` cosine over TF-IDF); `Adjacency` = Yes (`hydec/analysis/similarity.py:4-30`, `hydec/analysis/dependencyAnalysis.py`); metrics all No (evaluation block commented out, `hydec/experiment.py:79-155`).

Cross-tree constraints: none violated (re-verified — no Expert knowledge, so no Community-detection/FCA conflict; Static→Source code, Dynamic→Runtime log traces, Call graph→Static/Dynamic, Lexical→Structure/Call graph, Adjacency→Behavior/Structure all satisfied).

Profile re-derived from the (unchanged) table and **corrected** for group-colour propagation bugs that did not follow the propagation rules:

| Group | From → To | Reason |
|-------|-----------|--------|
| Visualization | Red → Yellow | Optional group, entirely unused by HyDec → absent-optional (Yellow); internal mandatory Reds do not propagate past the optional boundary |
| Relations | Yellow → Red | Mandatory OR group with zero present children → broken internally (Red); the Red stops at the optional Visualization parent |
| Representation | Red → Light_Green | Mandatory child Type is satisfied (Dark_Green); Visualization absent-optional must not force Red; some-but-not-all children present → Light_Green |
| Single Decomposition | Red → Yellow | Optional AND group, zero present children (HyDec computes no metrics) → absent-optional (Yellow) |
| Several Decompositions | Red → Yellow | Optional AND group, zero present children → absent-optional (Yellow) |
| Collector | Light_Green → Dark_Green | Mandatory AND group with all children present (Source + Collection Technique) → fully satisfied (Dark_Green) |

`Metrics` (Red) and `Quality Assessment` (Red) are correct as-is: Metrics is a *mandatory* OR group with zero present children (no metric of any kind), so it is genuinely broken, and that Red legitimately propagates to the mandatory Quality Assessment and the root.

Features still genuinely Unclear after adjudication: `Functional` (Magenta) — call-graph coupling is the grouping basis but there is no explicit functional/use-case criterion.


### Profile fix (2026-06-28) — AND "fully satisfied" propagation rule

**Profile-only change; no analysis content was reviewed or altered in this pass.** A
cross-cutting correction to the group-propagation rule (made explicit in `codebase-map`,
`docs-map`, `verify-analysis`) was applied to `HyDec.profile`: an AND node is only
`Dark_Green` ("Group: fully satisfied") when every **mandatory** child is fully
satisfied — a present **leaf** counts (`Light_Green` is a leaf's max; leaves are never
`Dark_Green`), but a mandatory child **group** that is only `Light_Green` (partially
satisfied) caps the AND parent at `Light_Green`. The previous derivation treated a merely
*present* mandatory child group as enough for `Dark_Green`, overstating coverage.

AND cells changed `Dark_Green` → `Light_Green` in `HyDec.profile`: `Collector`, `Representation`, `Domain Knowledge`, `Services Refactoring`, `Refactoring`. (Nodes
already at a higher-priority colour — `Red`/`Orange`/`Magenta` — were unaffected; AND
nodes whose mandatory child is a present leaf, e.g. `Type`, correctly stay `Dark_Green`.)
