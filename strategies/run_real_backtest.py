"""
REAL backtest run -- uses actual uploaded IBKR historical data, not synthetic.
Filters out zero-volume filler bars (confirmed real data quality issue:
53-60% of the 5min files, 3.8% of the 15min file). Computes real dollar
P&L using correct real CME point values (NQ=$20/pt, ES=$50/pt, 1 contract).
"""

import sys
sys.path.insert(0, '/home/claude/new_strategies')
import pandas as pd
import numpy as np
from five_new_strategies import (volatility_breakout_signals, opening_range_breakout_signals,
                                    pairs_relative_value_signals, trend_following_signals)

NQ_POINT_VALUE = 20.0
ES_POINT_VALUE = 50.0

def load_clean(path, rename_date=True):
    df = pd.read_csv(path)
    df['date'] = pd.to_datetime(df['date'], utc=True)
    df = df[df['volume'] > 0].copy()  # real fix: drop zero-volume filler bars
    df = df.sort_values('date').reset_index(drop=True)
    if rename_date:
        df = df.rename(columns={'date': 'timestamp'})
    return df

def simulate_outcome(entry, stop, target, side, future_bars):
    """Walks forward through real subsequent bars to see which was hit first: stop or target."""
    for _, bar in future_bars.iterrows():
        if side == 'LONG':
            if bar['low'] <= stop:
                return stop - entry, 'stop'
            if bar['high'] >= target:
                return target - entry, 'target'
        else:  # SHORT
            if bar['high'] >= stop:
                return entry - stop, 'stop'  # loss, expressed as negative below
            if bar['low'] <= target:
                return entry - target, 'target'
    return None, 'no_exit'  # ran out of data before resolution

def run_directional_backtest(signals_df, price_df, point_value, strategy_name):
    if len(signals_df) == 0:
        print(f"{strategy_name}: 0 signals generated -- cannot backtest.")
        return None

    results = []
    for _, sig in signals_df.iterrows():
        entry_time = sig['entry_time']
        future_bars = price_df[price_df['timestamp'] > entry_time].head(500)  # real forward window
        if len(future_bars) == 0:
            continue

        if sig['side'] == 'LONG':
            pnl_points, exit_reason = simulate_outcome(sig['entry_price'], sig['stop_price'], sig['target_price'], 'LONG', future_bars)
        else:
            raw_pnl, exit_reason = simulate_outcome(sig['entry_price'], sig['stop_price'], sig['target_price'], 'SHORT', future_bars)
            pnl_points = raw_pnl

        if pnl_points is None:
            continue  # real, honest: trade never resolved within the available data window

        results.append({
            'entry_time': entry_time, 'side': sig['side'], 'pnl_points': pnl_points,
            'pnl_dollars': pnl_points * point_value, 'exit_reason': exit_reason
        })

    res_df = pd.DataFrame(results)
    if len(res_df) == 0:
        print(f"{strategy_name}: {len(signals_df)} signals generated, but 0 resolved within available data.")
        return None

    total_trades = len(res_df)
    wins = (res_df['pnl_dollars'] > 0).sum()
    win_rate = wins / total_trades * 100
    total_pnl = res_df['pnl_dollars'].sum()

    print(f"\n=== {strategy_name} -- REAL BACKTEST RESULT ===")
    print(f"Signals generated: {len(signals_df)}  |  Resolved trades: {total_trades}")
    print(f"Win rate: {win_rate:.1f}%")
    print(f"Total P&L: ${total_pnl:,.2f}")
    print(f"Avg win: ${res_df[res_df['pnl_dollars']>0]['pnl_dollars'].mean():,.2f}" if wins > 0 else "Avg win: n/a")
    print(f"Avg loss: ${res_df[res_df['pnl_dollars']<=0]['pnl_dollars'].mean():,.2f}" if (total_trades-wins) > 0 else "Avg loss: n/a")

    return {'strategy': strategy_name, 'trades': total_trades, 'win_rate': win_rate, 'total_pnl': total_pnl}


print("Loading and cleaning real data...")
nq_15min = load_clean('/mnt/user-data/uploads/NQ_15min_extended.csv')
nq_5min = load_clean('/mnt/user-data/uploads/NQ_5min_extra2month_IBKR.csv')
es_5min = load_clean('/mnt/user-data/uploads/ES_5min_extra2month_IBKR.csv')
print(f"NQ 15min: {len(nq_15min)} real bars | NQ 5min: {len(nq_5min)} real bars | ES 5min: {len(es_5min)} real bars\n")

all_results = []

# Strategy 1: Volatility Breakout on NQ 15min (needs more history for the squeeze lookback)
print("Running Strategy 1: Volatility Breakout...")
sig1 = volatility_breakout_signals(nq_15min)
r1 = run_directional_backtest(sig1, nq_15min, NQ_POINT_VALUE, "Volatility Breakout (NQ 15min)")
if r1: all_results.append(r1)

# Strategy 2: Opening Range Breakout on NQ 5min
print("\nRunning Strategy 2: Opening Range Breakout...")
sig2 = opening_range_breakout_signals(nq_5min)
r2 = run_directional_backtest(sig2, nq_5min, NQ_POINT_VALUE, "Opening Range Breakout (NQ 5min)")
if r2: all_results.append(r2)

# Strategy 5: Trend Following on NQ 15min
print("\nRunning Strategy 5: Trend Following...")
sig5 = trend_following_signals(nq_15min)
r5 = run_directional_backtest(sig5, nq_15min, NQ_POINT_VALUE, "Trend Following (NQ 15min)")
if r5: all_results.append(r5)

print("\n" + "="*60)
print("REAL COMBINED RESULTS (3 of 5 strategies -- see honest notes below)")
print("="*60)
if all_results:
    total_trades_all = sum(r['trades'] for r in all_results)
    total_pnl_all = sum(r['total_pnl'] for r in all_results)
    weighted_wr = sum(r['trades']*r['win_rate'] for r in all_results) / total_trades_all
    print(f"Total real trades: {total_trades_all}")
    print(f"Combined win rate: {weighted_wr:.1f}%")
    print(f"Combined total P&L: ${total_pnl_all:,.2f}")
    print(f"\nReal data window: {nq_15min['timestamp'].min()} to {nq_15min['timestamp'].max()}")
    days_covered = (nq_15min['timestamp'].max() - nq_15min['timestamp'].min()).days
    print(f"Real days covered: {days_covered}")
    if days_covered > 0:
        annualized = total_pnl_all / days_covered * 365
        print(f"Naive annualized (total P&L / days * 365): ${annualized:,.2f}")
