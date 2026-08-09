---
description: Scaffold one campaign folder with campaign.md from template
argument-hint: <EA> <SYMBOL-TF> <slug>
---
1. Require the backtest-campaigns skill (invoke it if not loaded).
2. Create `<SL_REPORTS_ROOT>/<EA>/<SYMBOL-TF>/<YYYY-MM-DD>-<slug>/` with subdir `sets/`. Phase folders (`is/ oos/ xbroker/ xrange/ xmodel/`) are created on demand when the first report of that phase is collected — empty phases are absent, not empty directories (see the `backtest-campaigns` skill).
3. Write `campaign.md` from the template in the backtest-campaigns skill (question, EA, symbol+TF, seed sets, IS window, frozen OOS window + registry entry, pass bars, max-candidates cap, expected job count).
4. Remind: freeze seed .set copies into `sets/` before enqueuing; record every enqueue in `manifest.jsonl` via `scripts/campaign_manifest.py`.
