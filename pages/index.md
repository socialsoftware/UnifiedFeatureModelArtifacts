---
layout: default
title: Home
nav_title: Home
nav_order: 1
permalink: /
---

# Artifact appendix

This site is the companion appendix to the paper *A Unified Feature Model for
Microservice Identification and Refactoring*. It documents and links every
artifact behind the results: the unified feature model, the per-tool mappings
used in the evaluation, the exported figures, the meta-review data, and the
LLM-based mapping tooling.

<div class="note" markdown="1">
**Paper:** *to appear — DOI pending.*
**Archived artifacts:** *Zenodo DOI pending.*
**Source repository:** [github.com/socialsoftware/UnifiedFeatureModelArtifacts](https://github.com/socialsoftware/UnifiedFeatureModelArtifacts)
</div>

## Abstract

Several approaches have been proposed for the automatic identification of microservices within monolithic systems. These methodologies differ in their data collection and analysis techniques, the decomposition algorithms applied, and the mechanisms used to visualize and refine candidate microservices. Despite this diversity, systematic experimentation and comparison across approaches remain limited by the absence of a common conceptual framework. Furthermore, current research indicates that no single optimal method exists; rather, integrating multiple approaches is necessary to fully explore the trade-offs inherent in any design solution.

To address this gap, this paper proposes a feature model for variant-rich microservice identification tools, grounded in an extensive analysis of the state of the art. We evaluate this feature model through a systematic mapping of representative literature and by analyzing its instantiation within the architecture of an existing microservice identification tool. Our findings are two-fold. First, the proposed feature model successfully captures the primary variation points of existing methodologies, providing a unifying foundation for analyzing, comparing, and designing microservice identification tools. Second, we observe that current tools address only a small set of these variations, ultimately lacking the capability to provide a common framework for comparing and integrating different approaches.

## What's here

<ul class="cards">
  <li>
    <h3><a href="{{ '/feature-model/' | relative_url }}">Feature model</a></h3>
    <p>The proposed model: 99 features and 21 cross-tree constraints, rendered
    in full, plus every colour profile from the evaluation.</p>
    <p class="card-files">Downloads: FeatureIDE XML, rendered PNG, profiles</p>
  </li>
  <li>
    <h3><a href="{{ '/initial-model/' | relative_url }}">Initial model</a></h3>
    <p>The model before generalisation, derived from a single tool. Published so
    the two can be compared — the difference is what the bottom-up phase
    added.</p>
    <p class="card-files">Downloads: FeatureIDE XML, rendered PNG</p>
  </li>
  <li>
    <h3><a href="{{ '/meta-review/' | relative_url }}">Meta-review</a></h3>
    <p>The 11 secondary studies reviewed during the bottom-up modelling phase,
    with the concepts each one reports per feature-model dimension.</p>
    <p class="card-files">Downloads: CSV, PDF</p>
  </li>
  <li>
    <h3><a href="{{ '/skills/' | relative_url }}">Skills</a></h3>
    <p>The six Claude Code skills that produced the evaluation — extracting
    tools from papers, mapping each one onto the model, reconciling repeated
    runs, and merging the results.</p>
    <p class="card-files">Downloads: each <code>SKILL.md</code></p>
  </li>
  <li>
    <h3><a href="{{ '/evaluation/' | relative_url }}">Evaluation</a></h3>
    <p>Seven tools, grouped by the paper they came from, each with its automated
    and revised mappings. Also the merged mappings showing what the tools cover
    together.</p>
    <p class="card-files">Downloads: analyses, colour profiles</p>
  </li>
</ul>

## Licences

- **Code** — the mapping tooling is licensed under the
  [MIT License](https://github.com/socialsoftware/UnifiedFeatureModelArtifacts/blob/main/LICENSE).
- **Research artifacts** — the feature model, tool mappings, images, generated
  analyses, and meta-review data are licensed under
  [CC BY 4.0](https://github.com/socialsoftware/UnifiedFeatureModelArtifacts/blob/main/LICENSE-DATA).

## Citation

If you use these artifacts, please cite the paper. See
[`CITATION.cff`](https://github.com/socialsoftware/UnifiedFeatureModelArtifacts/blob/main/CITATION.cff)
or use the "Cite this repository" button on GitHub.
