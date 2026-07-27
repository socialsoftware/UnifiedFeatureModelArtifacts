# HyDec

Hybrid (static + dynamic) hierarchical-DBSCAN tool that recommends a target microservice for each class/method of a monolithic Java application. Bundles two approaches: HierDec (static-only, EASE 2022) and HyDec (static + dynamic, ICSOC 2022).

## Relevant Files

| File | Description |
|------|-------------|
| [Combining Static and Dynamic Analysis to Decompose Monolithic Application into Microservices (ICSOC 2022)](../../../papers/tools/HyDec.pdf) | Paper PDF |
| [analysis.md](./analysis.md) | Feature model coverage analysis |
| [HyDec.profile](../../../feature_model/representation/.profiles/HyDec.profile) | FeatureIDE colour profile |
| [../../../../extracted-codebases/HyDec](../../../../extracted-codebases/HyDec) | Extracted codebase |
| [Wang2024.md](../../papers/Wang2024.md) | Tool inventory |

---

## Prerequisites

- Python 3.9 or higher.
- Install the package and dependencies:
  ```sh
  cd ../extracted-codebases/HyDec
  pip install -e .          # or: pip install -r requirements.txt
  ```
- **Pre-computed analysis data is required.** HyDec/HierDec do *not* parse Java themselves; they consume matrices produced by the companion services:
  - [decomp-java-analysis-service](https://github.com/khaledsellami/decomp-java-analysis-service) — static structural + semantic analysis
  - [decomp-parsing-service](https://github.com/khaledsellami/decomp-parsing-service) — parsing
  - Dynamic data (execution-trace call matrix) must be generated separately and **is not automated** (`README.md — "generating dynamic analysis results is required and is not automated"`).

## How to Run

Provide a data folder with `dynamic_data/`, `semantic_data/`, and `structural_data/` subfolders (each a `*_calls.npy` / `*_tfidf.npy` matrix plus a `*_names.json`), then:

```sh
python main.py decompose your_app_name \
    --dynamic    path_to_my_data/dynamic_data \
    --semantic   path_to_my_data/semantic_data \
    --structural path_to_my_data/structural_data \
    --hyperparams docs/hyperparameter_input_example.json \
    --approach   hyDec        # or hierDec for static-only
```

- `--granularity class|method` selects the unit of decomposition (default `class`).
- HierDec can also pull data live from the gRPC parsing services with `--repo <github-or-path>` (no manual data prep); this path does **not** work for HyDec because dynamic data is required.
- Output is written to `./logs/<app>/<experiment_id>/layers.csv` (one row per hierarchical layer) plus `experiment_metadata.json`.

Run as a gRPC server instead: `python main.py start` (see `protos/hydec/*/hydec.proto`).

## Gotchas

- **No quality metrics are computed.** The `EvaluationHandler` / coupling-cohesion code in `hydec/experiment.py` is entirely commented out; scoring was done in the papers' experimental harness, not the tool.
- **Output is layered, not a single decomposition.** `layers.csv` contains every DBSCAN layer; the final recommended decomposition is the last layer (`generate_decomposition` returns `layers[-1]`).
- **Outliers.** With `include_outliers=true`, atoms in clusters smaller than `min_samples` are tagged `-1` (`hydec/hybridDecomp.py:146-159`).
- **scikit-learn API drift.** The code uses `OneHotEncoder(sparse=False, ...)` (`hydec/analysis/dependencyAnalysis.py:32`), which was removed in newer scikit-learn (`sparse` → `sparse_output`); pin an older sklearn if you hit a `TypeError`.
- **`decparsing` module is optional.** If installed it is used; otherwise the tool falls back to the gRPC `ParsingClient` (`hydec/dataHandler.py:34-45`).
