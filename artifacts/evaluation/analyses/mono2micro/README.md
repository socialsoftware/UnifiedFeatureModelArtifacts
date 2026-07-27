# mono2micro

mono2micro (SocialSoftware / IST, Rito Silva group) — a tool suite that decomposes Spring-Boot monoliths (FenixFramework / Spring Data ORMs) into microservices by building weighted similarity matrices over static accesses, structure, git-repository and code2vec-embedding data, clustering entities with SciPy hierarchical clustering, and minimising the distributed-transaction complexity introduced (Lopes, MSc Thesis 2023; lineage ECSA2019 / ICSA2020 / ECSA2020).

> Not to be confused with the commercial **IBM Mono2Micro** (Kalia et al., FSE 2021), analysed separately under `mono2micro_IBM`.

## Relevant Files

| File | Description |
|------|-------------|
| [Microservices identification in monolith systems (MSc Thesis 2023)](../../../papers/thesis/Lopes2023.pdf) | Paper PDF |
| [analysis.md](./analysis.md) | Feature model coverage analysis |
| [feature_model/representation/.profiles/mono2micro.profile](../../../feature_model/representation/.profiles/mono2micro.profile) | FeatureIDE colour profile |
| [../../../../extracted-codebases/mono2micro](../../../../extracted-codebases/mono2micro) | Extracted codebase |
| [evaluation/papers/Lopes2023.md](../../papers/Lopes2023.md) | Tool inventory |

---

## Prerequisites

- **Java 8+** and Maven — Spring-Boot backend (`backend/pom.xml`).
- **Node.js 10+ / npm 6+** — React frontend (`frontend/package.json`).
- **Python 3.5+** with `pipenv` — FastAPI scripts server for SciPy clustering + Code2Vec (`scripts/requirements.txt`).
- **MongoDB** — the backend persists codebases / representations / decompositions via Spring Data + GridFS.
- **Docker + docker-compose** — for the one-command path (`docker-compose.yml`).
- **External inputs the repo does not bundle:**
  - The **code2vec model** (`scripts/models/java-large-released-model.tar.gz`, downloaded in setup) — needed only for the vectorization strategies.
  - **Representation files** produced by the collectors (the monolith codebases / pre-built representations are linked from the README's Google Drive folders).

## How to Run

The system has four components (collectors → backend → scripts → frontend).

### Docker (recommended)

```bash
docker-compose build
docker-compose up
```

Web UI at <http://localhost:3000>; Mongo Express at <http://localhost:8081>.

### Manual

1. **Collectors** — run the relevant collector against a target monolith to produce representation JSON files (see each `collectors/*/README.md`):
   - `collectors/spoon-callgraph` — static Spoon AST parse → entity accesses / call sequences (prompts for the repo clone URL and ORM technology).
   - `collectors/structure-collector` — entity fields, associations, inheritance.
   - `collectors/commit-collection` — git history → author + commit co-change files.
   - `scripts/code2vec` (+ `collectors/code2vec-callgraph`) — code embeddings.
2. **Backend (Spring Boot):**
   ```bash
   cd backend/
   mvn clean install -DskipTests
   java -Djava.security.egd=file:/dev/./urandom -jar ./target/mono2micro-0.0.1-SNAPSHOT.jar
   ```
   First create `backend/src/main/resources/specific.properties` with the python command (see `specific.properties.example`), and ensure `/codebases` is empty before building (Spring-Boot jar file-count limit).
3. **Scripts (FastAPI / SciPy + Code2Vec):**
   ```bash
   cd scripts/
   pip install -r requirements.txt
   python main.py
   ```
4. **Frontend (React):**
   ```bash
   cd frontend/
   npm install --legacy-peer-deps
   npm start
   ```

### Typical workflow in the UI

Create a codebase by uploading collector output → create a **strategy** (Accesses / Repository / Structure / Class·Entity·Functionality Vectorization) → build a **similarity** matrix (set criterion weights) → cut the dendrogram to get a **decomposition** (or import an **Expert** one) → inspect metrics, edit clusters (merge/split/transfer/rename/form), redesign functionalities into Sagas, and optionally **Export to CML**.

## Gotchas

- **Two different "Mono2Micro" tools.** This is the IST/SocialSoftware research tool, *not* IBM Mono2Micro. They share a name and goal but nothing else.
- **`/codebases` must be empty before `mvn package`** — otherwise the Spring-Boot jar exceeds the 65 535-file limit (`README.md`, setup note).
- **Static "frequency".** The read/write/access counts used as behavioural weights are derived statically from parsed traces, not from runtime monitoring — relevant when reading the feature-model mapping (causes the `Frequency` cross-tree constraint flag).
- **Structure strategy is a stub.** `Strategy.java:28` notes the structural decomposition strategy is "not yet implemented"; structure data is collectable/exportable but not a full decomposition driver.
- **code2vec model is large** (~1 GB download) and only needed for vectorization strategies; skip it if you only use Accesses/Repository/Structure.
- **CML export** needs a manually installed Context Mapper discovery jar (`tools/cml-converter/README.md`).

## Colour profile

See [`feature_model/representation/.profiles/mono2micro.profile`](../../../feature_model/representation/.profiles/mono2micro.profile) — load it in FeatureIDE over `feature_model/representation/feature_model.xml` to view this tool's coverage on the canonical model. The single constraint flag (`Frequency`, orange) is explained in [analysis.md](./analysis.md#cross-tree-constraint-violations).