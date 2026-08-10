"""
PULL REAL 13F WHALE DATA FROM SEC EDGAR -- server-side script (required,
since data.sec.gov explicitly does not support CORS -- confirmed directly
from SEC.gov's own documentation, browser JS cannot query this API at all).

Outputs a static JSON snapshot that the terminal reads client-side. Not
live-live -- updates whenever this script is rerun and pushed, same
honest pattern as trade_log.csv and system_status.json.

IMPORTANT: SEC requires a real, working User-Agent identifying you --
replace YOUR_NAME and YOUR_EMAIL below before running. Fake/generic
User-Agents get your IP blocked for ~10 minutes per SEC's own policy.

Run with: python pull_13f_whales.py
Produces: whales_13f.json
"""

import requests
import json
import time
import xml.etree.ElementTree as ET

HEADERS = {"User-Agent": "AEC Quant System YOUR_NAME YOUR_EMAIL@example.com"}

WHALES = {
    "Berkshire Hathaway": "0001067983",
    "Bridgewater Associates": "0001350694",
    "Renaissance Technologies": "0001037389",
    "Pershing Square": "0001336528",
    "Third Point": "0001040273",
    "Citadel Advisors": "0001423053",
}


def get_latest_13f_filing(cik):
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    if resp.status_code != 200:
        print(f"  failed ({resp.status_code}) for CIK {cik}")
        return None
    data = resp.json()
    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    accession_numbers = recent.get("accessionNumber", [])
    dates = recent.get("filingDate", [])
    for i, form in enumerate(forms):
        if form == "13F-HR":
            return {"accession_number": accession_numbers[i], "filing_date": dates[i], "cik": cik}
    return None


def get_holdings(cik, accession_number):
    """Fetch and parse the real information table (actual holdings) for a filing."""
    acc_nodash = accession_number.replace("-", "")
    index_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_nodash}/"
    resp = requests.get(index_url, headers=HEADERS, timeout=15)
    if resp.status_code != 200:
        return []

    # find the information table XML filename from the index page
    import re
    xml_files = re.findall(r'href="[^"]*?(\w+\.xml)"', resp.text)
    info_table_file = None
    for f in xml_files:
        if "form13f" in f.lower() or "infotable" in f.lower():
            info_table_file = f
            break
    if not info_table_file:
        return []

    table_url = index_url + info_table_file
    resp = requests.get(table_url, headers=HEADERS, timeout=15)
    if resp.status_code != 200:
        return []

    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError:
        return []

    ns = {"n": "http://www.sec.gov/edgar/document/thirteenf/informationtable"}
    holdings = []
    for entry in root.findall(".//n:infoTable", ns):
        name = entry.findtext("n:nameOfIssuer", default="", namespaces=ns)
        value = entry.findtext("n:value", default="0", namespaces=ns)
        shares = entry.findtext(".//n:sshPrnamt", default="0", namespaces=ns)
        put_call = entry.findtext("n:putCall", default="", namespaces=ns)
        holdings.append({
            "issuer": name, "value_thousands": int(value) if value.isdigit() else 0,
            "shares": int(shares) if shares.isdigit() else 0, "put_call": put_call,
        })

    holdings.sort(key=lambda h: h["value_thousands"], reverse=True)
    return holdings[:15]  # top 15 real positions


results = {}
for name, cik in WHALES.items():
    print(f"Fetching {name} (CIK {cik})...")
    filing = get_latest_13f_filing(cik)
    if filing:
        print(f"  latest 13F-HR: {filing['filing_date']}, fetching real holdings...")
        holdings = get_holdings(cik, filing["accession_number"])
        filing["top_holdings"] = holdings
        results[name] = filing
        print(f"  got {len(holdings)} real positions")
    time.sleep(0.5)

output = {
    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "note": "Real SEC EDGAR 13F data. Not live -- reflects whenever this script was last run.",
    "whales": results,
}

with open("whales_13f.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"\nSaved {len(results)} whale filings with real holdings to whales_13f.json")
