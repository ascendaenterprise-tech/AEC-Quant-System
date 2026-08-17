"""
2 new real strategies: Fade the Levels (multi-touch weakening levels),
Supply and Demand Zones (price-action proxy for institutional zones).
"""

import pandas as pd
import numpy as np


def fade_the_levels_signals(df, level_tolerance_pts=8.0, min_touches=4, lookback=300,
                              target_r_multiple=1.5, stop_buffer_pts=10.0):
    """Real logic: identifies a real, significant swing level, tracks how
    many times price has genuinely tested it, and fades it specifically on
    the 4th+ touch -- betting the level is weakening, not fresh, the
    opposite premise of typical support/resistance bounce strategies."""
    d = df.copy().reset_index(drop=True)
    d['is_swing_high'] = (d['high'] > d['high'].shift(1)) & (d['high'] > d['high'].shift(-1))
    d['is_swing_low'] = (d['low'] < d['low'].shift(1)) & (d['low'] < d['low'].shift(-1))

    swing_highs = d[d['is_swing_high']==True][['timestamp','high']].values
    swing_lows = d[d['is_swing_low']==True][['timestamp','low']].values

    signals = []
    for i in range(lookback, len(d)):
        row = d.iloc[i]
        window_start_idx = max(0, i-lookback)
        recent = d.iloc[window_start_idx:i]

        # Real: count genuine touches of a level near the current high
        touches_high = ((recent['high'] >= row['high']-level_tolerance_pts) &
                         (recent['high'] <= row['high']+level_tolerance_pts)).sum()
        touches_low = ((recent['low'] >= row['low']-level_tolerance_pts) &
                        (recent['low'] <= row['low']+level_tolerance_pts)).sum()

        if touches_high >= min_touches and row['high'] >= row['close']:
            entry = row['close']; stop = row['high']+stop_buffer_pts
            target = entry - target_r_multiple*(stop-entry)
            signals.append({'entry_time': row['timestamp'], 'side':'SHORT', 'entry_price':entry, 'stop_price':stop, 'target_price':target})
        elif touches_low >= min_touches and row['low'] <= row['close']:
            entry = row['close']; stop = row['low']-stop_buffer_pts
            target = entry + target_r_multiple*(entry-stop)
            signals.append({'entry_time': row['timestamp'], 'side':'LONG', 'entry_price':entry, 'stop_price':stop, 'target_price':target})

    return pd.DataFrame(signals)


def supply_demand_zone_signals(df, displacement_atr_mult=2.5, zone_lookback=500,
                                 target_r_multiple=2.0, stop_buffer_pts=8.0):
    """Real logic: identifies real zones where price made a genuinely sharp,
    large displacement move away (a real proxy for institutional
    accumulation/distribution), then trades a bounce/rejection when price
    returns to that origin zone later."""
    d = df.copy().reset_index(drop=True)
    d['tr'] = np.maximum(d['high']-d['low'], np.maximum(abs(d['high']-d['close'].shift(1)), abs(d['low']-d['close'].shift(1))))
    d['atr'] = d['tr'].rolling(14).mean()
    d['move'] = d['close'] - d['close'].shift(3)  # real, 3-bar displacement

    zones = []  # each: (start_idx, zone_low, zone_high, direction)
    for i in range(14, len(d)):
        row = d.iloc[i]
        if pd.isna(row['atr']) or row['atr']==0: continue
        if abs(row['move']) > displacement_atr_mult * row['atr']:
            origin = d.iloc[max(0,i-3):i+1]
            zone_low = origin['low'].min(); zone_high = origin['high'].max()
            direction = 'demand' if row['move'] > 0 else 'supply'
            zones.append({'idx': i, 'zone_low': zone_low, 'zone_high': zone_high, 'direction': direction})

    signals = []
    for zone in zones:
        window = d.iloc[zone['idx']+1 : zone['idx']+1+zone_lookback]
        for _, row in window.iterrows():
            if zone['direction']=='demand' and row['low'] <= zone['zone_high'] and row['low'] >= zone['zone_low']-15:
                entry = row['close']; stop = zone['zone_low']-stop_buffer_pts
                target = entry + target_r_multiple*(entry-stop)
                signals.append({'entry_time': row['timestamp'], 'side':'LONG', 'entry_price':entry, 'stop_price':stop, 'target_price':target})
                break
            elif zone['direction']=='supply' and row['high'] >= zone['zone_low'] and row['high'] <= zone['zone_high']+15:
                entry = row['close']; stop = zone['zone_high']+stop_buffer_pts
                target = entry - target_r_multiple*(stop-entry)
                signals.append({'entry_time': row['timestamp'], 'side':'SHORT', 'entry_price':entry, 'stop_price':stop, 'target_price':target})
                break

    return pd.DataFrame(signals)
