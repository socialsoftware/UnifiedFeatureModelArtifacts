# Analysis — Micro2Micro

Codebase path: ../extracted-codebases/Micro2micro
Date: 2026-06-28

---

## Filled Analysis Template

### Goals

- Micro2Micro **refactors an existing microservice architecture into a better microservice architecture** (microservices-to-microservices), in support of evolutionary design, rather than decomposing a monolith. The user selects a subset of existing services to be re-partitioned (`Micro2MicroRefactoring_Experiment.java:39-50` — service sizes 2–4; `PreProcessing.getRefactoringFile:181-218` reads the services-to-refactor list from `task.txt`).
- It performs an **interactive, multi-objective search** that proposes Pareto-optimal re-partitionings and lets a developer steer them with must-link / cannot-link relations (`Micro2Micro.beginEvolution:43-76`, `InteractionHandler`, `UIController.addConstraint:100-108`).

### Phases

- **Pre-processing** — load the existing architecture (`package.json`), the structural dependency graph (`relationWeight.json`), semantic tokens (`words.dat`), and co-change history (`commit2json.json`); split classes into a refactoring part and a frozen non-refactoring part (`PreProcessing.java:43-50`, `getOriginalService:278-327`).
- **Search** — NSGA-II evolutionary loop (crossover + mutation + fast non-dominated sorting + crowding distance) optimising three modularity objectives (`Micro2Micro.beginAnEpoch:83-110`).
- **Interaction** — between epochs, constraints (real user via web GUI, or a simulated user model) are added and propagated by tweaking individuals (`InteractionSimulation.handleSeveralConstraints:121-156`, `InteractionHandler.handleOneConstraint:17-56`).
- **Post-processing** — stitch the refactored part back with the frozen services and export results to Excel (`Individual.stitchingCompleteArchitecture:153-166`, `PostProcessing.writeExcel`).

### Granularity

- The unit of decomposition is the **class / source file**. Entities are file names mapped to integer IDs via the `fileSequence` field (`PreProcessing.mapFileName2ID:255-272`), each assigned to a service in the solution vector `valueList` (`Individual.java:13-14`, comment "每个类被分配的微服务编号" = "the microservice ID assigned to each class").

### Representation Collection

#### Collector

##### Source

###### Development

- **Source code** — a class-to-class call/dependency graph is read from `relationWeight.json` (`dependGraph` matrix) (`StructureMatrixService.getInput:105-122`).
- **Version history** — commit co-change is read from `commit2json.json`; for every commit, the changed files (`document` list) are linked pairwise into a co-change matrix (`EvolutionaryMatrixService.getInput:60-106`).
- **Database schema** — [evidence not found].

##### Runtime

- [evidence not found] — no runtime traces or user-interaction logs are consumed; the only "interaction" is design-time must/cannot-link feedback, not runtime monitoring.

##### Higher-Level Models

- [evidence not found].

##### Documentation

- [evidence not found] for code-as-input; the `words.dat` semantic tokens are lexical content extracted from the code (see Lexical below), not separate documentation.

#### Collection Technique

- **Version analysis** — co-change is computed **in-tool** from a *raw* commit log: `commit2json.json` is a per-commit list of changed files (`{commitKey: {document: [...]}}`), and `EvolutionaryMatrixService.getInput:60-106` builds the co-change matrix itself (mapping file names to IDs and incrementing `coChangeMatrix[i][j]` for co-changed pairs, `:91-95`). Unlike the structural/lexical inputs, this representation is derived in-house, so it is genuine Version analysis, not External.
- **Static analysis** — [evidence not found] as an in-tool step. No AST parse, tokenisation, or dependency extraction happens in this package: the structural call/dependency graph and the per-class token bags both arrive pre-built (see External below). The tool computes cosine similarity over the pre-extracted tokens (`SemanticMatrixService.getSimi:81-135`), but building the underlying lexical/structural representation is not done here.

#### External

- The structural call/dependency graph (`dependGraph`) is read **pre-computed** from `relationWeight.json` (`StructureMatrixService.getInput:105-122`); the tool consumes the matrix but never parses the AST that produced it. Likewise, the per-class token bags in `words.dat` are read pre-extracted (`SemanticMatrixService.getList:47-78`) — the tokeniser is not in the package. So the structural and lexical *representations* are supplied by external upstream tooling, which the model captures via the **External** collector rather than in-house Static analysis.

### Representation

#### Analytical

##### Structure

- **Association (call dependency)** — `dependencyMatrix[i][j]` records how much class i calls/depends on class j; the derived structural weight reflects call coupling and shared resource/end-node usage (`StructureMatrixService.getDCW:46-64`, `getDRW:72-84`, `getDEW:86-98`).
- **Inner structure / Inheritance** — [evidence not found]; only inter-class call dependencies are modelled.

##### Behavior

- **Call graph** — the structural matrix is built from a directed call/dependency graph (`StructureMatrixService.getInput:108` reads `dependGraph`). It is a static call-dependency graph, not a runtime call trace.
- Frequency / CPU / Memory / Response time — [evidence not found]; `dependencyMatrix` counts are collapsed to binary weights (`calculateWeightMatrix:124-132`), so call frequency is discarded.

##### Evolution

- **By task (commit co-change)** — co-change is computed per commit over the changed-file set (`EvolutionaryMatrixService.getInput:66-98`). There is no author/contributor dimension.

#### Type

- **Microservices** — both the input *and* the target are microservice architectures. The "original" architecture being improved is itself a set of microservices (`PreProcessing.getOriginalService:278-327` reads `existingArchitecture` as a map of services→files; `Micro2MicroRefactoring_Experiment.java:39` iterates service sizes 2–4).
- **Monolith** — *not* the input. The tool always ingests an existing *microservice* architecture (`PreProcessing.getOriginalService:278-327` reads `package.json` as a service→files map, comment "iterate all the microservices in the system"). `QualityMeasurement.calculateBipartiteConnectivity:86-88` special-cases a monolith scenario (`notRefServiceNum==0` → skip bipartite coupling), but this is a defensive guard the pipeline never constructs, not a supported input mode, so **No**.

#### Visualization

##### Elements

- **Granularity view** and **Cluster view** — the Vue front-end renders the architecture per service. `ArchitectureView.vue` lays out one Ionic card per service with its classes listed inside (`MicroBoundariesFront/src/components/content/ArchitectureView.vue:5-19`, `:color="item.color"`), and `UsedResult.vue` renders the class-level network via vis.js (`new vis.Network`, `UsedResult.vue:111-160`). Backend `UIController.getRefactoringSolution:85-98` returns per-solution / per-service architecture (`serviceID -1` = service-level view). (Note: `echarts` is a declared dependency but is **not** used for rendering — its only import is `import { time } from "echarts"` in `App.vue:8`; the actual renderers are vis.js and Ionic.)

##### Relations

- **Structural relationship** — the vis.js network draws edges typed `structural` as directed arrows over the structural dependency data (`UsedResult.vue:86-93` — `if(edgeArray[3]==="structural"){ temp.arrows="to" }`; `serviceLink` edges are hidden). Control/data flow relations are not separately visualised.

### Refactoring

#### Domain Knowledge

##### Aggregation Criteria

- **Adjacency (structural coupling)** — structural connectivity drives the structural objective (`QualityMeasurement.calculateStructuralQ:298-306`).
- **Lexical** — semantic/conceptual similarity over class token vectors drives the conceptual objective (`QualityMeasurement.calculateConceptualQ:308-317`, `SemanticMatrixService.getSimi:81-135`).
- **Task** — commit co-change drives the evolutionary objective (`QualityMeasurement.calculateEvolutionaryQ:319-328`).
- **Functional / Contributor** — [evidence not found].

##### Expert knowledge

- **Must-link / cannot-link constraints** supplied by the developer steer the search: type `1` = must-link, `-1` = cannot-link (`Constraint.java:25`), added via the GUI (`UIController.addConstraint:100-108`) or a simulated user model (`InteractionSimulation.createOneConstraint:70-112`) and propagated by moving classes between services (`InteractionHandler.mustLinkConstraintPropagator:112-208`, `cannotLinkConstraintPropagator:292-363`).

#### Services Refactoring

##### Algorithms

- **Genetic algorithm (NSGA-II)** — crossover, mutation, fast non-dominated sorting and crowding-distance selection over a population of partitionings (`Micro2Micro.beginAnEpoch:83-110`, `FastNonDominatedSorting`, `Ranking.crowdingDistanceAssignment`, `Crossover`, `Mutation`). No hierarchical clustering, community detection, k-means, FCA or Hungarian algorithm is used (grep for these returned no matches).

##### Manual Editing

- Editing happens **indirectly** through must/cannot-link constraints rather than direct merge/split/transfer buttons. A must-link effectively *transfers* a class (and its must-linked group) into another service; a cannot-link forces a class out of a service (`InteractionHandler.moveClassesAmongServices:365-371`). A must-link propagator can also *split* a service when it would otherwise collapse (`postProcessingForMustLinkConstraint:216-275`). So Transfer and Split are present as side-effects, not as first-class manual operations. (Marked Unclear / Magenta.)
  - This should count as expert knowledge instead of manual editing, because the user does not directly invoke a split/transfer operation; it is a side-effect of constraint propagation.

#### Functionality Refactoring

- [evidence not found] — no asynchronisation or post-decomposition granularity-refinement transformation.

### Quality Assessment

#### Metrics

##### Single Decomposition

- **Coupling** — inter-service connectivity (`QualityMeasurement.calculateInterConnectivity:199-296`) plus bipartite coupling to the frozen part (`calculateBipartiteConnectivity:81-148`).
- **Cohesion** — intra-service connectivity (`calculateServiceIntraConnectivity:150-171`, `calculateIntraConnectivity:187-190`).
- The three optimisation objectives are structural Q, conceptual Q, evolutionary Q = intra − inter − bipartite for each matrix (`calculateStructuralQ/ConceptualQ/EvolutionaryQ:298-328`).
- **SMQ / CMQ / EMQ** modularity quality (structural / conceptual / evolutionary modularity = SCOH − SCOP) are also computed (`evaluateSMQ:346-390`, `evaluateCMQ:392-437`, `evaluateEMQ:439-483`).
- **Elements size** — service size is tracked operationally (e.g. `mustLinkConstraintPropagator:117-119`) but is not reported as a quality metric. (Mandatory leaf → Red.)
- Complexity / Team size — [evidence not found].

##### Several Decompositions

- **MoJoFM** — implemented as the move-and-join distance between two partitionings (`DistanceMeasurement.calculateMoJo:48-?`, `calculateEffort:32-37`, `calculateMaxMoJo:110`). Used as a *diversity* criterion to keep the initial population spread out (`PopulationInitializer.java:65,97` via `isIndividualAcceptable:16-25`) and as the effort to transform original→suggested. It compares multiple decompositions, so the "Several Decompositions" branch applies.
- **Compare metrics** — the Pareto front yields many solutions compared on the three objectives; the GUI shows used vs remaining results (`MicroBoundariesFront/src/components/content/UsedResult.vue`, `RemainingResult.vue`).

#### Graphical Comparison

- **Color** — the vis.js network colours each node by its service (`UsedResult.vue:153-157` — `color: colorlist[parseInt(str)+1]`) and the architecture cards colour each class by constraint status (`ArchitectureView.vue:85-91` — `Must`→secondary, `Cannot`→warning). Colour therefore distinguishes *services / constraint state within a single decomposition*, not a comparison *across* decompositions (the intent of the Graphical Comparison leaf). Marked Unclear / Magenta — colour is present but its purpose does not match the "compare decompositions" intent.
  - Visualization not Comparison

### Open Issues

- The structural graph (`relationWeight.json`) and semantic tokens (`words.dat`) are **pre-computed** inputs — the AST parser and tokenizer that produce them are not in this replication package, so their collection is **External**. The commit input (`commit2json.json`) is a *raw* commit log, and the co-change matrix is built in-tool (`EvolutionaryMatrixService:60-106`), so Version analysis is genuinely in-house.

### Extra notes

- The tool freezes a *non-refactoring part* and only re-partitions selected services; coupling to the frozen part is penalised via bipartite connectivity (`QualityMeasurement.calculateBipartiteConnectivity:81-148`).

---

## Feature Coverage Table

| Feature | Dimension | Supported | Evidence |
|---------|-----------|-----------|----------|
| Method | Granularity | No | [evidence not found] |
| Class | Granularity | Yes | `PreProcessing.mapFileName2ID:255-272` (`fileSequence`); `Individual.java:13-14` (per-class service ID) |
| Entity | Granularity | No | [evidence not found] |
| Functionality | Granularity | No | [evidence not found] |
| Package | Granularity | No | [evidence not found] (`package.json` groups files into *services*, not packages-as-granularity) |
| API endpoint | Granularity | No | [evidence not found] |
| Source code | Repr. Collection > Source > Development | Yes | `StructureMatrixService.getInput:105-122` (`dependGraph`); `SemanticMatrixService.getSimi:81-135` |
| Database schema | Repr. Collection > Source > Development | No | [evidence not found] |
| Version history | Repr. Collection > Source > Development | Yes | `EvolutionaryMatrixService.getInput:60-106` (`commit2json.json`) |
| Runtime log traces | Repr. Collection > Source > Runtime | No | [evidence not found] |
| User interactions | Repr. Collection > Source > Runtime | No | [evidence not found] (design-time must/cannot-link is not a runtime trace) |
| Business process model | Repr. Collection > Source > Higher-Level Models | No | [evidence not found] |
| Use case | Repr. Collection > Source > Higher-Level Models | No | [evidence not found] |
| Data flow diagram | Repr. Collection > Source > Higher-Level Models | No | [evidence not found] |
| Directly in the code | Repr. Collection > Source > Documentation | No | [evidence not found] |
| Paper document | Repr. Collection > Source > Documentation | No | [evidence not found] |
| Digital format | Repr. Collection > Source > Documentation | No | [evidence not found] |
| Static analysis | Repr. Collection > Collection Technique | No | No in-repo AST parse/tokenisation; `StructureMatrixService.getInput:105-122` and `SemanticMatrixService.getList:47-78` consume pre-built representations → satisfied via External, not Static analysis |
| Dynamic analysis | Repr. Collection > Collection Technique | No | [evidence not found] |
| Version analysis | Repr. Collection > Collection Technique | Yes | `EvolutionaryMatrixService.getInput:60-106` computes co-change in-tool from a raw commit log (`:91-95`) |
| Model analysis | Repr. Collection > Collection Technique | No | [evidence not found] |
| External | Repr. Collection | Yes | `StructureMatrixService.getInput:105-122` reads a pre-built `dependGraph`; `SemanticMatrixService.getList:47-78` reads pre-extracted `words.dat` token bags — the AST parser/tokeniser that produced them are not in the package |
| Inner structure | Representation > Analytical > Structure | No | [evidence not found] |
| Inheritance | Representation > Analytical > Inter Structure | No | [evidence not found] |
| Association | Representation > Analytical > Inter Structure | Yes | `StructureMatrixService.getDCW:46-64` (call dependency) |
| Call graph | Representation > Analytical > Behavior | Yes | `StructureMatrixService.getInput:108` (`dependGraph` directed call matrix) |
| Sequence of accesses | Representation > Analytical > Behavior | No | [evidence not found] |
| Frequency | Representation > Analytical > Behavior | No | counts collapsed to binary (`calculateWeightMatrix:124-132`) |
| CPU level | Representation > Analytical > Behavior | No | [evidence not found] |
| Memory level | Representation > Analytical > Behavior | No | [evidence not found] |
| Response time | Representation > Analytical > Behavior | No | [evidence not found] |
| By contributor | Representation > Analytical > Evolution | No | [evidence not found] |
| By task | Representation > Analytical > Evolution | Yes | `EvolutionaryMatrixService.getInput:66-98` (per-commit co-change) |
| Monolith | Representation > Type | No | input is always a *microservice* architecture (`getOriginalService:278-327`); monolith is only an anticipated guard (`calculateBipartiteConnectivity:86-88`), never constructed |
| Microservices | Representation > Type | Yes | `PreProcessing.getOriginalService:278-327` (existing services); solution = service assignment per class |
| Granularity view | Representation > Visualization > Elements | Yes | `UsedResult.vue:111-160` (vis.js node-per-class network); `UIController.getRefactoringSolution:85-98` |
| Cluster view | Representation > Visualization > Elements | Yes | `ArchitectureView.vue:5-19` (one card per service); `UIController.getRefactoringSolution:88-97` (`serviceID -1` = service level) |
| Structural relationship | Representation > Visualization > Relations | Yes | `UsedResult.vue:86-93` (vis.js edges typed `structural` drawn as directed arrows) |
| Control flow | Representation > Visualization > Relations | No | [evidence not found] |
| Data flow | Representation > Visualization > Relations | No | [evidence not found] |
| Task | Refactoring > Aggregation Criteria | Yes | `QualityMeasurement.calculateEvolutionaryQ:319-328` (co-change objective) |
| Contributor | Refactoring > Aggregation Criteria | No | [evidence not found] |
| Lexical | Refactoring > Aggregation Criteria | Yes | `QualityMeasurement.calculateConceptualQ:308-317`; `SemanticMatrixService.getSimi:81-135` |
| Functional | Refactoring > Aggregation Criteria | No | [evidence not found] |
| Adjacency | Refactoring > Aggregation Criteria | Yes | `QualityMeasurement.calculateStructuralQ:298-306` |
| Expert knowledge | Refactoring > Domain Knowledge | Yes | `Constraint.java:25`; `UIController.addConstraint:100-108`; `InteractionHandler.mustLinkConstraintPropagator:112-208` |
| Hierarchical clustering | Refactoring > Services Refactoring > Algorithms | No | [evidence not found] |
| Community detection | Refactoring > Services Refactoring > Algorithms | No | [evidence not found] |
| K-means++ | Refactoring > Services Refactoring > Algorithms | No | [evidence not found] |
| Formal concept analysis | Refactoring > Services Refactoring > Algorithms | No | [evidence not found] |
| Genetic algorithms | Refactoring > Services Refactoring > Algorithms | Yes | `Micro2Micro.beginAnEpoch:83-110` (NSGA-II); `Crossover`, `Mutation`, `FastNonDominatedSorting` |
| Hungarian algorithm | Refactoring > Services Refactoring > Algorithms | No | [evidence not found] (grep returned no matches) |
| Merge of clusters | Refactoring > Services Refactoring > Manual Editing | No | [evidence not found] |
| Splitting of clusters | Refactoring > Services Refactoring > Manual Editing | Unclear | side-effect of must-link propagation (`postProcessingForMustLinkConstraint:216-275`), not a manual op |
| Transfer of elements between clusters | Refactoring > Services Refactoring > Manual Editing | Unclear | indirect via constraint propagation (`moveClassesAmongServices:365-371`) |
| Asynchronization | Refactoring > Functionality Refactoring | No | [evidence not found] |
| Granularity refinement | Refactoring > Functionality Refactoring | No | [evidence not found] |
| Coupling | Quality Assessment > Metrics > Single Decomposition | Yes | `QualityMeasurement.calculateInterConnectivity:199-296`, `calculateBipartiteConnectivity:81-148` |
| Cohesion | Quality Assessment > Metrics > Single Decomposition | Yes | `QualityMeasurement.calculateIntraConnectivity:150-190` |
| Elements size | Quality Assessment > Metrics > Single Decomposition | No | tracked operationally (`mustLinkConstraintPropagator:117-119`) but not reported as a metric |
| Complexity | Quality Assessment > Metrics > Single Decomposition | No | [evidence not found] |
| Team size | Quality Assessment > Metrics > Single Decomposition | No | [evidence not found] |
| MoJoFM | Quality Assessment > Metrics > Several Decompositions | Yes | `DistanceMeasurement.calculateEffort:32-37`, `calculateMoJo:48-`, used at `PopulationInitializer.java:65,97` |
| Compare metrics | Quality Assessment > Metrics > Several Decompositions | Yes | Pareto front over 3 objectives; `UsedResult.vue` / `RemainingResult.vue` |
| Color | Quality Assessment > Graphical Comparison | Unclear | colour distinguishes services / constraint state within one decomposition, not across decompositions (`UsedResult.vue:153-157`; `ArchitectureView.vue:85-91`) |
| Sizes | Quality Assessment > Graphical Comparison | No | [evidence not found] |
| Distance between elements | Quality Assessment > Graphical Comparison | No | [evidence not found] |

---

## Observations

### Model Gap Candidates

- **Interactive / search-guiding constraints (must-link & cannot-link)**
  - **Would be:** a leaf (or pair of leaves) under *Refactoring > Domain Knowledge > Expert knowledge*, distinguishing *pairwise relational constraints* from generic "rules/thresholds".
  - **Evidence:** `Constraint.java:25` (type 1 = must-link, −1 = cannot-link), `InteractionHandler.mustLinkConstraintPropagator:112-208`, `UIController.addConstraint:100-108`.
  - **Rationale:** must-link/cannot-link (semi-supervised clustering constraints) are a recurring, distinctive way experts steer decomposition and deserve to be named rather than folded into a generic "Expert knowledge" leaf.

- **Modularity Quality (MQ / SMQ-CMQ-EMQ) metric family**
  - **Would be:** a leaf under *Quality Assessment > Metrics > Single Decomposition*, alongside Coupling/Cohesion.
  - **Evidence:** `QualityMeasurement.evaluateSMQ:346-390`, `evaluateCMQ:392-437`, `evaluateEMQ:439-483` (SCOH − SCOP).
  - **Rationale:** MQ (cohesion-minus-coupling modularity) is a standard composite metric across decomposition tools and is not exactly "Coupling" or "Cohesion" alone.

- **Multi-objective / Pareto optimisation**
  - **Would be:** a refinement under *Refactoring > Services Refactoring > Algorithms* (Genetic algorithms → multi-objective NSGA-II), or a cross-cutting attribute of the search.
  - **Evidence:** `Micro2Micro.beginAnEpoch:91-104` (fast non-dominated sorting + crowding distance), `Individual.getObjective:242-256` (3 objectives).
  - **Rationale:** producing a *set* of Pareto-optimal decompositions (rather than one) is a design choice the current flat "Genetic algorithms" leaf does not capture.

- **Frozen / partial-architecture refactoring scope**
  - **Would be:** an attribute of the input *Type* (refactor a *subset* of an existing architecture while freezing the rest).
  - **Evidence:** `PreProcessing.getOriginalService:298-319` (refactoring vs non-refactoring split), `QualityMeasurement.calculateBipartiteConnectivity:81-148` (coupling to the frozen part).
  - **Rationale:** microservices-to-microservices tools operate on a *partial* scope, which the monolith-centric `Type` dimension does not express.

### Other features outside the model

- **Diversity-controlled population initialisation** — MoJo distance enforces a minimum spread between initial individuals (`PopulationInitializer.java:65,97`, `DistanceMeasurement.isIndividualAcceptable:16-25`). Internal search heuristic, too low-level for the model.
- **Simulated user model** — a Gaussian-paced generator of must/cannot-link relations used for offline experiments (`InteractionSimulation.java:45-156`). Experiment scaffolding, not a tool feature.
- **Usage recorder / time recorder** — logs interaction events and timing for the user study (`UsageRecorder`, `ProgramRecorder`). Evaluation instrumentation.
- **Excel result export** — `PostProcessing.writeExcel` (Apache POI). Output format, not a model feature.

### Model Vocabulary Fit

- **Type = Monolith vs Microservices.** The model assumes the input is a monolith being decomposed. Micro2Micro's input is an *existing microservice architecture*, so **Monolith is No** (`getOriginalService:278-327`) and `Microservices` plays both the input and output role. The dimension would benefit from a notion of "source architecture style" that includes microservices.
- **Manual Editing = Merge/Split/Transfer.** Micro2Micro has no direct merge/split/transfer UI; the equivalent effect is achieved *indirectly* by must/cannot-link constraints that the propagator translates into class moves and service splits. The vocabulary partially overlaps but the mechanism (declarative constraints vs imperative edits) differs.
- **Static analysis vs External.** The tool consumes a pre-built structural dependency graph and pre-extracted token bags rather than performing the parse/tokenisation itself. The model's **External** collector is the designated satisfier for representations obtained from external tooling (and its cross-tree rules, e.g. `Structure/Call graph → ... OR External`, explicitly allow it), so this is mapped to **External** rather than a hedged Static analysis. External does not require the codebase to invoke the external tool explicitly — only that the representation originates outside the tool. Version analysis is the exception: its co-change matrix is built in-house from a raw commit log.
- **Behavior > Call graph.** The `dependGraph` is a *static* call/dependency graph; the model lists Call graph under Behavior, but here it is structural, illustrating the structure/behaviour overlap for static call graphs.

### Cross-tree constraint violations

- None found. The constraint `Community detection → NOT Expert knowledge` and `Formal concept analysis → NOT Expert knowledge` are not triggered, because the algorithm is a genetic algorithm, not community detection or FCA, even though Expert knowledge (constraints) is used. Mandatory co-features (Version analysis ← Version history; Lexical ← Structure/Call graph; Adjacency ← Structure; Task ← By task Evolution; Coupling/Cohesion ← Structure) are all satisfied. `Structure → Static analysis OR Model analysis OR External` and `Call graph → Static analysis OR Dynamic analysis OR Model analysis OR External` are satisfied via **External** (the structural graph is externally produced, not parsed in-tool). `Structural relationship → Structure OR Evolution` is satisfied (both present), and `Splitting/Transfer of clusters → Cluster view` is satisfied (Cluster view present).
- Note: `Elements size` (mandatory leaf under Single Decomposition) is **absent**, and `Microservices Decomposition and Refactoring` root requires Quality Assessment metrics to include it — flagged as a missing-mandatory (Red) leaf rather than a cross-tree violation per se.

### Noteworthy design decisions

- **Microservices-to-microservices, not monolith-to-microservices.** This is the headline distinction from every other tool analysed; it reframes the whole `Type` and scope discussion (`Micro2MicroRefactoring_Experiment.java:39-50`).
- **Human-in-the-loop multi-objective search.** Pareto NSGA-II proposes diverse candidates; the developer prunes the search space with must/cannot-link relations injected *between epochs* (`Micro2Micro.beginEvolution:66-74`). Interaction shapes the search rather than post-editing a single result.
- **Three co-equal modularity objectives** (structural, conceptual, evolutionary) over three independent matrices, each combining intra-, inter- and bipartite-connectivity (`QualityMeasurement.calculateStructuralQ/ConceptualQ/EvolutionaryQ:298-328`).
- **Constraint propagation as repair.** Must-link can collapse services, triggering a hyper-graph-based split to preserve the target service count (`InteractionHandler.postProcessingForMustLinkConstraint:216-275`) — an elegant way to keep solutions feasible after expert input.
- **Replication package ships pre-computed inputs.** The collectors that build `relationWeight.json` / `commit2json.json` / `words.dat` are not included, which limits direct re-running on new systems.

---

## Reconciliation Log

Date: 2026-06-28
Versions compared: eee4d4f, 29f7dfc, cc53285, d9b7b1c, working tree

| Feature | From → To | Adjudicating evidence | Which version(s) were wrong |
|---------|-----------|-----------------------|-----------------------------|
| Structural relationship | Unclear → Yes | `MicroBoundariesFront/src/components/content/UsedResult.vue:86-93` — vis.js edges typed `structural` drawn as directed arrows (`temp.arrows="to"`); the prior "Unclear" inferred only from `package.json:"echarts"`, which is unused | all prior versions (eee4d4f, 29f7dfc, cc53285, d9b7b1c) marked Unclear citing the wrong/weak echarts evidence |

Notes on the other disagreements across versions (verdicts confirmed, **not** changed — prior runs that disagreed were wrong):

| Feature | Working-tree verdict (confirmed) | Adjudicating evidence | Wrong prior run(s) |
|---------|----------------------------------|-----------------------|--------------------|
| MoJoFM | Yes | `search/target/DistanceMeasurement.java:32-37` (`MoJoFM = 1 - MoJo/MaxMoJo`) + `:48-104` (full `calculateMoJo`) + `:16-25` (used in population diversification) — implemented in-tool, not external | eee4d4f, 29f7dfc marked No ("paper-only") |
| Call graph | Yes | `search/matrix/StructureMatrixService.java:46-64` `getDCW` — directional `dependencyMatrix[i][j]` "how much class i calls class j" | eee4d4f, 29f7dfc, cc53285 marked No |
| Version analysis | Yes | `search/matrix/EvolutionaryMatrixService.java:60-106` computes the co-change matrix from `commit2json.json` in-tool (not just a copied input) | cc53285 marked Unclear |
| Monolith | Unclear (superseded — see 2026-07-08 re-adjudication → No) | `search/target/QualityMeasurement.java:86-88` — monolith mode is an *anticipated alternative* (`notRefServiceNum==0`); the studied input is a microservice subset | cc53285 marked Yes |
| Control flow | No | `UsedResult.vue:86-94` renders only `structural`/`serviceLink` edge types; no control-flow edges | cc53285 marked Unclear |
| Sizes | No | `UsedResult.vue:130-133` / `RemainingResult.vue` use fixed node `size` constants; `ArchitectureView.vue:62-68` `colWidth`/`colHeight` are responsive layout, not a size-encoded comparison | eee4d4f, 29f7dfc marked Yes |
| Directly in the code | No | `words.dat` is lexical tokens extracted from source code feeding the **Lexical** criterion (`SemanticMatrixService.getSimi:81-135`), not a documentation source | eee4d4f, 29f7dfc marked Yes (mis-mapped lexical-from-code as documentation) |
| Static analysis | Unclear (superseded — see 2026-07-08 re-adjudication → No) | `StructureMatrixService.getInput:105-122` *consumes* a pre-built `dependGraph`; the AST parser that produced it is not in the package | eee4d4f, 29f7dfc marked Yes |
| Splitting / Transfer of clusters | Unclear | `InteractionHandler.postProcessingForMustLinkConstraint:212-270` (split via hyper-graph) and `moveClassesAmongServices` (transfer) occur as *side-effects* of constraint propagation, not as first-class manual edits | — (only working tree marks Unclear; consistent) |

Features still genuinely Unclear after adjudication: **Color** (colour present but encodes service/constraint state within one decomposition, not a cross-decomposition comparison); **Splitting of clusters** and **Transfer of elements between clusters** (present only as constraint-propagation side-effects). (**Static analysis** and **Monolith** were later reclassified — see 2026-07-08 entry below.)

### Re-adjudication (2026-07-08) — Static analysis → No, External → Yes

Re-examining the three inputs individually against the model's collector vocabulary (`External` is a sibling of Collection Technique under Representation Collection, and `Structure/Call graph → ... OR External` explicitly allow externally-produced representations):

| Feature | From → To | Adjudicating evidence |
|---------|-----------|-----------------------|
| Static analysis | Unclear → No | No in-repo AST parse or tokenisation. `StructureMatrixService.getInput:105-122` reads a pre-built `dependGraph`; `SemanticMatrixService.getList:47-78` reads pre-extracted `words.dat` token bags. The tool computes cosine similarity in-tool (`getSimi:81-135`) but does not build the underlying structural/lexical representation. |
| External | No → Yes | The structural call/dependency graph and the per-class token bags are both supplied by external upstream tooling (parser/tokeniser absent from the package). External requires only that the representation originate outside the tool — not that the codebase invoke that tool explicitly. |
| Monolith | Unclear → No | Input is always a microservice architecture (`getOriginalService:278-327` reads `package.json` as a service→files map, comment "iterate all the microservices in the system"). The `notRefServiceNum==0` monolith branch (`calculateBipartiteConnectivity:86-88`) is a defensive guard for a context the pipeline never builds, not a supported mode. |

Version analysis stays **Yes**: `commit2json.json` is a *raw* commit log and `EvolutionaryMatrixService.getInput:60-106` computes the co-change matrix in-house (`:91-95`), so it is genuine in-tool Version analysis, not External.


### Profile fix (2026-06-28) — AND "fully satisfied" propagation rule

**Profile-only change; no analysis content was reviewed or altered in this pass.** A
cross-cutting correction to the group-propagation rule (made explicit in `codebase-map`,
`docs-map`, `verify-analysis`) was applied to `Micro2Micro.profile`: an AND node is only
`Dark_Green` ("Group: fully satisfied") when every **mandatory** child is fully
satisfied — a present **leaf** counts (`Light_Green` is a leaf's max; leaves are never
`Dark_Green`), but a mandatory child **group** that is only `Light_Green` (partially
satisfied) caps the AND parent at `Light_Green`. The previous derivation treated a merely
*present* mandatory child group as enough for `Dark_Green`, overstating coverage.

AND cells changed `Dark_Green` → `Light_Green` in `Micro2Micro.profile`: `Collector`, `Visualization`, `Representation`, `Domain Knowledge`, `Services Refactoring`, `Refactoring`, `Quality Assessment`, `Microservices Decomposition and Refactoring (root)`. (Nodes
already at a higher-priority colour — `Red`/`Orange`/`Magenta` — were unaffected; AND
nodes whose mandatory child is a present leaf, e.g. `Type`, correctly stay `Dark_Green`.)
