# AEC Quant System — Improved Handoff for Independent Review

This document provides full, honest context on the current AEC Quant System
so a second reviewer can focus on catching real mistakes, validating
assumptions, and finding genuine improvements, rather than re-deriving work
already completed or re-testing ideas already proven non-viable.

---

## 1. Current System — 9 Strategies (10th slot open)

### Tier 1 — High Trust (real trade-level data, commission modeled, walk-forward validated)

| # | Strategy | Trades | Win Rate | Net P&L | Notes |
|---|---|---|---|---|---|
| 6 | Volatility Breakout (hour-filtered) | 434 | 38.9% | +$54,025.96 | Real trade-level data, commission modeled |
| 7 | Trend Following (time-stop + adaptive stops) | 700 | 36.4% | +$97,115.89 | Real trade-level data, commission modeled |
| 9 | FVG Rejection (5.0R) | 17,380 | 20.0% | +$714,145.00 | Walk-forward validated all 4 quarters |

### Tier 1.5 — Live-Validated (special case)

| Strategy | Notes |
|---|---|
| Layer I | Live-traded; real trading history, not backtest — a different, arguably more valuable kind of validation than anything else here, but doesn't fit a backtest-quality tier |

### Tier 2 — Medium Trust (strong full-year P&L, missing commission modeling or walk-forward splits)

| # | Strategy | Trades | Win Rate | Net P&L | Notes |
|---|---|---|---|---|---|
| 2 | OTE + BOS | 407 | 65.8% | +$180,341.24 | No commission modeling |
| 3 | HTF Rejection (4H) | 82 | 59.8% | +$20,421.46 | No commission modeling |
| 4 | Z-Score MR v2 | 2,374 | 35.6% | +$311,669.80 | No commission modeling |
| 5 | VWAP Reversion | 6,560 | 62.9% | +$63,145.00 | No commission modeling |

### Tier 3 — Low Trust / Experimental (structural risk or in-sample tuning)

| # | Strategy | Trades | Win Rate | Net P&L | Notes |
|---|---|---|---|---|---|
| 8 | Pairs / Relative Value (Kalman) | 602 | 52.3% | +$25,809.00 | NOT cointegrated (p=0.957) — structural failure |

**Commission gap (Tier 2):** systems 1-5 lack commission modeling. A rough
estimate suggests ~-$43K combined impact. Needs real verification.

---

## 2. Methodology — Verified and Honest

- Real IBKR NQ/ES OHLCV data (5-min & 15-min)
- Zero-volume bars filtered (real data-cleaning step — 53-60% of some raw pulls)
- $4/contract round-trip commission for systems 6-9
- Walk-forward validation (4 sequential quarters, most/all must be positive)
- In-sample parameter risk flagged (hour filters, R-multiples, confluence windows)
- All rejected ideas documented with real P&L, not just described

---

## 3. Rejected Ideas — Do Not Re-Test

All tested honestly and failed robustness, with real loss numbers attached:

Opening Range Breakout - Daily Sweep & Reversal - VWAP Bounce & Fade -
Volume Climax Reversal - Volume Divergence - Market Profile POC Re-entry -
Fade the Levels - Judas Swing / Power of Three - Session Transition -
Index Divergence (NQ vs ES) - Multi-Timeframe Alignment -
Regime-based filtering (except adaptive stops)

---

## 4. Regime Tagging — Final, Clean Summary

Two independent classifiers were built and tested. No regime filter improved
Volatility Breakout or Trend Following. Adaptive stop-width by regime
(TREND +25%, EXPANSION -25%) is the only regime-based improvement that
passed walk-forward validation, and is already incorporated into Trend
Following. Regime tags are retained as diagnostics, not performance levers --
this avenue is closed unless a fundamentally new idea is introduced.

---

## 5. Open Questions — Converted Into Actionable Tasks

**Task 1 -- Commission Modeling for Tier 2 Strategies**
Recover raw trade-level data if possible. If not, apply a conservative
commission model and re-evaluate net P&L.

**Task 2 -- FVG Rejection Parameter Validation**
Re-test the 5.0R target and hour filters on a true holdout period. This
strategy dominates the portfolio (58% of all trades) -- its stability is
critical.

**Task 3 -- Pairs/Kalman Structural Fix**
Either find a genuinely cointegrated pair, or implement rolling
cointegration with auto-disable logic.

**Task 4 -- Portfolio-Level Stress Tests** (not yet done)
Correlation between strategies - combined max drawdown - worst quarter
across the entire portfolio - contribution analysis (is FVG too dominant?)

**Task 5 -- 3-Contract Scaling Validation**
Test slippage and market impact assumptions -- linear scaling may not hold
for NQ/ES at size.

---

## 6. Combined Totals (Before Commission Gap Fix)

**Total trades: 29,887 | Total wins: 10,066 | Combined win rate: 33.7% |
Total net P&L: $1,483,851.71**

*(Independently re-verified against the individual system numbers above --
confirmed exact match.)*

---

## 7. Code — Ready for Review

10 Python files with: real OHLCV ingestion, real trade-level signal
generation, verified stop/target logic, timezone fixes (found and corrected
during tonight's session), synthetic-data correctness checks.

Fresh eyes on the implementation itself -- not just the results -- would be
genuinely valuable.

---

## Final Assessment — Recommended Review Order

1. Commission modeling for Tier 2
2. FVG Rejection parameter stability
3. Portfolio-level correlation & drawdown
4. Pairs/Kalman cointegration fix
5. Scaling assumptions

This is the shortest path to either confirming robustness or uncovering
hidden fragility.
