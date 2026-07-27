# Micro2Micro

Micro2Micro (NJU; Zhong et al., *IEEE TSE* 2025) — an interactive, multi-objective (NSGA-II) tool that **refactors an existing microservice architecture into a better one** (microservices-to-microservices) in support of evolutionary design, steered by developer-supplied must-link / cannot-link relations.

> Not a monolith-to-microservices tool: the input is itself a microservice architecture, of which the developer selects a subset of services to re-partition.

## Relevant Files

| File | Description |
|------|-------------|
| [Refactoring Microservices to Microservices in Support of Evolutionary Design (IEEE TSE 2025)](../../../papers/mono2micro_process/Zhong2025.pdf) | Paper PDF |
| [analysis.md](./analysis.md) | Feature model coverage analysis |
| [feature_model/representation/.profiles/Micro2Micro.profile](../../../feature_model/representation/.profiles/Micro2Micro.profile) | FeatureIDE colour profile |
| [../../../../extracted-codebases/Micro2micro](../../../../extracted-codebases/Micro2micro) | Extracted codebase |
| [evaluation/papers/Zhong2025.md](../../papers/Zhong2025.md) | Tool inventory |

---

## Prerequisites

- **Java 8+** and **Maven** — Spring-Boot backend (`code/code/MicroBoundaries-backup/pom.xml`).
- **Node.js / npm** — Vue 3 + Vite + ECharts front-end (`code/code/MicroBoundariesFront/package.json`).
- **Per-project input files** (pre-computed, bundled under `data/data/project input/<project>/`):
  - `relationWeight.json` — static structural call/dependency graph (`dependGraph` matrix) + `fileSequence`.
  - `words.dat` — per-class lexical token bag (for semantic similarity).
  - `commit2json.json` — commit co-change history (for evolutionary similarity).
  - `package.json` — the existing microservice architecture (service → file list).
  - For experiments, per-task `refactoring tasks/service size N/taskM/task.txt` lists the services to refactor.

## How to Run

The codebase ships as a zip; the backend lives in `code/code/MicroBoundaries-backup/` and the front-end in `code/code/MicroBoundariesFront/`. There are three scenarios (see `code/code/README.md`).

### 1. Refactoring without interaction (native mode)

Run `Micro2MicroRefactoring_Experiment.java` with `Configuration.FreeMode = true` (`util/Configuration.java:20`). Copy a case study's input files into `src/main/datafiles/<project>/` first. Results are written to Excel.

### 2. Refactoring with simulated interaction

Same entry point with `Configuration.FreeMode = false` — a simulated user model (`interaction/InteractionSimulation.java`) injects must/cannot-link relations between epochs.

### 3. Refactoring with real-user interaction (web GUI)

```bash
# backend
cd code/code/MicroBoundaries-backup
mvn -e spring-boot:run
# front-end (new terminal)
cd code/code/MicroBoundariesFront
npm install
npm run dev          # serves at e.g. http://localhost:8080/
```

Open the front-end URL, pick a project and the services to refactor, start the search, inspect the Pareto-front solutions, add must/cannot-link constraints (`/api/addConstraint`), ask for new suggestions (`/api/suggest`), then finish.

## Gotchas

- **Microservices-to-microservices, not monolith decomposition.** The "original" architecture is a set of existing microservices; the tool re-partitions a selected subset and freezes the rest (`util/PreProcessing.java:278-327`). The monolith path is only *anticipated* in code (`search/target/QualityMeasurement.java:86-88`), not the studied scenario.
- **Inputs are pre-computed.** The AST parser, tokenizer and commit miner that produce `relationWeight.json` / `words.dat` / `commit2json.json` are **not** in the replication package — you cannot regenerate inputs for a new system from this repo alone.
- **Directory casing.** The extracted folder is `Micro2micro` (lowercase second *m*); the tool, profile and analysis use the paper's casing **Micro2Micro**.
- **Two backend module names.** The backend folder is `MicroBoundaries-backup` and the artifact is `Nsga-0.0.1-SNAPSHOT.jar` — both refer to Micro2Micro.
- **No direct merge/split/transfer.** Manual editing is expressed only as must/cannot-link constraints, which the propagator turns into class moves / service splits (`interaction/InteractionHandler.java:112-275`).
- **Call frequency is discarded.** Dependency counts are collapsed to binary weights (`search/matrix/StructureMatrixService.java:124-132`), so no frequency/behavioural intensity survives.

## Colour profile

See [`feature_model/representation/.profiles/Micro2Micro.profile`](../../../feature_model/representation/.profiles/Micro2Micro.profile) — load it in FeatureIDE over `feature_model/representation/feature_model.xml` to view this tool's coverage. No cross-tree constraint violations were found; the mandatory `Elements size` metric is absent (Red). See [analysis.md](./analysis.md#cross-tree-constraint-violations).
