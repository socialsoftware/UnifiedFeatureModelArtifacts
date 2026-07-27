# Feature Model Dimensions Reference

This is the feature model for "Variant-Rich Monolith-to-Microservices Identification Tools".
Use this as the canonical schema when categorising tools from literature.

---

## 1. Granularity (OR — at least one)

The unit of decomposition targeted by the tool.

- **Method**
- **Class**
- **Entity** (database entity / data model)
- **Functionality** (use case, business capability)
- **Package**
- **API Endpoint** (endpoint / URI)

---

## 2. Representation Collection (OR — at least one)

### 2.1 Collector

#### 2.1.1 Source (OR — at least one)

**Development:**
- Source code
- Database schema
- Version history

**Runtime:**
- Runtime log traces
- User interactions

**Higher-Level Models:**
- Business process model
- Use case
- Data flow diagram

**Documentation:**
- Directly in the code (inline comments, annotations)
- Paper document
- Digital format (wiki, specs)

#### 2.1.2 Collection Technique (OR — at least one)

- **Static analysis** — requires: Source code OR Database schema
- **Dynamic analysis** — requires: Runtime log traces OR User interactions
- **Version analysis** — requires: Version history
- **Model analysis** — requires: Higher-Level Models OR Documentation

### 2.2 External (optional)

Domain knowledge provided externally (e.g., ontologies, taxonomies).

---

## 3. Representation (AND — all sub-dimensions apply)

### 3.1 Analytical (OR — at least one)

What structural/behavioural/evolutionary information is captured.

**Structure:**
- Inner structure (class internals, field/method composition)
- Inter Structure:
  - Inheritance
  - Association (calls, references, data access)

**Behavior:**
- Call graph
- Sequence of accesses
- Frequency (access frequency, call frequency)
- CPU level
- Memory level
- Response time

**Evolution:**
- By contributor (author-based co-change)
- By task (commit/issue-based co-change)

### 3.2 Type (AND — mandatory)

- **Monolith** — the graph/model represents the monolith being decomposed
- **Microservices** (mandatory) — the graph/model represents the target microservices architecture

### 3.3 Visualization (AND — optional)

#### 3.3.1 Elements (AND — mandatory)

- **Granularity view** (mandatory — individual entities visible)
- **Cluster view** (groups of entities shown together)

#### 3.3.2 Relations (OR — at least one)

- Structural relationship
- Control flow
- Data flow

---

## 4. Refactoring (AND — all sub-dimensions)

### 4.1 Domain Knowledge (AND — mandatory)

#### 4.1.1 Aggregation Criteria (OR — at least one)

The basis on which entities are grouped into services:

- **Task** — co-change by commit/issue
- **Contributor** — co-change by author
- **Lexical** — textual/semantic similarity over tokenizable representations (structure, call graph, sequence of accesses); e.g. topic modelling, NLP
- **Functional** — functional cohesion (call graph, use-case coverage)
- **Adjacency** — structural coupling (dependencies, associations)

#### 4.1.2 Expert knowledge (optional)

Human-provided rules, thresholds, or domain annotations guiding decomposition.

### 4.2 Services Refactoring (AND — mandatory)

#### 4.2.1 Algorithms (OR — at least one)

- Hierarchical clustering
- Community detection
- K-means++
- Formal concept analysis
- Genetic algorithms
- Hungarian algorithm

#### 4.2.2 Manual Editing (OR — optional)

- Merge of clusters
- Splitting of clusters
- Transfer of elements between clusters

### 4.3 Functionality Refactoring (OR — optional)

Post-decomposition transformations:
- **Asynchronization** (convert sync calls to async)
- **Granularity refinement** (adjust service boundaries)

---

## 5. Quality Assessment (AND)

### 5.1 Metrics (OR — at least one)

**Single Decomposition** (evaluate one solution):
- Coupling
- Cohesion
- Elements size (mandatory)
- Complexity
- Team size

**Several Decompositions** (compare multiple solutions):
- MoJoFM (mandatory)
- Compare metrics (other comparative metrics)

### 5.2 Graphical Comparison (OR — optional)

Visual ways to compare decompositions:
- Color
- Sizes
- Distance between elements

---

## Key Cross-Tree Constraints

| If selected… | Then requires… |
|---|---|
| Static analysis | Source code OR Database schema |
| Dynamic analysis | Runtime (Runtime log traces OR User interactions) |
| Version analysis | Version history |
| Model analysis | Higher-Level Models OR Documentation |
| Structure | Static analysis OR Model analysis OR External |
| Call graph | Static analysis OR Dynamic analysis OR Model analysis OR External |
| Sequence of accesses | Static analysis OR Dynamic analysis OR Model analysis OR External |
| Frequency OR CPU level OR Memory level OR Response time | Dynamic analysis OR External |
| Evolution | Version analysis OR External |
| Structural relationship | Structure OR Evolution |
| Control flow | Behavior OR Structure |
| Data flow | Behavior OR Structure |
| Task (Aggregation Criteria) | By task (Evolution) |
| Contributor (Aggregation Criteria) | By contributor (Evolution) |
| Lexical | Structure OR Call graph OR Sequence of accesses |
| Functional | Call graph OR Sequence of accesses |
| Adjacency | Behavior OR Structure |
| Community detection | NOT Expert knowledge |
| Formal concept analysis | NOT Expert knowledge |
| Merge/Splitting/Transfer of clusters | Cluster view |
| Coupling OR Cohesion OR Complexity | Structure OR Behavior |
| Team size | By contributor (Evolution) |
| Compare metrics | Single Decomposition |
