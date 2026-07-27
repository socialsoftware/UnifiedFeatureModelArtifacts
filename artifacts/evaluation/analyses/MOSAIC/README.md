# MOSAIC

Static-analysis tool that decomposes monolithic Java (Spring/MyBatis) systems into microservices by combining Louvain community detection with Gurobi ILP coupling-minimization — published at IEEE ICSA 2023.

## Relevant Files

| File | Description |
|------|-------------|
| [From monolithic to microservice architecture: an automated approach based on graph clustering and combinatorial optimization (ICSA 2023)](../../../papers/tools/MOSAIC.pdf) | Paper PDF |
| [analysis.md](./analysis.md) | Feature model coverage analysis |
| [../../../feature_model/representation/.profiles/MOSAIC.profile](../../../feature_model/representation/.profiles/MOSAIC.profile) | FeatureIDE colour profile |
| [../../../../extracted-codebases/MOSAIC](../../../../extracted-codebases/MOSAIC) | Extracted codebase |
| [../../papers/Wang2024.md](../../papers/Wang2024.md) | Tool inventory |

---

## Prerequisites

- **Python 3.7** (the bundled `javalang/__pycache__` is compiled for cpython-3.7).
- Jupyter Notebook / JupyterLab.
- Python packages:
  - `networkx` — graph data structure
  - `pygraphviz` (requires Graphviz + dev headers, e.g. `libgraphviz-dev`) — graph rendering
  - `python-louvain` — exposes the `community` / `community_louvain` module
  - `gurobipy` — the ILP solver; **requires a Gurobi licence** (free academic licence available)
- `javalang` is **bundled** in the repo (`./javalang`), no install needed.

## How to Run

The pipeline is two Jupyter notebooks, run in order:

1. **`1-System_analysis.ipynb`** — static analysis.
   - Set `project` to one of the names in `projects.json` (`spring-petclinic`, `jpetstore`, `springblog`, `cargo-tracking`).
   - For a first run with no refinement file: set `read_from_file = False` and provide layer refinements (or leave the lists empty); set `update_refinement = True` to save them. For the bundled cases a `*_refinement.json` already exists, so `read_from_file = True`, `update_refinement = False` works.
   - Running all cells produces, under `applications/<project>/results/`: `*_nodes.csv`, `*_edges.csv`, `*_edges_written.csv`, `*_graph.gml`, `*_graph.png`.

2. **`2-Decomposition_optimization.ipynb`** — decomposition + optimization.
   - Set `project` to the same value.
   - Optionally adjust edge weights (`w['Calls']` etc.) and refine entity clusters (`entity_ids_to_remove`, `entities_clusters_to_place`).
   - Running all cells produces `*_communities.csv`, `*_communities_improved_optimization.lp`, `*_sol_communities_improved_optimization.csv`, `*_sol_*.png`, `*_sol_*.txt` (coupling/cohesion report).

To run the tool on a **new** monolith: add an entry to `projects.json` with `source_basedir` pointing at the Java sources, then run both notebooks.

### SOTA comparison (optional)

`applications/spring-petclinic/results/sota_approaches/springpetclinic-comparison.ipynb` scores external class-level decompositions (`baseline`, `kamimura`) on the same coupling/cohesion metrics over the petclinic graph.

## Gotchas

- **Gurobi licence required** — `gurobipy`/`gurobi` will not solve without a valid licence; the notebook imports it as `import gurobi as gb`, so the module must be importable under that name (newer installs expose `gurobipy`; you may need a shim or to edit the import).
- **Python 3.7-specific bytecode** is checked in (`javalang/__pycache__`); use a 3.7 environment to avoid surprises, or delete the `.pyc` files.
- **`jpetstore` and `cargo-tracking` sources are not all present**: `projects.json` lists `cargo-tracking` but the `applications/` tree ships results mainly for spring-petclinic and springblog; check the `source/` folder exists before running.
- **`update_refinement` bug**: the save branch writes to an undefined `exclusions_file` variable (`json.dump(data, exclusions_file)` — should be `refinement_file`) (`1-System_analysis.ipynb` Cell `c5d5f9b7`). Saving a fresh refinement file will raise `NameError`; create the JSON manually or fix the cell.
- **Static-only**: no runtime data is collected, so dynamically dispatched calls / reflection are not captured in the call graph.
- **Annotation-driven layer detection** assumes Spring/JPA-style annotations (`@Service`, `@Repository`, etc.); plain-POJO monoliths require manual `force_*` refinement lists.
