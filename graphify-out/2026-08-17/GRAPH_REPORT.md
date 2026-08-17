# Graph Report - idx-stock-workers  (2026-08-17)

## Corpus Check
- 61 files · ~12,950 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 354 nodes · 369 edges · 55 communities (54 shown, 1 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
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

## God Nodes (most connected - your core abstractions)
1. `collect_news_once()` - 11 edges
2. `IDX Stock Workers` - 10 edges
3. `run_once()` - 9 edges
4. `Future Plan — Company Vault & Impact Analysis` - 9 edges
5. `analyze_article_impact()` - 8 edges
6. `Roadmap Development` - 7 edges
7. `get_connection()` - 6 edges
8. `_article_from_entry()` - 6 edges
9. `_parse_frontmatter()` - 5 edges
10. `load_company_vault()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `run_once()` --calls--> `get_connection()`  [EXTRACTED]
  workers/news_impact_worker.py → app/core/db.py
- `run_once()` --calls--> `enrich_companies_with_vault()`  [EXTRACTED]
  workers/news_impact_worker.py → app/repositories/company_vault_loader.py
- `run_once()` --calls--> `get_ai_config()`  [EXTRACTED]
  workers/news_impact_worker.py → app/core/config.py
- `run_once()` --calls--> `get_connection()`  [EXTRACTED]
  workers/news_collector_worker.py → app/core/db.py
- `run_once()` --calls--> `company_universe()`  [EXTRACTED]
  workers/news_impact_worker.py → app/repositories/impact_repository.py

## Import Cycles
- None detected.

## Communities (55 total, 1 thin omitted)

### Community 0 - "news_collector.py"
Cohesion: 0.21
Nodes (19): get_connection(), Connection, active_sources(), insert_article(), log_fetch(), mark_source_result(), parsed_datetime(), Any (+11 more)

### Community 1 - "RTK Commands by Workflow"
Cohesion: 0.50
Nodes (7): enrich_companies_with_vault(), load_company_vault(), _parse_frontmatter(), _parse_list(), _parse_scalar(), Any, Path

### Community 2 - "What You Must Do When Invoked"
Cohesion: 0.33
Nodes (5): Driver bisnis, Ringkasan bisnis, Risiko utama, Sensitif terhadap berita, Sumber pendapatan utama

### Community 3 - "IDX Stock Workers"
Cohesion: 0.17
Nodes (11): AI impact worker, Database contract, Environment, IDX Stock Workers, Install, News collector, Run continuous local, Run sekali (+3 more)

### Community 4 - "analyze_article_impact"
Cohesion: 0.24
Nodes (16): AIConfig, get_ai_config(), company_universe(), pending_articles(), Any, Connection, save_impact_analysis(), analyze_article_impact() (+8 more)

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
Cohesion: 0.12
Nodes (15): Arsitektur Target, Format Vault, Future Plan — Company Vault & Impact Analysis, Kondisi Saat Ini, Phase 2 — Hash & Versioning Vault, Phase 3 — Two-Stage AI Analysis, Phase 4 — Keyword Retrieval Lokal, Phase 5 — Vector Retrieval Lokal (+7 more)

## Knowledge Gaps
- **248 isolated node(s):** `idx-stock-workers`, `News collector`, `Struktur`, `Environment`, `Install` (+243 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_connection()` connect `news_collector.py` to `analyze_article_impact`?**
  _High betweenness centrality (0.007) - this node is a cross-community bridge._
- **Why does `run_once()` connect `analyze_article_impact` to `news_collector.py`, `RTK Commands by Workflow`?**
  _High betweenness centrality (0.003) - this node is a cross-community bridge._
- **What connects `idx-stock-workers`, `News collector`, `Struktur` to the rest of the system?**
  _248 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Future Plan — Company Vault & Impact Analysis` be split into smaller, more focused modules?**
  _Cohesion score 0.125 - nodes in this community are weakly interconnected._