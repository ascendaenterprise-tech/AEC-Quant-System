"""
Real regime classifier -- Trend / Chop / Expansion, built purely from
OHLCV structure (no external data, no indicators beyond what price/volume
can produce). Used to tag existing trades and test whether real,
per-regime expectancy reveals a genuine, earned filter.
"""

import pandas as pd
import numpy as np


def classify_regime(df, structure_lookback=20, overlap_lookback=10, atr_period=14, expansion_mult=1.2,
                      trend_efficiency_percentile=75, trend_overlap_percentile=25):
    d = df.copy().reset_index(drop=True)
    d['tr'] = np.maximum(d['high']-d['low'], np.maximum(abs(d['high']-d['close'].shift(1)), abs(d['low']-d['close'].shift(1))))
    d['atr'] = d['tr'].rolling(atr_period).mean()
    d['atr_rolling_avg'] = d['atr'].rolling(100, min_periods=30).mean()

    prior_high = d['high'].shift(1); prior_low = d['low'].shift(1)
    overlap = (np.minimum(d['high'], prior_high) - np.maximum(d['low'], prior_low)).clip(lower=0)
    bar_range = (d['high']-d['low']).replace(0, np.nan)
    d['overlap_pct'] = overlap / bar_range
    d['avg_overlap'] = d['overlap_pct'].rolling(overlap_lookback).mean()

    d['net_move'] = d['close'] - d['close'].shift(structure_lookback)
    d['total_path'] = d['tr'].rolling(structure_lookback).sum()
    d['efficiency'] = abs(d['net_move']) / d['total_path'].replace(0, np.nan)

    # Real, data-driven thresholds instead of arbitrary guesses
    real_eff_threshold = d['efficiency'].quantile(trend_efficiency_percentile/100)
    real_overlap_threshold = d['avg_overlap'].quantile(trend_overlap_percentile/100)
    real_chop_overlap_threshold = d['avg_overlap'].quantile(60/100)

    regimes = []
    for i in range(len(d)):
        row = d.iloc[i]
        if pd.isna(row['atr']) or pd.isna(row['atr_rolling_avg']) or pd.isna(row['avg_overlap']) or pd.isna(row['efficiency']):
            regimes.append('UNKNOWN')
            continue

        is_expansion = row['atr'] > expansion_mult * row['atr_rolling_avg']
        is_trend = row['efficiency'] > real_eff_threshold and row['avg_overlap'] < real_overlap_threshold
        is_chop = row['avg_overlap'] >= real_chop_overlap_threshold and row['efficiency'] <= d['efficiency'].quantile(0.40)

        if is_expansion:
            regimes.append('EXPANSION')
        elif is_trend:
            regimes.append('TREND')
        elif is_chop:
            regimes.append('CHOP')
        else:
            regimes.append('NEUTRAL')

    d['regime'] = regimes
    return d[['timestamp', 'regime']]
