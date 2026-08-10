"""
MERGE BACKTEST RESULTS INTO trade_log.csv -- adds a 'source' column
('live' vs 'backtest') so both are visible on the same dashboard, clearly
distinguishable. Run this from inside your cloned AEC-Quant-System folder.
"""

import pandas as pd
import os

LIVE_LOG = "trade_log.csv"
BACKTEST_FILE = "backtest_results_5month.csv"

if os.path.exists(LIVE_LOG):
    df_live = pd.read_csv(LIVE_LOG)
    df_live["source"] = "live"
    print(f"Loaded {len(df_live)} real live trades.")
else:
    df_live = pd.DataFrame(columns=["trade_id","entry_timestamp","symbol","side",
                                      "entry_price","exit_price","qty","pnl","duration_sec",
                                      "was_intended_as_system_signal","matched_signal","notes","source"])
    print("No existing trade_log.csv found -- starting fresh with live trades only.")

df_bt = pd.read_csv(BACKTEST_FILE)
df_bt = df_bt[df_bt["system"].isin(["Layer I", "OTE+BOS"])].copy()

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
    "notes": df_bt["system"] + " backtest - " + df_bt["reason"],
    "source": "backtest",
})

print(f"Loaded {len(df_bt_formatted)} backtest trades (Layer I + OTE+BOS).")

df_merged = pd.concat([df_live, df_bt_formatted], ignore_index=True)
df_merged.to_csv(LIVE_LOG, index=False)

print(f"\nDone. {LIVE_LOG} now has {len(df_merged)} total rows "
      f"({len(df_live)} live + {len(df_bt_formatted)} backtest).")
print("Both are tagged in the 'source' column so they're always distinguishable.")

