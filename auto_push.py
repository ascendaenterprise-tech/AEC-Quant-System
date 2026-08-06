"""
AUTO-PUSH TO GITHUB -- watches trade_log.csv for changes, automatically
commits and pushes to your GitHub repo whenever it changes. This is
what makes the GitHub Pages dashboard update within seconds of a real
trade closing, instead of requiring you to manually git push each time.

SETUP REQUIRED FIRST (one-time):
1. This script must live INSIDE your git repo folder (the same one with
   index.html), not in intraday_pull -- or copy trade_log.csv there too.
2. Git must be configured to push WITHOUT asking for a password each
   time -- either an SSH key set up with GitHub, or a Personal Access
   Token saved via `git credential-manager` / Windows Credential Manager.
   If `git push` currently asks you to log in every time, that needs to
   be fixed first or this script will hang waiting for input.
3. Run `git remote -v` in that folder to confirm it's already linked to
   your GitHub repo.

Run with: python auto_push.py
Leave it running in its own terminal alongside the executor.
"""

import subprocess
import time
import os
import shutil

CHECK_INTERVAL_SEC = 15
SOURCE_TRADE_LOG = "C:/Users/Axiom/Desktop/intraday_pull/trade_log.csv"
REPO_TRADE_LOG = "trade_log.csv"  # relative to wherever this script runs FROM (should be the repo folder)


def get_file_hash(path):
    if not os.path.exists(path):
        return None
    return os.path.getmtime(path)


def sync_and_push():
    if not os.path.exists(SOURCE_TRADE_LOG):
        print(f"  source file not found: {SOURCE_TRADE_LOG}")
        return False
    shutil.copy(SOURCE_TRADE_LOG, REPO_TRADE_LOG)

    result = subprocess.run(["git", "add", REPO_TRADE_LOG], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  git add failed: {result.stderr}")
        return False

    result = subprocess.run(
        ["git", "commit", "-m", f"auto-update trade_log.csv {time.strftime('%Y-%m-%d %H:%M:%S')}"],
        capture_output=True, text=True
    )
    if "nothing to commit" in result.stdout:
        return False  # no real change, don't push
    if result.returncode != 0:
        print(f"  git commit failed: {result.stderr}")
        return False

    result = subprocess.run(["git", "push"], capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        print(f"  git push failed: {result.stderr}")
        return False

    print(f"  pushed successfully at {time.strftime('%H:%M:%S')}")
    return True


if __name__ == "__main__":
    print("Auto-push watcher started. Checking for changes every "
          f"{CHECK_INTERVAL_SEC}s.\n")
    print("Verify first: are you running this FROM your git repo folder "
          "(the one with index.html)? If not, Ctrl+C and cd there first.\n")

    last_mtime = None
    try:
        while True:
            current_mtime = get_file_hash(SOURCE_TRADE_LOG)
            if current_mtime is not None and current_mtime != last_mtime:
                print(f"[{time.strftime('%H:%M:%S')}] trade_log.csv changed, syncing...")
                if sync_and_push():
                    last_mtime = current_mtime
            time.sleep(CHECK_INTERVAL_SEC)
    except KeyboardInterrupt:
        print("\nStopped.")
