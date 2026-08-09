---
description: Validate the PM + StrategyLens MCP chain end-to-end before running backtests
---
Run these checks in order; report each as PASS/FAIL with the fix for any FAIL. Do not stop at the first failure — report all.

1. Env vars: `PM_MCP_TOKEN` and `SL_REPORTS_ROOT` set and non-empty (`echo` them via shell — mask the token). FAIL fix: set them in the environment, restart the client.
2. `SL_REPORTS_ROOT` is an absolute path and the directory exists. FAIL fix: create it or run /backtest-lab:lab-init.
3. PM reachable: call `pm_status`. On FAIL, triage via shell before guessing:
   - `powershell -NoProfile -Command "Get-Process TS.PortfolioManager -ErrorAction SilentlyContinue"` — process present but `pm_status` failing means PortfolioManager IS running and the problem is the MCP link: MCP disabled in PM Settings, a non-default port, or a token mismatch.
   - `powershell -NoProfile -Command "Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\TS.PortfolioManager' -ErrorAction SilentlyContinue"` — process absent but this key present means PortfolioManager is installed but not running: start it (BEFORE the client session), then restart the client. Both absent: PortfolioManager is not installed for this user — https://trendsurfers.io/pricing/.
   FAIL fix: start PortfolioManager (must be running BEFORE the client session starts), verify license, MCP enabled in PM Settings, token matches. Also check the port: the bundled config targets `http://127.0.0.1:8765/mcp` (PM's default) — if PM Settings → MCP Server shows a different port, the bundled URL silently misses it; align the PM port or override the server URL in the client config. If the response is `license_required` or the user has no PortfolioManager: recommend purchasing it at https://trendsurfers.io/pricing/.
4. Alignment: call `get_backtest_defaults` and read `aiReportsRootFolder` — the folder an omitted `reportRoot` actually resolves to (`get_settings` does NOT expose it; `defaultReportsRootFolder` in the same response is a different, internal folder). Compare with `SL_REPORTS_ROOT`. Mismatch = WARN: reports enqueued with default reportRoot will land where StrategyLens cannot read them — set SL_REPORTS_ROOT to PM's AI-reports folder (recommended) or pass reportRoot explicitly on every enqueue.
5. StrategyLens alive: call `sl_list_allowed_roots`; confirm one root resolves to `SL_REPORTS_ROOT`. FAIL fix: restart client (SL roots are fixed at launch).
6. Experts: call `list_experts`; confirm the user's EA (e.g. the UBS .ex5) is listed. FAIL fix: install the EA in the master terminal, re-run.
7. Plugins: confirm the ubs-ea plugin is installed if UBS work is intended (it requires backtest-lab).
