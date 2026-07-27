# IBM Mono2Micro

IBM Mono2Micro — a closed-source (now withdrawn) AI-assisted toolset for decomposing monolithic Java EE applications into candidate microservices, introduced in the ESEC/FSE 2021 industry paper. It combines static instrumentation, dynamic runtime-trace collection, and ML-based spatio-temporal clustering, and generates partial microservice code. Analysed from online documentation only (no local codebase).

## Relevant Files

| File | Description |
|------|-------------|
| [analysis.md](./analysis.md) | Feature model coverage analysis |
| [../../feature_model/representation/.profiles/mono2micro_IBM.profile](../../feature_model/representation/.profiles/mono2micro_IBM.profile) | FeatureIDE colour profile |

---

## Documentation Sources

- **Entry point:** https://ibm-cloud-architecture.github.io/modernization-playbook/applications/m2m/
- **Fetched:** 2026-06-22
- **Pages visited:** 4 (1 search overview + 3 fetched pages; the IBM blog returned HTTP 403)

| # | URL | Purpose |
|---|-----|---------|
| 1 | https://ibm-cloud-architecture.github.io/modernization-playbook/applications/m2m/ | Entry point — full operational workflow, components (Bluejay/Flicker/AIPL/Cardinal/UI), inputs, outputs, UI editing, prerequisites |
| 2 | https://ar5iv.labs.arxiv.org/html/2107.09698 | ESEC/FSE 2021 paper (technical ground truth) — granularity, traces, CCTs, DCR/ICR/DCP/ICP features, hierarchical clustering, BCP/ICP/SM/IFN/NED metrics |
| 3 | https://heidloff.net/article/step-by-step-instructions-mono2micro/ | Community step-by-step — UI colour coding (purple/green/red), Flicker recording, final_graph.json visualization |
| 4 | https://www.ibm.com/blog/ibm-cio-organizations-application-modernization-journey-mono2micro/ | IBM blog (attempted) — **HTTP 403, not retrieved** |

> Note: IBM's official product documentation pages for Mono2Micro have been retired (the product was withdrawn). The arxiv paper and the IBM Cloud Architecture modernization playbook are the durable references.

---

## Prerequisites

From the modernization playbook:

- **Docker** 17.06 CE or higher (supports multi-stage builds) — ~3 GB free storage for images and containerized microservices
- **Java** 1.8
- **Maven** 3.6.3
- **Git CLI**
- Internet connectivity (DockerHub, Maven Central)
- A Docker network for inter-container communication (`docker network create defaultappNetwork`)
- Input: Java EE monolith **source code** + build files (Maven/Gradle) + deployment descriptors (web.xml, ejb-jar.xml, application.xml, persistence.xml) + a runnable set of **functional test cases** covering the business use cases of interest

---

## How to Run

High-level workflow (semi-automated, human-in-the-loop):

1. **Instrument (Bluejay):** static analysis instruments every Java method entry/exit. Produces a `-klu` mirror of the source, `refTable.json` (signatures, class variables, inheritance), and `symTable.json` (class/package dependencies).
2. **Collect runtime traces (Flicker):** compile & deploy the instrumented app; run Flicker in a separate terminal, labelling each business use case; execute the corresponding functional tests; issue `STOP` (uppercase) per use case. Produces context JSON files with use-case names and start/stop timestamps. *Critical:* do not let server log files be overwritten during test runs.
3. **Analyse (AIPL / Oriole):** point the AI engine at the input dirs (`contexts/`, `logs/`, `tables/`, optional `config.ini`). It builds class-level calling-context trees, computes the spatio-temporal similarity matrix, and hierarchically clusters into the target number of partitions. Produces `final_graph.json`, `Oriole-Report.html` (partitions ↔ use cases), `Cardinal-Report.html` (inter-partition invocations).
4. **Visualize / edit (UI):** open the Mono2Micro web app, load `final_graph.json`. Choose **Business Logic** view, **Natural Seams** view, or a **Custom** view. Rename partitions (pencil icon) and drag-and-drop classes between partitions. Save the edited graph and optionally re-run AIPL with `regen_p` + the `UserModifiedGraph` config to regenerate from the edited graph.
5. **Generate code (Cardinal):** generates per-partition Java source (e.g. `monolith-web`, `monolith-partition0`) — proxy classes (remote calls), service classes (REST/JAX-RS interfaces), utility classes, and dummy placeholders — plus `CardinalFileSummary.txt`. Deploy partitions as Docker containers with JAX-RS endpoints.

---

## Gotchas

- **Product withdrawn / closed-source:** Mono2Micro is no longer distributed by IBM; you cannot install it fresh. Treat the steps above as documentation of how it worked, not a reproducible setup.
- **Test coverage drives quality:** classes never hit by the executed test cases land in a special **"Unobserved"** partition. Poor test coverage → many unobserved classes → weaker recommendations.
- **Decomposition unit is the class**, even though instrumentation is at method granularity.
- **Cluster count is an input, set before analysis** — there is no in-UI merge/split; only drag-and-drop transfer of classes between existing partitions. Changing the partition count means re-running analysis.
- **"Use cases" are operator-defined labels** tied to test runs (via Flicker), not formal higher-level models — keep this in mind when reading the feature mapping.
- **IBM blog page (source #4) is 403-gated** for automated fetchers; its content was not used in the analysis.
