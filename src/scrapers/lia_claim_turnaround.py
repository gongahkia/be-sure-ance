from __future__ import annotations

import argparse
import io
import json
import logging
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

from src.backend import helper
from src.lib.http_identity import BOT_USER_AGENT
from src.lib.lia_claim_turnaround import (
    LIA_2024_RESULTS_URL,
    LIA_2025_RESULTS_URL,
    LIA_MAKING_CLAIM_URL,
    parse_annual_claim_payouts,
    parse_claim_handling_standards,
)

REQUEST_TIMEOUT_SECONDS = 30
logging.getLogger("pypdf").setLevel(logging.ERROR)
ANNUAL_REPORTS = [
    (2025, LIA_2025_RESULTS_URL),
    (2024, LIA_2024_RESULTS_URL),
]


def fetch_source_text(url: str, session=requests) -> str:
    response = session.get(
        url,
        timeout=REQUEST_TIMEOUT_SECONDS,
        headers={"User-Agent": BOT_USER_AGENT},
    )
    response.raise_for_status()

    content_type = response.headers.get("content-type", "").lower()
    if "pdf" in content_type or url.lower().endswith(".pdf"):
        return pdf_text(response.content)
    return html_text(response.text)


def pdf_text(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def html_text(content: str) -> str:
    return BeautifulSoup(content, "html.parser").get_text(" ", strip=True)


def scrape_claim_turnaround_metrics(session=requests, scraped_at: str | None = None):
    scraped_at = scraped_at or datetime.now(timezone.utc).isoformat()
    rows = []
    claim_text = fetch_source_text(LIA_MAKING_CLAIM_URL, session=session)
    rows.extend(
        parse_claim_handling_standards(
            claim_text,
            source_url=LIA_MAKING_CLAIM_URL,
            source_year=datetime.now(timezone.utc).year,
            scraped_at=scraped_at,
        )
    )

    for source_year, source_url in ANNUAL_REPORTS:
        report_text = fetch_source_text(source_url, session=session)
        rows.extend(
            parse_annual_claim_payouts(
                report_text,
                source_url=source_url,
                source_year=source_year,
                scraped_at=scraped_at,
            )
        )
    return rows


def upsert_claim_turnaround_metrics(metrics) -> None:
    rows = [metric.as_row() for metric in metrics]
    if helper.dry_run_enabled():
        print(json.dumps({"claim_turnaround_metric_count": len(rows)}, indent=2))
        return
    if not rows:
        print("No LIA claim turnaround rows to upsert.")
        return

    helper.require_write_key()
    response = (
        helper.require_client()
        .table("claim_turnaround_metrics")
        .upsert(rows, on_conflict="carrier_key,metric_key,source_year,source_url")
        .execute()
    )
    if response.data is None:
        raise RuntimeError("Claim turnaround metric upsert returned no data.")
    print(f"Claim turnaround metrics upserted: {len(rows)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.parse_known_args()
    helper.initialize_supabase()
    metrics = scrape_claim_turnaround_metrics()
    upsert_claim_turnaround_metrics(metrics)


if __name__ == "__main__":
    main()
