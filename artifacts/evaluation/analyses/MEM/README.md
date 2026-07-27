# MEM

Microservice Extraction Model — Mazlami et al.'s coupling-based extractor that
clusters a monolith's source files using logical (co-change), semantic (textual),
and contributor (shared-author) coupling. Paper: *Extraction of Microservices from
Monolithic Software Architectures* (ICWS 2017).

## Relevant Files

| File | Description |
|------|-------------|
| [Extraction of Microservices from Monolithic Software Architectures (ICWS 2017)](../../../papers/tools/MEM.pdf) | Paper PDF |
| [analysis.md](./analysis.md) | Feature model coverage analysis |
| [feature_model/representation/.profiles/MEM.profile](../../../feature_model/representation/.profiles/MEM.profile) | FeatureIDE colour profile |
| [../../../../extracted-codebases/MEM-backend](../../../../extracted-codebases/MEM-backend) | Extracted codebase — backend (Java/Spring Boot extractor) |
| [../../../../extracted-codebases/MEM-frontend](../../../../extracted-codebases/MEM-frontend) | Extracted codebase — frontend (Angular vis.js visualiser) |
| [evaluation/papers/Wang2024.md](../../papers/Wang2024.md) | Tool inventory |

---

## Prerequisites

**Backend** (`MEM-backend`, the extractor — all analysis happens here):
- **Java 8** (`pom.xml:10` — `java.version = 1.8`); the Spring Boot 1.4.1 parent
  predates Java 9+ and will not build on modern JDKs without adjustments.
- **Maven** (the build is a standard `pom.xml`).
- A local **Git** working copy of each monolith to analyse (the tool clones repos
  by URL via JGit).

**Frontend** (`MEM-frontend`, optional — only for the graph view):
- **Node.js / npm** (Angular 2 + SystemJS seed, `package.json`). This is an old
  angular-seed; expect dependency friction on current Node versions.

## How to Run

The decomposition is fully usable **headlessly** from the backend; the frontend is
only a visualiser.

1. **Backend:** build and run the Spring Boot app
   (`src/main/java/.../main/Main.java:23`):
   ```bash
   cd ../../../../extracted-codebases/MEM-backend
   mvn spring-boot:run
   ```
   It exposes a REST API. The decomposition endpoint is
   `POST /repositories/{repoId}/decomposition`
   (`controllers/DecompositionController.java:48`) with a JSON body matching
   `DecompositionParameters` (`models/DecompositionParameters.java`):
   - `logicalCoupling`, `semanticCoupling`, `contributorCoupling` (booleans —
     enable any subset of the three strategies),
   - `numServices` (target number of services),
   - `intervalSeconds` (time-window size for logical coupling),
   - `sizeThreshold` (max cluster size before degree-split).
   Repositories are registered/cloned first via the repository endpoints
   (`controllers/RepositoryController.java`).
2. A plain-text report `~/<repo>_<id>.txt` listing `service | classes` is written
   on each run (`services/reporting/TextFileReport.java:18`).
3. **Frontend (optional):** start the Angular seed and open the dashboard to render
   the clustered graph (`MEM-frontend/.../dashboard/graph/graph.component.ts`).

## Gotchas

- **Version history is mandatory.** Logical and contributor coupling both replay
  the Git commit log (`services/git/HistoryService.java:32-43`); a repo with no/poor
  history yields weak couplings. Only the *semantic* strategy uses file contents.
- **"Static analysis" is lexical only.** Semantic coupling tokenises raw file text
  for TF-IDF (`ClassContentVisitor.java:46-58`); it does **not** parse the AST,
  call graph, or dependencies. The bundled ANTLR jar
  (`lib/antlr4-runtime-4.5.3.jar`) is not used in this path.
- **Only `.java`, `.py`, `.rb` files** are read for semantic coupling
  (`ClassContentVisitor.java:23`); other languages are ignored by that strategy.
- **O(n²) coupling computation** over all file pairs
  (`SemanticCouplingEngine.java:41-47`, `ContributorCouplingEngine.java:28-44`) —
  slow on large repositories.
- **No manual editing.** Clusters cannot be merged/split/transferred interactively;
  all control is via the pre-run parameters above.
- **Two separate repos.** `MEM-backend` (extractor) and `MEM-frontend` (viewer) are
  cloned independently; the backend works without the frontend.
- **Aged toolchain.** Spring Boot 1.4.1 / Java 8 backend and an Angular 2 seed
  frontend; building on current JDK/Node versions will likely need pinning.
