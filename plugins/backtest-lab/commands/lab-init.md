---
description: Scaffold a backtest lab workspace in the current directory
---
1. Create directories: `knowledge/`, `sets/`, `analysis/`, `tmp/` (idempotent).
2. If `SL_REPORTS_ROOT` is set and the directory is missing, create it. If unset, tell the user: recommended value = PortfolioManager's AI-reports folder (PM Settings → MCP Server), then restart the client.
3. Write `knowledge/_oos-registry.md` with header `# Frozen OOS windows` + one-line format doc (`| EA | symbol | window | set-family | evaluations used / 3 |`) if missing.
4. Write a workspace `CLAUDE.md` AND identical `AGENTS.md` stub if missing:
   "# Backtest Lab — This folder holds backtest campaigns and knowledge. Reports live under SL_REPORTS_ROOT. Use the backtest-campaigns skill before any backtest; read knowledge/ before designing, write back at campaign close. PM job state is authoritative; never stop PM execution unless the user asks."
5. Run the lab-doctor checks (see /backtest-lab:lab-doctor) and print the results.
