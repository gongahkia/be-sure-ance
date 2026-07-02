from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from src.backend import helper
from src.lib.http_identity import BOT_USER_AGENT
from src.lib.mas_regulatory import (
    MAS_NEWS_URL,
    extract_events_from_text,
    parse_mas_news_listing,
)

REQUEST_TIMEOUT_SECONDS = 30
MAX_DETAIL_PAGES = 20


def fetch_html(url: str, session=requests) -> str:
    response = session.get(
        url,
        timeout=REQUEST_TIMEOUT_SECONDS,
        headers={"User-Agent": BOT_USER_AGENT},
    )
    response.raise_for_status()
    text = response.text
    if "Sorry, this service is currently unavailable" in text:
        raise RuntimeError(f"MAS source unavailable: {url}")
    return text


def html_text(html: str) -> str:
    return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)


def scrape_mas_regulatory_events(session=requests, scraped_at: str | None = None):
    scraped_at = scraped_at or datetime.now(timezone.utc).isoformat()
    try:
        listing_html = fetch_html(MAS_NEWS_URL, session=session)
    except RuntimeError as error:
        print(error)
        return []
    news_items = parse_mas_news_listing(listing_html)[:MAX_DETAIL_PAGES]
    events = []
    for item in news_items:
        try:
            detail_html = fetch_html(item.source_url, session=session)
        except RuntimeError as error:
            print(error)
            continue
        detail_text = html_text(detail_html)
        events.extend(
            extract_events_from_text(
                title=item.title,
                text=detail_text,
                source_url=item.source_url,
                published_at=item.published_at,
                scraped_at=scraped_at,
            )
        )
    return events


def upsert_mas_regulatory_events(events) -> None:
    rows = [event.as_row() for event in events]
    if helper.dry_run_enabled():
        print(json.dumps({"mas_regulatory_event_count": len(rows)}, indent=2))
        return
    if not rows:
        print("No MAS regulatory events to upsert.")
        return

    helper.require_write_key()
    response = (
        helper.require_client()
        .table("mas_regulatory_events")
        .upsert(rows, on_conflict="carrier_key,event_title,source_url")
        .execute()
    )
    if response.data is None:
        raise RuntimeError("MAS regulatory event upsert returned no data.")
    print(f"MAS regulatory events upserted: {len(rows)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.parse_known_args()
    helper.initialize_data_store()
    events = scrape_mas_regulatory_events()
    upsert_mas_regulatory_events(events)


if __name__ == "__main__":
    main()
