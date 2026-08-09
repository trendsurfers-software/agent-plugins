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
3. Set the environment variable `SL_REPORTS_ROOT` to PortfolioManager's **AI reports folder** — the exact path shown in PM Settings → MCP Server (absolute path; the directory must exist). Keeping these two the same is what makes the combo run smoothly: PortfolioManager writes every backtest report into that folder, and StrategyLens is allowed to read exactly that folder — so reports are analyzable the moment a backtest finishes, with no copying and no permission errors.
   - StrategyLens can be allowed **more than one folder** if you need it (say, an archive of older reports). Claude Code: set the environment variables `SL_REPORTS_ROOT_2` (and `SL_REPORTS_ROOT_3`) to the extra folders — the plugin picks them up automatically after a client restart; unset slots are simply ignored. Codex: add each extra folder as one more path at the end of the `args` list in the `config.toml` block below. Never remove the main reports folder when adding extras.
4. Restart the client (Claude Code or Codex). Environment variable changes are not picked up mid-session.

The bundled configuration targets `http://127.0.0.1:8765/mcp` — PortfolioManager's default MCP port. If you changed the port in PM Settings → MCP Server, set the environment variable `PM_MCP_URL` to the full endpoint (e.g. `http://127.0.0.1:9000/mcp`) and restart the client; when unset, the default above is used. Codex users set the URL directly in the `config.toml` block below instead.

### Setting the environment variables — step by step

Two variables matter: `SL_REPORTS_ROOT` (you set it once) and `PM_MCP_TOKEN` (PortfolioManager manages it for you). Everything happens once, on the Windows PC where PortfolioManager runs.

**Set the variable in Windows (every app reads this):**

1. Press the Windows key, type `environment`, and open **"Edit environment variables for your account"**.
2. Under *User variables*, click **New…** — Name: `SL_REPORTS_ROOT`, Value: the full path of PortfolioManager's AI-reports folder (shown in PM Settings → MCP Server). Click OK.
3. Check that `PM_MCP_TOKEN` already appears in the same list — PortfolioManager adds and refreshes it by itself whenever its MCP server is on. Only add it by hand if it is missing.
4. Fully restart the app you use — quit it from the system-tray icon too, not just the window. Apps read these variables only at startup.

**Then, depending on what you use:**

- **Claude Code in a terminal or IDE (VS Code / JetBrains):** nothing more to do — open a new terminal or window.
- **Claude desktop app (including Cowork):** fully quit the app (tray icon → Quit) and start it again. It picks up the same Windows variables.
- **Codex — CLI, IDE extension, or the ChatGPT desktop app:** the same Windows variables are picked up. Additionally paste the `config.toml` block below once — all Codex surfaces on the same machine share that file. In the ChatGPT desktop app, run Codex in a **local** environment (its settings pane), not a cloud one.
- **ChatGPT on the web, or Codex cloud tasks: cannot be used.** Those run on OpenAI's servers and cannot reach the PortfolioManager on your PC. Any cloud-hosted agent has the same limitation — use one of the local options above.

*Advanced (optional, Claude Code only):* variables can also live in `%USERPROFILE%\.claude\settings.json` as `{"env": {"SL_REPORTS_ROOT": "C:\\path\\to\\pm-ai-reports"}}` — they then apply to every Claude Code session no matter how it was launched. Do not put `PM_MCP_TOKEN` there: a copied value goes stale when the token regenerates; the Windows variable is always current.

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
