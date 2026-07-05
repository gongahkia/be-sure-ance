from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from src.backend import helper
from src.lib.http_identity import BROWSER_USER_AGENT
from src.lib.mas_regulatory import (
    MAS_ENFORCEMENT_URL,
    MAS_NEWS_URL,
    direct_mas_news_items,
    extract_events_from_text,
    extract_date,
    is_mas_unavailable,
    parse_mas_news_listing,
)
from src.lib.scraper_health import record_scraper_failure, record_scraper_success

REQUEST_TIMEOUT_SECONDS = 30
MAX_DETAIL_PAGES = 20


def fetch_html(url: str, session=requests) -> str:
    try:
        response = session.get(
            url,
            timeout=REQUEST_TIMEOUT_SECONDS,
            headers={"User-Agent": BROWSER_USER_AGENT},
        )
        response.raise_for_status()
    except requests.RequestException as error:
        raise RuntimeError(f"MAS source unavailable: {url}: {error}") from error
    text = response.text
    if is_mas_unavailable(text):
        raise RuntimeError(f"MAS source unavailable: {url}")
    return text


def html_text(html: str) -> str:
    return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)


def scrape_mas_regulatory_events(session=requests, scraped_at: str | None = None):
    scraped_at = scraped_at or datetime.now(timezone.utc).isoformat()
    errors = []
    news_items = []
    for source_url in (MAS_NEWS_URL, MAS_ENFORCEMENT_URL):
        try:
            listing_html = fetch_html(source_url, session=session)
        except RuntimeError as error:
            errors.append(str(error))
            print(error)
            continue
        news_items.extend(parse_mas_news_listing(listing_html))
    news_items.extend(direct_mas_news_items())
    news_items = dedupe_news_items(news_items)

    if not news_items:
        if errors:
            record_scraper_failure(
                "mas_regulatory",
                "; ".join(errors),
                dry_run=helper.dry_run_enabled(),
            )
        return []

    news_items = news_items[:MAX_DETAIL_PAGES]
    events = []
    for item in news_items:
        try:
            detail_html = fetch_html(item.source_url, session=session)
        except RuntimeError as error:
            errors.append(str(error))
            print(error)
            continue
        detail_text = html_text(detail_html)
        published_at = item.published_at or extract_date(detail_text) or extract_date(item.title)
        if not published_at:
            errors.append(f"MAS source missing published date: {item.source_url}")
            continue
        events.extend(
            extract_events_from_text(
                title=item.title,
                text=detail_text,
                source_url=item.source_url,
                published_at=published_at,
                scraped_at=scraped_at,
            )
        )
    if not events and errors:
        record_scraper_failure(
            "mas_regulatory",
            "; ".join(errors),
            dry_run=helper.dry_run_enabled(),
        )
    return events


def dedupe_news_items(items):
    seen = set()
    deduped = []
    for item in items:
        if item.source_url in seen:
            continue
        seen.add(item.source_url)
        deduped.append(item)
    return deduped


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
    record_scraper_success("mas_regulatory", len(rows))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.parse_known_args()
    helper.initialize_data_store()
    events = scrape_mas_regulatory_events()
    upsert_mas_regulatory_events(events)


if __name__ == "__main__":
    main()
