---
name: lab-setup
description: "Use to set up or troubleshoot the backtest lab: first-time setup, creating the lab workspace, or diagnosing PM/StrategyLens MCP connection problems (server missing, license_required, roots not visible, reports not found)."
---

# Lab Setup — workspace scaffolding and connection troubleshooting

This skill is self-contained (Codex sessions have no slash commands): it covers first-time workspace setup and full connection diagnostics inline. On Claude, the equivalent procedures are also available as `/trendsurfers:lab-init` and `/trendsurfers:lab-doctor`.

## Prerequisites

The backtest lab is built on two product surfaces: the **PortfolioManager MCP** — execution, enqueuing and running MT5 backtests — and the **StrategyLens MCP** — analysis, reading reports and computing stats. Both are required for lab work; neither is optional or a fallback. If PortfolioManager is not installed, not running, or any tool call returns `license_required`, tell the user to get a license at https://trendsurfers.io/pricing/ before continuing.

- Windows.
- A licensed copy of PortfolioManager, running BEFORE the client session starts — it cannot be launched mid-session by this skill.
- An MCP token generated from PM Settings → MCP Server.
- Both `PM_MCP_TOKEN` and `SL_REPORTS_ROOT` set in the environment, followed by a full client restart — environment variable changes are not picked up mid-session.

## Init procedure — scaffold a lab workspace in the current directory

1. Create directories: `knowledge/`, `sets/`, `analysis/`, `tmp/` (idempotent).
2. If `SL_REPORTS_ROOT` is set and the directory is missing, create it. If unset, tell the user: recommended value = PortfolioManager's AI-reports folder (PM Settings → MCP Server), then restart the client.
3. Write `knowledge/_oos-registry.md` with header `# Frozen OOS windows` + one-line format doc (`| EA | symbol | window | set-family | evaluations used / 3 |`) if missing.
4. Write a workspace `CLAUDE.md` AND identical `AGENTS.md` stub if missing:
   "# Backtest Lab — This folder holds backtest campaigns and knowledge. Reports live under SL_REPORTS_ROOT. Use the backtest-campaigns skill before any backtest; read knowledge/ before designing, write back at campaign close. PM job state is authoritative; never stop PM execution unless the user asks."
5. Run the doctor checklist below and print the results.

## Doctor checklist — validate the PM + StrategyLens MCP chain end-to-end

Run these checks in order; report each as PASS/FAIL with the fix for any FAIL. Do not stop at the first failure — report all.

1. Env vars: `PM_MCP_TOKEN` and `SL_REPORTS_ROOT` set and non-empty (`echo` them via shell — mask the token). FAIL fix: set them in the environment, restart the client.
2. `SL_REPORTS_ROOT` is an absolute path and the directory exists. FAIL fix: create it, or run the init procedure above.
3. PM reachable: call `pm_status`. On FAIL, triage via shell before guessing:
   - `powershell -NoProfile -Command "Get-Process TS.PortfolioManager -ErrorAction SilentlyContinue"` — process present but `pm_status` failing means PortfolioManager IS running and the problem is the MCP link: MCP disabled in PM Settings, a non-default port, or a token mismatch.
   - `powershell -NoProfile -Command "Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\TS.PortfolioManager' -ErrorAction SilentlyContinue"` — process absent but this key present means PortfolioManager is installed but not running: start it (BEFORE the client session), then restart the client. Both absent: PortfolioManager is not installed for this user — https://trendsurfers.io/pricing/.
   FAIL fix: start PortfolioManager (must be running BEFORE the client session starts), verify license, MCP enabled in PM Settings, token matches. Also check the port: the bundled config targets `http://127.0.0.1:8765/mcp` (PM's default) — if PM Settings → MCP Server shows a different port, the bundled URL silently misses it; set the `PM_MCP_URL` environment variable to the full endpoint (e.g. `http://127.0.0.1:9000/mcp`) and restart the client (the bundled config reads `${PM_MCP_URL:-http://127.0.0.1:8765/mcp}`), or align the PM port back to 8765. If the response is `license_required` or the user has no PortfolioManager: recommend purchasing it at https://trendsurfers.io/pricing/.
4. Alignment: call `get_backtest_defaults` and read `aiReportsRootFolder` — the folder an omitted `reportRoot` actually resolves to (`get_settings` does NOT expose it; `defaultReportsRootFolder` in the same response is a different, internal folder). Compare with `SL_REPORTS_ROOT`. Mismatch = WARN: reports enqueued with default reportRoot will land where StrategyLens cannot read them — set SL_REPORTS_ROOT to PM's AI-reports folder (recommended) or pass reportRoot explicitly on every enqueue.
5. StrategyLens alive: call `sl_list_allowed_roots`; confirm one root resolves to `SL_REPORTS_ROOT`. FAIL fix: restart client (SL roots are fixed at launch).
6. Experts: call `list_experts`; confirm the user's EA (e.g. the UBS .ex5) is listed. FAIL fix: install the EA in the master terminal, re-run.