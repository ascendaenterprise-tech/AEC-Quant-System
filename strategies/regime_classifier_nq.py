"""
NQ-calibrated regime classifier -- implements the 5-component hierarchy
(Swing Structure, Range Compression, Expansion Burst, Directional
Clustering, Overlap Density) exactly as specified, tuned for NQ's real
wider volatility profile vs the earlier ES-generic thresholds.
"""

import pandas as pd
import numpy as np


def classify_regime_nq(df):
    d = df.copy().reset_index(drop=True)

    # ---- 1. Swing Structure (3-bar swing) ----
    d['swing_high'] = (d['high'] > d['high'].shift(1)) & (d['high'] > d['high'].shift(2)) & \
                        (d['high'] > d['high'].shift(-1)) & (d['high'] > d['high'].shift(-2))
    d['swing_low'] = (d['low'] < d['low'].shift(1)) & (d['low'] < d['low'].shift(2)) & \
                       (d['low'] < d['low'].shift(-1)) & (d['low'] < d['low'].shift(-2))

    # ---- 2. Range Compression ----
    d['range'] = d['high'] - d['low']
    d['median_range_20'] = d['range'].rolling(20).median()
    d['compression'] = d['range'] / d['median_range_20'].replace(0, np.nan)

    # ---- 3. Expansion Burst ----
    d['tr'] = np.maximum(d['high']-d['low'], np.maximum(abs(d['high']-d['close'].shift(1)), abs(d['low']-d['close'].shift(1))))
    d['atr14'] = d['tr'].rolling(14).mean()
    d['median_atr_50'] = d['atr14'].rolling(50).median()
    d['expansion_burst'] = d['atr14'] / d['median_atr_50'].replace(0, np.nan)

    # ---- 4. Directional Clustering ----
    d['close_position'] = (d['close']-d['low']) / (d['high']-d['low']).replace(0, np.nan)
    d['clustered'] = (d['close_position'] >= 0.8) | (d['close_position'] <= 0.2)
    d['cluster_count_8'] = d['clustered'].rolling(8).sum()

    # ---- 5. Overlap Density ----
    prior_high = d['high'].shift(1); prior_low = d['low'].shift(1)
    overlap_range = (np.minimum(d['high'], prior_high) - np.maximum(d['low'], prior_low)).clip(lower=0)
    d['overlap'] = overlap_range / d['range'].replace(0, np.nan)

    # ---- Real swing structure classification over last 5 swings ----
    swing_events = []
    last_swing_type = None
    last_swing_val = None
    swing_class = []
    recent_swings = []
    for i in range(len(d)):
        row = d.iloc[i]
        if row['swing_high']:
            hh_hl = last_swing_type=='high' and last_swing_val is not None and row['high']>last_swing_val
            recent_swings.append('HH' if (last_swing_val is None or row['high']>last_swing_val) else 'LH')
            last_swing_type='high'; last_swing_val=row['high']
        elif row['swing_low']:
            recent_swings.append('HL' if (last_swing_val is None or row['low']>last_swing_val) else 'LL')
            last_swing_type='low'; last_swing_val=row['low']
        recent_swings_trimmed = recent_swings[-5:]
        aligned = sum(1 for s in recent_swings_trimmed if s in ('HH','HL')) 
        aligned = max(aligned, sum(1 for s in recent_swings_trimmed if s in ('LH','LL')))
        if aligned >= 3: swing_class.append('TREND')
        elif aligned == 2: swing_class.append('TRANSITION')
        else: swing_class.append('CHOP')
    d['swing_structure'] = swing_class

    # ---- Real directional clustering classification ----
    def cluster_class(c):
        if pd.isna(c): return 'UNKNOWN'
        if c >= 5: return 'TREND'
        elif c >= 3: return 'TRANSITION'
        else: return 'CHOP'
    d['clustering_class'] = d['cluster_count_8'].apply(cluster_class)

    # ---- Real hierarchy, applied in exact specified order ----
    regimes = []
    for i in range(len(d)):
        row = d.iloc[i]
        if pd.isna(row['compression']) or pd.isna(row['expansion_burst']) or pd.isna(row['overlap']):
            regimes.append('UNKNOWN'); continue

        if row['swing_structure']=='TREND' and row['clustering_class']=='TREND' and row['overlap']<0.30:
            regimes.append('TREND')
        elif row['expansion_burst']>1.35 and row['compression']>0.55 and row['overlap']<0.45:
            regimes.append('EXPANSION')
        elif row['compression']<0.55 and row['expansion_burst']<1.0 and row['overlap']<0.55:
            regimes.append('COMPRESSION')
        elif row['overlap']>0.55 and row['clustering_class']=='CHOP' and row['swing_structure']=='CHOP':
            regimes.append('CHOP')
        elif row['swing_structure']=='TRANSITION' and row['clustering_class']=='TRANSITION' and 0.30<=row['overlap']<=0.55:
            regimes.append('TRANSITION')
        else:
            regimes.append('NEUTRAL')

    d['regime'] = regimes
    return d[['timestamp', 'regime']]
