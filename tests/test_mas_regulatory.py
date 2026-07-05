import unittest
from pathlib import Path

from bs4 import BeautifulSoup

from src.lib.http_identity import BROWSER_USER_AGENT
from src.lib.mas_regulatory import (
    MAS_BASE_URL,
    MAS_DIRECT_NEWS_ITEMS,
    MATCHED_STATUS,
    NEEDS_REVIEW_STATUS,
    direct_mas_news_items,
    extract_events_from_text,
    is_mas_unavailable,
    parse_mas_news_listing,
)
from src.scrapers.mas_regulatory import scrape_mas_regulatory_events

ROOT = Path(__file__).resolve().parents[1]
LISTING = (ROOT / "tests/fixtures/mas_regulatory_listing.html").read_text()
DETAIL = BeautifulSoup(
    (ROOT / "tests/fixtures/mas_regulatory_detail.html").read_text(),
    "html.parser",
).get_text(" ", strip=True)


class MasRegulatoryTests(unittest.TestCase):
    def test_listing_parser_extracts_source_link_and_published_date(self):
        items = parse_mas_news_listing(LISTING)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].published_at, "2026-07-01")
        self.assertEqual(
            items[0].source_url,
            f"{MAS_BASE_URL}/news/media-releases/2026/key-enforcement-actions-taken-by-mas-in-q2-2026",
        )

    def test_event_extraction_tags_high_and_low_confidence_matches(self):
        events = extract_events_from_text(
            title="Key Enforcement Actions Taken by MAS in Q2 2026",
            text=DETAIL,
            source_url="https://www.mas.gov.sg/news/media-releases/2026/key",
            published_at="2026-07-01",
            scraped_at="2026-07-02T00:00:00+00:00",
        )

        by_carrier = {event.carrier_key: event for event in events}
        self.assertEqual(by_carrier["aia"].match_status, MATCHED_STATUS)
        self.assertEqual(by_carrier["aia"].match_confidence, 0.95)
        self.assertEqual(by_carrier["aia"].event_type, "composition_penalty")
        self.assertEqual(by_carrier["aia"].event_date, "2026-05-25")
        self.assertEqual(by_carrier["income"].match_status, NEEDS_REVIEW_STATUS)
        self.assertEqual(by_carrier["income"].match_confidence, 0.7)
        self.assertEqual(by_carrier["income"].event_type, "reprimand")
        self.assertEqual(by_carrier["income"].event_date, "2026-05-18")

    def test_event_rows_are_source_linked_and_dated(self):
        row = extract_events_from_text(
            title="MAS issued a reprimand to AIA Singapore Private Limited",
            text="01 July 2026 MAS issued a reprimand to AIA Singapore Private Limited.",
            source_url="https://www.mas.gov.sg/news/media-releases/2026/aia",
            published_at="2026-07-01",
            scraped_at="2026-07-02T00:00:00+00:00",
        )[0].as_row()

        self.assertEqual(row["source_url"], "https://www.mas.gov.sg/news/media-releases/2026/aia")
        self.assertEqual(row["event_date"], "2026-07-01")
        self.assertEqual(row["source_published_at"], "2026-07-01")
        self.assertEqual(row["match_status"], MATCHED_STATUS)
        self.assertIn("not advice", row["limitations"][0])

    def test_direct_catalog_contains_quarterly_official_releases(self):
        items = direct_mas_news_items()
        urls = [item.source_url for item in items]

        self.assertGreaterEqual(len(items), 6)
        self.assertIn(MAS_DIRECT_NEWS_ITEMS[0][1], urls)

    def test_maintenance_pages_are_source_unavailable(self):
        self.assertTrue(is_mas_unavailable("<title>Maintenance</title>"))
        self.assertTrue(is_mas_unavailable("This site is currently undergoing scheduled maintenance."))

    def test_direct_catalog_is_used_when_listing_pages_are_unavailable(self):
        seen_user_agents = []

        class Response:
            def __init__(self, text):
                self.text = text

            def raise_for_status(self):
                return None

        class Session:
            def get(self, url, timeout, headers):
                seen_user_agents.append(headers.get("User-Agent"))
                if url == MAS_DIRECT_NEWS_ITEMS[0][1]:
                    return Response((ROOT / "tests/fixtures/mas_regulatory_detail.html").read_text())
                return Response("<title>Maintenance</title>")

        events = scrape_mas_regulatory_events(
            session=Session(),
            scraped_at="2026-07-02T00:00:00+00:00",
        )
        by_carrier = {event.carrier_key: event for event in events}

        self.assertIn("aia", by_carrier)
        self.assertEqual(by_carrier["aia"].source_url, MAS_DIRECT_NEWS_ITEMS[0][1])
        self.assertEqual(set(seen_user_agents), {BROWSER_USER_AGENT})


if __name__ == "__main__":
    unittest.main()
