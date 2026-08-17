"""
AEC -- 5 NEW STRATEGY SYSTEMS -- real, complete signal logic.

Each strategy follows a consistent interface: takes a real OHLCV DataFrame
(columns: timestamp, open, high, low, close, volume -- adjust column names
below to match your real data once provided) and returns a DataFrame of
real trade signals (entry_time, side, entry_price, stop_price, target_price).

HONEST NOTE: this is real, complete strategy LOGIC, verified for correct
computation on synthetic test data (see verify_logic.py). It has NOT been
backtested against real market data yet -- that requires your actual
historical price files. No performance numbers exist for these yet, and
none should be trusted until they come from a real backtest.
"""

import pandas as pd
import numpy as np


# ============================================================
# STRATEGY 1: VOLATILITY BREAKOUT (Bollinger Band Squeeze)
# ============================================================
def volatility_breakout_signals(df, bb_period=20, bb_std=2.0, squeeze_lookback=100,
                                  squeeze_percentile=20, target_r_multiple=2.5, stop_atr_mult=1.0):
    """
    Real logic: identifies periods of unusually LOW volatility (a genuine
    'squeeze' -- Bollinger Band width in the bottom percentile of its own
    recent history), then trades the breakout when price closes outside
    the bands, in the breakout's direction.
    """
    d = df.copy()
    d['sma'] = d['close'].rolling(bb_period).mean()
    d['std'] = d['close'].rolling(bb_period).std()
    d['upper_band'] = d['sma'] + bb_std * d['std']
    d['lower_band'] = d['sma'] - bb_std * d['std']
    d['band_width'] = (d['upper_band'] - d['lower_band']) / d['sma']

    # Real squeeze condition: current band width in the bottom Nth percentile
    # of its own recent history -- genuinely compressed, not an arbitrary cutoff
    d['width_percentile'] = d['band_width'].rolling(squeeze_lookback).apply(
        lambda x: (x.iloc[-1] <= np.percentile(x, squeeze_percentile)), raw=False
    )

    # Real ATR for stop sizing
    d['tr'] = np.maximum(d['high'] - d['low'],
                np.maximum(abs(d['high'] - d['close'].shift(1)), abs(d['low'] - d['close'].shift(1))))
    d['atr'] = d['tr'].rolling(14).mean()

    signals = []
    in_squeeze = False
    for i in range(squeeze_lookback + bb_period, len(d)):
        row = d.iloc[i]
        prev = d.iloc[i-1]

        if row['width_percentile'] == 1:
            in_squeeze = True
            continue

        if in_squeeze:
            # Real breakout: close decisively outside the band right after a squeeze
            if row['close'] > row['upper_band'] and prev['close'] <= prev['upper_band']:
                entry = row['close']
                stop = entry - stop_atr_mult * row['atr']
                target = entry + target_r_multiple * (entry - stop)
                signals.append({'entry_time': row.get('timestamp', i), 'side': 'LONG',
                                 'entry_price': entry, 'stop_price': stop, 'target_price': target})
                in_squeeze = False
            elif row['close'] < row['lower_band'] and prev['close'] >= prev['lower_band']:
                entry = row['close']
                stop = entry + stop_atr_mult * row['atr']
                target = entry - target_r_multiple * (stop - entry)
                signals.append({'entry_time': row.get('timestamp', i), 'side': 'SHORT',
                                 'entry_price': entry, 'stop_price': stop, 'target_price': target})
                in_squeeze = False

    return pd.DataFrame(signals)


# ============================================================
# STRATEGY 2: OPENING RANGE BREAKOUT (ORB)
# ============================================================
def opening_range_breakout_signals(df, session_open_hour=9, session_open_min=30,
                                     range_minutes=30, target_r_multiple=2.0):
    """
    Real logic: defines the opening range as the high/low of the first N
    minutes of the NY session, then trades a real breakout beyond that
    range -- a genuine, classic institutional-flow-based edge.
    Requires a real 'timestamp' column (datetime, any timezone) in the input data.
    Correctly handles timezone conversion to US/Eastern so '9:30' is accurate
    year-round regardless of daylight saving time.
    """
    d = df.copy()
    d['timestamp'] = pd.to_datetime(d['timestamp'])
    if d['timestamp'].dt.tz is None:
        d['timestamp'] = d['timestamp'].dt.tz_localize('UTC')
    d['timestamp_et'] = d['timestamp'].dt.tz_convert('America/New_York')
    d['date'] = d['timestamp_et'].dt.date
    d['time'] = d['timestamp_et'].dt.time

    signals = []
    for date, day_data in d.groupby('date'):
        day_data = day_data.sort_values('timestamp_et')
        session_start = pd.Timestamp(f"{date} {session_open_hour:02d}:{session_open_min:02d}:00", tz='America/New_York')
        range_end = session_start + pd.Timedelta(minutes=range_minutes)

        opening_range = day_data[(day_data['timestamp_et'] >= session_start) & (day_data['timestamp_et'] < range_end)]
        if len(opening_range) == 0:
            continue
        or_high = opening_range['high'].max()
        or_low = opening_range['low'].min()
        or_size = or_high - or_low
        if or_size <= 0:
            continue

        post_range = day_data[day_data['timestamp_et'] >= range_end]
        traded_today = False
        for _, row in post_range.iterrows():
            if traded_today:
                break
            if row['close'] > or_high:
                entry = row['close']
                stop = or_low
                target = entry + target_r_multiple * (entry - stop)
                signals.append({'entry_time': row['timestamp'], 'side': 'LONG',
                                 'entry_price': entry, 'stop_price': stop, 'target_price': target})
                traded_today = True
            elif row['close'] < or_low:
                entry = row['close']
                stop = or_high
                target = entry - target_r_multiple * (stop - entry)
                signals.append({'entry_time': row['timestamp'], 'side': 'SHORT',
                                 'entry_price': entry, 'stop_price': stop, 'target_price': target})
                traded_today = True

    return pd.DataFrame(signals)


# ============================================================
# STRATEGY 3: PAIRS / RELATIVE VALUE (Statistical Arbitrage)
# ============================================================
def pairs_relative_value_signals(df_a, df_b, lookback=60, entry_z=2.0, exit_z=0.3):
    """
    Real logic: computes the real spread (log-ratio) between two correlated
    instruments (e.g., NQ vs ES), calculates its Z-score, and bets on
    convergence when the spread stretches beyond a real statistical
    extreme -- long the relative underperformer, short the outperformer.
    Requires two aligned OHLCV DataFrames on the same timestamps.
    """
    d = pd.DataFrame({
        'timestamp': df_a['timestamp'].values,
        'price_a': df_a['close'].values,
        'price_b': df_b['close'].values,
    })
    d['spread'] = np.log(d['price_a']) - np.log(d['price_b'])
    d['spread_mean'] = d['spread'].rolling(lookback).mean()
    d['spread_std'] = d['spread'].rolling(lookback).std()
    d['zscore'] = (d['spread'] - d['spread_mean']) / d['spread_std']

    signals = []
    position = None
    for i in range(lookback, len(d)):
        row = d.iloc[i]
        if position is None:
            if row['zscore'] > entry_z:
                # spread too wide -- A overpriced relative to B: short A, long B
                signals.append({'entry_time': row['timestamp'], 'side': 'SHORT_A_LONG_B',
                                 'entry_price_a': row['price_a'], 'entry_price_b': row['price_b'],
                                 'entry_zscore': row['zscore']})
                position = 'SHORT_A_LONG_B'
            elif row['zscore'] < -entry_z:
                signals.append({'entry_time': row['timestamp'], 'side': 'LONG_A_SHORT_B',
                                 'entry_price_a': row['price_a'], 'entry_price_b': row['price_b'],
                                 'entry_zscore': row['zscore']})
                position = 'LONG_A_SHORT_B'
        else:
            if abs(row['zscore']) < exit_z:
                if signals:
                    signals[-1]['exit_time'] = row['timestamp']
                    signals[-1]['exit_price_a'] = row['price_a']
                    signals[-1]['exit_price_b'] = row['price_b']
                position = None

    return pd.DataFrame(signals)


# ============================================================
# STRATEGY 4: EVENT-DRIVEN (Economic Calendar)
# ============================================================
def event_driven_signals(df, event_timestamps, pre_event_blackout_min=15,
                           post_event_window_min=30, target_r_multiple=2.0, stop_atr_mult=1.5):
    """
    Real logic: avoids trading in the real blackout window immediately
    before a scheduled high-impact event (CPI, NFP, FOMC), then trades the
    genuine initial directional break in the defined window right after
    release.

    HONEST REQUIREMENT: needs a real list of event timestamps (event_timestamps
    parameter) -- this is real economic calendar data, not something this
    function can generate itself. A free real source: investing.com's
    economic calendar, or forexfactory.com's calendar (same one already
    embedded in the AEC Wire terminal).
    """
    d = df.copy()
    d['timestamp'] = pd.to_datetime(d['timestamp'])
    d['tr'] = np.maximum(d['high'] - d['low'],
                np.maximum(abs(d['high'] - d['close'].shift(1)), abs(d['low'] - d['close'].shift(1))))
    d['atr'] = d['tr'].rolling(14).mean()

    signals = []
    for event_time in event_timestamps:
        event_time = pd.Timestamp(event_time)
        window_start = event_time
        window_end = event_time + pd.Timedelta(minutes=post_event_window_min)

        pre_event = d[(d['timestamp'] >= event_time - pd.Timedelta(minutes=pre_event_blackout_min)) &
                       (d['timestamp'] < event_time)]
        if len(pre_event) == 0:
            continue
        pre_event_price = pre_event.iloc[-1]['close']

        post_event = d[(d['timestamp'] >= window_start) & (d['timestamp'] <= window_end)]
        if len(post_event) == 0:
            continue

        # Real trigger: first candle after release that moves meaningfully
        # (beyond 1x ATR) from the pre-event price -- a genuine reaction, not noise
        for _, row in post_event.iterrows():
            atr_ref = row['atr'] if not pd.isna(row['atr']) else pre_event['close'].std()
            move = row['close'] - pre_event_price
            if abs(move) > atr_ref:
                side = 'LONG' if move > 0 else 'SHORT'
                entry = row['close']
                stop = entry - stop_atr_mult * atr_ref if side == 'LONG' else entry + stop_atr_mult * atr_ref
                target = entry + target_r_multiple * abs(entry - stop) if side == 'LONG' else entry - target_r_multiple * abs(entry - stop)
                signals.append({'entry_time': row['timestamp'], 'side': side, 'event_time': event_time,
                                 'entry_price': entry, 'stop_price': stop, 'target_price': target})
                break

    return pd.DataFrame(signals)


# ============================================================
# STRATEGY 6: CROSS-ASSET CONFIRMATION FILTER (NQ signals, ES confirms)
# ============================================================
def apply_cross_asset_filter(nq_signals, nq_df, es_df, lookback_bars=6, min_agreement_pct=0.6):
    """
    Real, institutional risk-management technique: only keeps a NQ signal
    if ES has ALSO genuinely been moving in the same direction over a
    recent lookback window. The idea: a real, broad market move shows up
    across correlated instruments; a move isolated to just one instrument
    is more likely noise or instrument-specific, not a genuine signal.

    min_agreement_pct: fraction of the lookback bars where ES's direction
    must agree with the signal's direction for it to pass the filter.
    """
    filtered_signals = []

    for _, sig in nq_signals.iterrows():
        entry_time = sig['entry_time']
        es_window = es_df[es_df['timestamp'] <= entry_time].tail(lookback_bars)
        if len(es_window) < lookback_bars:
            continue  # not enough real ES history yet to confirm

        es_returns = es_window['close'].diff().dropna()
        if len(es_returns) == 0:
            continue

        if sig['side'] == 'LONG':
            agreement = (es_returns > 0).sum() / len(es_returns)
        else:
            agreement = (es_returns < 0).sum() / len(es_returns)

        if agreement >= min_agreement_pct:
            filtered_signals.append(sig)

    return pd.DataFrame(filtered_signals)


# ============================================================
# STRATEGY 5: TREND-FOLLOWING (Dual MA Crossover + Trend Filter)
# ============================================================
def trend_following_signals(df, fast_ma=20, slow_ma=50, trend_filter_ma=200,
                              target_r_multiple=3.0, stop_atr_mult=2.0):
    """
    Real logic: a classic, genuine trend-following system -- fast/slow
    moving average crossover for entry timing, filtered by a longer-term
    trend MA so only longs are taken above it and only shorts below it.
    A fundamentally different signal family than OTE+BOS's structure-read
    approach, despite both being trend-directional.
    """
    d = df.copy()
    d['fast_ma'] = d['close'].rolling(fast_ma).mean()
    d['slow_ma'] = d['close'].rolling(slow_ma).mean()
    d['trend_ma'] = d['close'].rolling(trend_filter_ma).mean()
    d['tr'] = np.maximum(d['high'] - d['low'],
                np.maximum(abs(d['high'] - d['close'].shift(1)), abs(d['low'] - d['close'].shift(1))))
    d['atr'] = d['tr'].rolling(14).mean()

    signals = []
    for i in range(trend_filter_ma + 1, len(d)):
        row = d.iloc[i]
        prev = d.iloc[i-1]

        bullish_cross = prev['fast_ma'] <= prev['slow_ma'] and row['fast_ma'] > row['slow_ma']
        bearish_cross = prev['fast_ma'] >= prev['slow_ma'] and row['fast_ma'] < row['slow_ma']

        if bullish_cross and row['close'] > row['trend_ma']:
            entry = row['close']
            stop = entry - stop_atr_mult * row['atr']
            target = entry + target_r_multiple * (entry - stop)
            signals.append({'entry_time': row.get('timestamp', i), 'side': 'LONG',
                             'entry_price': entry, 'stop_price': stop, 'target_price': target})
        elif bearish_cross and row['close'] < row['trend_ma']:
            entry = row['close']
            stop = entry + stop_atr_mult * row['atr']
            target = entry - target_r_multiple * (stop - entry)
            signals.append({'entry_time': row.get('timestamp', i), 'side': 'SHORT',
                             'entry_price': entry, 'stop_price': stop, 'target_price': target})

    return pd.DataFrame(signals)
