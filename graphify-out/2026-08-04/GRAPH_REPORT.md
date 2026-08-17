# Graph Report - idx-stock-workers  (2026-08-01)

## Corpus Check
- 25 files · ~14,007 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 138 nodes · 184 edges · 22 communities (17 shown, 5 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

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

## God Nodes (most connected - your core abstractions)
1. `collect_news_once()` - 12 edges
2. `What You Must Do When Invoked` - 12 edges
3. `RTK Commands by Workflow` - 11 edges
4. `/graphify` - 10 edges
5. `IDX Stock Workers` - 10 edges
6. `run_once()` - 9 edges
7. `analyze_article_impact()` - 8 edges
8. `graphify reference: extra exports and benchmark` - 8 edges
9. `get_connection()` - 6 edges
10. `_article_from_entry()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `run_once()` --calls--> `get_ai_config()`  [EXTRACTED]
  workers/news_impact_worker.py → app/core/config.py
- `run_once()` --calls--> `get_connection()`  [EXTRACTED]
  workers/news_impact_worker.py → app/core/db.py
- `run_once()` --calls--> `analyze_article_impact()`  [EXTRACTED]
  workers/news_impact_worker.py → app/services/impact_analyzer.py
- `run_once()` --calls--> `collect_news_once()`  [EXTRACTED]
  workers/news_collector_worker.py → app/services/news_collector.py
- `run_once()` --calls--> `get_connection()`  [EXTRACTED]
  workers/news_collector_worker.py → app/core/db.py

## Import Cycles
- None detected.

## Communities (22 total, 5 thin omitted)

### Community 0 - "news_collector.py"
Cohesion: 0.30
Nodes (16): active_sources(), ensure_news_schema(), insert_article(), log_fetch(), mark_source_result(), parsed_datetime(), Any, Connection (+8 more)

### Community 1 - "RTK Commands by Workflow"
Cohesion: 0.13
Nodes (14): Analysis & Debug (70-90% savings), Build & Compile (80-90% savings), Files & Search (60-75% savings), Git (59-80% savings), GitHub (26-87% savings), Golden Rule, Infrastructure (85% savings), JavaScript/TypeScript Tooling (70-90% savings) (+6 more)

### Community 2 - "What You Must Do When Invoked"
Cohesion: 0.13
Nodes (15): Part A - Structural extraction for code files, Part B - Semantic extraction (parallel subagents), Part C - Merge AST + semantic into final extraction, Step 0 - GitHub repos and multi-path merge (only if a URL or several paths), Step 1 - Ensure graphify is installed, Step 2.5 - Video and audio (only if video files detected), Step 2 - Detect files, Step 3 - Extract entities and relationships (+7 more)

### Community 3 - "IDX Stock Workers"
Cohesion: 0.17
Nodes (11): AI impact worker, Database contract, Environment, IDX Stock Workers, Install, News collector, Run continuous local, Run sekali (+3 more)

### Community 4 - "analyze_article_impact"
Cohesion: 0.42
Nodes (8): AIConfig, get_ai_config(), analyze_article_impact(), _compact_universe(), _extract_json(), Any, _response_json(), Response

### Community 5 - "news_impact_worker.py"
Cohesion: 0.49
Nodes (8): company_universe(), ensure_impact_schema(), pending_articles(), Any, Connection, save_impact_analysis(), main(), run_once()

### Community 6 - "/graphify"
Cohesion: 0.20
Nodes (9): For /graphify add and --watch, For /graphify query, For the commit hook and native AGENTS.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Usage (+1 more)

### Community 7 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 8 - "get_connection"
Cohesion: 0.53
Nodes (4): get_connection(), Connection, main(), run_once()

### Community 9 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 10 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 11 - "graphify reference: commit hook and native AGENTS.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native AGENTS.md integration (Trae), graphify reference: commit hook and native AGENTS.md integration

### Community 12 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

## Knowledge Gaps
- **64 isolated node(s):** `idx-stock-workers`, `Usage`, `What graphify is for`, `Step 0 - GitHub repos and multi-path merge (only if a URL or several paths)`, `Step 1 - Ensure graphify is installed` (+59 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_connection()` connect `get_connection` to `news_impact_worker.py`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Why does `What You Must Do When Invoked` connect `What You Must Do When Invoked` to `/graphify`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Why does `collect_news_once()` connect `news_collector.py` to `get_connection`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **What connects `idx-stock-workers`, `Usage`, `What graphify is for` to the rest of the system?**
  _64 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `RTK Commands by Workflow` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._
- **Should `What You Must Do When Invoked` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._