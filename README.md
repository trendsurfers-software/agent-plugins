# TrendSurfers Agent Plugins

AI-agent plugins for TrendSurfers PortfolioManager + StrategyLens — Claude Code and OpenAI Codex.

## What this is

One plugin — `trendsurfers` — with two capability packs:

- **Backtest lab** — disciplined MT5 backtest campaigns driven through two product surfaces: the **PortfolioManager MCP**, which is the *execution* surface (enqueue, run, and manage MT5 backtests), and the **StrategyLens MCP**, which is the *analysis* surface (read reports, compute stats). Enforces in-sample/out-of-sample methodology, robustness checks (cross-broker, cross-range, cross-tick-model), and a per-EA knowledge base so a dead configuration is never silently re-run.
- **UBS domain pack** — for the Ultimate Breakout System (UBS) Expert Advisor: reading and designing `.set` files, choosing risk modes, deployment guidance, and campaign templates tuned to UBS. It has no orchestration of its own — all execution and analysis route through the backtest lab tools in this same plugin.

## Requirements

- Windows only.
- A licensed copy of PortfolioManager, **running before the client session starts** (Claude Code or Codex). It cannot be launched mid-session by these plugins. No license yet? Purchase one at https://trendsurfers.io/pricing/.
- Node.js (for `npx`) — the StrategyLens MCP server ships as an npm package and is launched on demand via `npx`; no separate install step.

## Setup

1. In PortfolioManager: **Settings → MCP Server** → enable it. PortfolioManager writes the generated token to the `PM_MCP_TOKEN` user environment variable automatically whenever its MCP server starts or the token is regenerated.
2. Verify `PM_MCP_TOKEN` is present in your environment (`echo %PM_MCP_TOKEN%` in a NEW terminal); set it manually from Settings → MCP Server only if absent.
3. Set the environment variable `SL_REPORTS_ROOT` to PortfolioManager's AI-reports folder — an absolute path, and the directory must already exist.
4. Restart the client (Claude Code or Codex). Environment variable changes are not picked up mid-session.

The bundled configuration targets `http://127.0.0.1:8765/mcp` — PortfolioManager's default MCP port. If you changed the port in PM Settings → MCP Server, set the environment variable `PM_MCP_URL` to the full endpoint (e.g. `http://127.0.0.1:9000/mcp`) and restart the client; when unset, the default above is used. Codex users set the URL directly in the `config.toml` block below instead.

### Setting the environment variables, per client

The variables in play: `PM_MCP_TOKEN` (PortfolioManager maintains it automatically — see step 1), `SL_REPORTS_ROOT` (you set it once), and optionally `PM_MCP_URL` (only for a non-default PM port).

**Windows user environment (works for every client — recommended).** Start menu → *"Edit environment variables for your account"* → add the variable under *User variables*. Or from any terminal:

```
setx SL_REPORTS_ROOT "C:\path\to\pm-ai-reports"
```

`setx` (and the GUI) affect **future** processes only — fully restart the client afterwards, including quitting any tray icon. A common trap: `set X=...` (cmd) or `$env:X=...` (PowerShell) only lives inside that one shell window and is gone the moment the client launches from anywhere else.

**Claude Code — terminal, VS Code/JetBrains extensions, and desktop-app (Cowork) local sessions.** All surfaces read the Windows user environment above. Alternatively, pin the variables in `%USERPROFILE%\.claude\settings.json` so every Claude Code session gets them regardless of how it was launched:

```json
{
  "env": {
    "SL_REPORTS_ROOT": "C:\\path\\to\\pm-ai-reports",
    "PM_MCP_URL": "http://127.0.0.1:8765/mcp"
  }
}
```

Leave `PM_MCP_TOKEN` out of `settings.json` — PortfolioManager keeps the Windows user variable current automatically, and a copied value in `settings.json` would go stale on token regeneration.

**Claude Desktop app.** The app is not launched from a terminal, so shell-only exports never reach it. Use the Windows user environment (or the `settings.json` block above for its Cowork sessions), then fully quit and relaunch the app.

**Codex CLI and IDE extension.** Inherit the Windows user environment like any local program. The `bearer_token_env_var = "PM_MCP_TOKEN"` line in `~/.codex/config.toml` (block below) tells Codex which variable holds the PM token.

**Codex in ChatGPT (web, or cloud tasks) — not supported.** Those sessions run in OpenAI's cloud sandbox and cannot reach PortfolioManager at `127.0.0.1`. The same applies to any cloud-hosted agent: these plugins require a client running on the same Windows machine as PortfolioManager — Claude Code, the Claude desktop app, Codex CLI, or the Codex IDE extension.

## Install — Claude Code

```
/plugin marketplace add trendsurfers-software/agent-plugins
/plugin install trendsurfers@trendsurfers
/trendsurfers:lab-init
```

`/trendsurfers:lab-init` scaffolds the lab workspace in the current directory and runs the same connection checks as `/trendsurfers:lab-doctor`.

## Install — Codex

1. Clone this repo.
2. Point Codex at the local catalog: `.agents/plugins/marketplace.json`. This lists the plugin as a local-path source (`./plugins/trendsurfers`).
3. Invoke `$lab-setup` — Codex sessions have no slash commands, so this skill covers both first-time workspace setup and the full connection diagnostics inline (the same checks as `lab-doctor` above).

Codex always needs the PortfolioManager server declared in `~/.codex/config.toml` — the bundled plugin MCP config is Claude-shaped and its token header does not map to Codex's `bearer_token_env_var`, so PM authentication fails without this block even when the catalog is picked up. Add the StrategyLens entry too if your setup does not pick up the local catalog:

```toml
[mcp_servers.ts-portfolio-manager]
url = "http://127.0.0.1:8765/mcp"
bearer_token_env_var = "PM_MCP_TOKEN"

[mcp_servers.strategy-lens]
command = "cmd"
args = ["/c", "npx", "-y", "@trendsurfers/strategy-lens-mcp@latest", "<your SL_REPORTS_ROOT path>"]
```

## Reproducibility note

The StrategyLens MCP package is pinned to `@latest` deliberately, so every campaign runs against the current release. To pin a specific version instead — for a reproducible archived campaign, for example — replace `@latest` with `@trendsurfers/strategy-lens-mcp@<version>` in the plugin's bundled `plugins/trendsurfers/.mcp.json`, or in the `args` array of the `config.toml` block above.

## First campaign

```
cd <your lab workspace>       # created by lab-init
/trendsurfers:lab-campaign <EA> <SYMBOL-TF> <slug>
```

Read the `backtest-campaigns` skill first — it defines the mandatory campaign folder structure, IS/OOS methodology, and reporting rules that apply before you enqueue anything.

## License

© TrendSurfers. All rights reserved. Free to use with a licensed PortfolioManager; no redistribution.

MetaTrader 5 is a trademark of MetaQuotes Ltd. TrendSurfers is not affiliated with, endorsed by, or sponsored by MetaQuotes.
