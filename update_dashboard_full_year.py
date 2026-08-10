"""
UPDATE trade_log.csv WITH THE FULL-YEAR BACKTEST -- replaces the old
5-month backtest rows entirely (superseded by this larger dataset),
leaves all real 'live' trades untouched.
"""

import pandas as pd
import os

LIVE_LOG = "trade_log.csv"
NEW_BACKTEST_FILE = "backtest_results_full_year.csv"

df_current = pd.read_csv(LIVE_LOG)

df_live_only = df_current[df_current["source"] == "live"].copy()
old_backtest_count = (df_current["source"] == "backtest").sum()
print(f"Keeping {len(df_live_only)} real live trades.")
print(f"Removing {old_backtest_count} old backtest rows (superseded by the new full-year data).")

df_bt = pd.read_csv(NEW_BACKTEST_FILE)
df_bt["entry_time"] = pd.to_datetime(df_bt["entry_time"])
df_bt["exit_time"] = pd.to_datetime(df_bt["exit_time"])
duration_sec = (df_bt["exit_time"] - df_bt["entry_time"]).dt.total_seconds()

df_bt_formatted = pd.DataFrame({
    "trade_id": [f"{row.system}_{row.entry_time.isoformat()}" for row in df_bt.itertuples()],
    "entry_timestamp": df_bt["entry_time"].apply(lambda x: x.isoformat()),
    "symbol": "NQ",
    "side": df_bt["side"],
    "entry_price": df_bt["entry_price"],
    "exit_price": df_bt["exit_price"],
    "qty": 1,
    "pnl": df_bt["pnl"],
    "duration_sec": duration_sec,
    "was_intended_as_system_signal": True,
    "matched_signal": True,
    "notes": df_bt["system"] + " backtest (full year) - " + df_bt["reason"],
    "source": "backtest",
})

print(f"Loaded {len(df_bt_formatted)} new backtest trades (Layer I + OTE+BOS, full year).")

df_merged = pd.concat([df_live_only, df_bt_formatted], ignore_index=True)
df_merged.to_csv(LIVE_LOG, index=False)

print(f"\nDone. {LIVE_LOG} now has {len(df_merged)} total rows "
      f"({len(df_live_only)} live + {len(df_bt_formatted)} backtest, full year).")
