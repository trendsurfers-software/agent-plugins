---
name: ubs-ea
description: Use when working with the Ultimate Breakout System (UBS) MQL5 Expert Advisor by tradewithwim.com — reading, writing, or troubleshooting its .set files, choosing Risk and lot-sizing inputs, selecting entry engines, deploying via AutoLoader/OneChart, or backtesting it for any symbol and timeframe. Backtest execution and analysis route through this plugin's backtest-campaigns skill and bundled MCP servers.
---

# Ultimate Breakout System (UBS) EA

UBS is a closed-source commercial MT5 Expert Advisor sold by tradewithwim.com. It installs as
`MQL5\Experts\Market\Ultimate Breakout System.ex5` and is configured entirely through `.set`
files — there is no source to read, so a `.set` file plus its backtest report is the working
specification for a given strategy.

UBS is **symbol-agnostic**. It trades any instrument — metals, indices, crypto, and 5-digit FX —
not only gold. The gold-heavy product/family labels are marketing names for specific `.set`
bundles, not an engine restriction: the same two entry engines and one exit engine run on every
symbol. Select the instrument with `ForceSymbol` (or the tester symbol) and **derive the
per-symbol point value before converting any distance to money** (see Units below) — that
derivation is the only thing that changes between symbols.

## Engine model — one engine, two entry modes, one shared exit

UBS is **one engine with two selectable entry modes and one shared exit engine.** Almost all
strategy character lives in the exit block, not the entry.

- `Run_Strategy=1` — **Breakout of Support/Resistance.** A swing-pivot engine (the `ST1_*`
  inputs). Pending stop orders rest at a detected high/low level *before* the move; the order can
  expire unfilled (`ST1_Expiration_hours`). Main dials: `ST1_HL_strength_L/R`, `ST1_countback`,
  `ST1_MinDist_to_HL`, `ST1_UpDiff`/`ST1_DownDiff`.
- `Run_Strategy=2` — **Volatility Breakout.** Fires *after* a candle body-move exceeds
  `DevFactor × ATR`. Main dials: `DevFactor`, `AtrPeriod`, `VolCandles`, `minSize`.
- `0` is not a selectable entry mode — the EA's dropdown offers only the two above.

Both entry modes feed the **same exit logic** (per the vendor manual) — picking an engine changes
entries only. Every Trade Exit / Trailing SL / Trailing TP / Break-even / Grid block applies
regardless of which entry engine is active, and both engines' input blocks are always present in
every `.set` file; the inactive engine's inputs simply go unused at runtime. Change
`Exit_TrailSL_size` and you change what kind of EA the set behaves like — see Scalper vs swing
below.

Full input dictionary and enum decodes: `reference/parameters.md`.

## `.set` file format

`.set` files are **UTF-16LE**. In Python, `open(path, encoding='utf-16')`.

```
; saved on 2026.04.17 07:53:42
Name=value||start||step||stop||optimizeFlag     # numeric/bool — only field 1 (value) is live
Name=value                                      # string inputs, no || suffix
filters_=--------- trading filters ---------    # section-header pseudo-input (a title, not a setting)
MondayStart=00:00                               # trailing Mon–Sun schedule block
```

Rules that matter:

- **Only the first `||`-delimited field (the value) is live.** The `start||step||stop||flag`
  tail is optimizer scaffolding.
- **The `start||step||stop` range fields are optimizer leftovers, NOT validity bounds.** Live
  values routinely sit far outside their own declared range (for example `MaxSpread=500` with a
  declared max of 10). **Never "fix" a UBS value back into its declared range — you will break
  working sets.** Treat the range only as a weak hint about what was once swept.
- **String inputs have no `||` suffix.**
- **Section headers appear as pseudo-inputs** whose value is a `---...---` title string (e.g.
  `Vol_Entry=--- Volatility Breakout Entry ---`). They delimit the group that follows; they are
  not configurable parameters.
- A trailing **Mon–Sun schedule block** (`MondayStart`/`MondayEnd` … `SundayStart`/`SundayEnd`)
  carries the trading-hours window as `HH:MM` strings.

**Three schema generations ship under the one "V6.3" label.** Fields appear and vanish between
generations — some sets carry `UseCommonFolder`, `Lic_key`, `URL`, `PrintSetLoadingInfo`; an older
generation instead uses `autoload`, `OnlyLoaderForceSymbol`, and unprefixed `override*` keys.
**Always test whether a field exists before reading it. Never hardcode the input list.**

`scripts/parse_set.py` (bundled with this plugin) reads and diffs `.set` files — it handles the
BOM, the `||`-field split, and banner lines a naive parser would turn into a bogus empty-name
input.

## Risk is a MODE SELECTOR, not a dial

`Risk` chooses which sizing formula is live. It uses **sentinel values, not 0–4 ordinals**, so a
`Risk` number carries no ordering (`9999` is not "more risk than `123`"). Get this wrong and a
sizing edit is a silent no-op: **every input belonging to an inactive mode is inert regardless of
its value.**

| `Risk` | Mode | Input that drives size |
|---|---|---|
| `0` | **Manual_Lotsize** — fixed lot | `StartLots` |
| `9999` | Lots_Per_Balance | `LotPerBalance_step` → `lots = floor(balance / step) × 0.01` |
| `999` | Risk Per Trade (%) | `Manual_RiskPerTrade` |
| `5555` | Risk Per Trade in $ | `MaxRiskInDollar_input` |
| `123` | Use Max Risk Per Strategy | `MaxRiskPerStrategy_Value` + `HistoricalMaxDD` |

`Risk=0` (Manual_Lotsize) is the common shipped case: `StartLots` drives size and the lot is
fixed, rescaled only by Variable Values (see DefaultValue below). `Risk=123` and `Risk=9999` size
from live balance, so they **compound**; `Risk=0` does not. **Never carry a drawdown-percent figure
between modes** — a DD% from a compounding `Risk=123` run does not describe a fixed-lot `Risk=0`
set, or vice versa.

`MaxLots` is a hard cap applied after every mode. `CheckMargin` is the final gate before an order
is sent, independent of sizing mode.

### `Risk=123` — the Max-Risk-Per-Strategy calibration pair

This mode is a two-input calibration, and it is the one place a backtest statistic is a legitimate
*input*:

- `HistoricalMaxDD` = the strategy's historical max drawdown in account currency **at 0.01 lots**.
  You read it once from a backtest of that strategy and feed it back in. It is a *designed*
  calibration input, not junk metadata. It is live only under `Risk=123`; under any other mode it
  is inert.
- `MaxRiskPerStrategy_Value` = the percent of balance you are willing to expose to that known worst
  case.

```
lots = 0.01 × (MaxRiskPerStrategy_Value / 100 × balance) / HistoricalMaxDD     [then capped by MaxLots]
```

Read it as: *"risk `MaxRiskPerStrategy_Value`% of balance against a strategy whose worst historical
drawdown was `HistoricalMaxDD` per 0.01 lots."* Raising `MaxRiskPerStrategy_Value` or lowering
`HistoricalMaxDD` both scale lots up linearly, until `MaxLots` clamps.

## DefaultValue anchors the set to a price regime

The Variable Values block keeps one optimized set portable across time for instruments whose price
level trends over years (gold, crypto, indices). The vendor manual (see `reference/parameters.md`)
states the distance formula:

```
scaled distance = original × (currentPrice / DefaultValue)
```

applied to SL / TP / trailing / entry-distance inputs. Lots move the **opposite** way, so that
per-trade dollar risk is held constant (the manual's stated purpose — *"so the risk remains the
same over the years"*):

```
lots = StartLots × (DefaultValue / currentPrice)
```

The product of the two is constant, so **only per-trade dollar risk is held invariant across price
regimes** — P&L is not, because changing the stop distance changes which trades survive.

Consequences:

- A **stale anchor invalidates a set.** A gold set anchored at `DefaultValue=4100` run against gold
  near 2000 silently gets every distance × ~0.49 and every lot × ~2.05.
- **Two backtests whose sets carry different `DefaultValue`s are not comparable** — their distance
  and lot scales differ. Confirm both sets share the same anchor before comparing Sharpe/DD/PF.
- **Intuition trap:** a set run at a *lower* price level does not de-risk by cutting lots — the
  stop shrinks in dollars, so lots must *rise* to keep the same dollar risk.

`ATRDefault` overrides `DefaultValue` when non-zero; `ATRDefault=0` (the usual case) falls back to
the price-ratio method. Lot re-scaling only applies when `AdjustLotsizeToVariableValues` is enabled
**and** `Risk` is `Manual_Lotsize` or `Lots_Per_Balance` — it is silently inert with other modes
(per the vendor manual).

**Pre-flight anchor check before trusting or comparing any set:** read `ATRDefault` first (non-zero
governs); if `0`, compare `DefaultValue` against the instrument's actual price for the backtest
period; and confirm both sets share the same anchor before comparing two runs of the same strategy.

## Units — distances are raw MT5 points, not pips

The vendor manual labels every distance input "pips" regardless of instrument and states no units
doctrine. In practice the values are raw MT5 `Point()` units for whatever symbol is loaded.
**Before converting any distance input to money, check the symbol's digits and contract size on
the actual broker.** A wrong digits assumption makes every dollar figure wrong by a factor of ten.

Point value per lot for common symbols (check against your own account before relying on it):

| Symbol | Digits | Contract size | $ per point per lot |
|---|---|---|---|
| XAUUSD | 2 | 100 | $1.00 |
| XAGUSD | 3 | 1,000 | $1.00 |
| US30 | 2 | 1 | $0.01 |
| DE40 | 2 | 1 | $0.01 |
| ETHUSD | 2 | 1 | $0.01 |
| JP225 | 2 | 0.01 | $0.0001 (account-currency dependent) |
| EURUSD / 5-digit FX | 5 | 100,000 | $1.00 (standard MT5) |

- **Metals are $1/point/lot; indices and ETH are $0.01/point/lot — a 100× difference.** That is
  why index sets carry far larger raw point numbers than metals sets for the same money (an index
  `Exit_stop` in the thousands can be the same dollar risk as a gold `Exit_stop` in the hundreds).
- **Non-USD-denominated symbols** (JP225 in yen, DE40 in euro) fold the account-currency conversion
  into the per-point figure, so it is account-specific rather than a symbol constant — re-derive it
  against your own account.
- Worked: `Exit_stop=400` on 2-digit XAUUSD = a $4.00 price move = **$400 risk per lot**. The same
  `Exit_stop=1000` is $1,000/lot on XAUUSD but $10/lot on US30.

**For any symbol not in the table:** read digits and contract size from the broker's symbol spec,
or derive contract size from your own backtest deal table. Every MT5 deal satisfies

```
profit = (closePrice − openPrice) × volume × contract_size     (sign follows direction)
```

with `commission` and `swap` as separate fields. Pull the deal fields with the StrategyLens MCP
(`sl_get_trades`: `direction`, `volume`, `openPrice`, `closePrice`, `profit`, `commission`,
`swap`) and solve for `contract_size`. Until StrategyLens exposes derived instrument facts
directly, this is the path.

## Timeframe enum decode

Every "Timeframe" input (`ST1_Timeframe`, `Entry_Timing`, `Exit_Timing`, `VolTimeframe`,
`VolAtrTimeframe`, `ATR_Timeframe`, `GridTiming`, `confirmationCandleTimeframe*`, …) is a standard
MQL5 `ENUM_TIMEFRAMES` value:

| 0 | 1 | 5 | 15 | 30 | 16385 | 16386 | 16387 | 16388 | 16390 | 16392 | 16396 | 16408 | 32769 | 49153 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CURRENT | M1 | M5 | M15 | M30 | **H1** | H2 | H3 | **H4** | H6 | H8 | H12 | **D1** | W1 | MN1 |

**A `.set` filename often disagrees with its own `ForceSymbol` and timeframe inputs.** Read the
set, not the name — decode `ForceSymbol`, `ST1_Timeframe`/`Entry_Timing`, and `VolTimeframe` from
the file itself.

## Scalper vs swing — classify by ratio, never by name

Whether a set behaves as a scalper or a swing set is an **exit** decision, readable from the trail
and stop distances:

```
Exit_TrailSL_size / Exit_stop  ≤ 0.071
AND Exit_TrailSL_Start / Exit_stop ≤ 0.20      ⇒ SCALPER
```

- **Classify by this ratio, not by the folder or marketing name.** Files sitting in "scalper"
  folders can trail at half their stop (i.e. behave as swing sets), and vice versa.
- **Do not use `MaxTrades` to classify.** Scalper and swing sets both run high `MaxTrades` values,
  so it does not discriminate.
- The entry is essentially the same across both cohorts; the difference lives in the trail.

**Validate any scalper set with real-tick data on the target broker's feed**, never on
1-minute-OHLC. A scalper's edge is spread- and tick-sensitive: a report produced on a coarse tick
model is a screening hint at best, never a verdict. Route the backtest through the
`backtest-campaigns` skill and the PortfolioManager MCP; a scalper report on generated or
1-minute-OHLC ticks does not settle whether the set survives.

## Initial-sweep sizing policy

For a first broad sweep across many UBS sets/symbols — **before** any per-set risk calibration —
force `Risk=0` (Manual_Lotsize) with a fixed `StartLots` by asset class:

| Asset class | `StartLots` |
|---|---|
| Forex pairs | 0.01 |
| Metals | 0.1 |
| Commodities | 1 |
| Indices / crypto | start at 1, then validate against the broker's min lot / lot step / margin with a single 1-job smoke run before scaling the sweep |

Fixed manual lots make every report in the sweep directly comparable (no compounding, no
balance-coupled sizing). **If a set ships with a non-zero `Risk`, override BOTH `Risk=0` and
`StartLots`** — otherwise the lot input is inert (Risk-is-a-mode-selector, above). Risk-mode
calibration (`Risk=123`, etc.) comes only *after* a set survives in-sample and out-of-sample — the
balance-sizing dial is a cliff, not a slope (small changes can flip a survivable step to ruin with
no advance warning), so select it by drawdown tolerance, not by optimizing it. Sweep structure,
in-sample/out-of-sample splits, and the anti-overfitting protocol are owned by the
`backtest-campaigns` skill — follow it; do not restate it here.

## Backtesting rules

- **Force `UseAutoLoader=false` in tester sets.** In the Strategy Tester you run one set on one
  chart, not the multi-strategy AutoLoader path.
- **Set `Broker_GMT_OFFSET_Summer`/`_Winter` correctly for every backtest.** The Strategy Tester
  cannot perform the `AutoGMT` web lookup, so it falls back to those manual offsets — they matter
  in every tester run even when `AutoGMT=true`.
- **Verify the report↔set pairing against the report's own embedded `Inputs:` block, never by
  filename.**
- **You cannot infer "no commission modeled" from `Gross Profit − Gross Loss = Net Profit`.** That
  identity holds either way, because MT5 folds commission into per-deal profit. Read the Deals
  table's `Commission` column (via the StrategyLens MCP `commission` field) to see the real cost.
- **Route all analysis through the StrategyLens MCP** (see below). It is the analysis authority;
  do not hand-compute report statistics.

## Triage: reading an unknown UBS set in 60 seconds

1. `python scripts/parse_set.py <file>` (run from the installed plugin's root, where `scripts/`
   lives) — dump it (absent `Run_Strategy` ⇒ older schema generation).
2. `Run_Strategy` → which entry engine.
3. `ST1_Timeframe` / `Entry_Timing` / `VolTimeframe` → decode via the timeframe table; compare
   against the filename (they often disagree — trust the set).
4. `Risk` → which sizing mode is live. Everything else about sizing follows from this.
5. `DefaultValue` (+ `ATRDefault`, `AdjustLotsizeToVariableValues`) → which price regime the set is
   anchored to.
6. `Exit_TrailSL_size / Exit_stop` (and `Exit_TrailSL_Start / Exit_stop`) → scalper or swing.
7. `EA_MagicNumber` → family. `1000` is the unconfigured factory placeholder and tells you nothing.

## Common mistakes

| Mistake | Reality |
|---|---|
| "This value is outside its range, it's corrupt" | The `start\|\|step\|\|stop` fields are stale optimizer leftovers, not validity bounds. Leave out-of-range live values alone. |
| "`Exit_stop=400` is 400 pips" | Raw points. On 2-digit gold = $4.00 price = $400/lot. Check digits and contract size per symbol first. |
| "Turn `Risk` down to reduce risk" | `Risk` selects the sizing MODE, using sentinel values. Under one mode, another mode's inputs do nothing at all. |
| "`HistoricalMaxDD` is leftover backtest metadata" | It is a designed calibration input — max DD in account currency at 0.01 lots. Under `Risk=123` it sets lot size via the formula above; under any other mode it is inert. |
| "The folder says scalper" | Classify by the trail/stop ratio. Folder and marketing labels misclassify real files. |
| "This set has no commission modeled — Gross−Gross=Net" | Invalid test. MT5 folds commission into per-deal profit. Read the Deals `Commission` column. |
| "Backtest at gold 2000 validates my gold-4100 set" | `DefaultValue` rescales every distance. Different anchors = incomparable backtests. |
| "`AutoGMT=true` gets the real GMT offset in a backtest" | The tester cannot make the web request; it falls back to `Broker_GMT_OFFSET_Summer/Winter`, so those matter in every backtest. |
| "The filename tells me the symbol and timeframe" | Frequently wrong. Read `ForceSymbol` and the timeframe enums from the set. |

## References and related skills

| File | Covers |
|---|---|
| `reference/parameters.md` | Complete input dictionary by section, UI-label ↔ `.set`-key map, enum decodes, units warning |
| `reference/deployment.md` | AutoLoader / OneChart deployment, folder resolution, per-set vs master override semantics |
| `scripts/parse_set.py` | `.set` parser — dump and `--diff` (bundled with this plugin) |

This skill is the UBS-specific knowledge layer. Execution and analysis run through the product
surfaces, affirmatively: the **PortfolioManager MCP** is the execution surface (enqueue and run
backtests) and the **StrategyLens MCP** is the analysis surface (read reports, compute stats). If
PortfolioManager is not installed, not running, or any tool call returns `license_required`, tell
the user to get a license at https://trendsurfers.io/pricing/ before continuing.

- Read the **`backtest-campaigns`** skill for campaign folder structure, in-sample/out-of-sample
  methodology, and the anti-overfitting and sizing protocol — every UBS backtest belongs to a
  campaign; this skill does not restate that methodology.
- Use the **`set-generator`** skill to design new UBS parameter candidates: express them as
  `parameterOverrides` layered on a seed `.set` and submit through the PortfolioManager MCP, rather
  than hand-writing new `.set` files.
- Consult and update the **`ea-knowledge-base`** skill for what is already known about a given UBS
  set + symbol + timeframe before designing, and after every verdict.
