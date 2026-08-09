# TrendSurfers Agent Plugins

AI-agent plugins for TrendSurfers PortfolioManager + StrategyLens — Claude Code and OpenAI Codex.

## What this is

One marketplace, two plugins:

- **backtest-lab** — disciplined MT5 backtest campaigns driven through two product surfaces: the **PortfolioManager MCP**, which is the *execution* surface (enqueue, run, and manage MT5 backtests), and the **StrategyLens MCP**, which is the *analysis* surface (read reports, compute stats). Enforces in-sample/out-of-sample methodology, robustness checks (cross-broker, cross-range, cross-tick-model), and a per-EA knowledge base so a dead configuration is never silently re-run.
- **ubs-ea** — a domain pack for the Ultimate Breakout System (UBS) Expert Advisor: reading and designing `.set` files, choosing risk modes, deployment guidance, and campaign templates tuned to UBS. **Requires `backtest-lab`** — it has no orchestration of its own and routes all execution and analysis through it.

## Requirements

- Windows only.
- A licensed copy of PortfolioManager, **running before the client session starts** (Claude Code or Codex). It cannot be launched mid-session by these plugins. No license yet? Purchase one at https://trendsurfers.io/pricing/.
- Node.js (for `npx`) — the StrategyLens MCP server ships as an npm package and is launched on demand via `npx`; no separate install step.

## Setup

1. In PortfolioManager: **Settings → MCP Server** → enable it. PortfolioManager writes the generated token to the `PM_MCP_TOKEN` user environment variable automatically whenever its MCP server starts or the token is regenerated.
2. Verify `PM_MCP_TOKEN` is present in your environment (`echo %PM_MCP_TOKEN%` in a NEW terminal); set it manually from Settings → MCP Server only if absent.
3. Set the environment variable `SL_REPORTS_ROOT` to PortfolioManager's AI-reports folder — an absolute path, and the directory must already exist.
4. Restart the client (Claude Code or Codex). Environment variable changes are not picked up mid-session.

The bundled configuration targets `http://127.0.0.1:8765/mcp` — PortfolioManager's default MCP port. If you changed the port in PM Settings → MCP Server, either change it back to 8765 or override the server URL in your client configuration.

## Install — Claude Code

```
/plugin marketplace add trendsurfers-software/agent-plugins
/plugin install backtest-lab@trendsurfers
/plugin install ubs-ea@trendsurfers
/backtest-lab:lab-init
```

`ubs-ea` declares `backtest-lab` as a dependency; installing both explicitly (either order) is still the recommended path.

`/backtest-lab:lab-init` scaffolds the lab workspace in the current directory and runs the same connection checks as `/backtest-lab:lab-doctor`.

## Install — Codex

1. Clone this repo.
2. Point Codex at the local catalog: `.agents/plugins/marketplace.json`. This lists both plugins as local-path sources (`./plugins/backtest-lab`, `./plugins/ubs-ea`).
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

The StrategyLens MCP package is pinned to `@latest` deliberately, so every campaign runs against the current release. To pin a specific version instead — for a reproducible archived campaign, for example — replace `@latest` with `@trendsurfers/strategy-lens-mcp@<version>` in the plugin's bundled `plugins/backtest-lab/.mcp.json`, or in the `args` array of the `config.toml` block above.

## First campaign

```
cd <your lab workspace>       # created by lab-init
/backtest-lab:lab-campaign <EA> <SYMBOL-TF> <slug>
```

Read the `backtest-campaigns` skill first — it defines the mandatory campaign folder structure, IS/OOS methodology, and reporting rules that apply before you enqueue anything.

## License

© TrendSurfers. All rights reserved. Free to use with a licensed PortfolioManager; no redistribution.

MetaTrader 5 is a trademark of MetaQuotes Ltd. TrendSurfers is not affiliated with, endorsed by, or sponsored by MetaQuotes.
