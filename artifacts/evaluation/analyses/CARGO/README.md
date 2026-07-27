# CARGO

CARGO (Context-sensitive lAbel pRopaGatiOn) — an un-/semi-supervised microservice partition discovery and refinement tool that statically builds a context- and flow-sensitive System Dependency Graph (with call, data, heap, and DB-transaction edges) of a Java EE monolith and runs label propagation over it. Paper: Nitin et al., *CARGO: AI-Guided Dependency Analysis for Migrating Monolithic Applications to Microservices Architecture*, ASE 2023. Public codebase: IBM Konveyor `tackle-data-gravity-insights` (the `dgi` package).

## Relevant Files

| File | Description |
|------|-------------|
| [CARGO (ASE 2023)](../../../papers/tools/CARGO.pdf) | Paper PDF |
| [analysis.md](./analysis.md) | Feature model coverage analysis |
| [../../../feature_model/representation/.profiles/CARGO.profile](../../../feature_model/representation/.profiles/CARGO.profile) | FeatureIDE colour profile |
| [../../../../extracted-codebases/CARGO](../../../../extracted-codebases/CARGO) | Extracted codebase (`tackle-data-gravity-insights` / `dgi`) |
| [../../papers/Wang2024.md](../../papers/Wang2024.md) | Tool inventory |

---

## Prerequisites

- **Python** (the `dgi` package; install with `pip install -U tackle-dgi` or from source via `setup.py`).
- **Neo4j** instance to store the graphs (`docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH="neo4j:konveyor" neo4j:4.4.17`). Set `NEO4J_BOLT_URL`.
- **DOOP / JackEE** static-analysis facts (for `c2g --doop`) — produced outside this repo.
- **Tackle-DiVA** output (DiVA transaction JSON) — for `tx2g`.
- The **`cargo`** Python package — the partitioning algorithm imported by `dgi/partitioning/partition.py` is an **external dependency not included in this repo**; `partition` will not run without it.

## How to Run

The pipeline incrementally populates one shared Neo4j graph, then partitions it:

```bash
# 1. Code dependencies (call/data/heap) from DOOP facts
dgi c2g --doop true -d <doop_facts_dir> -a class

# 2. SQL schema (tables/columns/foreign keys) from a DDL file
dgi s2g -i <schema.ddl>

# 3. Transaction (CRUD) edges from Tackle-DiVA output
dgi tx2g -i <diva_transactions.json> -a class

# 4. Run the CARGO partitioning algorithm
#    native (unsupervised): provide a max number of partitions
dgi partition -k 5 -o <output_dir>
#    refinement (semi-supervised): seed from another tool's partitions
dgi partition -i <seed_partitions.json> -o <output_dir>
```

Output: `partitions.json` (method → partition id) plus `partition_id` stamped on each `MethodNode`/`ClassNode` in Neo4j (`dgi/partitioning/partition.py:60-82`).

See `docs/getting-started.md` and `docs/demo.md` in the codebase for a full walkthrough.

## Gotchas

- **Algorithm is closed-source here.** `from cargo import Cargo` (`dgi/partitioning/partition.py:24`) pulls a separate package; the public `dgi` repo ships only the graph builders and the `partition` entry point. Decompositions cannot be reproduced from this repo alone.
- **Front-end vs algorithm.** All file:line evidence for graph construction comes from the codebase; algorithm and metric details come from the paper (`papers/tools/CARGO.pdf`), since the algorithm is not in the repo.
- **Fully static.** Despite "transaction" and "data flow" terminology, the entire SDG is statically derived (DOOP/JackEE/DiVA). Runtime CPU/latency/throughput figures in the paper are *deployment-time evaluation*, not graph collection.
- **Granularity is dual.** Label propagation runs over *method* nodes but partitions are reported at *class* level via majority vote (`dgi/partitioning/partition.py:68-71`).
- **No bundled visualiser.** Graphs are browsed in the generic Neo4j UI; there is no cluster/decomposition view shipped.
- **Seed input ≈ "expert knowledge".** Refinement mode consumes a user/tool-supplied seed partitioning, which sits near the `Community detection → NOT Expert knowledge` constraint (see analysis.md). Pointer to the colour profile: [`CARGO.profile`](../../../feature_model/representation/.profiles/CARGO.profile).
