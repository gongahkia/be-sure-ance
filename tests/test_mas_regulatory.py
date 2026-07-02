import unittest
from pathlib import Path

from bs4 import BeautifulSoup

from src.lib.mas_regulatory import (
    MAS_BASE_URL,
    MATCHED_STATUS,
    NEEDS_REVIEW_STATUS,
    extract_events_from_text,
    parse_mas_news_listing,
)

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


if __name__ == "__main__":
    unittest.main()
