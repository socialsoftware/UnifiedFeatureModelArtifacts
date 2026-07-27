# Analysis — mono2micro

Codebase path: `../extracted-codebases/mono2micro` (resolves to `/home/ana/repos/ist/tese/extracted-codebases/mono2micro`)
Date: 2026-06-28

mono2micro (SocialSoftware / IST, Rito Silva group) decomposes Spring-Boot monoliths (FenixFramework / Spring Data ORMs) into microservices. It builds weighted similarity matrices over several monolith representations (static accesses, structure, git repository history, and code2vec embeddings), clusters entities with SciPy hierarchical clustering, evaluates the resulting decompositions with coupling/cohesion/complexity/performance metrics, and supports a functionality-redesign step (Saga / local-transaction modelling) plus CML/contract export. Not to be confused with the commercial **IBM Mono2Micro** (analysed separately under `mono2micro_IBM`).

---

## Filled Analysis Template

### Goals

- Decompose a monolith into microservices while minimising the number of system transactions associated with a business transaction, i.e. controlling the relaxed consistency introduced by the decomposition (`README.md — "minimizes the number of system transactions (microservices) associated with a business transaction, aiming to control introduction of relaxed consistency"`).
- Offer multiple decomposition *strategies* over the same codebase and recommend the best parameters per strategy (`backend/.../strategy/domain/Strategy.java:35` lists 7 strategy types; `backend/.../clusteringAlgorithm/SciPyClustering.java:135` `generateMultipleDecompositions`).

### Phases

- **Collection** — external collectors extract representations from a codebase: statically (Spoon AST), dynamically (AspectJ + Kieker runtime traces), or from git (`README.md — "The collectors are responsible for collecting all the necessary data from a given codebase, either with static or dynamic analysis"`; collectors: `collectors/spoon-callgraph`, `collectors/dynamic-collection`, `collectors/structure-collector`, `collectors/commit-collection`, `scripts/code2vec`).
- **Representation building** — the backend turns collected files into `Similarity` matrices weighted by criteria (`backend/.../similarity/domain/SimilarityScipy.java`, `backend/.../similarity/domain/similarityMatrix/weights/`).
- **Clustering / decomposition** — SciPy hierarchical clustering cuts the dendrogram (`scripts/scipyAlgorithm/createDecomposition.py:15`); also an `Expert` import path (`backend/.../clusteringAlgorithm/Expert.java:28`).
- **Quality assessment** — per-decomposition metrics and pairwise comparison (`backend/.../metrics/`, `backend/.../comparisonTool/`).
- **Functionality refactoring** — redesign functionalities into Sagas / local transactions and export a CML contract (`backend/.../functionality/domain/FunctionalityRedesign.java:20`, `tools/cml-converter/README.md`).

### Granularity

- **Entity** (domain/data entity) is the primary unit clustered for the Accesses/Repository/Structure strategies — clusters are filled with `DomainEntity` objects (`backend/.../clusteringAlgorithm/SciPyClustering.java:123`); the structure weights explicitly "Filter out the primitive types and leave only the entities" (`backend/.../similarity/domain/similarityMatrix/weights/StructureWeights.java:135`).
- **Functionality** is a clustering primitive for the functionality-vectorization strategies (`scripts/scipyAlgorithm/createDecomposition.py:165` `clusterPrimitiveType == 'Functionality'`; `Strategy.FUNCTIONALITY_VECTORIZATION_*` at `backend/.../strategy/domain/Strategy.java:40`).
- **Class** is a clustering primitive for the class-vectorization strategy (`scripts/scipyAlgorithm/createDecomposition.py:162` `clusterPrimitiveType == 'Class'`; `Strategy.CLASS_VECTORIZATION_STRATEGY` at `backend/.../strategy/domain/Strategy.java:38`).
- Method / Package / API endpoint are not units of decomposition.

### Representation Collection

#### Collector

##### Source

###### Development

- **Source code** — the Spoon collector statically parses Java source via the Spoon AST library to extract entity accesses / call sequences (`collectors/spoon-callgraph/pom.xml` depends on `fr.inria.gforge.spoon:spoon-core`; `collectors/spoon-callgraph/README.md — "a .json file with the sequence of calls of the program will be created"`). The structure collector extracts entity fields/associations/inheritance (`collectors/structure-collector/README.md`).
- **Version history** — the commit collector reads git history (`collectors/commit-collection/readme.md — "history.py - a class to interact with the history of a repository"`, "`commit_log_script.sh` - scripts to obtain the history of a repository"); produces author and commit co-change files consumed by `RepositoryWeights` (`backend/.../similarity/domain/similarityMatrix/weights/RepositoryWeights.java:92`).
- **Database schema** — not collected directly; entity/field structure is inferred from ORM-annotated source, not from a schema file (`collectors/structure-collector/README.md`).

###### Runtime

- **Runtime log traces** — collected. A dynamic collector instruments the running monolith with AspectJ `@Around` advice and Kieker monitoring probes, emitting `OperationExecutionRecord`s with entry/exit timestamps, trace IDs and execution order (`collectors/dynamic-collection/aspects/AbstractOperationExecutionAspect.java:36`, `:221`; `configs/aop.xml` weaves `pt.ist..*`). The resulting trace JSON (`{id, f, a:[...]}`) is the same format consumed by the backend `TraceDto`, so accesses may be sourced dynamically as an alternative to the static spoon collector.
- User interactions — not collected.

###### Higher-Level Models

- [evidence not found]

###### Documentation

- [evidence not found]

#### Collection Technique

- **Static analysis** — Spoon AST parsing of source code (`collectors/spoon-callgraph/pom.xml`, `fr.inria.gforge.spoon:spoon-core`); code2vec also extracts AST path-contexts statically (`scripts/code2vec/extractor.py`).
- **Dynamic analysis** — AspectJ + Kieker runtime instrumentation of the executing monolith captures operation-execution traces (`collectors/dynamic-collection/aspects/AbstractOperationExecutionAspect.java`); the project README states collectors gather data "either with static or dynamic analysis". Accesses can therefore be obtained from runtime traces in addition to static parsing.
- **Version analysis** — git log mining for author/commit co-change (`collectors/commit-collection/readme.md`).
- Model analysis — not used.

### Representation

#### Analytical

##### Structure

- **Inner structure** — entity fields are read to compute association weights (`StructureWeights.java:226` iterates `entityFields.get(e1ID)`), but fields are used as relationships, not as standalone inner-structure features. Treated as indirect.
  - Trully not present
- **Inheritance** — `heritageWeight`, super/subclass relationships (`StructureWeights.java:90`, `:253` `e1ExtendsE2`/`e2ExtendsE1`).
- **Association** — one-to-one and one-to-many field references between entities (`StructureWeights.java:24` `oneToOneWeight`/`oneToManyWeight`; `:232` `e1Field.getIsList()`).

##### Behavior

- **Call graph** — collectors are call-graph based (`collectors/spoon-callgraph`, `collectors/java-callgraph`, `collectors/code2vec-callgraph`); functionality-vectorization-by-call-graph strategy uses it (`Strategy.FUNCTIONALITY_VECTORIZATION_CALLGRAPH_STRATEGY` at `Strategy.java:40`; `backend/.../similarity/domain/SimilarityScipyFunctionalityVectorizationByCallGraph.java`).
- **Sequence of accesses** — the accesses representation captures ordered read/write accesses per functionality trace, and a `sequenceMetricWeight` rewards consecutive entity-pair accesses (`AccessesWeights.java:27`, `:227` next-access pair counting; `FunctionalityTracesIterator`).
- **Frequency** — traces carry a `frequency` (occurrence count) and accesses an `AccessWithFrequency` (`collectors/dynamic-collection/scripts/src/main/java/domain/AccessWithFrequency.java`; backend `functionality/dto/TraceDto.java:12`); when traces come from the dynamic collector this is genuine *runtime* access frequency. Read/write counts are also tallied per entity pair (`AccessesWeights.java:96`; `createDecomposition.py:117`). Because a dynamic collector exists, the `Frequency → Dynamic analysis OR External` constraint is satisfied.
- CPU level / Memory level / Response time — not captured. (A `Performance` metric exists but it is hop-count based, not runtime response time — see Quality Assessment.)

##### Evolution

- **By contributor** — author co-change: fraction of shared authors between two entities (`RepositoryWeights.java:17` `authorMetricWeight`; `:146` shared-author count).
- **By task** — commit co-change: fraction of commits in which two entities changed together (`RepositoryWeights.java:18` `commitMetricWeight`; `:139` commit-change ratio).

#### Type

- **Monolith** — representations and similarity matrices model the monolith being decomposed (`backend/.../representation/domain/`, `backend/.../similarity/domain/`).
- **Microservices** — the output `Decomposition` of `Partition`/`Cluster` objects is the target microservice architecture (`backend/.../decomposition/domain/PartitionsDecomposition.java`, `backend/.../cluster/Partition.java`).

#### Visualization

##### Elements

- **Granularity view** — individual entities/accesses are rendered (`frontend/src/components/view/accessesViews/`, `frontend/src/components/view/structureView/StructureView.js`).
- **Cluster view** — clusters are rendered as groups (`frontend/src/components/view/utils/ClusterView.js`, `ClusterViewDialogs.js`).

##### Relations

- **Structural relationship** — structure view renders entity associations/inheritance (`frontend/src/components/view/structureView/StructureView.js`).
- **Control flow** — functionality/access views render call/access sequences (`frontend/src/components/view/accessesViews/functionalityView/`).
- **Data flow** — access views render entity read/write data accesses (`frontend/src/components/view/accessesViews/accessView/`).

### Refactoring

#### Domain Knowledge

##### Aggregation Criteria

- **Adjacency** — structural coupling via field associations and inheritance (`StructureWeights.java`), and entity-pair access coupling (`AccessesWeights.java`).
- **Functional** — functional cohesion via shared functionality accesses; entities accessed by the same functionalities are pulled together (`AccessesWeights.java:297` shared-functionality counting; cohesion is functionality-based, `CohesionMetricCalculator.java:23`).
- **Lexical** — code2vec embeddings group entities/classes/functionalities by learned vector similarity (`CodeEmbeddingsRepresentation.java:10`; `scripts/code2vec/`; class/entity/functionality vectorization strategies).
- **Task** — commit co-change (`RepositoryWeights.java:18`).
- **Contributor** — author co-change (`RepositoryWeights.java:17`).

##### Expert knowledge

- An **Expert** clustering path lets the architect upload a hand-made clustering ("expert" decomposition) used as ground truth / starting point (`backend/.../clusteringAlgorithm/Expert.java:28`). The recommendation step also bounds the number of clusters (`SciPyClustering.java:252` `getMaxClusters`). Expert knowledge is used **with hierarchical clustering**, not with community detection or formal concept analysis, so no cross-tree constraint is violated.

#### Services Refactoring

##### Algorithms

- **Hierarchical clustering** — `scipy.cluster.hierarchy.linkage` + `cut_tree` by height or N clusters (`scripts/scipyAlgorithm/createDecomposition.py:15`–`:20`; linkage type configurable, `SciPyClustering.java:62`).
- Community detection / K-means++ / Formal concept analysis / Genetic algorithms / Hungarian algorithm — not used for decomposition. (The MoJoFM utility internally uses a bipartite/Hungarian-style move-join optimisation but that is a *comparison* metric, not a decomposition algorithm — `backend/.../utils/mojoCalculator/`.)

##### Manual Editing

- **Merge of clusters** (`backend/.../operation/merge/MergeOperation.java`).
- **Splitting of clusters** (`backend/.../operation/split/SplitOperation.java`).
- **Transfer of elements between clusters** (`backend/.../operation/transfer/TransferOperation.java`).
- Also **Rename** (`backend/.../operation/rename/RenameOperation.java`) and **Form cluster** from a selection (`backend/.../operation/formCluster/FormClusterOperation.java`) — not in the model (see Gap Candidates).

#### Functionality Refactoring

- **Asynchronization** — functionalities are redesigned into Sagas of local transactions typed COMPENSATABLE / PIVOT / RETRIABLE (`backend/.../functionality/domain/FunctionalityRedesign.java:20`; `backend/.../functionality/LocalTransactionTypes.java:3`), the classic synchronous-to-Saga (async, eventually-consistent) refactoring. CML export turns these into Sagas/Coordinations (`tools/cml-converter/README.md — "refactor functionalities into Sagas"`).
- Granularity refinement — not a distinct feature.
  - Still an feature, should be green

### Quality Assessment

#### Metrics

##### Single Decomposition

- **Coupling** — inter-cluster dependency ratio (`backend/.../metrics/decompositionMetrics/CouplingMetricCalculator.java:13`).
- **Cohesion** — intra-cluster functionality cohesion (`backend/.../metrics/decompositionMetrics/CohesionMetricCalculator.java:14`).
- **Complexity** — distributed-transaction complexity (`backend/.../metrics/decompositionMetrics/ComplexityMetricCalculator.java`; functionality/system/inconsistency complexity under `metrics/functionalityRedesignMetrics/`).
- **Elements size** — `maxClusterSize` is recorded per decomposition (`SciPyClustering.java:175` `decomposition.maxClusterSize()`).
- **Team size** — `TSR` (Team Size Reduction ratio) over per-cluster contributor sets (`backend/.../metrics/decompositionMetrics/TSRMetricCalculator.java:16`).

##### Several Decompositions

- **MoJoFM** — full MoJoFM implementation used to compare two decompositions (`backend/.../comparisonTool/domain/MoJoFM.java`; `backend/.../utils/mojoCalculator/`).
- **Compare metrics** — the comparison tool and recommendation report metric tables across many decompositions (`backend/.../comparisonTool/`, `SciPyClustering.java:177` writes each decomposition's metrics into a recommendation JSON).

##### Benchmarks

- Replication/evaluation packages for ICSA2020 / ECSA2020 with expert ground-truth (`data/icsa2020/README.md`, `backend/src/main/resources/evaluation/`).

#### Graphical Comparison

- **Color** and **Sizes** — cluster views colour and size nodes (`frontend/src/components/view/utils/ClusterView.js`, `GraphUtils.js`).
- The comparison tool view highlights matched/mismatched clusters (`frontend/src/components/comparisonTool/`).
- Distance between elements its present

### Open Issues

- The `STRUCTURE_STRATEGY` is only partially implemented ("A structural based decomposition strategy is not yet implemented. Only the minimum functionality was added", `Strategy.java:28`).

### Extra notes

- Persistence is MongoDB + GridFS; representations/similarity matrices/decompositions are stored as files (`backend/.../fileManager/GridFsService.java`).

---

## Feature Coverage Table

| Feature | Dimension | Supported | Evidence |
|---------|-----------|-----------|----------|
| Method | Granularity | No | [evidence not found] |
| Class | Granularity | Yes | `scripts/scipyAlgorithm/createDecomposition.py:162` (`clusterPrimitiveType == 'Class'`) |
| Entity | Granularity | Yes | `backend/.../clusteringAlgorithm/SciPyClustering.java:123` (`new DomainEntity(...)`); `StructureWeights.java:135` |
| Functionality | Granularity | Yes | `scripts/scipyAlgorithm/createDecomposition.py:165` (`clusterPrimitiveType == 'Functionality'`) |
| Package | Granularity | No | [evidence not found] |
| API endpoint | Granularity | No | [evidence not found] |
| Source code | Repr. Collection > Source > Development | Yes | `collectors/spoon-callgraph/pom.xml` (`spoon-core`); `collectors/structure-collector/README.md` |
| Database schema | Repr. Collection > Source > Development | No | structure is inferred from ORM-annotated source, not a schema file (`collectors/structure-collector/README.md`) |
| Version history | Repr. Collection > Source > Development | Yes | `collectors/commit-collection/readme.md`; `RepositoryWeights.java:92` |
| Runtime log traces | Repr. Collection > Source > Runtime | Yes | `collectors/dynamic-collection/aspects/AbstractOperationExecutionAspect.java:221` (Kieker `OperationExecutionRecord` runtime trace); output trace JSON `{id,f,a}` matches backend `TraceDto` |
| User interactions | Repr. Collection > Source > Runtime | No | [evidence not found] |
| Business process model | Repr. Collection > Source > Higher-Level Models | No | [evidence not found] |
| Use case | Repr. Collection > Source > Higher-Level Models | No | [evidence not found] |
| Data flow diagram | Repr. Collection > Source > Higher-Level Models | No | [evidence not found] |
| Directly in the code | Repr. Collection > Source > Documentation | No | [evidence not found] |
| Paper document | Repr. Collection > Source > Documentation | No | [evidence not found] |
| Digital format | Repr. Collection > Source > Documentation | No | [evidence not found] |
| Static analysis | Repr. Collection > Collection Technique | Yes | `collectors/spoon-callgraph/pom.xml` (Spoon AST); `scripts/code2vec/extractor.py` |
| Dynamic analysis | Repr. Collection > Collection Technique | Yes | `collectors/dynamic-collection/` AspectJ `@Around` weaving (`aspects/AbstractOperationExecutionAspect.java:36`, `configs/aop.xml`); README: collectors collect "either with static or dynamic analysis" |
| Version analysis | Repr. Collection > Collection Technique | Yes | `collectors/commit-collection/readme.md` (git log mining) |
| Model analysis | Repr. Collection > Collection Technique | No | [evidence not found] |
| External | Repr. Collection | No | [evidence not found] |
| Inner structure | Representation > Analytical > Structure | Unclear | `StructureWeights.java:226` reads entity fields, but only as relationships, not standalone |
| Inheritance | Representation > Analytical > Structure > Inter Structure | Yes | `StructureWeights.java:90` (`heritageWeight`), `:253` |
| Association | Representation > Analytical > Structure > Inter Structure | Yes | `StructureWeights.java:24` (`oneToOneWeight`/`oneToManyWeight`), `:232` |
| Call graph | Representation > Analytical > Behavior | Yes | `Strategy.java:40` (functionality-vectorization-call-graph); `collectors/spoon-callgraph` |
| Sequence of accesses | Representation > Analytical > Behavior | Yes | `AccessesWeights.java:27` (`sequenceMetricWeight`), `:227` |
| Frequency | Representation > Analytical > Behavior | Yes | `collectors/dynamic-collection/scripts/.../domain/AccessWithFrequency.java` + `TraceDto` `frequency` field (runtime occurrence count); also `AccessesWeights.java:96` read/write weights. Constraint `Frequency → Dynamic analysis` satisfied. |
| CPU level | Representation > Analytical > Behavior | No | [evidence not found] |
| Memory level | Representation > Analytical > Behavior | No | [evidence not found] |
| Response time | Representation > Analytical > Behavior | No | `PerformanceMetricCalculator.java:12` is hop-count, not runtime response time |
| By contributor | Representation > Analytical > Evolution | Yes | `RepositoryWeights.java:17` (`authorMetricWeight`), `:146` |
| By task | Representation > Analytical > Evolution | Yes | `RepositoryWeights.java:18` (`commitMetricWeight`), `:139` |
| Monolith | Representation > Type | Yes | `backend/.../representation/domain/`; similarity matrices model the monolith |
| Microservices | Representation > Type (mandatory) | Yes | `backend/.../decomposition/domain/PartitionsDecomposition.java` (output clusters) |
| Granularity view | Representation > Visualization > Elements (mandatory) | Yes | `frontend/src/components/view/structureView/StructureView.js` |
| Cluster view | Representation > Visualization > Elements | Yes | `frontend/src/components/view/utils/ClusterView.js` |
| Structural relationship | Representation > Visualization > Relations | Yes | `frontend/src/components/view/structureView/StructureView.js` |
| Control flow | Representation > Visualization > Relations | Yes | `frontend/src/components/view/accessesViews/functionalityView/` |
| Data flow | Representation > Visualization > Relations | Yes | `frontend/src/components/view/accessesViews/accessView/` |
| Task | Refactoring > Aggregation Criteria | Yes | `RepositoryWeights.java:18` (commit co-change) |
| Contributor | Refactoring > Aggregation Criteria | Yes | `RepositoryWeights.java:17` (author co-change) |
| Lexical | Refactoring > Aggregation Criteria | Yes | `CodeEmbeddingsRepresentation.java:10`; `scripts/code2vec/` |
| Functional | Refactoring > Aggregation Criteria | Yes | `AccessesWeights.java:297`; `CohesionMetricCalculator.java:23` |
| Adjacency | Refactoring > Aggregation Criteria | Yes | `StructureWeights.java` (associations + inheritance); `AccessesWeights.java` |
| Expert knowledge | Refactoring > Domain Knowledge | Yes | `backend/.../clusteringAlgorithm/Expert.java:28`; `SciPyClustering.java:252` |
| Hierarchical clustering | Refactoring > Services Refactoring > Algorithms | Yes | `scripts/scipyAlgorithm/createDecomposition.py:15` (`hierarchy.linkage`) |
| Community detection | Refactoring > Services Refactoring > Algorithms | No | [evidence not found] |
| K-means++ | Refactoring > Services Refactoring > Algorithms | No | [evidence not found] |
| Formal concept analysis | Refactoring > Services Refactoring > Algorithms | No | [evidence not found] |
| Genetic algorithms | Refactoring > Services Refactoring > Algorithms | No | [evidence not found] |
| Hungarian algorithm | Refactoring > Services Refactoring > Algorithms | No | used only inside MoJoFM comparison, not for decomposition (`backend/.../utils/mojoCalculator/`) |
| Merge of clusters | Refactoring > Services Refactoring > Manual Editing | Yes | `backend/.../operation/merge/MergeOperation.java` |
| Splitting of clusters | Refactoring > Services Refactoring > Manual Editing | Yes | `backend/.../operation/split/SplitOperation.java` |
| Transfer of elements between clusters | Refactoring > Services Refactoring > Manual Editing | Yes | `backend/.../operation/transfer/TransferOperation.java` |
| Asynchronization | Refactoring > Functionality Refactoring | Yes | `backend/.../functionality/domain/FunctionalityRedesign.java:20`; `LocalTransactionTypes.java:3` |
| Granularity refinement | Refactoring > Functionality Refactoring | No | [evidence not found] |
| Coupling | Quality Assessment > Single Decomposition | Yes | `backend/.../metrics/decompositionMetrics/CouplingMetricCalculator.java:13` |
| Cohesion | Quality Assessment > Single Decomposition | Yes | `backend/.../metrics/decompositionMetrics/CohesionMetricCalculator.java:14` |
| Elements size | Quality Assessment > Single Decomposition (mandatory) | Yes | `SciPyClustering.java:175` (`maxClusterSize`) |
| Complexity | Quality Assessment > Single Decomposition | Yes | `backend/.../metrics/decompositionMetrics/ComplexityMetricCalculator.java` |
| Team size | Quality Assessment > Single Decomposition | Yes | `backend/.../metrics/decompositionMetrics/TSRMetricCalculator.java:16` (TSR) |
| MoJoFM | Quality Assessment > Several Decompositions (mandatory) | Yes | `backend/.../comparisonTool/domain/MoJoFM.java`; `backend/.../utils/mojoCalculator/` |
| Compare metrics | Quality Assessment > Several Decompositions | Yes | `backend/.../comparisonTool/`; `SciPyClustering.java:177` |
| Color | Quality Assessment > Graphical Comparison | Yes | `frontend/src/components/view/utils/ClusterView.js`, `GraphUtils.js` |
| Sizes | Quality Assessment > Graphical Comparison | Yes | `frontend/src/components/view/utils/GraphUtils.js` |
| Distance between elements | Quality Assessment > Graphical Comparison | Unclear | force-directed graph layout positions nodes by similarity (`frontend/src/components/view/utils/GraphUtils.js`) but not an explicit comparison feature |

---

## Observations

### Model Gap Candidates

- **Silhouette score**
  - **Would be:** leaf under Quality Assessment > Metrics > Single Decomposition.
  - **Evidence:** `scripts/scipyAlgorithm/createDecomposition.py:31` (`metrics.silhouette_score`); surfaced as a decomposition metric at `SciPyClustering.java:81` (`addMetric("Silhouette Score", ...)`).
  - **Rationale:** an internal clustering-quality metric distinct from coupling/cohesion that the tool computes and reports for every decomposition; recurs in other clustering tools.

- **Purity (against an expert/reference decomposition)**
  - **Would be:** leaf under Quality Assessment > Metrics > Several Decompositions (alongside MoJoFM).
  - **Evidence:** `backend/.../comparisonTool/domain/Purity.java:11`.
  - **Rationale:** a second comparison metric (besides MoJoFM) that scores a decomposition against a ground-truth/expert one; the model currently only lists MoJoFM and "Compare metrics".

- **Performance / transaction-hop metric**
  - **Would be:** leaf under Quality Assessment > Metrics > Single Decomposition (a static performance proxy), or a note that "Response time" needs a static counterpart.
  - **Evidence:** `backend/.../metrics/decompositionMetrics/PerformanceMetricCalculator.java:12` ("the average of the number of hops between clusters for all traces").
  - **Rationale:** the model's only performance-flavoured features (CPU/Memory/Response time) are runtime-derived; this is a static, decomposition-level performance estimate with no slot.

- **Rename cluster (manual editing operation)**
  - **Would be:** leaf under Refactoring > Services Refactoring > Manual Editing (alongside Merge/Split/Transfer).
  - **Evidence:** `backend/.../operation/rename/RenameOperation.java`.
  - **Rationale:** a first-class manual-editing operation the model does not list.

- **Form cluster from selection (manual editing operation)**
  - **Would be:** leaf under Refactoring > Services Refactoring > Manual Editing.
  - **Evidence:** `backend/.../operation/formCluster/FormClusterOperation.java`.
  - **Rationale:** creating a new cluster from a hand-picked set of elements is a distinct manual operation beyond Merge/Split/Transfer.

- **Contract / CML export (post-decomposition artefact generation)**
  - **Would be:** leaf or group under Refactoring > Functionality Refactoring (a "contract/IDL generation" sibling).
  - **Evidence:** `tools/cml-converter/README.md` (generates Context Mapper CML: Bounded Contexts, Aggregates, Services, Sagas); contract export in `backend/.../functionality/`.
  - **Rationale:** generating a formal architecture description (CML / contract JSON) from the decomposition is a refactoring post-processing step with no counterpart in the model.

### Other features outside the model

- **Recommendation / parameter sweep** — automatic generation of many decompositions across weight combinations and cluster counts to recommend the best parameters (`backend/.../recommendation/`, `SciPyClustering.java:135`). This is an orchestration/search capability, too tool-specific to be a feature.
- **Code2Vec embedding model** — a learned neural representation (`scripts/code2vec/`); captured at the model level as the "Lexical" aggregation criterion, but the embedding technique itself is too low-level for the model.
- **Linkage type / cut type (height vs N clusters)** — hierarchical-clustering hyper-parameters (`createDecomposition.py:17`–`:20`); configuration detail, not a feature.
- **Weighted multi-criteria similarity matrix** — the tool blends several weighted criteria into one matrix (`similarity/domain/similarityMatrix/weights/`); an implementation mechanism rather than a model feature.

### Model Vocabulary Fit

- **"Frequency" (Behavior).** The model implies runtime call/access frequency (it requires Dynamic analysis OR External). mono2micro satisfies this: traces/accesses carry a runtime `frequency` produced by the dynamic (Kieker) collector (`AccessWithFrequency.java`, `TraceDto.java:12`). The static spoon collector also produces read/write counts (`AccessesWeights.java:96`), so frequency can be sourced either way; with the dynamic collector present the model's collection constraint holds.
- **"Response time" (Behavior).** mono2micro has a `Performance` metric, but it counts inter-cluster hops, not wall-clock response time — a different concept under the same word.
- **"Task"/"Contributor" (Aggregation Criteria).** mono2micro's "Repository" strategy mixes both (commit co-change = Task, author co-change = Contributor) into one strategy; the model splits them cleanly, which fits but slightly over-separates the tool's single strategy.
- **"Functional" vs "Adjacency".** The Accesses strategy is simultaneously functional (shared-functionality cohesion) and adjacency (entity-pair access coupling); a single matrix realises both criteria, so the boundary is blurry in the tool.

### Cross-tree constraint violations

- **None.** Earlier runs flagged `Frequency → Dynamic analysis OR External` as violated, on the assumption that mono2micro was static-only. That is incorrect: a dynamic (AspectJ + Kieker) collector exists (`collectors/dynamic-collection/`), so Dynamic analysis is present and the Frequency constraint is satisfied. `Frequency` is therefore `Light_Green`, not `Orange`.
- Expert knowledge is used **only** with hierarchical clustering (`Expert.java`, `SciPyClustering.java`), never with community detection or formal concept analysis, so the `Community detection → NOT Expert knowledge` / `Formal concept analysis → NOT Expert knowledge` constraints are **not** violated.

### Noteworthy design decisions

- **One weighted similarity matrix, many criteria.** Rather than separate pipelines, mono2micro fuses structural, behavioural, evolutionary and embedding signals into a single weighted distance matrix, then runs one clustering algorithm — a clean way to make criteria composable.
- **Consistency-first objective.** The decomposition objective is to minimise distributed-transaction (relaxed-consistency) complexity, not just coupling/cohesion; this drives the functionality-redesign-into-Sagas step and the complexity/inconsistency metrics.
- **Strategy/representation indirection.** Strategies declare which representations and representation-types they need (`Strategy.java:43`), making it cheap to add new criteria (e.g. the code2vec vectorization strategies reuse the same clustering backend).
- **Expert as ground truth.** Uploaded expert decompositions double as both a starting point and the reference for MoJoFM/Purity comparison, integrating manual knowledge and evaluation in one mechanism.
- **CML / Context Mapper bridge.** Exporting to a formal DDD modelling language (CML) positions the tool's output as the input to downstream architecture tooling, beyond a one-off clustering.
- **Partially-implemented Structure strategy.** The structural decomposition strategy is explicitly stubbed (`Strategy.java:28`); structure data is collectable and exportable but not a fully-fledged decomposition driver.
- **Dual collection paths for accesses.** Accesses feeding the similarity matrix can be produced either statically (Spoon AST) or dynamically (AspectJ + Kieker runtime traces), both emitting the same `{id, f, a}` trace JSON. The static path is the documented default; the dynamic collector is present in-tree.

---

## Reconciliation Log

Date: 2026-06-28
Versions compared: `73d063a` / `e83c6fd` / `8fa8699` / `29f7dfc` (Gen A — first run, identical tables modulo the "Syntax"→"Analytical" rename), `cc53285` (Gen B — second rerun), `d9b7b1c` (Gen C — third rerun, = parent of working tree), working tree.

| Feature | From → To | Adjudicating evidence | Which version(s) were wrong |
|---------|-----------|-----------------------|-----------------------------|
| Runtime log traces | No → Yes | `collectors/dynamic-collection/aspects/AbstractOperationExecutionAspect.java:36,221` (AspectJ `@Around` + Kieker `OperationExecutionRecord`); output `{id,f,a}` JSON matches backend `TraceDto` | Gen B + Gen C marked No (Gen A had it Yes) |
| Dynamic analysis | No → Yes | `collectors/dynamic-collection/configs/aop.xml` weaves `pt.ist..*`; README: collectors collect "either with static or dynamic analysis" | Gen B + Gen C marked No (Gen A had it Yes) |
| Frequency | Yes (Orange constraint violation) → Yes (no violation) | dynamic collector exists ⇒ `Frequency → Dynamic analysis OR External` satisfied; `domain/AccessWithFrequency.java`, `TraceDto.java:12` | Gen C wrongly flagged Orange violation |

Verdicts already correct in Gen C (current) and confirmed against evidence this run: Method=No (`createDecomposition.py` has only Class/Functionality/Entity primitives), Functionality=Yes (`createDecomposition.py:165`), Inner structure=Unclear (fields used only as relationships, `StructureWeights.java`), Elements size=Yes (`SciPyClustering.java:175`), Asynchronization=Yes (`FunctionalityType.SAGA`, `LocalTransactionTypes`), Granularity refinement=No (no "refine" in repo), Microservices=Yes, Data flow=Yes. These were the features where Gen A or Gen B disagreed but Gen C was right.

Features still genuinely Unclear after adjudication: **Inner structure** (entity fields are read but only to compute association/inheritance weights, never as a standalone inner-structure feature — `StructureWeights.java:125`–`165`); **Distance between elements** (the cluster view uses a `barnesHut` force/physics layout — `frontend/.../GraphUtils.js:24`–`28` — that positions connected nodes closer, but there is no explicit similarity-distance comparison feature).


### Profile fix (2026-06-28) — AND "fully satisfied" propagation rule

**Profile-only change; no analysis content was reviewed or altered in this pass.** A
cross-cutting correction to the group-propagation rule (made explicit in `codebase-map`,
`docs-map`, `verify-analysis`) was applied to `mono2micro.profile`: an AND node is only
`Dark_Green` ("Group: fully satisfied") when every **mandatory** child is fully
satisfied — a present **leaf** counts (`Light_Green` is a leaf's max; leaves are never
`Dark_Green`), but a mandatory child **group** that is only `Light_Green` (partially
satisfied) caps the AND parent at `Light_Green`. The previous derivation treated a merely
*present* mandatory child group as enough for `Dark_Green`, overstating coverage.

AND cells changed `Dark_Green` → `Light_Green` in `mono2micro.profile`: `Collector`, `Visualization`, `Representation`, `Domain Knowledge`, `Services Refactoring`, `Refactoring`, `Quality Assessment`, `Microservices Decomposition and Refactoring (root)`. (Nodes
already at a higher-priority colour — `Red`/`Orange`/`Magenta` — were unaffected; AND
nodes whose mandatory child is a present leaf, e.g. `Type`, correctly stay `Dark_Green`.)