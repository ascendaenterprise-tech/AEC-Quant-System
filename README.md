# AEC Quant System — Strategy Research & Trade Logs

Real, backtested trading strategy research for the AEC Quant System,
covering 4 systems with full trade-level data (Volatility Breakout, Trend
Following, FVG Rejection, Pairs/Kalman) plus the code for a further set of
tested-and-rejected strategies.

## Structure

- `strategies/` — all real strategy logic, tested against real NQ/ES OHLCV data
- `trade_logs/` — complete trade-level CSVs (entry/exit prices, side, win/loss,
  P&L) at 1x, 3x, 5x contract sizing, plus a win-rate-optimized variant
- `handoff_docs/` — the reviewer handoff package: system overview, trust
  tiers, risk map, rejected-idea graveyard, and real portfolio diagnostics
  (correlation, drawdown)

## Real, honest scope note

Trade-level data exists for 4 of the 9 total AEC systems. The original 5
(Layer I, OTE+BOS, HTF Rejection, Z-Score MR v2, VWAP Reversion) only have
summary statistics from earlier sessions — no raw trade log is included for
those here.

See `handoff_docs/HANDOFF_FOR_REVIEW.md` for the complete system context,
methodology, and open items.
