# Graph Report - idx-stock-workers  (2026-08-17)

## Corpus Check
- 79 files · ~26,135 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 505 nodes · 549 edges · 71 communities (65 shown, 6 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 2 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `cdc99f0c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- news_collector.py
- RTK Commands by Workflow
- What You Must Do When Invoked
- IDX Stock Workers
- analyze_article_impact
- news_impact_worker.py
- /graphify
- graphify reference: extra exports and benchmark
- get_connection
- graphify reference: query, path, explain
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native AGENTS.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- AGENTS.md
- extraction-spec.md
- idx-stock-workers
- BRIS.md
- BRPT.md
- BTPS.md
- CPIN.md
- ESSA.md
- EXCL.md
- GOTO.md
- HRUM.md
- ICBP.md
- INCO.md
- INDF.md
- INKP.md
- ISAT.md
- ITMG.md
- JSMR.md
- KLBF.md
- MAPA.md
- MAPI.md
- MBMA.md
- MDKA.md
- MEDC.md
- MIKA.md
- PGAS.md
- PGEO.md
- PTBA.md
- SIDO.md
- SMGR.md
- SRTG.md
- TLKM.md
- TOWR.md
- UNTR.md
- UNVR.md
- Future Plan — Company Vault & Impact Analysis
- planning.md
- news_impact.py
- What You Must Do When Invoked
- RTK Commands by Workflow
- graphify reference: extra exports and benchmark
- Phase 5 — Vector DB / Embedding Retrieval
- graphify reference: query, path, explain
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native AGENTS.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- Implementation Status
- AGENTS.md
- extraction-spec.md

## God Nodes (most connected - your core abstractions)
1. `What You Must Do When Invoked` - 12 edges
2. `collect_news_once()` - 11 edges
3. `RTK Commands by Workflow` - 11 edges
4. `analyze_article_impact()` - 10 edges
5. `run_once()` - 10 edges
6. `/graphify` - 10 edges
7. `check_required_tables()` - 9 edges
8. `get_ai_config()` - 8 edges
9. `_article_from_entry()` - 8 edges
10. `graphify reference: extra exports and benchmark` - 8 edges

## Surprising Connections (you probably didn't know these)
- `test_database_config_validation_and_immutability()` --calls--> `get_database_config()`  [EXTRACTED]
  tests/test_config_db.py → app/core/config.py
- `test_ai_config_bounds()` --calls--> `get_ai_config()`  [EXTRACTED]
  tests/test_config_db.py → app/core/config.py
- `run_once()` --calls--> `enrich_companies_with_vault()`  [EXTRACTED]
  workers/news_impact.py → app/knowledge/company_vault.py
- `test_extract_json_rejects_invalid_payload()` --calls--> `_extract_json()`  [EXTRACTED]
  tests/test_impact_analyzer.py → app/services/impact_analyzer.py
- `test_extract_json_supports_fenced_json()` --calls--> `_extract_json()`  [EXTRACTED]
  tests/test_impact_analyzer.py → app/services/impact_analyzer.py

## Import Cycles
- None detected.

## Communities (71 total, 6 thin omitted)

### Community 0 - "news_collector.py"
Cohesion: 0.27
Nodes (18): active_sources(), insert_article(), log_fetch(), mark_source_result(), parsed_datetime(), Any, Connection, seed_default_sources() (+10 more)

### Community 1 - "RTK Commands by Workflow"
Cohesion: 0.40
Nodes (8): enrich_companies_with_vault(), load_company_vault(), _parse_frontmatter(), _parse_list(), _parse_scalar(), Any, Path, test_frontmatter_and_enrichment()

### Community 2 - "What You Must Do When Invoked"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 3 - "IDX Stock Workers"
Cohesion: 0.25
Nodes (7): Database contract, Environment dan instalasi, IDX Stock Workers, Menjalankan worker, Struktur, Verifikasi, Worker

### Community 4 - "analyze_article_impact"
Cohesion: 0.36
Nodes (11): AIConfig, analyze_article_impact(), _compact_universe(), _extract_json(), Any, _response_json(), _shorten_profile(), Response (+3 more)

### Community 5 - "news_impact_worker.py"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 6 - "/graphify"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 7 - "graphify reference: extra exports and benchmark"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 8 - "get_connection"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 9 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 10 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 11 - "graphify reference: commit hook and native AGENTS.md integration"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 12 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 13 - "graphify reference: GitHub clone and cross-repo merge"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 14 - "graphify reference: transcribe video and audio"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 15 - "AGENTS.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 16 - "extraction-spec.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 22 - "BRIS.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 23 - "BRPT.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 24 - "BTPS.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 25 - "CPIN.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 26 - "ESSA.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 27 - "EXCL.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 28 - "GOTO.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 29 - "HRUM.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 30 - "ICBP.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 31 - "INCO.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 32 - "INDF.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 33 - "INKP.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 34 - "ISAT.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 35 - "ITMG.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 36 - "JSMR.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 37 - "KLBF.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 38 - "MAPA.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 39 - "MAPI.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 40 - "MBMA.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 41 - "MDKA.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 42 - "MEDC.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 43 - "MIKA.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 44 - "PGAS.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 45 - "PGEO.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 46 - "PTBA.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 47 - "SIDO.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 48 - "SMGR.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 49 - "SRTG.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 50 - "TLKM.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 51 - "TOWR.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 52 - "UNTR.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 53 - "UNVR.md"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 54 - "Future Plan — Company Vault & Impact Analysis"
Cohesion: 0.22
Nodes (8): Audit dan re-analysis, Fondasi selesai, Future Plan — Company Vault & Impact Analysis, Hash dan versioning vault, Prinsip biaya dan ownership, Retrieval kandidat, Roadmap tersisa, Target alur

### Community 55 - "planning.md"
Cohesion: 0.05
Nodes (43): 1. Keyword retrieval, 1. Loader vault lokal, 1. Table baru `company_profiles`, 2. Indexer, 2. Merge dengan company universe DB, 3. Update prompt AI, 3. Worker startup indexing, Cocok untuk (+35 more)

### Community 56 - "news_impact.py"
Cohesion: 0.12
Nodes (23): _bounded_int_env(), DatabaseConfig, get_ai_config(), get_database_config(), _required_env(), check_required_tables(), get_connection(), Connection (+15 more)

### Community 57 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native AGENTS.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 58 - "RTK Commands by Workflow"
Cohesion: 0.13
Nodes (14): Analysis & Debug (70-90% savings), Build & Compile (80-90% savings), Files & Search (60-75% savings), Git (59-80% savings), GitHub (26-87% savings), Golden Rule, Infrastructure (85% savings), JavaScript/TypeScript Tooling (70-90% savings) (+6 more)

### Community 59 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 60 - "Phase 5 — Vector DB / Embedding Retrieval"
Cohesion: 0.25
Nodes (8): Cocok untuk, Embedding model lokal, Flow, Output phase 5, Phase 5 — Vector DB / Embedding Retrieval, Pilihan paling natural, Pilihan stack, Risiko

### Community 61 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 62 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 63 - "graphify reference: commit hook and native AGENTS.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native AGENTS.md integration (Trae), graphify reference: commit hook and native AGENTS.md integration

### Community 64 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

## Knowledge Gaps
- **333 isolated node(s):** `idx-stock-workers`, `Usage`, `What graphify is for`, `Step 0 - GitHub repos and multi-path merge (only if a URL or several paths)`, `Step 1 - Ensure graphify is installed` (+328 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `collect_news_once()` connect `news_collector.py` to `news_impact.py`?**
  _High betweenness centrality (0.003) - this node is a cross-community bridge._
- **What connects `idx-stock-workers`, `Usage`, `What graphify is for` to the rest of the system?**
  _333 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `planning.md` be split into smaller, more focused modules?**
  _Cohesion score 0.045454545454545456 - nodes in this community are weakly interconnected._
- **Should `news_impact.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11904761904761904 - nodes in this community are weakly interconnected._
- **Should `What You Must Do When Invoked` be split into smaller, more focused modules?**
  _Cohesion score 0.08 - nodes in this community are weakly interconnected._
- **Should `RTK Commands by Workflow` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._