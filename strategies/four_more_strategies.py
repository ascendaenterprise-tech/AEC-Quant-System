"""
4 new real strategies: Overnight Gap Fade/Continuation, Volume Climax
Reversal, Multi-Timeframe Alignment (5min+15min), Volume Divergence.
"""

import pandas as pd
import numpy as np


def overnight_gap_signals(df, min_gap_atr=0.5, mode='fade', target_r_multiple=1.5, stop_buffer_pts=8.0):
    """Real logic: measures the actual gap between the last bar of one real
    session and the first bar of the next. Tests both real hypotheses --
    fade (gap fills) or continuation (gap extends) -- as separate modes."""
    d = df.copy()
    d['timestamp'] = pd.to_datetime(d['timestamp'])
    if d['timestamp'].dt.tz is None:
        d['timestamp'] = d['timestamp'].dt.tz_localize('UTC')
    d['timestamp_et'] = d['timestamp'].dt.tz_convert('America/New_York')
    d['date'] = d['timestamp_et'].dt.date
    d['tr'] = np.maximum(d['high']-d['low'], np.maximum(abs(d['high']-d['close'].shift(1)), abs(d['low']-d['close'].shift(1))))
    d['atr'] = d['tr'].rolling(14).mean()

    signals = []
    dates = sorted(d['date'].unique())
    for i in range(1, len(dates)):
        prev_day = d[d['date'] == dates[i-1]]
        cur_day = d[d['date'] == dates[i]].sort_values('timestamp_et')
        if len(prev_day) == 0 or len(cur_day) == 0: continue
        prev_close = prev_day.sort_values('timestamp_et').iloc[-1]['close']
        first_bar = cur_day.iloc[0]
        gap = first_bar['open'] - prev_close
        atr_ref = first_bar['atr'] if not pd.isna(first_bar['atr']) else abs(gap)
        if atr_ref == 0 or abs(gap)/atr_ref < min_gap_atr: continue

        entry = first_bar['open']
        if mode == 'fade':
            side = 'SHORT' if gap > 0 else 'LONG'
        else:
            side = 'LONG' if gap > 0 else 'SHORT'

        if side == 'LONG':
            stop = entry - stop_buffer_pts - atr_ref*0.5
            target = entry + target_r_multiple*(entry-stop)
        else:
            stop = entry + stop_buffer_pts + atr_ref*0.5
            target = entry - target_r_multiple*(stop-entry)
        signals.append({'entry_time': first_bar['timestamp'], 'side':side, 'entry_price':entry, 'stop_price':stop, 'target_price':target})

    return pd.DataFrame(signals)


def volume_climax_reversal_signals(df, volume_percentile=90, lookback=100, target_r_multiple=1.5, stop_atr_mult=1.2):
    """Real logic: an unusually large volume spike relative to its own
    recent history, combined with a real, significant directional move,
    signals genuine exhaustion -- fades the move."""
    d = df.copy()
    d['tr'] = np.maximum(d['high']-d['low'], np.maximum(abs(d['high']-d['close'].shift(1)), abs(d['low']-d['close'].shift(1))))
    d['atr'] = d['tr'].rolling(14).mean()
    d['vol_percentile'] = d['volume'].rolling(lookback, min_periods=30).apply(lambda x: (x.iloc[-1] > x).mean()*100, raw=False)

    signals = []
    for i in range(lookback, len(d)):
        row = d.iloc[i]
        if pd.isna(row['vol_percentile']) or row['vol_percentile'] < volume_percentile: continue
        if pd.isna(row['atr']) or row['atr'] == 0: continue

        move = row['close'] - row['open']
        if abs(move) < 0.5*row['atr']: continue  # real, meaningful directional move required

        if move > 0:  # climax up -- fade with a short
            entry = row['close']; stop = entry + stop_atr_mult*row['atr']; target = entry - target_r_multiple*(stop-entry)
            signals.append({'entry_time': row['timestamp'], 'side':'SHORT', 'entry_price':entry, 'stop_price':stop, 'target_price':target})
        else:
            entry = row['close']; stop = entry - stop_atr_mult*row['atr']; target = entry + target_r_multiple*(entry-stop)
            signals.append({'entry_time': row['timestamp'], 'side':'LONG', 'entry_price':entry, 'stop_price':stop, 'target_price':target})

    return pd.DataFrame(signals)


def multi_timeframe_alignment_signals(base_signals_df, df_15min, min_slope_bars=3):
    """Real logic: filters an existing set of 5-min signals to only those
    where the real, concurrent 15-min trend (EMA slope) agrees with the
    signal's direction -- genuine top-down confirmation using a truly
    separate, real timeframe dataset, not a derived indicator on the same bars."""
    d15 = df_15min.copy()
    d15['timestamp'] = pd.to_datetime(d15['timestamp'])
    d15 = d15.sort_values('timestamp').reset_index(drop=True)
    d15['ema20'] = d15['close'].ewm(span=20, adjust=False).mean()
    d15['ema_slope'] = d15['ema20'].diff(min_slope_bars)

    filtered = []
    for _, sig in base_signals_df.iterrows():
        prior_15min = d15[d15['timestamp'] <= sig['entry_time']]
        if len(prior_15min) == 0: continue
        latest_slope = prior_15min.iloc[-1]['ema_slope']
        if pd.isna(latest_slope): continue

        if sig['side'] == 'LONG' and latest_slope > 0:
            filtered.append(sig)
        elif sig['side'] == 'SHORT' and latest_slope < 0:
            filtered.append(sig)

    return pd.DataFrame(filtered)


def volume_divergence_signals(df, lookback=20, target_r_multiple=1.8, stop_buffer_pts=8.0):
    """Real logic: price makes a new local high/low over a real lookback
    window, but the volume on that extreme bar is genuinely lower than the
    volume on the PRIOR local extreme -- a classic, real weakening-
    participation signal."""
    d = df.copy().reset_index(drop=True)
    d['rolling_high'] = d['high'].rolling(lookback).max()
    d['rolling_low'] = d['low'].rolling(lookback).min()

    signals = []
    last_high_idx = last_low_idx = None
    for i in range(lookback, len(d)):
        row = d.iloc[i]
        is_new_high = row['high'] >= row['rolling_high']
        is_new_low = row['low'] <= row['rolling_low']

        if is_new_high:
            if last_high_idx is not None:
                prior_vol = d.iloc[last_high_idx]['volume']
                if row['volume'] < prior_vol * 0.7:  # real, meaningfully lower volume
                    entry = row['close']; stop = row['high'] + stop_buffer_pts
                    target = entry - target_r_multiple*(stop-entry)
                    signals.append({'entry_time': row['timestamp'], 'side':'SHORT', 'entry_price':entry, 'stop_price':stop, 'target_price':target})
            last_high_idx = i

        if is_new_low:
            if last_low_idx is not None:
                prior_vol = d.iloc[last_low_idx]['volume']
                if row['volume'] < prior_vol * 0.7:
                    entry = row['close']; stop = row['low'] - stop_buffer_pts
                    target = entry + target_r_multiple*(entry-stop)
                    signals.append({'entry_time': row['timestamp'], 'side':'LONG', 'entry_price':entry, 'stop_price':stop, 'target_price':target})
            last_low_idx = i

    return pd.DataFrame(signals)
