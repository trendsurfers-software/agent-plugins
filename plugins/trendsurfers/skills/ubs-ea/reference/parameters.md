# UBS parameter reference

The complete UBS input dictionary for `.set` files, by the file's own section order. Sources are
the EA's own Strategy Tester Inputs tab (authoritative for **UI label ↔ `.set` key** and enum
names) and the vendor manual (authoritative for documented behavior and defaults). Where the two
disagree on a label, the Inputs tab wins for naming; where the manual documents a behavior, cite
"see vendor manual" rather than restating a page number.

Section headers appear in real `.set` files as pseudo-inputs whose value is a `---...---` title
string (e.g. `Vol_Entry=--- Volatility Breakout Entry ---`) — they delimit the group that follows
and are not configurable parameters. They are omitted from the tables below.

Legend for the **Notes** column: *not vendor-documented* = the vendor manual is silent on this
input; treat the meaning as provisional and verify on your own installation before relying on it.

---

## Units warning — read before converting any distance to money

The vendor manual labels every distance input "pips" regardless of instrument and states no units
doctrine. In practice each distance input (`Exit_stop`, `Exit_limit`, `ST1_MinDist_to_HL`,
`GridStart`, …) is denominated in the broker's raw MT5 `SYMBOL_POINT` units for whatever symbol is
loaded — **not** a normalized "pip". Raw magnitudes therefore differ by one to two orders of
magnitude between a 2-digit gold quote, a 5-digit FX quote, and a whole-number index or crypto
quote, exactly as a raw point count would.

**Rule: before converting any input to money, check the symbol's digits and contract size on the
actual broker.** Never assume a fixed pip-to-point ratio — it differs per symbol's digit count.

**Worked example — XAUUSD, 2-digit gold quote, 100-oz contract:**

| Step | Value |
|---|---|
| Quote digits | 2 (e.g. `2600.12`) |
| 1 point (`SYMBOL_POINT`) | $0.01 of price |
| Contract size | 100 oz |
| $ per point per 1.00 lot | $0.01 × 100 = **$1.00** |
| `Exit_stop=400` | 400 points = $4.00 price move |
| Risk per 1.00 lot at `Exit_stop=400` | $4.00 × 100 = **$400** |

See the SKILL's Units section for the common-symbol point-value table and the deal-table derivation
(`profit = (closePrice − openPrice) × volume × contract_size`, via the StrategyLens MCP) for
symbols not in it.

---

## Parameter dictionary

Columns: **`.set` key** | **UI label** | **What it does** | **Units** | **Default** | **Notes**.

### Info Panel settings

| `.set` key | UI label | What it does | Units | Default | Notes |
|---|---|---|---|---|---|
| `ShowInfoPanel` | ShowInfoPanel | Show/hide the on-chart info panel (status, stats, open P/L, trade count) | bool | `true` | |
| `UpdateInfoTesting` | update infopanel during testing | Refresh the panel live during Strategy Tester runs | bool | `false` | |
| `InfoPanelSizeAdjust` | Adjustment for Infopanel size | Scales the panel; `1` = default size | ratio | `1` | |
| `SetFontSize` | Force Font Size (0=disabled) | Font-size override for the panel | int | `0` | Not vendor-documented |

### AutoLoad set files (OneChartSetup)

One EA instance on one chart can run many strategies at once, each its own `.set` file with its own
magic number, symbol, and parameters. Deployment detail: `reference/deployment.md`.

| `.set` key | UI label | What it does | Units | Default | Notes |
|---|---|---|---|---|---|
| `UseAutoLoader` | UseAutoLoader | Run all `.set` files from the AutoLoad folder off one chart | bool | `false` | Force `false` in tester sets |
| `Sets_Folder` | Folder with .set files | Sub-folder holding the sets to autoload | string | `Sets` | The UI label's parenthetical path is stale — see `reference/deployment.md` |
| `overrideAutoLoadLotsSettings` | Override Autoload Lotsize Settings | Replace each child's lotsize section with the master chart's inputs | bool | `false` | Two inputs cannot be overridden — see `reference/deployment.md` |
| `overrideNewsFilter` | Override Autoload Newsfilter settings | Override the news-filter section across all children | bool | `false` | |
| `overrideTimeSettings` | Override Autoload Trading Time settings | Override trading-hours across all children | bool | `false` | |
| `overrideProp` | Override Autoload Prop Firm Settings | Override the prop-firm section across all children | bool | `false` | |
| `ForcePendingMax` | Force Max Pending Order Per strategy | Caps pending orders per strategy on the older AutoLoader path | int | — | Not vendor-documented; older schema generation only |
| `UseCommonFolder` | — | Resolve `Sets_Folder` under the machine-wide Common\Files folder | bool | — | Not vendor-documented as a named input; older schema generation only |
| `PrintSetLoadingInfo` | — | Debug log toggle for set loading | bool | — | Not vendor-documented; later addition, absent from older sets |

### Custom optimization settings — section `CustomOptimization`

Active only when the Strategy Tester's Optimization Criteria is "custom max". The EA's Inputs tab
shows **four** rows in file order (the vendor manual's "3 criteria" text predates the fourth):

| `.set` key | UI label | What it does | Units | Default | Notes |
|---|---|---|---|---|---|
| `EP` | expected payoff | Minimum expected payoff (avg profit/trade); results below are discarded | account ccy | `0` | `0` = not used as an exclusion filter, but still contributes to the ranking score |
| `RF` | recovery factor | Minimum recovery factor = **net profit ÷ max drawdown = ret/DD**; results below are rejected | ratio | `0` | Carries the most weight in the custom-max ranking (see vendor manual) |
| `TR` | Minimum number of trades | Minimum trade count; fewer = invalid result | count | `0` | |
| `MTR` | Maximum number of trades | Upper bound on trade count; passes with more trades are discarded (mirror of `TR`) | count | `0` | `0` = disabled |

### Spread filter — section `spreadfilter_`

| `.set` key | UI label | What it does | Units | Default | Notes |
|---|---|---|---|---|---|
| `SpreadFilter` | SpreadFilter | Check current spread vs `MaxSpread` before trading | bool | `false` | |
| `MaxSpread` | MaxSpread | Max allowed spread for trading | points (see Units warning) | `3.0` | `999999` is the disabled sentinel |
| `DistForSpreadFilter` | DistForSpreadFilter | Distance factor: pending orders deleted only if price is closer than this | points | `2` | |

### Other settings — section `otherfilters_`

| `.set` key | UI label | What it does | Units | Default | Notes |
|---|---|---|---|---|---|
| `ForceSymbol` | ForceSymbol | Exact broker symbol for this set, for AutoLoader multi-symbol use | string | none | Must match the broker's exact symbol string incl. prefix/suffix; no fuzzy matching |
| `OnlyLoaderForceSymbol` | Disable ForceSymbol during single setup | Apply `ForceSymbol` only when loaded via AutoLoader | bool | — | Not vendor-documented; older schema generation |
| `setSL_TP_After_Entry` | Set SL/TP after entry | Set SL/TP after the order fills rather than at placement | bool | `false` | For brokers that disallow SL/TP on a pending order |
| `Virtual_expiration` | use virtual expiration | Manage pending-order expiration inside the EA rather than at the broker | bool | `true` | For brokers that disallow pending-order expiration dates |
| `PrintLogs` | PrintLogs | Verbose logging to the Experts/Journal tab | bool | — | Not vendor-documented |

### Virtual stop-loss settings

| `.set` key | UI label | What it does | Units | Default | Notes |
|---|---|---|---|---|---|
| `useVirtualStops` | Use Virtual SL | Enum — see Enum decode | enum | — | |
| `VirtualSL_Safety_Hardstop_dist` | hard SL distance when using virtual SL | Hard-SL safety-net distance beyond the virtual stop | points | `0` | |
| `SetVSL_to_hardSL_sec_delay` | Move hard SL to virtual SL after X seconds | Delay before the hard SL is moved to the virtual SL level | seconds | `0` | A large value means the broker holds no hard stop on a typical short-lived trade — the position lives on the EA-internal virtual stop, unprotected across a terminal/VPS outage |
| `Run_Strategy` | Run_Strategy | Enum — selects the entry engine; see Enum decode | enum | Breakout Support/Resistance | |
| `AllowBuyTrades` / `AllowSellTrades` | AllowBuyTrades / AllowSellTrades | Enable/disable buy / sell trades | bool | `true` | |

### Variable Values settings — section `Variable_Values_`

Keeps one optimized set portable across time for instruments whose price level trends over years.
Scaling behavior and the pre-flight anchor check are in the SKILL's DefaultValue section.

| `.set` key | UI label | What it does | Units | Default | Notes |
|---|---|---|---|---|---|
| `ATRDefault` | Default ATR value | If `>0`, scales all entry/exit distances relative to actual ATR | points | `0` | `>0` **overrides** `DefaultValue`; `0` falls back to the price-ratio method |
| `ATR_Period` | ATR Period | Candles used for this ATR calc | candles | `30` | Distinct key from the Volatility engine's `AtrPeriod` |
| `ATR_Timeframe` | ATR Timeframe | Timeframe for the ATR calc | enum TF | `PERIOD_D1` | |
| `DefaultValue` | default price for calculation | Reference price the distances scale against; used only when `ATRDefault=0` | price | `0` | `0` = disabled |

### Volatility Breakout entry (`Run_Strategy=2`) — section `Vol_Entry`

Both engines' input blocks are always present; the inactive engine's inputs go unused at runtime.

| `.set` key | UI label | What it does | Units | Default | Notes |
|---|---|---|---|---|---|
| `VolTimeframe` | Timeframe to monitor | TF of the candle(s) whose body-move is compared to ATR | enum TF | current | |
| `VolCandles` | number of Candles to Monitor | Number of candles over which the move is computed | candles | `1` | |
| `minSize` | Minimum Candle Size (pips) | Minimum absolute size for a move to qualify | points | `0` | UI labels this "pips"; its scale is not separately vendor-documented |
| `AtrPeriod` | ATR Period | Candles for this engine's own ATR | candles | `21` | Distinct key from Variable Values' `ATR_Period` |
| `VolAtrTimeframe` | ATR Timeframe | TF for this ATR | enum TF | current | |
| `DevFactor` | Deviation factor (candle size compared to ATR) | Move must exceed this many × ATR to trigger | multiplier | `2.4` | e.g. `2.4` = body-move must be 2.4× the ATR value |
| `VolMaxTrades` | Max number of open trades | Max concurrent trades in the trade direction | count | `1` | |

**Engine `2` rule:** at each `VolTimeframe` bar close it signals when the signed candle body-span
`Close[i] − Open[i-k]` (for any `k < VolCandles`) is at least `DevFactor × ATR(AtrPeriod,
VolAtrTimeframe)` and at least `minSize`; direction follows the sign; entry is on the next bar. The
comparison is a signed body-span, not the high-low range.

### Breakout Support/Resistance entry (`Run_Strategy=1`) — section `ST1_Entry_`

| `.set` key | UI label | What it does | Units | Default | Notes |
|---|---|---|---|---|---|
| `ST1_Timeframe` | Timeframe to use | TF for detecting recent highs/lows | enum TF | `PERIOD_CURRENT` | Do not leave at `PERIOD_CURRENT` once multiple sets share one chart |
| `Entry_Timing` | Entry Timing (when to check for new signals) | TF for checking new entry signals | enum TF | `PERIOD_H1` | |
| `ST1_HL_strength_L` | number of inferior candles to the LEFT of High/Low | Left-side pivot strength | candles | `2` | |
| `ST1_HL_strength_R` | number of inferior candles to the RIGHT of High/Low | Right-side pivot strength | candles | `6` | Manual's printed default can differ from the shipped build — trust a real `.set` |
| `ST1_countback` | max candles in history to look at | Look-back window for H/L identification | candles | `50` | |
| `ST1_MinDist_to_HL` | minimum distance away from High/Low | Min distance from current price to the H/L for a valid entry | points | `13` | See Units warning |
| `ST1_MinDist_to_HL_percentage` | minimum distance away in percentage | Same, as % of the H/L level | % | `0` | `0` = use absolute distance |
| `ST1_UpDiff` | Extra pips above High for entry | Offset added above the high for a buy entry (negative = inside the level) | points | `2` | |
| `ST1_DownDiff` | Extra pips below Low for entry | Offset below the low for a sell entry | points | `3` | |
| `ST1_MaxPendingOrders` | Maximum number of pending orders | Max simultaneous pending orders | count | `1` | |
| `MaxTrades` | max number of open trades | Max simultaneous open trades | count | `1` | Distinct key from `VolMaxTrades`; not a scalper/swing discriminator |
| `MinDist_orders` | Minimum distance between orders | Min distance between consecutive pending orders | points | `1` | |
| `ST1_Expiration_hours` | expiration time (in hours) for pending orders | Pending-order expiration | hours | `155` | `0` = no expiration |
| `EA_MagicNumber` | Magicnumber | Unique magic number for trade identification | int | `1000` | Must be unique per strategy for AutoLoader; `1000` is the factory placeholder |
| `EA_Comment` | Comment for trades | Trade comment | string | `Ultimate Breakout System` | |

### Trade exit settings — section `Trade_mg_`

| `.set` key | UI label | What it does | Units | Default | Notes |
|---|---|---|---|---|---|
| `Exit_Timing` | Period to check/modify SL/TP | TF for checking/modifying SL/TP | enum TF | `PERIOD_M1` | |
| `UseEveryTick` | check every tick | Check exit conditions every tick rather than per `Exit_Timing` period | bool | `true` | |
| `Exit_stop` | initial stoploss distance | Initial SL distance | points (see Units) | `175` | Scaled by Variable Values when enabled |
| `Exit_limit` | initial takeprofit distance | Initial TP distance | points (see Units) | `120` | Scaled by Variable Values when enabled |

### Trailing SL / TP / break-even

| `.set` key | UI label | What it does | Units | Default | Notes |
|---|---|---|---|---|---|
| `Exit_TrailSL_size` | Trail SL distance | Trailing-SL distance | points | `100` | Trail/stop ratio drives scalper-vs-swing classification |
| `Exit_TrailSL_Start` | Trail SL start distance | Distance at which the trailing SL activates | points | `160` | |
| `Exit_TrailSL_Stop` | Trail SL stop distance | Distance at which the trailing SL stops (a cap) | points | `100000` | Default is effectively "no cap" |
| `Exit_TrailSL_step` | Trail SL step size | Step by which the trailing SL advances | points | `0.4` | |
| `Exit_TrailTP_size` | Trail TP distance | Trailing-TP distance | points | `0` | `0` = disabled |
| `Exit_TrailTP_Start` | Trail TP start distance | Distance at which trailing TP begins | points | `0` | |
| `Exit_BE_start` | Breakeven start distance | Distance at which SL moves to break-even | points | `115` | |
| `Exit_BE_extra_pips` | Breakeven extra distance | Extra distance beyond break-even | points | `115` | |

### HIGH/LOW trailing SL — section `HL_settings_`

| `.set` key | UI label | What it does | Units | Default | Notes |
|---|---|---|---|---|---|
| `Exit_HL_UseBE` | Use only until break-even | HL trailing SL only used until break-even | bool | `false` | |
| `Exit_HL_trailingSL_timeframe` | Exit_HL_trailingSL_timeframe | TF for the H/L used by the trailing stop | enum TF | `PERIOD_CURRENT` | |
| `Exit_HL_countback` | number of candles to use | Look-back for H/L calc | candles | `0` | `0` disables the whole HL-trailing-SL function |
| `Exit_HL_trailingSL_candles_LEFT` | number of inferior candles to the LEFT of High/Low | Left-side strength | candles | `0` | |
| `Exit_HL_trailingSL_candles_RIGHT` | number of inferior candles to the RIGHT of High/Low | Right-side strength | candles | `0` | |
| `Exit_HL_TrailingSL_MinDist` | minimum distance to current price | Min distance from price to the trailing stop | points | `0` | |
| `Exit_HL_Minimum_Dist_For_Change` | minimum distance to last SL | Min change required to update the trailing stop | points | `0` | |
| `Exit_HL_trailingSL_extra_distance` | extra pips distance from HIGH/LOW | Extra distance beyond the H/L level | points | `0` | |

### Recovery trailing SL by time — section `TimeTL_`

| `.set` key | UI label | What it does | Units | Default | Notes |
|---|---|---|---|---|---|
| `Exit_TrailSL_after_X_Minutes` | Trail SL start after X minutes | Time after which this separate trailing SL activates | minutes | `0` | `0` disables |
| `Exit_TrailSL_after_X_Minutes_size` | Trail SL Distance | Trailing-SL distance for the time-based trail | points | `0` | |

### MagicTrail SL — section `MagicTrail_`

| `.set` key | UI label | What it does | Units | Default | Notes |
|---|---|---|---|---|---|
| `Exit_MagicTrail_Mode` | MagicTrail mode | Enum — see Enum decode | enum | off | Needs every-tick real-tick data to show its effect |
| `Exit_MagicTrail_start` | Start of Magictrail (in pips) | Starting distance for MagicTrail activation | points | `0.1` | |
| `Exit_MagicTrail_delay` | number of ticks before modifications | Ticks to wait before modifying the stop | ticks | `1` | |
| `Exit_MagicTrail_size` | pip movement of magictrail | Increment the stop moves by | points | `0.1` | |
| `Exit_MagicTrail_BE_extra_pips` | extra pips for breakeven stop | Extra distance beyond break-even (BE mode) | points | `1` | |
| `Exit_MagicTrail_Adjust_after_X_Minutes` | minutes of time delayed magictrail | Delay for a time-adjusted MagicTrail stop | minutes | `0` | `0` disables |
| `Exit_MagicTrail_Adjust_after_X_Minutes_start` | start distance of time delayed magictrail | Starting distance for the time-adjusted stop | points | `0` | |

### Grid settings — section `GridSettings`

| `.set` key | UI label | What it does | Units | Default | Notes |
|---|---|---|---|---|---|
| `EnableGrid` | EnableGrid | Enable the grid system to follow up on losing trades | bool | `false` | Vendor manual warns grid trading is much riskier |
| `GridStart` | Grid start distance in pips | Distance from the original trade where the grid starts | points | `50` | |
| `GridStep` | Grid step distance in pips | Distance between consecutive grid trades | points | `20` | |
| `GridTiming` | Grid check timeframe | TF that times grid start/next/exit checks | enum TF | `M15` | |
| `GridTakeProfitPips` | Total pips for TP | Grid closes when total pips exceed this | points | `10` | |
| `GridTakeProfitUSD` | Total profit for TP (use 0.X for % of balance) | Grid closes when total profit exceeds this | ccy, or fraction of balance if `0`–`1` | `50` | A value `<1` is read as a fraction of balance |
| `GridLossUSD` | Max loss for SL (use 0.X for % of balance) | Grid closes when total open loss exceeds this | ccy (**negative required**), or fraction if between `0` and `-1` | `0` | Must be entered as a negative number, else the grid-loss stop is silently broken |
| `StopTradingAfterGridLoss` | Stop trading at grid loss | Stop the EA entirely after a grid-loss close | bool | `false` | |
| `GridMultiplier` | GridMultiplier | Multiplies each new grid trade's lotsize vs the previous | multiplier | `1` | `>1` is martingale sizing |

### Prop firm settings — section `PropFirmSettings`

| `.set` key | UI label | What it does | Units | Default | Notes |
|---|---|---|---|---|---|
| `CloseAtMinEquity` | Close all trades/stop trading at min equity | Close all & stop trading if equity falls below this | ccy | `0` | `0` = disabled |
| `CloseAtMaxEquity` | Close all trades/stop trading at max equity | Close all & stop trading if equity exceeds this | ccy | `0` | `0` = disabled |
| `PropFirmMaxDailyDD` | Max Daily Drawdown | Close all & stop for the day if daily equity DD exceeds this | ccy | `0` | `0` = disabled; counts all losses that day plus open equity DD |
| `RandomizationValue` | Max Randomization_pips for entry and exit | Random per-trade offset to entry/exit (max = this) | points | `0` | Purpose: avoid copy-trading violations when several users run the same strategy |

### LotSize settings — section `LotSizeSettings_`

Decision order: `ManualBalance` (if nonzero) substitutes for real balance → `UseEquity` picks
equity vs balance → `Risk` mode selects the sizing formula → `MaxLots` clamp → `CheckMargin` gate
before order send. See the SKILL's Risk section for the sentinel-value mode table and formulas.

| `.set` key | UI label | What it does | Units | Default | Notes |
|---|---|---|---|---|---|
| `ManualBalance` | Force Fixed Manual Balance | Use this value as "balance" for all sizing, overriding the real account balance | ccy | `0` | `0` = use real account balance. Whether it replaces or caps, and its interaction with `UseEquity`, is not fully vendor-documented |
| `LotsAdjustMinChangePercent` | Adjust lotsize if balance changes X percent | Hysteresis: adjust lot size only once balance changes by this % | % | `5` | |
| `AdjustLotsizeToVariableValues` | Adjust lotsize to Variable Values | Re-scale lot size via Variable Values so risk stays constant as price level grows | bool | `false` | Only works with `Risk=Manual_Lotsize` or `Lots_Per_Balance`; silently inert otherwise |
| `Risk` | Risk | Position-sizing mode (sentinel values — see SKILL Risk section) | enum | Manual_Lotsize | Not 0–4 ordinals; a mode's non-driving inputs are inert |
| `StartLots` | manual lotsize | Fixed lot size, used when `Risk=Manual_Lotsize` | lots | `0.01` | Initial-sweep values: see the SKILL's Initial-sweep sizing policy. |
| `Manual_RiskPerTrade` | Max Risk Per Trade (%) | Max risk % per trade, used when `Risk=Risk Per Trade (%)` | % | `0` | |
| `MaxRiskInDollar_input` | Max Risk per Trade in $ | Max risk in currency per trade, used when `Risk=Risk Per Trade in $` | ccy | `0` | |
| `LotPerBalance_step` | LotsizeStep | Balance step per 0.01 lot, used when `Risk=Lots_Per_Balance` | ccy | `500` | e.g. step 500 → 0.01 lots per $500 balance |
| `MaxRiskPerStrategy_Value` | MaxRiskPerStrategy_Value | Max risk % for the strategy against its historical DD | % | `2` | Used when `Risk=Use Max Risk Per Strategy`; pairs with `HistoricalMaxDD` |
| `HistoricalMaxDD` | max historical drawdown (in $) at 0.01 lots | The strategy's historical max DD in account currency at 0.01 lots | ccy | per strategy | Live only under `Risk=123`; inert otherwise. Never overridden by AutoLoader |
| `MaxLots` | maximum lotsize per trade | Hard cap on lot size after all sizing modes | lots | `99` | |
| `UseEquity` | Use Equity Instead of Balance | Use equity instead of balance for sizing | bool | `false` | |
| `OnlyUp` | OnlyUp | Lot size only increases with balance/equity growth, never decreases | bool | `true` | Does not work with Risk-Per-Trade modes or with Variable Values enabled |
| `ResetHighestBalance` | Reset Highest Balance for OnlyUp | Reset the saved max-balance global used by `OnlyUp` | bool | `false` | Useful after a large withdrawal |
| `CheckMargin` | CheckMargin | Check free margin before placing trades | bool | `true` | Final gate, independent of sizing mode |

### GMT settings — section `GMT_Settings_`

| `.set` key | UI label | What it does | Units | Default | Notes |
|---|---|---|---|---|---|
| `Broker_GMT_OFFSET_Summer` | Broker_GMT_OFFSET_Summer | Broker GMT offset during summer/DST | hours | `3` | Used by the tester when `AutoGMT` cannot reach its web source |
| `Broker_GMT_OFFSET_Winter` | Broker_GMT_OFFSET_Winter | Broker GMT offset during winter/non-DST | hours | `2` | Same |
| `AutoGMT` | AutoGMT | Auto-detect the GMT offset from an external source; else use the manual offsets | bool | `true` | The external source must be in MT5's Allowed URLs; the Strategy Tester cannot reach it, so the manual offsets govern in backtests |

### News filters — NFP / Interest Rate / CPI

| `.set` key | UI label | What it does | Units | Default | Notes |
|---|---|---|---|---|---|
| `EnableNFP_Filter` | EnableNFP_Filter | Enable the NFP news filter | bool | `false` | |
| `NFP_CloseOpenTrades` | NFP_CloseOpenTrades | Close open trades during the NFP window | bool | `true` | |
| `NFP_ClosePendingOrders` | NFP_ClosePendingOrders | Delete pending orders during the NFP window | bool | `true` | |
| `NFP_MinutesBefore` | NFP_MinutesBefore | Minutes before the event the filter starts | minutes | `50` | |
| `NFP_MinutesAfter` | NFP_MinutesAfter | Minutes after the event the filter ends | minutes | `30` | |
| `EnableIR_Filter` … `IR_MinutesAfter` | (same shape) | Interest-rate news filter | — | IR defaults 60 before / 120 after | Same field shape as NFP |
| `EnableCPI_Filter` … `CPI_MinutesAfter` | (same shape) | CPI news filter | — | CPI defaults 60 before / 120 after | Same field shape as NFP |
| `UseMQL5Calendar` | — | Pull NFP/IR/CPI event times from MT5's built-in Economic Calendar | bool | — | Not vendor-documented; the built-in calendar is unreliable inside the Strategy Tester |
| `MQL5_CalendarDays` | number of days to search forward in MQL5 Calendar | Look-ahead window for calendar queries | days | — | Not vendor-documented; recent addition |

### Fake Breakout Filter (filters A–E)

Five same-shaped filters, each checking for a candle closing back below entry (buy) or above entry
(sell) on its own timeframe. How multiple enabled filters combine (AND vs OR) is not
vendor-documented.

| `.set` key | UI label | What it does | Units | Default | Notes |
|---|---|---|---|---|---|
| `confirmationCandleTimeframeA`–`E` | Filter_A Timeframe … Filter_E Timeframe | TF of each fake-breakout filter | enum TF | A=`M1`, B=`M5`, C=`M15`, D=`M30`, E=`H1` | |
| `UseConfirmationCandleA`–`E` | Enable Filter_A … Enable Filter_E | Enable each filter | bool | `false` | |

### Trading hours — section `timefilter_`

| `.set` key | UI label | What it does | Units | Default | Notes |
|---|---|---|---|---|---|
| `UseTradingTimeZones` | UseTradingTimeZones | Enable trading-time restrictions | bool | `false` | |
| `KillPending` | KillPending | Delete pending orders when non-trading hours begin | bool | `true` | |
| `KillOpen` | KillOpen | Close open trades when non-trading hours begin | bool | `true` | |
| `Time_Source` | Time_Source | Enum — see Enum decode | enum | Broker | |
| `MondayStart` … `SundayStart` | Monday Start Time … Sunday Start Time | Daily trading start time, one per weekday | `HH:MM` | `00:00` | |
| `MondayEnd` … `SundayEnd` | Monday End Time … Sunday End Time | Daily trading end time, one per weekday | `HH:MM` | `23:59` | |

### Display-only / non-functional inputs

| `.set` key | What it is |
|---|---|
| `LICURL`, `LICURLB` | Not functional parameters — string inputs whose value is human-readable instruction text, used to display a static message in the MT5 Inputs dialog |
| `BacktestSpeed` / `BacktestSpeed_string` | Tester-only visual playback speed; not a trading parameter. Not vendor-documented; absent from most sets |

---

## Enum decode

For a middle enum value the vendor does not document, verify it on your own installation (e.g. by
saving one tester profile per dropdown entry and diffing) before relying on it.

### `Run_Strategy` — entry engine

| Value | Meaning |
|---|---|
| `1` | Breakout of Support/Resistance (the `ST1_*` swing-pivot engine) |
| `2` | Volatility Breakout (the ATR × `DevFactor` engine) |
| `0` | Not a selectable dropdown entry — the EA offers only the two above |

Both engines share identical exit logic (see vendor manual) — the switch changes entries only.

### `useVirtualStops` (Use Virtual SL)

| Value | Meaning |
|---|---|
| `0` | OFF |
| `1`, `2` | Not vendor-documented (endpoints only are named) — verify on your own installation |
| `3` | ALL EXCEPT BE |

### `Exit_MagicTrail_Mode` (MagicTrail mode)

| Value | Meaning |
|---|---|
| `0` | OFF |
| `1` | Not vendor-documented — verify on your own installation |
| `2` | Breakeven |

### `Time_Source`

| Value | Meaning |
|---|---|
| `0` | GMT-0 |
| `1` | Not vendor-documented — verify on your own installation |
| `2` | Broker time |

**Note on the `.set` "default" field:** for `Time_Source` the live value is commonly `2` (Broker),
while the file's own 2nd `||`-field (the optimizer's baseline) reads `0`. That 2nd field is not the
compiled EA default — trust the value field (field 1) and the vendor manual's stated default, not
the 2nd field.

### `Entry_Timing` / `Exit_Timing` and every other "Timeframe" input

These are plain `ENUM_TIMEFRAMES` inputs sharing the standard MQL5 integer encoding:

| Int | TF | Int | TF | Int | TF |
|---|---|---|---|---|---|
| 0 | PERIOD_CURRENT | 30 | PERIOD_M30 | 16392 | PERIOD_H8 |
| 1 | PERIOD_M1 | 16385 | PERIOD_H1 | 16396 | PERIOD_H12 |
| 5 | PERIOD_M5 | 16386 | PERIOD_H2 | 16408 | PERIOD_D1 |
| 15 | PERIOD_M15 | 16387 | PERIOD_H3 | 32769 | PERIOD_W1 |
|  |  | 16388 | PERIOD_H4 | 49153 | PERIOD_MN1 |
|  |  | 16390 | PERIOD_H6 |  |  |

`Entry_Timing` default `PERIOD_H1` (`16385`); `Exit_Timing` default `PERIOD_M1` (`1`).

### `Risk`

Sentinel values, not ordinals: `0`=Manual_Lotsize, `9999`=Lots_Per_Balance, `999`=Risk Per Trade
(%), `5555`=Risk Per Trade in $, `123`=Use Max Risk Per Strategy. Full table, driving inputs, and
the `Risk=123` formula are in the SKILL's Risk section. Behavior of the `999` and `5555` modes
beyond their driving inputs is not independently confirmed here — verify on your own installation
before relying on those two.
