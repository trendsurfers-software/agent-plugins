# UBS deployment — AutoLoader / OneChart

UBS can run one strategy per chart, or many strategies from a single chart via its **AutoLoader
(OneChart)** model: one EA instance, attached to one chart, self-multiplexes N independent
strategies — each strategy is just a `.set` file in the AutoLoad folder, loaded and run as if
attached to its own chart, with its own magic number and symbol.

## The AutoLoad folder — Common\Files

Per the vendor manual, the AutoLoader reads its sets from the machine-wide Common folder:

```
%APPDATA%\MetaQuotes\Terminal\Common\Files\<Sets_Folder>\
```

This is the authoritative location. **It holds for portable installs too:** the Common folder is
machine-wide (`TERMINAL_COMMONDATA_PATH`) and does not move with a `/portable` terminal, so the
AutoLoader loads from Common\Files regardless of where the terminal itself lives. Copies placed
under a terminal's own `MQL5\Files\` folder are harmless dead weight — not the load path.

**The EA's UI input hint `Folder with .set files (MQL5\Files\Sets)` is stale and misleading — do
not trust it.** The vendor manual gives the correct Common\Files location. An input's description
string is authoritative for *naming*, not for *behavior*.

`Sets_Folder` accepts a **nested path**, not only a flat name (for example `MyPortfolio\GoldSets`).
Always read the master's actual `Sets_Folder` value and match it exactly — never assume a flat
folder name.

## Every failure mode is silent — verify from the log

A wrong folder, a mismatched `Sets_Folder` name, or a symbol mismatch produces **no error dialog
and no crash** — the EA simply loads zero strategies (or skips one child) and does nothing. So
every deployment must be confirmed from the Experts log line:

```
Successfully loaded N set file(s) from folder <name>
```

**`N` must equal the number of child `.set` files you placed in the folder.** If it is lower, a
child failed to load silently. The on-chart InfoPanel should likewise enumerate every loaded
strategy with its magic number and symbol.

| Failure | Symptom | Cause |
|---|---|---|
| Sets placed under `MQL5\Files\` instead of Common\Files | Zero strategies load, no trades, no log entries | Common\Files is the load path (above) |
| `Sets_Folder` name/path mismatch (assumed flat, master uses a nested path — or vice versa) | Same silent-empty failure | Never hardcode the folder name; read it from the live master `.set` |
| Broker-suffix symbol mismatch (`ForceSymbol=XAUUSD` when the broker needs `XAUUSD+`) | That one child never trades; siblings on the same chart are unaffected | UBS does not fuzzy-match symbol names |
| Duplicate `EA_MagicNumber` across two children | Strategies start managing each other's trades | Every child needs a distinct magic number |
| Reading a schema-generation field that this build does not carry | A decision keyed on a missing field mis-detects | Fields are generation-dependent — test existence first |

## Per-set vs master overrides

`overrideAutoLoadLotsSettings=true` on the master chart replaces **each child's lotsize section**
with the master's own Inputs — a way to centralise risk sizing across a whole portfolio from one
place. Per the vendor manual, **the master wins**, with two documented exceptions:

- **`AdjustLotsizeToVariableValues`** overrides onto children **only when the master sets it to
  `false`.** If the master has it `true`, that is read as "defer to each child's own value" — so a
  master with `AdjustLotsizeToVariableValues=true` does *not* force it on for every child, even with
  `overrideAutoLoadLotsSettings=true`. This is inverted from the usual expectation.
- **`HistoricalMaxDD`** (max historical drawdown at 0.01 lots) is **never overridden** — each child
  keeps its own calibration value, because it is a per-strategy constant (see the SKILL's Risk
  section).

The parallel override toggles cover the other sections: `overrideNewsFilter`,
`overrideTimeSettings`, `overrideProp`.

## Symbol resolution — `ForceSymbol`

Per the vendor manual, a child's `ForceSymbol` wins when non-empty; empty ⇒ the chart's
symbol. You **must** set `ForceSymbol` when the AutoLoader runs multiple sets on different symbols,
and it must be the broker's **exact** symbol string, including any prefix or suffix. UBS does no
fuzzy or prefix matching — a mismatch is a silent no-trade for that one child only.

Because published sets carry plain, unsuffixed symbol names, the set library is broker-agnostic by
construction: adjusting `ForceSymbol` to the destination broker's exact spelling is a manual step
every deployer must perform per broker.

`OnlyLoaderForceSymbol` (older schema generations only) is not vendor-documented; by its name it
likely means "apply `ForceSymbol` only when loaded via the AutoLoader, not when run standalone" —
treat that as provisional and verify on your own installation.

## Magic-number uniqueness

Every child needs a **distinct `EA_MagicNumber`** so the EA can tell which open trades belong to
which strategy (per the vendor manual — otherwise different strategies start managing each other's
trades). Audit a new portfolio for duplicate magic numbers before deploying it.

## Schema generations — check field existence

Three `.set` schema generations ship under the one "V6.3" label, and AutoLoader-related fields come
and go between them. Some generations carry `UseCommonFolder`, `URL`, and `Lic_key`; newer
generations drop them (Common-folder behavior is already hardcoded, so their absence is expected,
not a defect). **Test whether a field exists in the specific `.set` file before reading or writing
it** — writing one of these keys into a generation that lacks it adds a harmless dead key, but a
check that *requires* reading a missing field will mis-detect.

## Deployment recipe

1. **Target folder:** `%APPDATA%\MetaQuotes\Terminal\Common\Files\<Sets_Folder>\` — always this
   path, portable or not (create it if missing).
2. **Copy** every child `.set` file for the portfolio into that folder, matching the exact
   (possibly nested) `Sets_Folder` path the master specifies — do not assume flat.
3. **Per-child preflight:** confirm each child has a unique `EA_MagicNumber`, a `ForceSymbol`
   matching this broker's exact symbol spelling (adjust suffixes per broker), a non-stale
   `DefaultValue` anchor (see the SKILL's DefaultValue section), and no timing input left at a stale
   default period.
4. **Master inputs:** set `UseAutoLoader=true` and `Sets_Folder=<the same name as step 1>`.
5. **Override policy:** choose `overrideAutoLoadLotsSettings` — `true` to force one lotsize policy
   across all children (remembering `AdjustLotsizeToVariableValues` and `HistoricalMaxDD` follow the
   exception rules above); `false` to let every child keep its own lotsize section.
6. **Legacy fields:** only if this build exposes them (older schema generations — check first) set
   `UseCommonFolder`/`URL`/`Lic_key`. On newer builds these fields do not exist — skip them.
7. **Launch/attach** the EA to one chart and read the Experts log / InfoPanel: it should enumerate
   every loaded strategy with its magic number and symbol.
8. **Confirm the count:** `Successfully loaded N set file(s) from folder <name>` — `N` must equal
   the number of children placed. Anything lower is a silent partial failure.

Deployment moves the sets and wires the master; it does not validate that a set *survives* on the
destination broker. Run that validation as a campaign through the `backtest-campaigns` skill and the
PortfolioManager MCP (analysis via the StrategyLens MCP), especially for scalper sets, which must be
validated with real-tick data on the target feed.
