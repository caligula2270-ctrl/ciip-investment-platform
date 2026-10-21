#!/usr/bin/env python3
"""US daily closes from Stooq. Old dated quotes remain if upstream is unavailable."""
import csv
import io
import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DEST = Path(__file__).with_name("prices.json")
SYMBOLS = ["CPRT", "AMZN", "COST", "KNSL", "ADBE", "ASML", "AAON", "DE", "DHR", "FIVE", "FOUR", "FRPH", "INTU", "KEYS", "MEDP", "RMD", "STVN", "TRUP", "TXN", "ZTS", "GLNG"]
raw = json.loads(DEST.read_text()) if DEST.exists() else {"quotes": {}}
quotes = raw.setdefault("quotes", {})
success = 0
for ticker in SYMBOLS:
    url = "https://stooq.com/q/d/l/?s=" + ticker.lower() + ".us&i=d"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 QualityValueRadar/1.0"})
        with urllib.request.urlopen(req, timeout=18) as f:
            rows = list(csv.DictReader(io.StringIO(f.read().decode("utf-8-sig"))))
        if not rows:
            raise ValueError("no price")
        row = rows[-1]
        date = row["Date"]
        price = float(row["Close"])
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date) or price <= 0:
            raise ValueError("invalid daily close")
        previous = quotes.get(ticker, {})
        if date >= previous.get("date", ""):
            quotes[ticker] = {"price": round(price, 4), "currency": "USD", "date": date, "source": "Stooq / daily close", "sourceUrl": "https://stooq.com/q/?s=" + ticker.lower() + ".us"}
        success += 1
    except Exception as exc:
        print("WARN", ticker, str(exc)[:160])
raw["attemptedSymbols"] = len(SYMBOLS)
raw["successfulSymbols"] = success
raw["lastAttemptUTC"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
DEST.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n")
print("Updated:", success, "of", len(SYMBOLS))
if success == 0:
    raise SystemExit("All providers failed; existing dated prices preserved")
