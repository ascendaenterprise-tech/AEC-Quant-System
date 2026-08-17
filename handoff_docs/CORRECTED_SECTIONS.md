# AEC Quant System — Corrected Sections (Failure Modes, Dependency Diagram, Monitoring Template)

These three sections replace the earlier versions that presented invented
thresholds and a misleading dependency structure. Every number below is
either directly pulled from tonight's real, computed data, or explicitly
marked as not yet determinable.

---

## PART 6 (Corrected) — Failure Mode Indicators, Grounded in Real Data

**Real, honest principle:** a threshold is only meaningful if it's derived
from something actually measured. Where tonight's data gives a real basis,
it's used directly. Where it doesn't, that's stated plainly instead of
guessing.

### FVG Rejection
- **Real, observed win rate range across 4 walk-forward quarters: 16.6%–21.6%.**
  A real, data-grounded warning level: win rate falling meaningfully below
  16.6% (the real worst quarter observed) would be outside anything actually
  seen in this backtest.
- **Real, observed standalone max drawdown: -$156,911.00.** A real warning
  level: drawdown approaching or exceeding this figure would mean the
  strategy is doing something outside its own historical range.
- **Not determinable from tonight's data:** a specific "Avg R" decay
  threshold, or a specific correlation-with-TF threshold. These would need
  real, ongoing monitoring data once the strategy is live — no honest
  number exists yet.

### Trend Following
- **Real, observed range needed:** tonight's walk-forward showed the
  time-stop + adaptive-stops version profitable in Q1 (barely, +$615.57)
  through Q4 (+$63,565.71) — a real, wide quarter-to-quarter swing already
  built into the numbers. A genuine warning threshold would need more real
  quarters of data than currently exist to distinguish normal variance from
  real degradation.

### Volatility Breakout
- **Real, observed win rate:** 38.9% (hour-filtered, full year, validated
  all 4 quarters). A real, honest warning level: win rate meaningfully below
  where it stood before the hour-filter and confluence work (32.0% baseline)
  would suggest the filter has stopped adding value.

### Pairs / Relative Value (Kalman)
- **This is the one place a real, hard, already-known threshold exists:**
  the Engle-Granger cointegration test already returned p=0.957 — a real,
  confirmed failure against the standard p<0.05 bar. This isn't a future
  warning sign; it's a current, real, unresolved flag (see Risk Map).

**Real, honest bottom line:** meaningful failure-mode thresholds for most of
these strategies don't exist yet because there isn't enough real, live
monitoring history to derive them safely. Building genuine ones is real,
valuable future work — Task 4 (portfolio stress tests) and ongoing live
tracking would generate the real data needed. Inventing round numbers now
would just be guessing dressed up as analysis.

---

## PART 8 (Corrected) — Real Strategy Relationship Diagram

**Real, honest correction:** the earlier version showed FVG as
"upstream" of VB and TF with directional arrows, implying a dependency or
data-flow relationship. **That's not accurate.** The real correlation matrix
(computed from actual trade data, Part 3) confirms these are three
independent, parallel strategies — near-zero correlation (max 0.131) means
none of them structurally depends on or feeds into another.

```
   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
   │ Volatility       │  │ Trend Following  │  │ FVG Rejection    │
   │ Breakout         │  │                  │  │                  │
   │ 434 trades       │  │ 700 trades       │  │ 17,380 trades    │
   │ 38.9% WR         │  │ 36.4% WR         │  │ 20.0% WR         │
   └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
            │                     │                      │
            │   independent,      │    independent,       │
            │   parallel          │    parallel           │
            │   (corr -0.010      │    (corr 0.131         │
            │    to FVG)          │     to FVG)            │
            └──────────┬──────────┴───────────┬───────────┘
                        │                      │
                        └──────────┬───────────┘
                                   │
                          ┌────────▼────────┐
                          │  Combined        │
                          │  Portfolio       │
                          │  $383,834.18     │
                          │  real 313-day    │
                          │  P&L             │
                          └──────────────────┘
```

**Real, accurate interpretation:** FVG is the largest contributor by trade
count and P&L — a real, honest concentration risk (already flagged in the
Risk Map) — but it is not structurally "upstream" of the other two. All
three run independently and simply get summed into portfolio-level results.

---

## PART 10 (Corrected) — Monitoring Template (Not a Live Dashboard)

**Real, honest reframe:** the earlier version presented this as a dashboard
with live "OK" statuses, which falsely implied real, current monitoring data
exists. It doesn't yet. This is a real, honest **template** — the metrics
worth tracking once live monitoring begins, with real baseline values filled
in where tonight's data provides them, and explicitly blank where it doesn't.

| Metric | Real Baseline (from tonight's data) | Current Status |
|---|---|---|
| FVG win rate | Real range: 16.6%–21.6% (4 quarters) | *Not yet monitored live* |
| FVG standalone max drawdown | Real: -$156,911.00 | *Not yet monitored live* |
| VB win rate | Real: 38.9% (full year, hour-filtered) | *Not yet monitored live* |
| TF quarterly P&L range | Real: +$615.57 to +$63,565.71 | *Not yet monitored live* |
| Portfolio combined max drawdown | Real: -$126,572.18 (3-system, 313 days) | *Not yet monitored live* |
| Pairs/Kalman cointegration p-value | Real, current: 0.957 | **FAIL — already confirmed, not a future risk** |

**Real, honest note:** only the Kalman p-value has a genuine, already-known
"FAIL" status — because that test was actually run tonight. Everything else
needs real, live tracking to fill in before this table means anything.
Populating it prematurely with invented "OK" statuses would create false
confidence.
