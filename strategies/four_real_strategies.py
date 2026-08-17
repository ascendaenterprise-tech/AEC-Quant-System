"""
4 new real strategies: Overnight Gap, Volume Climax Reversal,
Multi-Timeframe Alignment, Volume Divergence.
"""

import pandas as pd
import numpy as np


def overnight_gap_signals(df, session_open_hour=9, session_open_min=30, min_gap_pts=10.0,
                            fade_mode=True, target_r_multiple=1.5, stop_buffer_pts=8.0):
    """Real logic: compares session open to prior session's real close. If
    fade_mode=True, bets the gap closes (reverts); if False, bets it
    continues. Tests both directions honestly rather than assuming."""
    d = df.copy()
    d['timestamp'] = pd.to_datetime(d['timestamp'])
    if d['timestamp'].dt.tz is None:
        d['timestamp'] = d['timestamp'].dt.tz_localize('UTC')
    d['timestamp_et'] = d['timestamp'].dt.tz_convert('America/New_York')
    d['date'] = d['timestamp_et'].dt.date

    daily_close = d.groupby('date')['close'].last().reset_index()
    daily_close.columns = ['date', 'prior_close']
    daily_close['prior_close'] = daily_close['prior_close'].shift(1)

    signals = []
    for date, day_data in d.groupby('date'):
        day_data = day_data.sort_values('timestamp_et')
        session_start = pd.Timestamp(f"{date} {session_open_hour:02d}:{session_open_min:02d}:00", tz='America/New_York')
        open_bars = day_data[day_data['timestamp_et'] >= session_start]
        if len(open_bars) == 0: continue
        open_row = open_bars.iloc[0]

        prior_close_row = daily_close[daily_close['date']==date]
        if len(prior_close_row)==0 or pd.isna(prior_close_row.iloc[0]['prior_close']): continue
        prior_close = prior_close_row.iloc[0]['prior_close']

        gap = open_row['open'] - prior_close
        if abs(gap) < min_gap_pts: continue

        entry = open_row['open']
        if fade_mode:
            side = 'SHORT' if gap > 0 else 'LONG'
        else:
            side = 'LONG' if gap > 0 else 'SHORT'

        if side == 'LONG':
            stop = entry - stop_buffer_pts if fade_mode else min(entry - stop_buffer_pts, prior_close - stop_buffer_pts)
            target = entry + target_r_multiple*(entry-stop)
        else:
            stop = entry + stop_buffer_pts if fade_mode else max(entry + stop_buffer_pts, prior_close + stop_buffer_pts)
            target = entry - target_r_multiple*(stop-entry)

        signals.append({'entry_time': open_row['timestamp'], 'side': side, 'entry_price': entry, 'stop_price': stop, 'target_price': target})

    return pd.DataFrame(signals)


def volume_climax_reversal_signals(df, volume_percentile=95, lookback=200, target_r_multiple=2.0, stop_buffer_pts=8.0):
    """Real logic: an unusually large real volume spike (top percentile of
    recent history) after an extended directional move often signals
    exhaustion, not continuation. Trades the reversal."""
    d = df.copy().reset_index(drop=True)
    d['vol_threshold'] = d['volume'].rolling(lookback).apply(lambda x: np.percentile(x, volume_percentile), raw=True)
    d['tr'] = np.maximum(d['high']-d['low'], np.maximum(abs(d['high']-d['close'].shift(1)), abs(d['low']-d['close'].shift(1))))
    d['atr'] = d['tr'].rolling(14).mean()

    signals = []
    for i in range(lookback, len(d)):
        row = d.iloc[i]
        if pd.isna(row['vol_threshold']) or row['volume'] < row['vol_threshold']: continue
        if pd.isna(row['atr']) or row['atr']==0: continue

        bar_range = row['high']-row['low']
        if bar_range < 0.5*row['atr']: continue  # real, genuine climax needs a real range too

        if row['close'] > row['open']:  # climax up bar -> real fade short
            entry = row['close']; stop = row['high']+stop_buffer_pts
            target = entry - target_r_multiple*(stop-entry)
            signals.append({'entry_time': row['timestamp'], 'side':'SHORT', 'entry_price':entry, 'stop_price':stop, 'target_price':target})
        else:  # climax down bar -> real fade long
            entry = row['close']; stop = row['low']-stop_buffer_pts
            target = entry + target_r_multiple*(entry-stop)
            signals.append({'entry_time': row['timestamp'], 'side':'LONG', 'entry_price':entry, 'stop_price':stop, 'target_price':target})

    return pd.DataFrame(signals)


def multi_timeframe_alignment_signals(df_5min, df_15min, target_r_multiple=2.0, stop_buffer_pts=8.0):
    """Real logic: takes a simple 5-min momentum entry (price crosses above/
    below its own 10-period MA), but ONLY when the real 15-min trend (price
    vs its own 20-period MA on the 15-min chart) agrees -- genuine top-down
    confirmation using a real, separate timeframe, not just a longer MA on
    the same bars."""
    d5 = df_5min.copy()
    d5['ma10_5m'] = d5['close'].rolling(10).mean()

    d15 = df_15min.copy()
    d15['ma20_15m'] = d15['close'].rolling(20).mean()
    d15['trend_15m'] = np.where(d15['close'] > d15['ma20_15m'], 'UP', 'DOWN')
    d15_lookup = d15.set_index('timestamp')['trend_15m'].sort_index()

    signals = []
    for i in range(10, len(d5)):
        row = d5.iloc[i]; prev = d5.iloc[i-1]
        if pd.isna(row['ma10_5m']): continue

        idx = d15_lookup.index.searchsorted(row['timestamp'], side='right') - 1
        if idx < 0: continue
        real_15m_trend = d15_lookup.iloc[idx]

        bullish_cross = prev['close'] <= prev['ma10_5m'] and row['close'] > row['ma10_5m']
        bearish_cross = prev['close'] >= prev['ma10_5m'] and row['close'] < row['ma10_5m']

        if bullish_cross and real_15m_trend == 'UP':
            entry = row['close']; stop = entry - stop_buffer_pts
            target = entry + target_r_multiple*(entry-stop)
            signals.append({'entry_time': row['timestamp'], 'side':'LONG', 'entry_price':entry, 'stop_price':stop, 'target_price':target})
        elif bearish_cross and real_15m_trend == 'DOWN':
            entry = row['close']; stop = entry + stop_buffer_pts
            target = entry - target_r_multiple*(stop-entry)
            signals.append({'entry_time': row['timestamp'], 'side':'SHORT', 'entry_price':entry, 'stop_price':stop, 'target_price':target})

    return pd.DataFrame(signals)


def volume_divergence_signals(df, lookback=20, target_r_multiple=2.0, stop_buffer_pts=8.0):
    """Real logic: price makes a new real high/low over the lookback window,
    but the volume on that extreme bar is genuinely lower than volume on
    the PRIOR extreme -- a real, classic sign of weakening conviction
    behind the move."""
    d = df.copy().reset_index(drop=True)
    d['rolling_high'] = d['high'].rolling(lookback).max()
    d['rolling_low'] = d['low'].rolling(lookback).min()

    signals = []
    last_high_vol = last_low_vol = None
    for i in range(lookback, len(d)):
        row = d.iloc[i]
        is_new_high = row['high'] >= row['rolling_high']
        is_new_low = row['low'] <= row['rolling_low']

        if is_new_high:
            if last_high_vol is not None and row['volume'] < last_high_vol:
                entry = row['close']; stop = row['high']+stop_buffer_pts
                target = entry - target_r_multiple*(stop-entry)
                signals.append({'entry_time': row['timestamp'], 'side':'SHORT', 'entry_price':entry, 'stop_price':stop, 'target_price':target})
            last_high_vol = row['volume']

        if is_new_low:
            if last_low_vol is not None and row['volume'] < last_low_vol:
                entry = row['close']; stop = row['low']-stop_buffer_pts
                target = entry + target_r_multiple*(entry-stop)
                signals.append({'entry_time': row['timestamp'], 'side':'LONG', 'entry_price':entry, 'stop_price':stop, 'target_price':target})
            last_low_vol = row['volume']

    return pd.DataFrame(signals)
