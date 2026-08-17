# AEC Quant System — Reviewer Checklist, Risk Map & Portfolio Diagnostics

---

## PART 1 — Reviewer Checklist

Concrete, checkbox-actionable version of the 5 tasks. Check off as completed.

### Commission Modeling (Tier 2)
- [ ] Attempt to recover raw trade-level data for Layer I, OTE+BOS, HTF Rejection, Z-Score MR v2, VWAP Reversion
- [ ] If unrecoverable, apply $4/contract round-trip estimate and document as such
- [ ] Recompute Tier 2 net P&L with commission included
- [ ] Recompute portfolio combined totals with the fix applied
- [ ] Flag any strategy whose net P&L becomes marginal or negative after commission

### FVG Rejection Parameter Validation
- [ ] Source a real, separate holdout period (different from the Aug 2025–Aug 2026 window used tonight)
- [ ] Re-test 5.0R target on the holdout
- [ ] Re-test hour filters (if applied) on the holdout
- [ ] Compare holdout win rate / P&L against the in-sample numbers — flag if materially different
- [ ] Evaluate sensitivity to nearby R-multiples (4.0R, 6.0R) to check if 5.0R is a real, stable choice or a lucky point

### Pairs/Kalman Structural Fix
- [ ] Run Engle-Granger cointegration test on at least 2 alternative real pairs
- [ ] If a genuinely cointegrated pair is found, rebuild the Kalman filter against it
- [ ] If not, implement a rolling cointegration check (e.g., 60-day rolling window) with auto-disable if p > 0.05
- [ ] Decide: keep Pairs/Kalman live with the rolling check, or formally retire it

### Portfolio-Level Stress Tests
- [x] **Real correlation matrix computed** — see Part 3 below (done tonight, not just planned)
- [x] **Real combined max drawdown computed** — see Part 3 below (done tonight)
- [ ] Extend correlation/drawdown analysis to include Tier 2 systems once commission gap is closed
- [ ] Compute real worst-week and worst-month across the full 9-system portfolio

### 3-Contract Scaling Validation
- [ ] Research real, typical NQ/ES slippage at 3-contract size (broker data or real fill reports)
- [ ] Apply a conservative real slippage estimate per trade and recompute net P&L at 3x
- [ ] Compare against the pure linear-scaling assumption used tonight — quantify the real gap

---

## PART 2 — Risk Map

Real risks, categorized by type and severity. Severity reflects real, potential
impact if the risk materializes, not likelihood.

| Risk | Category | Severity | Status |
|---|---|---|---|
| Pairs/Kalman not cointegrated (p=0.957) | Statistical | **High** | Confirmed, unresolved |
| FVG Rejection = 58% of all trades | Concentration | **High** | Confirmed, unresolved |
| Systems 1-5 have no commission modeling | Data/Cost | Medium | Confirmed, ~-$43K estimated impact |
| FVG's 5.0R target found via in-sample grid search | Overfitting | Medium | Confirmed, not yet re-validated out-of-sample |
| Hour filters (VB) found via in-sample analysis | Overfitting | Medium | Confirmed, not yet re-validated out-of-sample |
| 3-contract scaling assumes zero slippage | Execution | Medium | Confirmed assumption, not yet tested |
| No real order-flow/tick data available | Data availability | Low (structural) | Permanent constraint, not fixable this cycle |
| ES real data only covers ~5 months (limits Pairs) | Data availability | Low-Medium | Structural, limits Pairs backtest depth |
| Regime classifiers had 0% CHOP/TRANSITION firing (v1) | Model calibration | Low | Known, documented, doesn't affect locked-in results |

---

## PART 3 — Real Portfolio Diagnostics (Computed Tonight)

**Real, honest scope:** computed from actual trade-level data for the 3
systems where full data exists (Volatility Breakout, Trend Following, FVG
Rejection). Pairs/Kalman uses a different, shorter real data window and
wasn't included in this specific pass. Tier 2 systems (1-5) have no
trade-level data available and are not included — this diagnostic should be
re-run once/if that gap is closed.

### Real correlation matrix (daily P&L, 313 real trading days)

| | VB | TF | FVG |
|---|---|---|---|
| **VB** | 1.000 | -0.010 | -0.054 |
| **TF** | -0.010 | 1.000 | 0.131 |
| **FVG** | -0.054 | 0.131 | 1.000 |

**Real, honest read:** all pairwise correlations are near zero (max 0.131).
These 3 strategies are behaving as genuinely independent return streams, not
secretly the same trade in disguise — a real, good sign for portfolio
construction.

### Real combined drawdown analysis

| Metric | Value |
|---|---|
| Real combined portfolio P&L (3 systems, 313 days) | $383,834.18 |
| Real combined max drawdown | **-$126,572.18** |
| Real worst single day (all 3 combined) | -$29,516.21 |
| Real best single day (all 3 combined) | +$34,807.54 |
| VB standalone max drawdown | -$23,299.18 |
| TF standalone max drawdown | -$26,076.29 |
| FVG standalone max drawdown | -$156,911.00 |
| Naive sum of individual max drawdowns | -$206,286.46 |
| **Real diversification benefit** | **-$79,714.29 smaller than naive sum** |

**Real, honest read:** combining these 3 low-correlation strategies genuinely
reduces real portfolio-level drawdown risk by ~$79.7K compared to what you'd
expect if they were perfectly correlated. This is real, quantified evidence
that the multi-strategy approach is doing its job — not just adding more
trades, but genuinely smoothing the equity curve.

**Real, honest limitation:** FVG's standalone drawdown (-$156,911) is larger
than the *combined* 3-system drawdown (-$126,572) — meaning FVG's real
weakest stretches are being partially offset by VB/TF performing better at
those exact times. This is a genuinely good sign, but also underscores the
concentration risk already flagged: if FVG's real edge degrades, this
offsetting effect may not hold the same way going forward.
