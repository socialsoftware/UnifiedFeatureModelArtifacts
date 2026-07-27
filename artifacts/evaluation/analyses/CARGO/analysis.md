# Analysis — CARGO

Codebase path: ../extracted-codebases/CARGO
Date: 2026-06-28

> The public codebase is IBM Konveyor's `tackle-data-gravity-insights` (the `dgi`
> Python package), which implements the **data-collection front-end** of CARGO:
> the graph builders (`code2graph`, `schema2graph`, `tx2graph`) and the
> `partition` command. The CARGO partitioning algorithm itself is imported as an
> external pip dependency (`from cargo import Cargo`, `dgi/partitioning/partition.py:24`)
> and is **not** included in this repository. Algorithm- and metric-level findings
> are therefore corroborated from the paper (Nitin et al., *CARGO: AI-Guided
> Dependency Analysis for Migrating Monolithic Applications to Microservices
> Architecture*, ASE 2023, `papers/tools/CARGO.pdf`).

---

## Filled Analysis Template

### Goals
- Refine and/or discover microservice partitions of a monolithic Java EE
  application from a **context- and flow-sensitive System Dependency Graph (SDG)**
  that captures call-return, data-flow, heap-dependency, and DB-transaction edges
  (`README.md` lines 7–15; `papers/.md/tools/CARGO.md:52`).
- Primary motivation: avoid *distributed monoliths* and *distributed transactions*
  that off-the-shelf graph clustering produces by ignoring heap and DB relationships
  (`papers/.md/tools/CARGO.md:49`, `:92`, `:94`).

### Phases
- **c2g (Code2Graph):** build the call-return / data-flow / heap-dependency graph
  from DOOP/JackEE static-analysis facts (`dgi/cli.py:243`, `dgi/code2graph/method_graph_builder.py:51`).
- **s2g (Schema2Graph):** parse an SQL `*.DDL` schema into table/column nodes
  with foreign-key edges (`dgi/cli.py:107`, `dgi/schema2graph/schema_loader.py:76`).
- **tx2g (Transaction2Graph):** add CRUD transaction edges between methods/classes
  and DB tables, sourced from DiVA's transaction analysis (`dgi/cli.py:169`,
  `dgi/tx2graph/abstract_transaction_loader.py:208`).
- **partition:** run the CARGO label-propagation algorithm over the assembled graph
  to (re-)partition the monolith (`dgi/cli.py:338`, `dgi/partitioning/partition.py:43`).

### Granularity
- **Method** — SDG nodes are methods; `MethodNode` carries the partition assignment
  (`dgi/models/entities.py:52`, `dgi/code2graph/method_graph_builder.py:51`).
- **Class** — graphs and partitions can be built at class level (`ClassNode`,
  `dgi/models/entities.py:96`); method-level partition labels are aggregated up to
  classes by majority vote (`statistics.mode`, `dgi/partitioning/partition.py:68-71`).
- **Entity (DB table)** — `SQLTable`/`SQLColumn` nodes participate as graph nodes and
  receive transaction edges, but they are *not* themselves assigned to partitions
  (`dgi/models/entities.py:135`, `:147`). The unit of decomposition is the
  method/class; tables are context, not output.

## Representation Collection

### Collector

#### Source

##### Development
- **Source code** — static-analysis facts over Java EE bytecode/source produced by
  DOOP/JackEE are ingested by `c2g` (`dgi/cli.py:259-307`; `papers/.md/tools/CARGO.md:204`
  "We use Doop […] and datalog to implement all our static analysis").
- **Database schema** — `s2g` parses an SQL DDL file into table/column nodes and
  foreign-key edges (`dgi/cli.py:107`, `dgi/schema2graph/schema_loader.py:76`,
  `tests/fixtures/test-schema.ddl`).
- Version history — [evidence not found].

##### Runtime
- [evidence not found] — the SDG (including transaction edges) is *statically*
  derived; the paper explicitly contrasts CARGO with dynamic-tracing approaches
  (`papers/.md/tools/CARGO.md:50`, `:52`). DiVA transaction discovery is a static
  analysis of `@Transactional` JPA/JTA methods (`papers/.md/tools/CARGO.md:170`).

##### Higher-Level Models
- [evidence not found].

##### Documentation
- [evidence not found] for graph construction. (`@Transactional` annotations are
  read as program facts, not as documentation — see "Other features outside the model".)

#### Collection Technique
- **Static analysis** — the entire SDG is built from static program analysis
  (DOOP/JackEE datalog facts, DiVA static transaction analysis, DDL parsing):
  `dgi/cli.py:259-307`, `papers/.md/tools/CARGO.md:52`, `:170`, `:204`.
- Dynamic / Version / Model analysis — [evidence not found].

## Representation

### Analytical

#### Structure
- **Association** — call-return, data-flow, and heap-dependency edges between methods
  encode structural coupling (`dgi/models/relationships.py:61-88`,
  `dgi/models/entities.py:75-83`). Foreign-key edges between schema columns are also
  structural associations (`dgi/models/entities.py:143`).
- Inner structure — [evidence not found] (intra-procedural dependencies are
  deliberately abstracted away, `papers/.md/tools/CARGO.md:176`).
- Inheritance — [evidence not found].

#### Behavior
- **Call graph** — call-return edges are the cornerstone of the SDG
  (`dgi/models/relationships.py:80`, `dgi/code2graph/method_graph_builder.py:166`;
  `papers/.md/tools/CARGO.md:156`).
- **Sequence of accesses** — transaction edges record an ordered CRUD read/write set
  and a call-trace (stacktrace) from the entrypoint to each DB access
  (`dgi/tx2graph/abstract_transaction_loader.py:108-129`, `:208-232`;
  `TransactionCallTrace`, `dgi/models/relationships.py:54`). This is a static
  access/transaction sequence, not a runtime trace.
- **Frequency** — edge `weight` counts how many times a dependency recurs across
  contexts (`dgi/code2graph/method_graph_builder.py:126`, `:159`, `:188`); this is a
  static recurrence count, not runtime call frequency. Marked Unclear.
  - FIXME: should we update the constraint?
- CPU level / Memory level / Response time — measured only at deployment for
  evaluation (`papers/.md/tools/CARGO.md:215`), not part of the representation.

#### Evolution
- [evidence not found].

### Type
- **Monolith** — the SDG is the graph of the monolith being decomposed
  (`papers/.md/tools/CARGO.md:67`).
- **Microservices** (mandatory) — the output assigns each method/class a
  `partition_id` representing the target microservice
  (`dgi/partitioning/partition.py:60-71`, `partitions.json` at `:79`).

### Visualization
- Each `dgi` command writes into a **live Neo4j database** over a real Bolt/HTTP
  connection as the pipeline runs (`dgi/cli.py:264`; `to_neo4j`,
  `dgi/code2graph/json_to_neo4j_graph.py:20`; `tx2neo4j`,
  `dgi/tx2graph/abstract_transaction_loader.py:208`); this is not a one-off export to
  `partitions.json`. After `partition` runs, each node keeps its structural (call/data/heap)
  edges and additionally carries a `partition_id` property stamped back into the graph
  (`dgi/partitioning/partition.py:60-82`), so the partitioned graph is fully queryable. The
  decomposition is therefore browsable in Neo4j's own browser
  (`http://localhost:7474/browser/`, `dgi/tx2graph/README.md:54`), optionally guided by the
  bundled Cypher walkthrough (`docs/neo4j-guides/walkthrough.html`). What the tool does *not*
  ship is a purpose-built decomposition view of its own; visualisation is delegated to the
  generic Neo4j graph UI, where the user writes their own Cypher.

#### Elements
- **Granularity view** — individual method/class/table nodes are visible in the Neo4j
  browser (`docs/neo4j-guides/walkthrough.html`). Marked Unclear: the project relies on
  an external DB browser rather than a purpose-built granularity view.
- Cluster view — [evidence not found] as a *shipped* view. The decomposition itself *is*
  inspectable: every node carries a `partition_id` and its edges remain, so a user can group
  or colour nodes by partition with a hand-written Cypher query in the Neo4j browser
  (`dgi/partitioning/partition.py:60-82`). But no grouped/cluster rendering is bundled with the
  tool, so this stays **No** (the partitions are also written to `partitions.json`,
  `dgi/partitioning/partition.py:79`).

#### Relations
- **Structural relationship** — heap/data/call edges survive partitioning and stay attached to
  the now partition-labelled nodes, so the structural relations of the decomposed entities are
  queryable in Neo4j as typed edges (`dgi/models/relationships.py:61-88`). Unclear (generic DB
  viewer, no bespoke view).
- **Control flow** — call-return edges (`dgi/models/relationships.py:80`). Unclear.
- **Data flow** — data-dependency edges (`dgi/models/relationships.py:71`). Unclear.

## Refactoring

### Domain Knowledge

#### Aggregation Criteria
- **Functional** — label propagation groups methods/classes that are densely
  connected through call/data/heap dependencies (cohesive functional regions),
  isolating loosely coupled regions (`papers/.md/tools/CARGO.md:182`, `:194`).
- **Adjacency** — grouping is driven by structural coupling: call-return, data-flow,
  and heap-dependency edges of the SDG (`papers/.md/tools/CARGO.md:52`, `:194`).
- Lexical / Task / Contributor — [evidence not found].

#### Expert knowledge
- The user may supply a **seed partition file** to run CARGO in refinement /
  semi-supervised mode (`dgi/cli.py:314-320`, `dgi/partitioning/partition.py:51-54`;
  `papers/.md/tools/CARGO.md:192`, `:207`). The user also supplies the target number
  of partitions `K` (`dgi/cli.py:328`). The seeds are a partition assignment / config,
  not domain rules or thresholds, so this is borderline — marked Unclear (see
  Cross-tree constraint violations).
  - `--seed-input` and `--partitions` make this green

### Services Refactoring

#### Algorithms
- **Community detection** — CARGO is a "novel community detection algorithm" based on
  Label Propagation (LPA): context-sensitive label propagation over context- and
  transactional-snapshots of the SDG (`papers/.md/tools/CARGO.md:52`, `:180`, `:190`;
  abstract keyword "Community Detection", `:21`). Invoked via `cargo.run(...)`
  (`dgi/partitioning/partition.py:52-54`).
- Hierarchical clustering / K-means++ / Formal concept analysis / Genetic algorithms /
  Hungarian algorithm — [evidence not found].

#### Manual Editing
- No merge/split/transfer operations on resulting clusters are shipped
  ([evidence not found]). The seed-partition input is *pre*-partitioning guidance,
  not post-hoc cluster editing.

### Functionality Refactoring
- **Granularity refinement** — CARGO's core purpose in refinement mode is to *refine*
  the partition boundaries produced by another tool (`Algorithm++`), adjusting service
  boundaries to reduce coupling and distributed transactions (`papers/.md/tools/CARGO.md:69`,
  `:207`; `dgi/partitioning/partition.py:51-54`). Marked Unclear — this refines a
  *partitioning* rather than transforming application functionality, so it is a partial
  conceptual fit.
    - Pass to yellow, does not support **functionality** refactoring
- Asynchronization — [evidence not found].

## Quality Assessment

### Metrics

#### Single Decomposition
- No metric is shipped with the tool; all metrics are reported in the paper (`papers/.md/tools/CARGO.md:211-223`).
- **Coupling** — sum of inter-partition SDG edges over total edges
  (`papers/.md/tools/CARGO.md:220`).
- **Cohesion** — internal/(internal+external) edges, averaged over partitions
  (`papers/.md/tools/CARGO.md:221`).
- **Elements size** (mandatory) — partitions are counts of classes/methods; the
  benchmark applications are characterised by class counts (`papers/.md/tools/CARGO.md:200`).
  Marked Unclear: size is implicit, not reported as a dedicated metric.
- Complexity / Team size — [evidence not found].
- Additional metrics not in the model: **Database Transactional Purity**,
  **Inter-call Percentage (ICP)**, **Business Context Purity (BCP)** — see Model Gap
  Candidates (`papers/.md/tools/CARGO.md:211`, `:222`, `:223`).

#### Several Decompositions
- **Compare metrics** — the evaluation compares CARGO/`Algorithm++` against four
  baseline partitioners on the architectural metrics above
  (`papers/.md/tools/CARGO.md:63`, `:273-280`). This is a research-paper comparison,
  not a feature of the shipped tool. Marked Unclear.
- MoJoFM — [evidence not found].

#### Benchmarks
- 5 Java EE applications: Daytrader, Plants, AcmeAir, JPetStore, Proprietary1
  (`papers/.md/tools/CARGO.md:200`). `daytrader` transaction fixtures ship with the
  repo (`tests/fixtures/daytrader_transaction.json`).

### Graphical Comparison
- [evidence not found].

## Open Issues
- The partitioning algorithm is a closed pip dependency (`cargo`), so the repo alone
  cannot reproduce decompositions without that package and a populated Neo4j instance.
- No bundled decomposition visualiser or cluster view; relies on Neo4j browser.

## Extra notes
- CARGO operates both **stand-alone** (native/unsupervised, seeds = `i % K`) and as a
  **refinement add-on** (semi-supervised, seeded from another tool's output)
  (`papers/.md/tools/CARGO.md:206-207`; `dgi/partitioning/partition.py:51-54`).

---

## Feature Coverage Table

| Feature | Dimension | Supported | Evidence |
|---------|-----------|-----------|----------|
| Method | Granularity | Yes | `dgi/models/entities.py:52`; `dgi/code2graph/method_graph_builder.py:51` |
| Class | Granularity | Yes | `dgi/models/entities.py:96`; `dgi/partitioning/partition.py:68-71` |
| Entity | Granularity | No | `SQLTable` nodes are graph context, not a decomposition unit (`dgi/models/entities.py:147`) |
| Functionality | Granularity | No | [evidence not found] |
| Package | Granularity | No | [evidence not found] |
| API endpoint | Granularity | No | [evidence not found] |
| Source code | Repr. Collection > Source > Development | Yes | `dgi/cli.py:259-307`; `papers/.md/tools/CARGO.md:204` |
| Database schema | Repr. Collection > Source > Development | Yes | `dgi/schema2graph/schema_loader.py:76`; `tests/fixtures/test-schema.ddl` |
| Version history | Repr. Collection > Source > Development | No | [evidence not found] |
| Runtime log traces | Repr. Collection > Source > Runtime | No | SDG is static (`papers/.md/tools/CARGO.md:52`) |
| User interactions | Repr. Collection > Source > Runtime | No | [evidence not found] |
| Business process model | Repr. Collection > Source > Higher-Level Models | No | [evidence not found] |
| Use case | Repr. Collection > Source > Higher-Level Models | No | [evidence not found] |
| Data flow diagram | Repr. Collection > Source > Higher-Level Models | No | [evidence not found] |
| Directly in the code | Repr. Collection > Source > Documentation | No | `@Transactional` read as facts, not docs (`papers/.md/tools/CARGO.md:170`) |
| Paper document | Repr. Collection > Source > Documentation | No | [evidence not found] |
| Digital format | Repr. Collection > Source > Documentation | No | [evidence not found] |
| Static analysis | Repr. Collection > Collection Technique | Yes | `dgi/cli.py:259-307`; `papers/.md/tools/CARGO.md:52`, `:204` |
| Dynamic analysis | Repr. Collection > Collection Technique | No | `papers/.md/tools/CARGO.md:50`, `:52` |
| Version analysis | Repr. Collection > Collection Technique | No | [evidence not found] |
| Model analysis | Repr. Collection > Collection Technique | No | [evidence not found] |
| External | Repr. Collection | No | [evidence not found] |
| Inner structure | Representation > Structure | No | intra-procedural deps abstracted away (`papers/.md/tools/CARGO.md:176`) |
| Inheritance | Representation > Structure > Inter Structure | No | [evidence not found] |
| Association | Representation > Structure > Inter Structure | Yes | `dgi/models/relationships.py:61-88`; `dgi/models/entities.py:143` |
| Call graph | Representation > Behavior | Yes | `dgi/models/relationships.py:80`; `papers/.md/tools/CARGO.md:156` |
| Sequence of accesses | Representation > Behavior | Yes | `dgi/tx2graph/abstract_transaction_loader.py:108-129`, `:208-232`; `dgi/models/relationships.py:54` |
| Frequency | Representation > Behavior | Unclear | static edge `weight` (`dgi/code2graph/method_graph_builder.py:126`), not runtime frequency |
| CPU level | Representation > Behavior | No | deployment metric only (`papers/.md/tools/CARGO.md:215`) |
| Memory level | Representation > Behavior | No | [evidence not found] |
| Response time | Representation > Behavior | No | deployment metric only (`papers/.md/tools/CARGO.md:215`) |
| By contributor | Representation > Evolution | No | [evidence not found] |
| By task | Representation > Evolution | No | [evidence not found] |
| Monolith | Representation > Type | Yes | SDG of the monolith (`papers/.md/tools/CARGO.md:67`) |
| Microservices | Representation > Type (mandatory) | Yes | `partition_id` per node (`dgi/partitioning/partition.py:60-71`) |
| Granularity view | Representation > Visualization > Elements | Unclear | Neo4j browser shows nodes (`docs/neo4j-guides/walkthrough.html`) |
| Cluster view | Representation > Visualization > Elements | No | no cluster rendering; `partitions.json` only (`dgi/partitioning/partition.py:79`) |
| Structural relationship | Representation > Visualization > Relations | Unclear | Neo4j typed edges (`dgi/models/relationships.py:61-88`) |
| Control flow | Representation > Visualization > Relations | Unclear | call-return edges in Neo4j (`dgi/models/relationships.py:80`) |
| Data flow | Representation > Visualization > Relations | Unclear | data-dependency edges in Neo4j (`dgi/models/relationships.py:71`) |
| Task | Refactoring > Aggregation Criteria | No | [evidence not found] |
| Contributor | Refactoring > Aggregation Criteria | No | [evidence not found] |
| Lexical | Refactoring > Aggregation Criteria | No | [evidence not found] |
| Functional | Refactoring > Aggregation Criteria | Yes | `papers/.md/tools/CARGO.md:182`, `:194` |
| Adjacency | Refactoring > Aggregation Criteria | Yes | `papers/.md/tools/CARGO.md:52`, `:194` |
| Expert knowledge | Refactoring > Domain Knowledge | Unclear | seed partitions / `K` (`dgi/cli.py:314-328`; `papers/.md/tools/CARGO.md:192`) |
| Hierarchical clustering | Refactoring > Algorithms | No | [evidence not found] |
| Community detection | Refactoring > Algorithms | Yes | `papers/.md/tools/CARGO.md:52`, `:180`, `:190`; `dgi/partitioning/partition.py:52` |
| K-means++ | Refactoring > Algorithms | No | [evidence not found] |
| Formal concept analysis | Refactoring > Algorithms | No | [evidence not found] |
| Genetic algorithms | Refactoring > Algorithms | No | [evidence not found] |
| Hungarian algorithm | Refactoring > Algorithms | No | [evidence not found] |
| Merge of clusters | Refactoring > Manual Editing | No | [evidence not found] |
| Splitting of clusters | Refactoring > Manual Editing | No | [evidence not found] |
| Transfer of elements between clusters | Refactoring > Manual Editing | No | [evidence not found] |
| Asynchronization | Refactoring > Functionality Refactoring | No | [evidence not found] |
| Granularity refinement | Refactoring > Functionality Refactoring | Unclear | refines another tool's partitions (`papers/.md/tools/CARGO.md:69`, `:207`) |
| Coupling | Quality > Single Decomposition | Yes | `papers/.md/tools/CARGO.md:220` |
| Cohesion | Quality > Single Decomposition | Yes | `papers/.md/tools/CARGO.md:221` |
| Elements size | Quality > Single Decomposition (mandatory) | Unclear | implicit class/partition counts (`papers/.md/tools/CARGO.md:200`) |
| Complexity | Quality > Single Decomposition | No | [evidence not found] |
| Team size | Quality > Single Decomposition | No | [evidence not found] |
| MoJoFM | Quality > Several Decompositions (mandatory) | No | [evidence not found] |
| Compare metrics | Quality > Several Decompositions | Unclear | paper-only baseline comparison (`papers/.md/tools/CARGO.md:273-280`) |
| Color | Quality > Graphical Comparison | No | [evidence not found] |
| Sizes | Quality > Graphical Comparison | No | [evidence not found] |
| Distance between elements | Quality > Graphical Comparison | No | [evidence not found] |

---

## Observations

### Model Gap Candidates

- **Heap dependency / object-state coupling**
  - **Would be:** leaf under Representation > Analytical > Structure (Inter Structure)
    or Behavior.
  - **Evidence:** `dgi/models/relationships.py:61` (`HeapCarriedRelationship`);
    `dgi/code2graph/method_graph_builder.py:102`; `papers/.md/tools/CARGO.md:52`, `:92`.
  - **Rationale:** Heap-carried dependencies (shared object state between methods) are
    a first-class edge type central to CARGO's value proposition, yet the model's
    Structure vocabulary (Association/Inheritance) does not name them.

- **Database transaction edge / transactional coupling**
  - **Would be:** leaf under Representation > Analytical (a Structure or Behavior
    sub-feature capturing method↔table CRUD/transaction relations).
  - **Evidence:** `dgi/models/relationships.py:36-58`; `dgi/tx2graph/`;
    `papers/.md/tools/CARGO.md:170`.
  - **Rationale:** The application's dependency on DB transactions is the distinguishing
    representation in CARGO; the model has no concept for method-to-data transactional
    relationships beyond generic Association.

- **Database Transactional Purity (metric)**
  - **Would be:** leaf under Quality Assessment > Metrics > Single Decomposition.
  - **Evidence:** `papers/.md/tools/CARGO.md:211-213`.
  - **Rationale:** An entropy-based purity metric over DB tables vs partitions; a
    data-centric quality metric absent from the model.

- **Inter-call Percentage (ICP)**
  - **Would be:** leaf under Quality Assessment > Metrics > Single Decomposition
    (a coupling-family metric).
  - **Evidence:** `papers/.md/tools/CARGO.md:222`.
  - **Rationale:** Distinct call-volume-based coupling metric used in industry
    (IBM Mono2Micro) not captured by the generic "Coupling" leaf.

- **Business Context Purity (BCP)**
  - **Would be:** leaf under Quality Assessment > Metrics > Single Decomposition.
  - **Evidence:** `papers/.md/tools/CARGO.md:223`.
  - **Rationale:** Entropy of business use-cases per partition — a semantic-cohesion
    metric distinct from structural Cohesion.

- **Seed-based refinement mode (semi-supervised partition refinement)**
  - **Would be:** could motivate a feature under Refactoring expressing "refine an
    existing decomposition" as a usage mode, distinct from a fresh decomposition.
  - **Evidence:** `dgi/cli.py:314-320`; `dgi/partitioning/partition.py:51-54`;
    `papers/.md/tools/CARGO.md:69`, `:207`.
  - **Rationale:** Taking another tool's decomposition as input and improving it is a
    usage pattern the model does not represent (it assumes decomposition from scratch).

### Other features outside the model

- **Context- and flow-sensitivity of the SDG** (`papers/.md/tools/CARGO.md:67`, `:150`,
  `:156`) — object-sensitive (2ObjH) contexts on edges. A program-analysis precision
  property, too low-level for the model.
- **`@Transactional` JPA/JTA annotations as analysis facts** (`papers/.md/tools/CARGO.md:170`)
  — annotations are consumed as static program facts to discover transactions, not as
  Documentation in the modelling sense.
- **Neo4j as graph store/backend** (`README.md` lines 27–42; `dgi/code2graph/json_to_neo4j_graph.py`)
  — an implementation/storage choice, not a feature-model concept.
- **Edge `weight` as static recurrence count** (`dgi/code2graph/method_graph_builder.py:126`)
  — a graph-weighting detail rather than runtime Frequency.

### Model Vocabulary Fit

- **Granularity (Method vs Class):** CARGO blurs the two — it propagates labels over a
  *method*-node SDG but reports *class*-level partitions via majority vote
  (`dgi/partitioning/partition.py:68-71`). The model's exclusive-leaf framing handles
  this only by marking both Yes.
- **Entity:** DB tables exist as graph nodes but are never assigned to a service. The
  model's "Entity" granularity implies the entity *is* the decomposition unit, which
  does not fit here.
- **Functionality Refactoring > Granularity refinement:** the model implies refining
  *service granularity post-decomposition*; CARGO refines a *partitioning produced by
  another tool*. Overlapping but not identical concepts — marked Unclear.
- **Visualization:** the model assumes the tool ships a decomposition view; CARGO
  delegates to a generic Neo4j browser, so Granularity-view / Relations evidence is
  indirect (Unclear) and Cluster view is absent.
- **Expert knowledge:** the model frames this as human rules/thresholds; CARGO's
  "expert" input is a *seed partition assignment* plus `K`, which is a softer fit.

### Cross-tree constraint violations

- **Community detection → NOT Expert knowledge.** CARGO's algorithm is Community
  detection (`papers/.md/tools/CARGO.md:52`, `:190`), and in refinement/semi-supervised
  mode it consumes user-supplied seed partitions (`dgi/cli.py:314-320`;
  `papers/.md/tools/CARGO.md:192`, `:207`). If those seeds are read as **Expert
  knowledge**, this co-selection **violates** the constraint. The fit is borderline:
  the seeds are a partition assignment / `K` value, not domain rules — so Expert
  knowledge is marked Unclear (Magenta) rather than confirmed. Native (unsupervised)
  mode has no such input and is constraint-clean. Flagged as a potential violation.

### Noteworthy design decisions

- **Refinement-first philosophy.** CARGO is designed to *augment* existing partitioners
  (FoSCI++, MEM++, Mono2Micro++, CoGCN++) rather than replace them
  (`papers/.md/tools/CARGO.md:69`, `:273-280`). This dual role (stand-alone vs add-on)
  is unusual among the analysed tools.
- **Data-centric SDG.** Treating DB tables and transactions as first-class graph
  citizens — and adding heap-dependency edges — is the core differentiator, aimed at
  eliminating distributed transactions and distributed-monolith coupling
  (`papers/.md/tools/CARGO.md:49`, `:52`, `:94`).
- **Fully static, context-sensitive analysis** via DOOP/JackEE datalog
  (`papers/.md/tools/CARGO.md:204`) — a deliberate rejection of dynamic tracing
  (`papers/.md/tools/CARGO.md:50`).
- **Closed algorithm, open front-end.** The public `dgi` repo ships only the graph
  builders and the `partition` entry point; the `cargo` algorithm itself is an external
  dependency (`dgi/partitioning/partition.py:24`), limiting reproducibility.
- **Neo4j-backed pipeline** with three independent ingest commands (`c2g`, `s2g`,
  `tx2g`) that incrementally populate one shared graph before `partition` runs.

---

## Reconciliation Log

Date: 2026-06-28
Versions compared: `4ff06b4`, `29f7dfc`, `cc53285`, `d9b7b1c` (current on disk) + working tree

The current on-disk table (`d9b7b1c`) was confirmed correct on every disputed
feature; no table verdict was changed. The non-determinism surfaced across earlier
reruns (`4ff06b4`/`29f7dfc`/`cc53285`) was adjudicated against ground truth (the
`dgi` codebase and the CARGO paper, `papers/.md/tools/CARGO.md`). The
`CARGO.profile`, however, had been generated from the stale `cc53285` table and
**did not match** the current analysis; it has been fully re-derived from the table
below.

| Feature | Disputed values (versions) → Reconciled | Adjudicating evidence | Which version(s) were wrong |
|---------|------------------------------------------|-----------------------|-----------------------------|
| Runtime log traces | Unclear (4ff06b4/29f7dfc) / Yes (cc53285) → **No** | `dgi/tx2graph/abstract_transaction_loader.py:208-258` parses a pre-computed transaction JSON (`json.load(open(input_file))`); paper: SDG is built statically (`papers/.md/tools/CARGO.md:50`, `:52`) | cc53285 (Yes), 4ff06b4/29f7dfc (Unclear) |
| Dynamic analysis | Unclear / Yes (cc53285) → **No** | DiVA transaction discovery is static `@Transactional` analysis (`papers/.md/tools/CARGO.md:170`); paper explicitly contrasts CARGO with dynamic tracing (`:50`) | cc53285 (Yes), 4ff06b4/29f7dfc (Unclear) |
| External | No (4ff06b4/29f7dfc/d9b7b1c) / Yes (cc53285) → **No** | `from cargo import Cargo` is a pip dependency, not externally-provided domain knowledge (`dgi/partitioning/partition.py:24`, `requirements.txt:10`) | cc53285 (Yes) |
| Inner structure | No / Yes (cc53285) → **No** | `dgi/models/entities.py:52-160` defines only *inter*-node relationships (heap/data/call/transaction flows); no intra-class field/method composition; paper abstracts intra-procedural deps (`papers/.md/tools/CARGO.md:176`) | cc53285 (Yes) |
| Microservices | No (4ff06b4/29f7dfc) / Yes (cc53285/d9b7b1c) → **Yes** | each node receives a `partition_id`; `partitions.json` is the target decomposition (`dgi/partitioning/partition.py:60-79`) | 4ff06b4/29f7dfc (No) |
| Community detection | Yes / Unclear (cc53285) → **Yes** | "novel community detection algorithm called …CARGO" (`papers/.md/tools/CARGO.md:52`, `:180`, `:190`) | cc53285 (Unclear) |
| Hierarchical clustering / K-means++ / Genetic / Hungarian | No / Unclear (cc53285) → **No** | paper names the algorithm as LPA-based community detection only (`papers/.md/tools/CARGO.md:68`, `:182`); none of these are present | cc53285 (Unclear) |
| Coupling | No (older) / Yes (d9b7b1c) → **Yes** | metric defined in `papers/.md/tools/CARGO.md:220` | 4ff06b4/29f7dfc/cc53285 (No) |
| Cohesion | No (older) / Yes (d9b7b1c) → **Yes** | metric defined in `papers/.md/tools/CARGO.md:221` | 4ff06b4/29f7dfc/cc53285 (No) |
| Frequency | Yes (older) / Unclear (d9b7b1c) → **Unclear** | edge `weight` is a static recurrence count (`dgi/models/relationships.py:66`), not runtime frequency | 4ff06b4/29f7dfc/cc53285 (Yes) |
| Expert knowledge | Yes (older) / Unclear (d9b7b1c) → **Unclear** | `--seed-input` supplies a seed *partition assignment* + `K`, not domain rules/thresholds (`dgi/cli.py:314-336`); semi-supervised seeding (`papers/.md/tools/CARGO.md:192`, `:207`) | 4ff06b4/29f7dfc/cc53285 (Yes) |
| Compare metrics | No (older) / Unclear (d9b7b1c) → **Unclear** | paper-only baseline comparison, not a shipped tool feature (`papers/.md/tools/CARGO.md:273-280`) | 4ff06b4/29f7dfc/cc53285 (No) |
| Granularity refinement | No (older) / Unclear (d9b7b1c) → **Unclear** | refines *another tool's* partition (Algorithm++), a partial conceptual fit (`papers/.md/tools/CARGO.md:69`, `:207`) | 4ff06b4/29f7dfc/cc53285 (No) |

Features still genuinely Unclear after adjudication: **Frequency** (static `weight`,
not runtime), **Expert knowledge** (seed assignment vs. domain rules — borderline,
see cross-tree note), **Granularity view** / **Structural relationship** /
**Control flow** / **Data flow** (delegated to the generic Neo4j browser, no bespoke
view), **Cluster view** is **No** (only `partitions.json`, no grouped rendering),
**Elements size** (implicit class/partition counts, not a reported metric),
**Compare metrics** and **Granularity refinement** (as above).

Cross-tree constraint check: **Community detection → NOT Expert knowledge.** Community
detection is confirmed (Light_Green); Expert knowledge is only **Unclear** (Magenta),
not confirmed, and native (unsupervised) mode takes no seed input. No confirmed
violation, so no `Orange` is applied; the borderline is flagged in the table above.

### Second pass (2026-06-28) — profile group-propagation only

No leaf verdict changed; the Feature Coverage Table is identical to the first pass.
This pass corrected **group colour propagation** in `CARGO.profile` for the
mandatory-`Magenta` case, which the previous derivation handled incorrectly. CARGO is
the only analysed tool with a **mandatory leaf in the `Magenta` (unclear) state**:
`Granularity view` (mandatory child of `Elements`) and `Elements size` (mandatory child
of `Single Decomposition`). The earlier profile let these flow up to `Dark_Green`
("fully satisfied"), overstating certainty.

The rule was made explicit in `codebase-map`, `docs-map`, and `verify-analysis`: **a
mandatory `Magenta` child makes its group `Magenta`** (uncertainty in a required child
propagates up; confirmed sibling leaves do not rescue the group), and for an OR group
whose only present branch is `Magenta` the group is `Magenta` too. Optional `Magenta`
children do **not** block a parent's `Dark_Green`. Priority is now
`Red > Orange > Magenta > Light_Green > Yellow`.

Group cells changed in `CARGO.profile`:

| Group | From → To | Why |
|-------|-----------|-----|
| `Elements` | Dark_Green → **Magenta** | mandatory `Granularity view`=Magenta |
| `Relations` | Light_Green → **Magenta** | mandatory OR, all present children Magenta |
| `Functionality Refactoring` | Light_Green → **Magenta** | optional OR; only present child (`Granularity refinement`) is Magenta (`Asynchronization` absent) |
| `Visualization` | Dark_Green → **Magenta** | both mandatory children (Elements, Relations) Magenta |
| `Single Decomposition` | Dark_Green → **Magenta** | mandatory `Elements size`=Magenta (Coupling/Cohesion confirmed but do not rescue) |
| `Metrics` | Light_Green → **Magenta** | mandatory OR; only present branch (Single Decomposition) is Magenta, sibling Several Decompositions is Red |
| `Quality Assessment` | Dark_Green → **Magenta** | mandatory `Metrics`=Magenta |
| `Microservices Decomposition and Refactoring` (root) | Dark_Green → **Magenta** | mandatory `Quality Assessment`=Magenta |

`Representation` stays `Dark_Green`: its mandatory children (`Analytical`, `Type`) are
confirmed and `Visualization` is **optional**, so its `Magenta` does not block the
parent. *(Superseded by the third pass below: `Representation` becomes `Light_Green`
because the mandatory child group `Analytical` is only partially satisfied.)*

### Third pass (2026-06-28) — AND "fully satisfied" propagation

No leaf verdict changed; the Feature Coverage Table is unchanged. This pass corrected a
separate group-propagation gap: the rule treated a mandatory child as good enough for a
`Dark_Green` AND if it was merely **present** (`Light_Green` or `Dark_Green`). Per the
legend, `Dark_Green` means "Group: **fully satisfied**", so an AND should only be
`Dark_Green` when every mandatory child is fully satisfied — and a **mandatory child
group at `Light_Green` (partially satisfied) caps the AND parent at `Light_Green`**. A
**leaf** is fully satisfied when present (`Light_Green` is a leaf's max; leaves are never
`Dark_Green`), so AND nodes whose mandatory children are present leaves (e.g. `Type`)
stay `Dark_Green`.

The rule was made explicit in `codebase-map`, `docs-map`, and `verify-analysis`
(table row + rule 6).

Group cells changed in `CARGO.profile`:

| Group | From → To | Why |
|-------|-----------|-----|
| `Collector` | Dark_Green → **Light_Green** | mandatory child groups `Source` and `Collection Technique` both only `Light_Green` |
| `Representation` | Dark_Green → **Light_Green** | mandatory child group `Analytical` only `Light_Green` (`Type` is Dark_Green, but `Analytical` caps it) |
| `Domain Knowledge` | Dark_Green → **Light_Green** | mandatory child group `Aggregation Criteria` only `Light_Green` (optional `Expert knowledge`=Magenta doesn't matter) |
| `Services Refactoring` | Dark_Green → **Light_Green** | mandatory child group `Algorithms` only `Light_Green` (`Manual Editing` optional) |
| `Refactoring` | Dark_Green → **Light_Green** | both mandatory child groups (`Domain Knowledge`, `Services Refactoring`) now `Light_Green` |

`Type` stays `Dark_Green` (mandatory leaf `Microservices` present = fully satisfied).
`Quality Assessment` and the root stay `Magenta` (Magenta > Light_Green priority).
