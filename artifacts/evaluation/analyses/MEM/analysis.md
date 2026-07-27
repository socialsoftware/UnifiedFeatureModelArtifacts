# Analysis — MEM

Codebase path: ../extracted-codebases/MEM-backend (+ ../extracted-codebases/MEM-frontend)
Date: 2026-06-28

> MEM (Mazlami et al., *Extraction of Microservices from Monolithic Software
> Architectures*, ICWS 2017, `papers/tools/MEM.pdf`) is the reference
> coupling-based extraction model. The public code is split into a Java/Spring
> Boot **backend** (`MEM-backend`, the extractor) that does all the analysis and
> clustering, and an Angular **frontend** (`MEM-frontend`) that renders the
> resulting decomposition graph. All algorithmic findings come from the backend;
> visualisation findings come from the frontend.

---

## Filled Analysis Template

### Goals
- Extract candidate microservices from a monolithic codebase by building a
  weighted **coupling graph** over the monolith's source files and clustering it
  (`services/decomposition/DecompositionService.java:70`).
- Three independent coupling strategies, combined linearly into a single weighted
  graph: **logical** (co-change), **semantic** (textual similarity), and
  **contributor** (shared-author) coupling (`DecompositionService.java:84-115`,
  `graph/LinearGraphCombination.java:59-71`).

### Phases
- **History extraction:** clone the Git repo and replay its commit log into
  `ChangeEvent`s, then clean deleted/renamed files
  (`services/git/HistoryService.java:32-43`, `git/GitClient.java`).
- **Coupling computation:** run whichever of the three engines are enabled
  (`DecompositionService.java:84-115`).
- **Graph combination:** merge per-pair couplings on the same edge and sum their
  (weighted) scores into one `BaseCoupling` graph
  (`LinearGraphCombination.java:59-71`).
- **Clustering:** Minimum Spanning Tree → edge removal → connected components,
  with degree-based splitting of oversized clusters
  (`graph/MSTGraphClusterer.java:31-73`).
- **Evaluation + report:** compute per-service and per-decomposition metrics
  asynchronously and dump a text report
  (`services/evaluation/EvaluationService.java:40-51`,
  `services/reporting/TextFileReport.java:17-44`).
- **Visualisation:** frontend renders the clustered graph with vis.js
  (`MEM-frontend/.../dashboard/graph/graph.component.ts:35-113`).

### Granularity
- Unit of decomposition is the **source file / class**: couplings and graph nodes
  are keyed by file path (`*.java`, `*.py`, `*.rb`)
  (`semanticcoupling/classprocessing/ClassContentVisitor.java:23`,
  `models/graph/ClassNode.java`). Size metrics are reported in *classes* and *LOC*
  (`models/evaluation/MicroserviceMetrics.java:55-61`).
- No method-, package-, entity-, or endpoint-level granularity
  (`[evidence not found]`).

## Representation Collection

### Collector

#### Source

##### Development
- **Version history** — the primary source. Commit history is replayed into
  `ChangeEvent`s and drives both logical and contributor coupling
  (`services/git/HistoryService.java:32-43`, `git/GitClient.java`).
- **Source code** — file *contents* are read for semantic coupling (raw text of
  `.java/.py/.rb` files, import lines filtered)
  (`semanticcoupling/classprocessing/ClassContentVisitor.java:46-58`).
- Database schema: not used (`[evidence not found]`).

##### Runtime
- None. No log traces, profiling, or user-interaction capture
  (`[evidence not found]`).

##### Higher-Level Models / Documentation
- None (`[evidence not found]`).

#### Collection Technique
- **Version analysis** — commit-log replay over the cloned repo
  (`services/git/HistoryService.java:32-35`; logical coupling bins commits into
  time intervals, `logicalcoupling/LogicalCouplingEngine.java:40-64`).
- **Static analysis** — file contents are read and tokenised for TF-IDF semantic
  similarity (`ClassContentVisitor.java:46-58`,
  `semanticcoupling/tfidf/TfIdfWrapper.java`). This is shallow static reading
  (lexical token extraction), not AST/dependency analysis.
- No dynamic or model analysis (`[evidence not found]`).

## Representation

### Analytical

#### Structure
- No structural code analysis (no call graph, inheritance, or association edges
  are extracted). The "edges" in the graph are coupling weights, not structural
  dependencies (`LinearGraphCombination.java:59-71`). Inner/inter structure:
  `[evidence not found]`.

#### Behavior
- None — no runtime behaviour, frequency, CPU/memory/response-time data
  (`[evidence not found]`).

#### Evolution
- **By task (commit-based co-change)** — logical coupling: files that change
  together within the same time interval get a coupling score
  (`LogicalCouplingEngine.java:40-64`).
- **By contributor (author-based co-change)** — contributor coupling: files
  sharing authors get a similarity score
  (`contributors/ContributorCouplingEngine.java:23-62`).

### Type
- **Monolith** — the coupling graph is a graph of the monolith's files
  (`graph/MSTGraphClusterer.java:31`, `models/graph/ClassNode.java`).
- **Microservices** — output is a set of `Component`/`Microservice` clusters
  representing the target services (`models/graph/Decomposition.java`,
  `models/graph/Microservice.java`, `conversion/GraphRepresentation.java`).

### Visualization

#### Elements
- **Granularity view** — individual class/file nodes are drawn
  (`graph.component.ts:64-81`).
- **Cluster view** — nodes are grouped into per-component clusters via
  `network.cluster(...)`, expandable on click
  (`graph.component.ts:88-112`).

#### Relations
- **Structural relationship** — edges between clustered nodes are drawn
  (`graph.component.ts:70-81`; edges produced by
  `conversion/GraphRepresentationConverter.java:18-34`). These are the coupling
  edges, the only relation type rendered. No separate control-flow / data-flow
  views (`[evidence not found]`).

## Refactoring

### Domain Knowledge

#### Aggregation Criteria
- **Task** — logical (commit) co-change coupling
  (`LogicalCouplingEngine.java:40-64`).
- **Contributor** — shared-author coupling
  (`ContributorCouplingEngine.java:48-62`).
- **Lexical** — semantic coupling via TF-IDF cosine similarity over file tokens
  (`SemanticCouplingEngine.java:41-50`, `tfidf/TfIdfWrapper.java`).
- Functional / Adjacency: not used (`[evidence not found]`).

#### Expert knowledge
- None — the strategy toggles, target service count, interval, and split
  threshold are numeric parameters, not domain rules/annotations
  (`models/DecompositionParameters.java:22-32`). No expert-knowledge input
  (`[evidence not found]`).

### Services Refactoring

#### Algorithms
- **Minimum Spanning Tree + edge-cutting → connected components**: build an MST of
  the coupling graph, then iteratively remove the highest-distance edges until the
  target number of connected components is reached
  (`MSTGraphClusterer.java:75-108`, `graph/MinimumSpanningTree.java`,
  `graph/ConnectedComponents.java`).
- **Degree-based splitting** of clusters that exceed the size threshold: remove
  the highest-degree node and re-compute connected components
  (`MSTGraphClusterer.java:59-73`).
- This MST + highest-distance-edge-removal is a *divisive* (top-down) graph partitioning. It is the tool's only decomposition algorithm and maps only loosely onto the model's vocabulary; it is mapped to **Hierarchical clustering (Unclear)** as the closest divisive-hierarchical fit rather than left absent, which would erase the tool's sole algorithm — see Model Gap Candidates and Model Vocabulary Fit.
  - Just a new algorithm, it should not be confused with the model's Hierarchical clustering (agglomerative) or Community detection (modularity-based) algorithms, which are absent.

#### Manual Editing
- None — clusters cannot be merged/split/transferred by the user; the only
  controls are pre-run parameters (`DecompositionParameters.java`, `graph.component.ts`).
  (`[evidence not found]`).

### Functionality Refactoring
- None — no asynchronisation or granularity-refinement post-processing
  (`[evidence not found]`).

## Quality Assessment

### Metrics

#### Single Decomposition
- **Elements size** — average LOC and average number of classes per service
  (`DecompositionEvaluationService.java:44-45`,
  `MicroserviceMetrics.java:55-61`).
- **Team size** — contributors per microservice and contributor overlap across
  services (`DecompositionEvaluationService.java:42-43`,
  `MicroserviceMetrics.java:51-53`).
- Coupling/Cohesion: indirectly present as **inter-service similarity** (TF-IDF
  similarity between services, a proxy for cohesion/coupling)
  (`DecompositionEvaluationService.java:74-88`,
  `MicroserviceSimilarityService.java:31-35`) — see Vocabulary Fit. 
  - Not really the same thing, **inter-service similarity** should be other metric
- Complexity:
  `[evidence not found]`.

#### Several Decompositions
- No MoJoFM and no cross-decomposition comparison metric
  (`[evidence not found]`). Metrics are computed per decomposition only.

### Graphical Comparison
- No comparison-of-decompositions view. The frontend draws a single decomposition;
  per-cluster **colour** is assigned to distinguish services
  (`conversion/GraphRepresentationConverter.java:40`,
  `utils/HexColorGenerator.java`) — this is colour-coding within one
  decomposition, not a comparison between decompositions.
    - Visualization, not comparison, so Yellow

## Open Issues
- Semantic coupling is O(n²) over all file pairs (`SemanticCouplingEngine.java:41-47`)
  and contributor coupling likewise (`ContributorCouplingEngine.java:28-44`);
  scalability is a noted concern for large repos.

## Extra notes
- Strategy weights (`logicalCouplingFactor`, etc.) exist in the combination class
  but are hard-wired to 1 and not exposed in `DecompositionParameters`
  (`LinearGraphCombination.java:19-23`, `:44-57`).

---

## Feature Coverage Table

| Feature | Dimension | Supported | Evidence |
|---------|-----------|-----------|----------|
| Method | Granularity | No | [evidence not found] |
| Class | Granularity | Yes | `ClassContentVisitor.java:23` (file/class unit); `models/graph/ClassNode.java` |
| Entity | Granularity | No | [evidence not found] |
| Functionality | Granularity | No | [evidence not found] |
| Package | Granularity | No | [evidence not found] |
| API endpoint | Granularity | No | [evidence not found] |
| Source code | Repr. Collection > Source > Development | Yes | `ClassContentVisitor.java:46-58` (reads `.java/.py/.rb` contents) |
| Database schema | Repr. Collection > Source > Development | No | [evidence not found] |
| Version history | Repr. Collection > Source > Development | Yes | `services/git/HistoryService.java:32-43` |
| Runtime log traces | Repr. Collection > Source > Runtime | No | [evidence not found] |
| User interactions | Repr. Collection > Source > Runtime | No | [evidence not found] |
| Business process model | Repr. Collection > Source > Higher-Level Models | No | [evidence not found] |
| Use case | Repr. Collection > Source > Higher-Level Models | No | [evidence not found] |
| Data flow diagram | Repr. Collection > Source > Higher-Level Models | No | [evidence not found] |
| Directly in the code | Repr. Collection > Source > Documentation | No | [evidence not found] |
| Paper document | Repr. Collection > Source > Documentation | No | [evidence not found] |
| Digital format | Repr. Collection > Source > Documentation | No | [evidence not found] |
| Static analysis | Repr. Collection > Collection Technique | Yes | `ClassContentVisitor.java:46-58`, `tfidf/TfIdfWrapper.java` (lexical token extraction) |
| Dynamic analysis | Repr. Collection > Collection Technique | No | [evidence not found] |
| Version analysis | Repr. Collection > Collection Technique | Yes | `HistoryService.java:32-35`; `LogicalCouplingEngine.java:40-64` |
| Model analysis | Repr. Collection > Collection Technique | No | [evidence not found] |
| External | Repr. Collection > External | No | [evidence not found] |
| Inner structure | Representation > Analytical > Structure | No | [evidence not found] |
| Inheritance | Representation > Analytical > Structure > Inter | No | [evidence not found] |
| Association | Representation > Analytical > Structure > Inter | No | [evidence not found] |
| Call graph | Representation > Analytical > Behavior | No | [evidence not found] |
| Sequence of accesses | Representation > Analytical > Behavior | No | [evidence not found] |
| Frequency | Representation > Analytical > Behavior | No | [evidence not found] |
| CPU level | Representation > Analytical > Behavior | No | [evidence not found] |
| Memory level | Representation > Analytical > Behavior | No | [evidence not found] |
| Response time | Representation > Analytical > Behavior | No | [evidence not found] |
| By contributor | Representation > Analytical > Evolution | Yes | `ContributorCouplingEngine.java:65-83` |
| By task | Representation > Analytical > Evolution | Yes | `LogicalCouplingEngine.java:40-64` |
| Monolith | Representation > Type | Yes | `MSTGraphClusterer.java:31`; `models/graph/ClassNode.java` |
| Microservices | Representation > Type | Yes | `models/graph/Microservice.java`; `models/graph/Decomposition.java` |
| Granularity view | Representation > Visualization > Elements | Yes | `graph.component.ts:64-81` |
| Cluster view | Representation > Visualization > Elements | Yes | `graph.component.ts:88-112` |
| Structural relationship | Representation > Visualization > Relations | Yes | `graph.component.ts:70-81`; `GraphRepresentationConverter.java:18-34` |
| Control flow | Representation > Visualization > Relations | No | [evidence not found] |
| Data flow | Representation > Visualization > Relations | No | [evidence not found] |
| Task | Refactoring > Domain Knowledge > Aggregation Criteria | Yes | `LogicalCouplingEngine.java:40-64` |
| Contributor | Refactoring > Domain Knowledge > Aggregation Criteria | Yes | `ContributorCouplingEngine.java:48-62` |
| Lexical | Refactoring > Domain Knowledge > Aggregation Criteria | Yes (⚠ violation) | `SemanticCouplingEngine.java:41-50`; `tfidf/TfIdfWrapper.java` — TF-IDF over raw source text; no Structure/Call graph/Sequence representation present (constraint `Lexical → Structure OR Call graph OR Sequence of accesses` unsatisfied) |
| Functional | Refactoring > Domain Knowledge > Aggregation Criteria | No | [evidence not found] |
| Adjacency | Refactoring > Domain Knowledge > Aggregation Criteria | No | [evidence not found] |
| Expert knowledge | Refactoring > Domain Knowledge | No | [evidence not found] (`DecompositionParameters.java:22-32` — numeric params only) |
| Hierarchical clustering | Refactoring > Services Refactoring > Algorithms | Unclear | `MSTGraphClusterer.java:75-108` (MST + iterative highest-distance edge removal until target component count — a *divisive* top-down partitioning that fits the hierarchical-clustering label only loosely; the closest model vocabulary for the tool's sole algorithm) |
| Community detection | Refactoring > Services Refactoring > Algorithms | No | [evidence not found] |
| K-means++ | Refactoring > Services Refactoring > Algorithms | No | [evidence not found] |
| Formal concept analysis | Refactoring > Services Refactoring > Algorithms | No | [evidence not found] |
| Genetic algorithms | Refactoring > Services Refactoring > Algorithms | No | [evidence not found] |
| Hungarian algorithm | Refactoring > Services Refactoring > Algorithms | No | [evidence not found] |
| Merge of clusters | Refactoring > Services Refactoring > Manual Editing | No | [evidence not found] |
| Splitting of clusters | Refactoring > Services Refactoring > Manual Editing | No | [evidence not found] (degree-split is automatic, `MSTGraphClusterer.java:59-73`, not user-driven) |
| Transfer of elements between clusters | Refactoring > Services Refactoring > Manual Editing | No | [evidence not found] |
| Asynchronization | Refactoring > Functionality Refactoring | No | [evidence not found] |
| Granularity refinement | Refactoring > Functionality Refactoring | No | [evidence not found] |
| Coupling | Quality Assessment > Metrics > Single | Unclear | Indirect: inter-service TF-IDF similarity, `DecompositionEvaluationService.java:74-88` |
| Cohesion | Quality Assessment > Metrics > Single | Unclear | Indirect: inter-service TF-IDF similarity (proxy), `MicroserviceSimilarityService.java:31-35` |
| Elements size | Quality Assessment > Metrics > Single | Yes | `DecompositionEvaluationService.java:44-45`; `MicroserviceMetrics.java:55-61` |
| Complexity | Quality Assessment > Metrics > Single | No | [evidence not found] |
| Team size | Quality Assessment > Metrics > Single | Yes | `DecompositionEvaluationService.java:42-43`; `MicroserviceMetrics.java:51-53` |
| MoJoFM | Quality Assessment > Metrics > Several | No | [evidence not found] |
| Compare metrics | Quality Assessment > Metrics > Several | No | [evidence not found] |
| Color | Quality Assessment > Graphical Comparison | Unclear | Per-cluster colour within one decomposition, `GraphRepresentationConverter.java:40`; not a comparison across decompositions |
| Sizes | Quality Assessment > Graphical Comparison | No | [evidence not found] |
| Distance between elements | Quality Assessment > Graphical Comparison | No | [evidence not found] |

---

## Observations

### Model Gap Candidates

- **MST / edge-cutting graph clustering**
  - **Would be:** leaf under Refactoring > Services Refactoring > Algorithms
  - **Evidence:** `MSTGraphClusterer.java:75-108` (Minimum Spanning Tree of the
    coupling graph, then remove highest-distance edges until target component
    count); `graph/MinimumSpanningTree.java`, `graph/ConnectedComponents.java`.
  - **Rationale:** This is the tool's core decomposition algorithm and matches
    none of the six listed algorithms — it is a graph-theoretic MST/min-cut
    family distinct from hierarchical agglomerative clustering and community
    detection.

- **Degree-based cluster splitting**
  - **Would be:** leaf under Refactoring > Services Refactoring (a post-clustering
    size-balancing step, sibling of Algorithms)
  - **Evidence:** `MSTGraphClusterer.java:59-73` (remove highest-degree node from
    oversized cluster and recompute components).
  - **Rationale:** An automatic structural refinement of cluster sizes that is
    neither user-driven Manual Editing nor one of the listed algorithms.

- **Inter-service similarity (decomposition quality proxy)**
  - **Would be:** leaf under Quality Assessment > Metrics > Single Decomposition
    (a cohesion/coupling proxy)
  - **Evidence:** `MicroserviceSimilarityService.java:31-35`,
    `DecompositionEvaluationService.java:74-88` (average pairwise TF-IDF
    similarity between services).
  - **Rationale:** A textual-similarity-based quality signal that maps only
    loosely onto the model's structural Coupling/Cohesion vocabulary.

- **Contributor overlap across services**
  - **Would be:** leaf under Quality Assessment > Metrics > Single Decomposition
    (a Team-size-related metric)
  - **Evidence:** `DecompositionEvaluationService.java:56-64`,
    `:91-95`.
  - **Rationale:** Measures how many contributors are shared between services — a
    socio-technical metric beyond the headcount captured by Team size.

### Other features outside the model

- **Linear coupling combination with per-strategy weights** — three coupling
  scores summed into one edge weight, each multiplied by a (currently fixed)
  factor (`LinearGraphCombination.java:59-71`, `:19-23`). Too implementation-specific
  to be a model feature, but notable as a multi-criteria aggregation mechanism.
- **Text-file report export** — a plain-text dump of `service id | classes`
  (`TextFileReport.java:17-44`). A trivial export, below the model's scope.
- **History cleaning (deleted/renamed file reconciliation)** — pre-processing of
  the commit log (`HistoryService.java:38-117`). A data-hygiene step, not a model
  dimension.

### Model Vocabulary Fit

- **Static analysis** is technically selected (file contents are read and
  tokenised), but MEM's "static analysis" is purely *lexical* — it never parses
  code structure (no AST, call graph, or dependency edges). The model's Static
  analysis node carries an implicit structural connotation that overstates what
  MEM does. The bundled ANTLR runtime (`lib/antlr4-runtime-4.5.3.jar`) is not used
  for source parsing in this path.
- **Coupling / Cohesion** metrics: MEM has no structural coupling/cohesion metric.
  Its only quality signal is *textual* inter-service similarity
  (`MicroserviceSimilarityService.java:31-35`), so the mapping is a proxy, marked
  Unclear.
- **Lexical aggregation criterion** fits the semantic-coupling strategy descriptively (TF-IDF over tokenised file content), but it derives from *raw source text*, not from a Structure / Call graph / Sequence-of-accesses representation. The model requires Lexical to be backed by one of those, so this is recorded as a cross-tree constraint violation (see below) rather than a clean fit — the model's vocabulary does not allow purely text-derived lexical coupling without an underlying structural representation.

### Cross-tree constraint violations

- ***Lexical → Structure OR Call graph OR Sequence of accesses*** — **VIOLATED.** MEM's Lexical (semantic) coupling is TF-IDF over *raw file text* read line by line (`ClassContentVisitor.java:46-58` reads file contents, filtering imports; `TfIdfWrapper.java`). No Structure (Inner structure / Association), Call graph, or Sequence-of-accesses representation is built — all are `No` in the table, and
  MEM never parses code structure (no AST/dependency analysis). So the antecedent for Lexical is unsatisfied: tokenising raw text is *not* a Structure representation in the model's sense. `Lexical` is marked Orange in the profile.
- *Task → By task (Evolution)* and *Contributor → By contributor (Evolution)*: both Evolution sub-features are present (`LogicalCouplingEngine`, `ContributorCouplingEngine`), so the aggregation criteria are well-grounded.
- *Team size → By contributor (Evolution)*: satisfied (`MicroserviceMetrics.java:51-53`).
- *Static analysis → Source code*: satisfied (`ClassContentVisitor.java:46-58`).
- *Version analysis → Version history*: satisfied (`HistoryService.java:32-35`).
- No Expert-knowledge feature is used, so the
  *Community detection / FCA → NOT Expert knowledge* constraints are not at risk
  (and neither algorithm is used anyway).

### Noteworthy design decisions

- **Evolution-first, not structure-first.** Unlike most static extraction tools,
  MEM's primary signal is the *version history* (logical + contributor coupling).
  Source code is read only for the optional semantic-similarity strategy. This
  makes MEM a strong exemplar of the Evolution branch of the feature model.
- **Composable strategies.** Any subset of the three couplings can be enabled and
  are fused into one weighted graph (`DecompositionService.java:84-115`), which is
  exactly the kind of *variability* the feature model is meant to capture.
- **MST + min-cut clustering** rather than agglomerative hierarchical or
  community detection — a deliberately simple graph-theoretic approach with a
  target-service-count knob and an automatic size-split safeguard.
- **Two-repo split.** All analysis is in the backend; the frontend is a thin
  vis.js visualiser. The decomposition is fully usable headlessly via
  `main/Main.java` without the frontend.

---

## Reconciliation Log

Date: 2026-06-28
Versions compared: f9c6d41, 29f7dfc, cc53285, d9b7b1c (working tree)

Two verdicts changed; the rest were confirmed against the codebase under `../extracted-codebases/MEM-backend` (+ `MEM-frontend`).

<!-- prettier-ignore-start -->
| Feature | From → To | Adjudicating evidence | Which version(s) were wrong |
|---------|-----------|-----------------------|-----------------------------|
| Lexical | Yes → Yes (⚠ violation, Orange) | `ClassContentVisitor.java:20-58` reads **raw file text** (line-by-line, imports filtered); TF-IDF runs over that text via `TfIdfWrapper.java`. No Structure / Call graph / Sequence-of-accesses representation exists (all `No` in the table), so the constraint `Lexical → Structure OR Call graph OR Sequence of accesses` is unsatisfied. | d9b7b1c (working tree) had dropped the violation cc53285 correctly flagged |
| Hierarchical clustering | No → Unclear (Magenta) | `MSTGraphClusterer.java:75-108` — MST + iterative removal of highest-distance edges until the target component count: a *divisive* top-down partitioning. It is the tool's only algorithm and fits the hierarchical label loosely; marking it absent would force the mandatory Algorithms group (and Refactoring/root) Red and erase that MEM clearly does decompose. | f9c6d41/d9b7b1c marked No; cc53285's Unclear was closer |
<!-- prettier-ignore-end -->

Confirmed unchanged against ground truth this run:

- **Coupling = Unclear, Cohesion = Unclear** (Magenta) — the only quality signal is inter-service TF-IDF *similarity* (`MicroserviceSimilarityService.java:31-35` → `TfIdfWrapper.computeSimilarity`), a textual proxy, not a structural coupling/cohesion metric.
- **Color = Unclear** (Magenta) — `GraphRepresentationConverter.java:40` / `HexColorGenerator` assign a per-cluster hex colour *within one* decomposition (`colorGenerator.getNextColor()`), not a cross-decomposition comparison encoding. (cc53285's plain `Yes` overstated it.)
- **Elements size = Yes** (`MicroserviceMetrics.java:55-61` — `getSizeInLoc`, `getSizeInClasses`); **Team size = Yes** (`getNumOfContributors`).
- **By task = Yes** (`LogicalCouplingEngine.java:40-64`), **By contributor = Yes** (`ContributorCouplingEngine.java`), **Version analysis = Yes** (`HistoryService.java:32-35`), **Static analysis = Yes** (lexical token read, `ClassContentVisitor.java:46-58`).
- **Visualization** — Granularity view + Cluster view + Structural relationship = Yes (frontend `graph.component.ts`).

Cross-tree constraints re-verified: `Task → By task`, `Contributor → By contributor`, `Team size → By contributor`, `Static analysis → Source code`, `Version analysis → Version history` all satisfied; no Expert knowledge, so no Community-detection/FCA conflict. The one violation is **Lexical → Structure/Call graph/Sequence (VIOLATED)**, recorded above.

Features still genuinely Unclear after adjudication: `Hierarchical clustering` (divisive MST/min-cut, loose fit), `Coupling`, `Cohesion` (textual-similarity proxies), `Color` (single-decomposition colour-coding, not comparison).


### Profile fix (2026-06-28) — AND "fully satisfied" propagation rule

**Profile-only change; no analysis content was reviewed or altered in this pass.** A
cross-cutting correction to the group-propagation rule (made explicit in `codebase-map`,
`docs-map`, `verify-analysis`) was applied to `MEM.profile`: an AND node is only
`Dark_Green` ("Group: fully satisfied") when every **mandatory** child is fully
satisfied — a present **leaf** counts (`Light_Green` is a leaf's max; leaves are never
`Dark_Green`), but a mandatory child **group** that is only `Light_Green` (partially
satisfied) caps the AND parent at `Light_Green`. The previous derivation treated a merely
*present* mandatory child group as enough for `Dark_Green`, overstating coverage.

AND cells changed `Dark_Green` → `Light_Green` in `MEM.profile`: `Collector`, `Visualization`, `Representation`, `Services Refactoring`, `Quality Assessment`. (Nodes
already at a higher-priority colour — `Red`/`Orange`/`Magenta` — were unaffected; AND
nodes whose mandatory child is a present leaf, e.g. `Type`, correctly stay `Dark_Green`.)
