"""Traceable latest 10-Q/10-K filing pointers and equity-note review gates.

SEC submissions lists forms/URLs but does NOT certify that cover shares,
dilution, convertible classes, equity award footnotes or subsequent events have
been reviewed. Always demand manual note reconciliation.
"""
import datetime as dt

TOPICS = [
    "Consolidated statements of stockholders' equity",
    "Earnings per share / weighted average diluted shares",
    "Stock-based compensation and anti-dilutive awards",
    "Share repurchase authorizations and subsequent repurchases",
    "Convertible or exchangeable classes and noncontrolling interests",
    "Subsequent events, splits and share issuances",
]


def latest_equity_filings(submissions, cik, as_of):
    current = submissions.get("filings", {}).get("recent", {})
    keys = ("form", "accessionNumber", "primaryDocument", "filingDate",
            "reportDate")
    size = min((len(current.get(k, [])) for k in keys), default=0)
    filings = []
    for i in range(size):
        form = current["form"][i]
        if form not in ("10-K", "10-Q", "10-K/A", "10-Q/A"):
            continue
        try:
            filed = dt.date.fromisoformat(current["filingDate"][i])
            if filed > as_of:continue
            accession = current["accessionNumber"][i]
            primary = current["primaryDocument"][i]
            if not accession or not primary or "/" in primary or ".." in primary:
                continue
            base = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}"
            filings.append({
                "form": form, "filed": str(filed),
                "fiscal_period_end": current["reportDate"][i],
                "accession": accession,
                "primary_document": primary,
                "document_url": f"{base}/{primary}",
                "filing_index_url": f"{base}/{accession}-index.html",
                "document_review_status": "not_reviewed",
            })
            if len(filings)>=3:break
        except (ValueError, KeyError, TypeError):continue
    return {
        "schema": "ciip-capital-notes-v1",
        "status": "document_links_only_manual_review",
        "filings": filings,
        "review_topics": TOPICS,
        "reviewed_notes": [],
        "notes_conclusion": None,
        "verified_current_fully_diluted_shares": None,
        "warning": (
            "SEC filing pointers are verified against submissions metadata only. "
            "No equity/option/convertible notes were extracted or legally/accountingly reconciled; "
            "current fully diluted shares MUST NOT be represented as verified."
        ),
    }
