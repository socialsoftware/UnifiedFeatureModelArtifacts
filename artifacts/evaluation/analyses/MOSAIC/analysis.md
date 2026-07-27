# Analysis — MOSAIC

Codebase path: `../extracted-codebases/MOSAIC`
Date: 2026-06-28

---

## Filled Analysis Template

### Goals

Automatically identify microservice candidates from a monolithic Java (Spring/MyBatis) system by combining graph clustering (Louvain community detection) with combinatorial optimization (ILP minimizing inter-service coupling). Published at IEEE ICSA 2023 (`readme.md:1-6`).

### Phases

1. **System analysis** (`1-System_analysis.ipynb`): static parsing of Java source into a directed graph of methods and entities with typed edges (Calls/Persists/Uses/References/Extends).
2. **Decomposition & optimization** (`2-Decomposition_optimization.ipynb`): Louvain clustering of the weighted graph + Gurobi ILP that assigns nodes to microservices minimizing coupling.

### Granularity

- **Method** — graph nodes of type `Method`, one per method declaration (`1-System_analysis.ipynb` Cell `22303794` — `nodes_file.write(... 'Method,' ...)`).
- **Entity** — graph nodes of type `Entity`, one per entity class (`1-System_analysis.ipynb` Cell `22303794` — `nodes_file.write(... 'Entity,' ...)`).
- Classes are also a working unit: the analysis classifies each class as Logic / Repository / Entity / Interface (`1-System_analysis.ipynb` Cell `c72fd4fc`), and the SOTA comparison clusters at the *class* level (`applications/spring-petclinic/results/sota_approaches/springpetclinic-comparison.ipynb` Cell `333f7f00` — class-name dictionaries).
  - MOSAIC never assigns classes to microservices, so no.

## Representation Collection

### Collector

#### Source

##### Development

- **Source code** — Java `.java` files walked from the project source directory and parsed (`1-System_analysis.ipynb` Cell `a97c9013` — `filename.endswith('.java')`; Cell `f449eb89` — `javalang.parse.parse(...)`).
- Database schema: [evidence not found] — persistence is inferred from `@Repository`/Spring Data interfaces, not from a DB schema.
- Version history: [evidence not found].

##### Runtime

- [evidence not found] — purely static; no logs, traces, or runtime instrumentation.

##### Higher-Level Models

- [evidence not found].

##### Documentation

- [evidence not found] — annotations are read as code structure, not as documentation.

#### Collection Technique

- **Static analysis** — AST parsing of Java source with the bundled `javalang` library (`1-System_analysis.ipynb` Cell `f449eb89`; `javalang/parse.py`). No dynamic, version, or model analysis.

## Representation

### Analytical

#### Structure

- **Inner structure** — field declarations of each class are collected to map variable names to types (`1-System_analysis.ipynb` Cell `2f676ad4` — `get_field_declarations_with_varnames`, `FieldDeclaration`).
- **Inheritance** — entity `extends` relationships become `Extends` edges (`1-System_analysis.ipynb` Cell `2ec5871f` — `collect_inheritance`; Cell `63eb996a` — `',Extends,'`).
- **Association** — field references between entities (`References`), method-to-entity usage (`Uses`), and repository persistence (`Persists`) edges (`1-System_analysis.ipynb` Cell `63eb996a`).

#### Behavior

- **Call graph** — method-to-method invocations are resolved through class-variable type tracking and emitted as `Calls` edges (`1-System_analysis.ipynb` Cell `d6e603ab` — `inspect_method_invocation`; Cell `63eb996a` — `',Calls,'`).
- Sequence of accesses / Frequency / CPU / Memory / Response time: [evidence not found] — no ordering or runtime quantities are captured.

#### Evolution

- [evidence not found] — no commit/author history is used.

### Type

- **Monolith** — a `networkx.DiGraph` of the monolith with typed/weighted edges (`1-System_analysis.ipynb` Cell `be873f87` — `G = nx.DiGraph()`; persisted as `*_graph.gml`).
- **Microservices** — the ILP solution assigns each node to a microservice `k`, written to `*_sol_*.csv` (`2-Decomposition_optimization.ipynb` Cell `3519b123` — `results_csv.write(f'{i},{k}\n')`).

### Visualization

#### Elements

- **Granularity view** — the full node/edge graph is drawn and displayed (`1-System_analysis.ipynb` Cell `be873f87` — `DrawInitialGraph`, `*_graph.png`).
- **Cluster view** — the solution graph colours each node by its microservice (`2-Decomposition_optimization.ipynb` Cell `63ce5fa3` — `DrawSol`, per-cluster `colors[k]`).

#### Relations

- **Structural relationship** — `References`/`Extends`/`Uses` edges drawn between nodes (`1-System_analysis.ipynb` Cell `be873f87`).
- **Control flow** — `Calls` edges (drawn in black) represent invocation flow (`2-Decomposition_optimization.ipynb` Cell `63ce5fa3` — `rel_type in ['Calls','Persists','References']`).
- **Data flow** — `Persists`/`Uses` edges represent data access/persistence relationships (`1-System_analysis.ipynb` Cell `63eb996a`).

## Refactoring

### Domain Knowledge

#### Aggregation Criteria

- **Adjacency** — edges carry weights per relationship type and clustering/optimization minimize cross-cluster weighted coupling (`2-Decomposition_optimization.ipynb` Cell `e53fae46` — weight dict; Cell `bceb7240` — `coupling = ... w*(1-y[i,j])`).
- **Functional** — call-graph edges (`Calls`) drive functional cohesion of methods within a service (`1-System_analysis.ipynb` Cell `d6e603ab`; weight `w['Calls']=0.8`).
- Lexical / Task / Contributor: [evidence not found].

#### Expert knowledge

- User-provided **layer refinement** (force/exclude classes & packages as entity/logic/repository) (`1-System_analysis.ipynb` Cell `1a61ce0a`).
- User-tunable **edge weights** per relationship type (`2-Decomposition_optimization.ipynb` Cell `e53fae46`).
- User **entity-cluster refinement**: remove an entity from a cluster or force it into a chosen cluster (`2-Decomposition_optimization.ipynb` Cell `021636e9` — `entity_ids_to_remove`, `entities_clusters_to_place`).

### Services Refactoring

#### Algorithms

- **Community detection** — Louvain (`community_louvain.best_partition`) on the undirected weighted graph, run both on the whole graph and the entity subgraph (`2-Decomposition_optimization.ipynb` Cell `b1205d9e` and Cell `476f02c9`).
- **ILP / combinatorial optimization** (not in model) — a Gurobi binary program assigns nodes to microservices minimizing coupling, subject to belonging/composition/community constraints (`2-Decomposition_optimization.ipynb` Cell `bceb7240` — `gb.Model()`, `model.setObjective(coupling, GRB.MINIMIZE)`; Cell `081eb8b2` — `model.optimize()`).

#### Manual Editing

- **Transfer of elements between clusters** — entities can be removed from / placed into specific clusters before optimization (`2-Decomposition_optimization.ipynb` Cell `021636e9`).
- Merge / Splitting of clusters: [evidence not found] as explicit operations.

### Functionality Refactoring

- [evidence not found] — no async conversion or service-boundary refinement is produced.

## Quality Assessment

### Metrics

#### Single Decomposition

- **Coupling** — sum of weights of inter-microservice edges; also the ILP objective (`2-Decomposition_optimization.ipynb` Cell `bceb7240`; Cell `b4f4589c` — `Total coupling value`).
- **Cohesion** — per-microservice inside/outside weight ratio, averaged (`2-Decomposition_optimization.ipynb` Cell `78f5ab5d` — `cohesion_dict[k] = inside_w[k]/outside_w[k]`).
- **Elements size** — number of microservices found and entities per microservice are reported (`2-Decomposition_optimization.ipynb` Cell `b4f4589c` — `Found {n_micros} microservices`, per-service entity lists).
- Complexity / Team size: [evidence not found].

#### Several Decompositions

- **Compare metrics** — the SOTA comparison notebook recomputes coupling/cohesion and cross-microservice counts for external decompositions (baseline, Kamimura) over the same graph (`applications/spring-petclinic/results/sota_approaches/springpetclinic-comparison.ipynb` Cell `af954790`; `sota_approaches/kamimura.txt`, `baseline.txt`).
- MoJoFM: [evidence not found].

#### Benchmarks

- Four bundled systems serve as evaluation cases: spring-petclinic, jpetstore, springblog, cargo-tracking (`projects.json`).

### Graphical Comparison

- **Color** — clusters/microservices are distinguished by node colour in the solution graph (`2-Decomposition_optimization.ipynb` Cell `63ce5fa3` — `colors` list applied per cluster `k`); the SOTA notebook colours nodes by external partition too (`springpetclinic-comparison.ipynb` Cell `63ce5fa3`).
- Sizes / Distance between elements: [evidence not found] as comparison encodings.

---

## Feature Coverage Table

| Feature | Dimension | Supported | Evidence |
|---------|-----------|-----------|----------|
| Method | Granularity | Yes | `1-System_analysis.ipynb` Cell `22303794` |
| Class | Granularity | Unclear | Class-level role classification & class-based SOTA clustering, but graph nodes are Method/Entity (`springpetclinic-comparison.ipynb` Cell `333f7f00`) |
| Entity | Granularity | Yes | `1-System_analysis.ipynb` Cell `22303794` |
| Functionality | Granularity | No | [evidence not found] |
| Package | Granularity | No | Packages used only for layer classification, not as units (`1-System_analysis.ipynb` Cell `c72fd4fc`) |
| API endpoint | Granularity | No | [evidence not found] |
| Source code | Repr. Collection > Source > Development | Yes | `1-System_analysis.ipynb` Cell `a97c9013`, Cell `f449eb89` |
| Database schema | Repr. Collection > Source > Development | No | [evidence not found] |
| Version history | Repr. Collection > Source > Development | No | [evidence not found] |
| Runtime log traces | Repr. Collection > Source > Runtime | No | [evidence not found] |
| User interactions | Repr. Collection > Source > Runtime | No | [evidence not found] |
| Business process model | Repr. Collection > Source > Higher-Level Models | No | [evidence not found] |
| Use case | Repr. Collection > Source > Higher-Level Models | No | [evidence not found] |
| Data flow diagram | Repr. Collection > Source > Higher-Level Models | No | [evidence not found] |
| Directly in the code | Repr. Collection > Source > Documentation | No | Annotations read as structure, not documentation (`1-System_analysis.ipynb` Cell `f449eb89`) |
| Paper document | Repr. Collection > Source > Documentation | No | [evidence not found] |
| Digital format | Repr. Collection > Source > Documentation | No | [evidence not found] |
| Static analysis | Repr. Collection > Collection Technique | Yes | `1-System_analysis.ipynb` Cell `f449eb89` (javalang AST) |
| Dynamic analysis | Repr. Collection > Collection Technique | No | [evidence not found] |
| Version analysis | Repr. Collection > Collection Technique | No | [evidence not found] |
| Model analysis | Repr. Collection > Collection Technique | No | [evidence not found] |
| External | Repr. Collection | No | [evidence not found] |
| Inner structure | Representation > Analytical > Structure | Yes | `1-System_analysis.ipynb` Cell `2f676ad4` (field declarations) |
| Inheritance | Representation > Analytical > Structure | Yes | `1-System_analysis.ipynb` Cell `2ec5871f`, Cell `63eb996a` (`Extends`) |
| Association | Representation > Analytical > Structure | Yes | `1-System_analysis.ipynb` Cell `63eb996a` (`References`/`Uses`/`Persists`) |
| Call graph | Representation > Analytical > Behavior | Yes | `1-System_analysis.ipynb` Cell `d6e603ab`, Cell `63eb996a` (`Calls`) |
| Sequence of accesses | Representation > Analytical > Behavior | No | [evidence not found] |
| Frequency | Representation > Analytical > Behavior | No | [evidence not found] |
| CPU level | Representation > Analytical > Behavior | No | [evidence not found] |
| Memory level | Representation > Analytical > Behavior | No | [evidence not found] |
| Response time | Representation > Analytical > Behavior | No | [evidence not found] |
| By contributor | Representation > Analytical > Evolution | No | [evidence not found] |
| By task | Representation > Analytical > Evolution | No | [evidence not found] |
| Monolith | Representation > Type | Yes | `1-System_analysis.ipynb` Cell `be873f87` (`nx.DiGraph`) |
| Microservices | Representation > Type | Yes | `2-Decomposition_optimization.ipynb` Cell `3519b123` (solution csv) |
| Granularity view | Representation > Visualization > Elements | Yes | `1-System_analysis.ipynb` Cell `be873f87` (`*_graph.png`) |
| Cluster view | Representation > Visualization > Elements | Yes | `2-Decomposition_optimization.ipynb` Cell `63ce5fa3` (`DrawSol`, coloured clusters) |
| Structural relationship | Representation > Visualization > Relations | Yes | `1-System_analysis.ipynb` Cell `be873f87` (`References`/`Extends` edges) |
| Control flow | Representation > Visualization > Relations | Yes | `2-Decomposition_optimization.ipynb` Cell `63ce5fa3` (`Calls` edges) |
| Data flow | Representation > Visualization > Relations | Yes | `1-System_analysis.ipynb` Cell `63eb996a` (`Persists`/`Uses` edges) |
| Task | Refactoring > Aggregation Criteria | No | [evidence not found] |
| Contributor | Refactoring > Aggregation Criteria | No | [evidence not found] |
| Lexical | Refactoring > Aggregation Criteria | No | [evidence not found] |
| Functional | Refactoring > Aggregation Criteria | Yes | Call-graph edges drive method cohesion (`1-System_analysis.ipynb` Cell `d6e603ab`; weight `w['Calls']`) |
| Adjacency | Refactoring > Aggregation Criteria | Yes | `2-Decomposition_optimization.ipynb` Cell `bceb7240` (weighted coupling) |
| Expert knowledge | Refactoring > Domain Knowledge | Yes | `1-System_analysis.ipynb` Cell `1a61ce0a`; `2-Decomposition_optimization.ipynb` Cell `e53fae46`, Cell `021636e9` |
| Hierarchical clustering | Refactoring > Services > Algorithms | No | [evidence not found] |
| Community detection | Refactoring > Services > Algorithms | Yes (Orange — violation) | `2-Decomposition_optimization.ipynb` Cell `b1205d9e` (Louvain) |
| K-means++ | Refactoring > Services > Algorithms | No | [evidence not found] |
| Formal concept analysis | Refactoring > Services > Algorithms | No | [evidence not found] |
| Genetic algorithms | Refactoring > Services > Algorithms | No | [evidence not found] |
| Hungarian algorithm | Refactoring > Services > Algorithms | No | [evidence not found] |
| Merge of clusters | Refactoring > Services > Manual Editing | No | [evidence not found] |
| Splitting of clusters | Refactoring > Services > Manual Editing | No | [evidence not found] |
| Transfer of elements between clusters | Refactoring > Services > Manual Editing | Yes | `2-Decomposition_optimization.ipynb` Cell `021636e9` |
| Asynchronization | Refactoring > Functionality Refactoring | No | [evidence not found] |
| Granularity refinement | Refactoring > Functionality Refactoring | No | [evidence not found] |
| Coupling | Quality > Metrics > Single Decomposition | Yes | `2-Decomposition_optimization.ipynb` Cell `bceb7240`, Cell `b4f4589c` |
| Cohesion | Quality > Metrics > Single Decomposition | Yes | `2-Decomposition_optimization.ipynb` Cell `78f5ab5d` |
| Elements size | Quality > Metrics > Single Decomposition | Yes | `2-Decomposition_optimization.ipynb` Cell `b4f4589c` (`Found {n_micros} microservices`) |
| Complexity | Quality > Metrics > Single Decomposition | No | [evidence not found] |
| Team size | Quality > Metrics > Single Decomposition | No | [evidence not found] |
| MoJoFM | Quality > Metrics > Several Decompositions | No | [evidence not found] |
| Compare metrics | Quality > Metrics > Several Decompositions | Yes | `springpetclinic-comparison.ipynb` Cell `af954790`; `sota_approaches/kamimura.txt` |
| Color | Quality > Graphical Comparison | Yes | `2-Decomposition_optimization.ipynb` Cell `63ce5fa3`; `springpetclinic-comparison.ipynb` Cell `63ce5fa3` |
| Sizes | Quality > Graphical Comparison | No | [evidence not found] |
| Distance between elements | Quality > Graphical Comparison | No | [evidence not found] |

---

## Observations

### Model Gap Candidates

- **Combinatorial / ILP optimization**
  - **Would be:** leaf under `Refactoring > Services Refactoring > Algorithms`.
  - **Evidence:** `2-Decomposition_optimization.ipynb` Cell `bceb7240` (`gb.Model()`, binary vars `x/z/y`, `setObjective(coupling, GRB.MINIMIZE)`), Cell `081eb8b2` (`model.optimize()`).
  - **Rationale:** MOSAIC's defining contribution is exact ILP optimization on top of clustering; the current Algorithms group (hierarchical, community detection, k-means++, FCA, genetic, Hungarian) has no entry for an exact mathematical-programming solver, so the tool's main algorithm is unrepresentable.

- **Two-stage clustering-then-optimization pipeline**
  - **Would be:** this is really an *ordering/composition* of two Algorithms (community detection feeding ILP), which the model treats as a flat OR group.
  - **Evidence:** Louvain partitions seed ILP constraints (`2-Decomposition_optimization.ipynb` Cell `bd909d53` builds `communities_to_relax`; Cell `bceb7240` constraint `(8)bonding-y-to-communities`).
  - **Rationale:** the model can mark both algorithms as present but cannot express that one constrains the other; worth noting as a vocabulary limitation rather than a new leaf.

### Other features outside the model

- **Layer inference (Logic / Repository / Entity / Interface)** — classes are typed by Spring/JPA annotations (`@Service`, `@Controller`, `@Repository`) before graph construction (`1-System_analysis.ipynb` Cell `f449eb89`, Cell `c72fd4fc`). Too tool-specific (annotation-driven role tagging) to be a model dimension.
- **Synthetic persistence-method nodes** — framework CRUD methods (`save`, `findAll`) absent from source are inferred and added to the graph (`1-System_analysis.ipynb` Cell `d064063e`, Cell `076d1a9e`). A graph-construction heuristic, not a feature-model concept.
- **Isolated-node pruning** — optionally removes weakly-disconnected nodes before export (`1-System_analysis.ipynb` Cell `63807bcb`). Low-level cleanup.
- **Cross-cut counts** (method calls / references / uses / persists crossing microservices) — reported alongside coupling/cohesion (`2-Decomposition_optimization.ipynb` Cell `b4f4589c`). These are coupling sub-counts, already covered by Coupling.

### Model Vocabulary Fit

- **Algorithms group** is the weakest fit: MOSAIC's core is an ILP solver, which has no vocabulary in the model (see gap candidate). Community detection is present only as a *pre-step*.
- **Expert knowledge vs Aggregation Criteria**: the user-tunable edge weights are simultaneously expert knowledge *and* the parameterization of the Adjacency criterion, so the two dimensions overlap for this tool.
- **Manual Editing**: MOSAIC's "place entity into cluster / remove from cluster" maps cleanly to *Transfer of elements*, but it happens **before** optimization (it constrains the solver) rather than as post-hoc editing of a finished decomposition, which is the model's implicit framing.

### Cross-tree constraint violations

- **Community detection → NOT Expert knowledge** — **VIOLATED.** MOSAIC runs Louvain community detection (`2-Decomposition_optimization.ipynb` Cell `b1205d9e`) *and* relies on expert knowledge: user layer refinement (`1-System_analysis.ipynb` Cell `1a61ce0a`), user-set edge weights (`2-Decomposition_optimization.ipynb` Cell `e53fae46`), and manual entity-cluster placement (Cell `021636e9`). Both features are present together, which the model forbids. `Community detection` is marked Orange and `Expert knowledge` is marked Orange in the profile.

### Noteworthy design decisions

- **Coupling minimization is exact, not heuristic**: unlike most surveyed tools, MOSAIC frames service assignment as an ILP and solves it optimally with Gurobi, using Louvain only to seed entity clusters and reduce the search space (`2-Decomposition_optimization.ipynb` Cell `bceb7240`).
- **Entities anchor microservices**: constraint `(2)microservice-composition` forbids entity-only services, and entity clusters are forced into matching microservices (`(7)bonding-x-to-entity-clusters`), making data ownership the backbone of each service.
- **Typed, weighted edges encode relationship semantics** (Calls 0.8, Persists 1.0, Uses 0.6, References 0.2, Extends 0.0), letting the architect tune how strongly each relationship resists being cut (`2-Decomposition_optimization.ipynb` Cell `e53fae46`).
- **Built-in SOTA comparison**: the repo ships a notebook that scores external decompositions (Kamimura, a baseline) on the same metrics over the same graph, supporting comparative evaluation (`springpetclinic-comparison.ipynb`).
- **Notebook-driven, interactive**: configuration and refinement happen by editing notebook cells (`project`, weights, cluster placement), so the tool is semi-automated and expects a human in the loop.

---

## Reconciliation Log

Date: 2026-06-28
Versions compared: 866147a, 7dc8f18, d4056ce, f4884de, 73d063a, 29f7dfc, cc53285, d9b7b1c (working tree)

No coverage-table verdicts changed; all claims confirmed against the codebase under `../extracted-codebases/MOSAIC`. The analysis has been stable across versions on its central findings (Louvain + ILP pipeline, Class=Unclear, the Community-detection/Expert-knowledge constraint violation); spot-checks this run re-confirmed every `Yes`/`Unclear`/violation verdict:

- **Community detection = Yes** — `community_louvain.best_partition(H, weight='w')` in `2-Decomposition_optimization.ipynb`.
- **Expert knowledge = Yes** — layer refinement (`exclude_packages`, `force_entity_classes` in `1-System_analysis.ipynb`), tunable edge weights (`Calls 0.8`, `Uses 0.6`, `References 0.2`), and manual entity placement (`entity_ids_to_remove`, `entities_clusters_to_place`).
- **ILP optimization** — `gb.Model()`, `setObjective(coupling, GRB.MINIMIZE)`, `model.optimize()` (the model-gap algorithm, not a leaf).
- **Representation** — Method/Entity nodes; `Calls`/`Persists`/`Uses`/`References`/`Extends` edges; `FieldDeclaration` (Inner structure), `collect_inheritance` (Inheritance), `inspect_method_invocation` (Call graph) all confirmed = Yes.
- **Visualization** — `DrawInitialGraph` (Granularity view) + `DrawSol` (Cluster view); `DrawSol` styles edges per `rel_type` → Structural relationship (`References`/`Extends`), Control flow (`Calls`), Data flow (`Persists`/`Uses`) all = Yes.
- **Metrics** — `Coupling`, `Cohesion` (`cohesion_dict[k] = inside_w[k]/outside_w[k]`), `Elements size` = Yes; `Compare metrics` = Yes (SOTA comparison recomputes coupling/cohesion for `kamimura`/`baseline`).
- **Class = Unclear** — graph nodes are Method/Entity; class is only a grouping label / SOTA-comparison unit. Stays Magenta.

Cross-tree constraint violation (re-confirmed): **Community detection → NOT Expert knowledge** is VIOLATED — both are present, so both leaves are marked `Orange`, and the Orange legitimately propagates up (Algorithms, Services Refactoring, Domain Knowledge, Refactoring, and the root → Orange).

Profile re-derived from the (unchanged) table and **corrected** for group-colour propagation bugs (same OR-group / "all-children-present" issues fixed in CARGO/HyDec):

| Group | From → To | Reason |
|-------|-----------|--------|
| Metrics | Red → Light_Green | Mandatory OR group with a *satisfied* branch (Single Decomposition present); a sibling branch's missing mandatory leaf (MoJoFM in Several Decompositions) must not force the OR group Red |
| Quality Assessment | Red → Dark_Green | Mandatory AND group; both children now present (Metrics + Graphical Comparison), no mandatory child Red → fully satisfied |
| Microservices Decomposition and Refactoring (root) | Red → Orange | Root no longer spuriously Red (Metrics fixed); the real state is the constraint-violation Orange propagating from Refactoring |
| Single Decomposition | Dark_Green → Light_Green | AND group with some-but-not-all children present (Complexity, Team size absent) → partially satisfied |
| Analytical | Dark_Green → Light_Green | OR group with Evolution branch absent → not all children present |
| Representation Collection | Dark_Green → Light_Green | External child absent → not all children present |
| Structure | Light_Green → Dark_Green | All children present (Inner structure + Inter Structure) → fully satisfied |
| Inter Structure | Light_Green → Dark_Green | Both children present (Inheritance + Association) → fully satisfied |

`Several Decompositions` stays `Red` (Compare metrics present but mandatory MoJoFM absent → broken branch; this is the legitimate per-CARGO precedent, distinct from the OR-group bug above).

Features still genuinely Unclear after adjudication: `Class` (Magenta) — class is a grouping label / SOTA-comparison unit, not a first-class graph node.


### Profile fix (2026-06-28) — AND "fully satisfied" propagation rule

**Profile-only change; no analysis content was reviewed or altered in this pass.** A
cross-cutting correction to the group-propagation rule (made explicit in `codebase-map`,
`docs-map`, `verify-analysis`) was applied to `MOSAIC.profile`: an AND node is only
`Dark_Green` ("Group: fully satisfied") when every **mandatory** child is fully
satisfied — a present **leaf** counts (`Light_Green` is a leaf's max; leaves are never
`Dark_Green`), but a mandatory child **group** that is only `Light_Green` (partially
satisfied) caps the AND parent at `Light_Green`. The previous derivation treated a merely
*present* mandatory child group as enough for `Dark_Green`, overstating coverage.

AND cells changed `Dark_Green` → `Light_Green` in `MOSAIC.profile`: `Collector`, `Visualization`, `Representation`, `Quality Assessment`. (Nodes
already at a higher-priority colour — `Red`/`Orange`/`Magenta` — were unaffected; AND
nodes whose mandatory child is a present leaf, e.g. `Type`, correctly stay `Dark_Green`.)
