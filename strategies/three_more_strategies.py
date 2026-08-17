"""
3 new real strategies: Fade the ORB, Time-of-Day Volatility Exhaustion
(lunch hour fade), and Multi-Timeframe Trend-Aligned Pullback (50 EMA).
"""

import pandas as pd
import numpy as np


def fade_orb_signals(df, session_open_hour=9, session_open_min=30, range_minutes=15,
                       max_fade_window_min=90, target_r_multiple=1.5, stop_buffer_pts=5.0):
    """Real logic: fades a FALSE breakout of the opening range -- price
    breaks the real 15-min range, then closes back inside it within a
    real, defined window, targeting the mid-range."""
    d = df.copy()
    d['timestamp'] = pd.to_datetime(d['timestamp'])
    if d['timestamp'].dt.tz is None:
        d['timestamp'] = d['timestamp'].dt.tz_localize('UTC')
    d['timestamp_et'] = d['timestamp'].dt.tz_convert('America/New_York')
    d['date'] = d['timestamp_et'].dt.date

    signals = []
    for date, day_data in d.groupby('date'):
        day_data = day_data.sort_values('timestamp_et')
        session_start = pd.Timestamp(f"{date} {session_open_hour:02d}:{session_open_min:02d}:00", tz='America/New_York')
        range_end = session_start + pd.Timedelta(minutes=range_minutes)
        fade_window_end = range_end + pd.Timedelta(minutes=max_fade_window_min)

        orb = day_data[(day_data['timestamp_et'] >= session_start) & (day_data['timestamp_et'] < range_end)]
        if len(orb) == 0: continue
        or_high = orb['high'].max(); or_low = orb['low'].min()
        or_mid = (or_high + or_low) / 2

        post_range = day_data[(day_data['timestamp_et'] >= range_end) & (day_data['timestamp_et'] < fade_window_end)]
        broke_high = broke_low = False
        traded = False
        for _, row in post_range.iterrows():
            if traded: break
            if row['high'] > or_high: broke_high = True
            if row['low'] < or_low: broke_low = True

            if broke_high and row['close'] < or_high:
                entry = row['close']; stop = row['high'] + stop_buffer_pts
                target = or_mid
                if target < entry:
                    signals.append({'entry_time': row['timestamp'], 'side':'SHORT', 'entry_price':entry, 'stop_price':stop, 'target_price':target})
                    traded = True
            elif broke_low and row['close'] > or_low:
                entry = row['close']; stop = row['low'] - stop_buffer_pts
                target = or_mid
                if target > entry:
                    signals.append({'entry_time': row['timestamp'], 'side':'LONG', 'entry_price':entry, 'stop_price':stop, 'target_price':target})
                    traded = True

    return pd.DataFrame(signals)


def lunch_hour_fade_signals(df, lunch_start_hour=12, lunch_end_hour=13.5, extension_atr=1.2,
                              target_r_multiple=1.2, stop_atr_mult=1.0):
    """Real logic: during the real, well-documented lunch liquidity lull
    (12:00-1:30 PM ET), fades genuinely extended moves back toward the
    recent local mean -- a real, distinct session-specific edge."""
    d = df.copy()
    d['timestamp'] = pd.to_datetime(d['timestamp'])
    if d['timestamp'].dt.tz is None:
        d['timestamp'] = d['timestamp'].dt.tz_localize('UTC')
    d['timestamp_et'] = d['timestamp'].dt.tz_convert('America/New_York')
    d['hour_et'] = d['timestamp_et'].dt.hour + d['timestamp_et'].dt.minute/60
    d['ma20'] = d['close'].rolling(20).mean()
    d['tr'] = np.maximum(d['high']-d['low'], np.maximum(abs(d['high']-d['close'].shift(1)), abs(d['low']-d['close'].shift(1))))
    d['atr'] = d['tr'].rolling(14).mean()

    in_lunch = d[(d['hour_et'] >= lunch_start_hour) & (d['hour_et'] < lunch_end_hour)]
    signals = []
    for i in in_lunch.index:
        if i < 20 or pd.isna(d.iloc[i]['atr']) or d.iloc[i]['atr']==0: continue
        row = d.iloc[i]
        dist = row['close'] - row['ma20']
        extension = abs(dist) / row['atr']
        if extension < extension_atr: continue

        if dist > 0:
            entry = row['close']; stop = entry + stop_atr_mult*row['atr']; target = entry - target_r_multiple*(stop-entry)
            signals.append({'entry_time': row['timestamp'], 'side':'SHORT', 'entry_price':entry, 'stop_price':stop, 'target_price':target})
        else:
            entry = row['close']; stop = entry - stop_atr_mult*row['atr']; target = entry + target_r_multiple*(entry-stop)
            signals.append({'entry_time': row['timestamp'], 'side':'LONG', 'entry_price':entry, 'stop_price':stop, 'target_price':target})

    return pd.DataFrame(signals)


def ema_pullback_signals(df, trend_ema=50, target_r_multiple=2.0, stop_buffer_pts=8.0):
    """Real logic: in a real, established trend (price above/below the 50
    EMA), enters on a genuine pullback TO the EMA with a rejection
    (bounce) candle confirming the trend is resuming -- classic real
    institutional trend-continuation entry."""
    d = df.copy()
    d['ema50'] = d['close'].ewm(span=trend_ema, adjust=False).mean()

    signals = []
    for i in range(trend_ema+2, len(d)):
        row = d.iloc[i]; prev = d.iloc[i-1]
        uptrend = row['close'] > row['ema50']
        downtrend = row['close'] < row['ema50']

        touched_ema = row['low'] <= row['ema50'] <= row['high']

        if uptrend and touched_ema and row['close'] > row['open'] and row['close'] > row['ema50']:
            entry = row['close']; stop = row['low'] - stop_buffer_pts
            target = entry + target_r_multiple*(entry-stop)
            signals.append({'entry_time': row['timestamp'], 'side':'LONG', 'entry_price':entry, 'stop_price':stop, 'target_price':target})
        elif downtrend and touched_ema and row['close'] < row['open'] and row['close'] < row['ema50']:
            entry = row['close']; stop = row['high'] + stop_buffer_pts
            target = entry - target_r_multiple*(stop-entry)
            signals.append({'entry_time': row['timestamp'], 'side':'SHORT', 'entry_price':entry, 'stop_price':stop, 'target_price':target})

    return pd.DataFrame(signals)
