---
name: extract-codebases-from-paper
description: This skill should be used when the user says "extract tools from <paper>", "get codebases from <paper>", "extract codebases from <paper>", "run extract-codebases-from-paper on <paper>", or provides a path to a survey PDF and wants to extract the tools/approaches it covers and download their public codebases. Produces a tool inventory file in evaluation/papers/ and clones repositories into ../extracted-codebases/ (outside the thesis repo).
allowed-tools: Read, Write, Bash
---

# extract-codebases-from-paper

Extract all tools and approaches from a survey paper, then clone their public codebases for later analysis.

## Inputs

The user provides a path to a survey PDF, e.g.:

```
papers/surveys/Wang2024.pdf
```

Derive the paper key from the filename (e.g., `Wang2024`).

## Output files

- `evaluation/papers/<PaperKey>.md` — tool inventory (inside the thesis repo)
- `../extracted-codebases/<tool-name>/` — cloned repositories (outside the thesis repo, to keep it clean)

**Never modify** `my_paper/text.md` or any other existing file in the thesis repo.

## Procedure

### Step 1 — Read the paper

Read the PDF:

```
Read: <provided path>
```

If it is a large PDF (>10 pages), read in page ranges of 20 pages at a time until the full paper is covered. Always read the full references section — it contains author names, paper titles, venues, and sometimes artifact URLs that are needed for the search step.

### Step 2 — Extract tools

Identify every tool, approach, prototype, or system studied or surveyed in the paper. For each one, record:

- **Name** — exact name as used in the paper
- **Description** — one sentence summary of what it does
- **Paper title** — full title of the paper that introduces or describes the tool (from the reference list)
- **Authors** — author list as it appears in the reference
- **Venue + Year** — conference/journal name and year of publication
- **Repository URL** — any GitHub/GitLab/Bitbucket URL explicitly mentioned in the paper or its references. If none is given, mark as `none` and proceed to Step 3.5.
- **Reference** — the citation marker as it appears in the paper (e.g., "[42]")

### Step 3 — Ensure the extraction directory exists

```bash
mkdir -p ../extracted-codebases
```

### Step 3.5 — Proactive repo search for tools without an explicit URL

For every tool where no repository URL was found in the paper, run the following staged search using `curl` and `python3`. Use `GIT_ASKPASS=false GIT_TERMINAL_PROMPT=0` for all git operations. Run searches in parallel where possible.

**Stage A — GitHub API search**

Run all three queries and collect candidates:

1. Search by tool name:
   ```bash
   curl -s "https://api.github.com/search/repositories?q=<ToolName>+microservice&per_page=10"
   ```

2. Search by paper title keywords (3–5 distinctive words from the title):
   ```bash
   curl -s "https://api.github.com/search/repositories?q=<title-keywords>+in:name,description&per_page=10"
   ```

3. Search by first author's GitHub account — try username variations (`firstnamelastname`, `firstname-lastname`, `flastname`) using the users endpoint, then list their public repos:
   ```bash
   curl -s "https://api.github.com/users/<username-variant>/repos?per_page=50"
   ```

Parse all results with `python3 -c "import sys,json; ..."`. Filter candidates by: description or name contains tool-related keywords, language matches expected (Java/Python), creation date roughly matches or postdates the paper year.

**Stage B — Known research group namespaces**

If the paper mentions an author affiliation or lab name, try that as a GitHub org:
```bash
curl -s "https://api.github.com/orgs/<org-name>/repos?per_page=50"
```

Also try common academic/industrial orgs that publish microservice tools (e.g. `konveyor`, `IBM`, `sosygroup`, `resess`).

**Stage C — Fetch artifact/replication pages**

If the paper's reference list contains any URL that is not a direct repo link (e.g., a project page, a GitHub Pages site, or a DOI with supplementary material), fetch it:
```bash
curl -s "<url>" | grep -oE 'https://github\.com/[^"' ]+' | sort -u
```

Extract any GitHub/GitLab URLs found in the page HTML.

**Evaluating candidates:**

A candidate repo is accepted if at least one of these holds:
- Its description or README explicitly mentions the tool name or paper title
- It is owned by a confirmed author account and its name/description relates to microservice decomposition
- It is linked from the paper's own artifact page

If a candidate is plausible but unconfirmed, record the URL and mark status as `unverified — check manually`. If no candidate survives the filter, mark the tool as `no public repo found`.

### Step 4 — Clone available repositories

For each tool that has a confirmed or unverified repository URL:

```bash
export GIT_ASKPASS=false GIT_TERMINAL_PROMPT=0
git clone --depth=1 <url> ../extracted-codebases/<tool-name>
```

Use `--depth=1` to avoid downloading full history. If the clone fails (private repo, dead link, etc.), record the failure reason.

After a successful clone, record the commit hash:

```bash
git -C ../extracted-codebases/<tool-name> rev-parse HEAD
```

### Step 5 — Write the tool inventory

Write `evaluation/papers/<PaperKey>.md` with the following structure:

```markdown
# Tool Inventory — <PaperKey>

Extracted from: <paper path>
Date: <today's date>

## Tools

| Tool | Paper | Authors | Venue | Year | Repo URL | Local Path | Status |
|------|-------|---------|-------|------|----------|------------|--------|
| ToolName | Full paper title | Author1, Author2, ... | ICSE | 2023 | https://... or none found | ../extracted-codebases/tool-name | cloned / failed: <reason> / unverified — check manually / no public repo found |

## Notes

Any relevant notes about the survey scope, exclusions, or ambiguities.
```

### Step 6 — Report to the user

Summarise:
- Total tools found
- How many were cloned successfully
- How many were found but unverified (need manual check)
- How many had no public repository despite the search
- How many failed (with reasons)
- Path to the inventory file and the extraction directory

For tools where no repo was found, list them explicitly with their full reference so the user can search manually:

> **No repo found for:**
> - **HyDec** — "Combining Static and Dynamic Analysis to Decompose Monolithic Application into Microservices", Sellami et al., ICSOC 2022
> - **Log2MS** — "Log2MS: ...", Liu et al., ICWS 2022

## Reference files

- **`references/feature-model-dimensions.md`** — the feature model schema (for context on what to look for in tools)
