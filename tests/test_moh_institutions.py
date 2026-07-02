import json
import unittest
from pathlib import Path

from src.lib.moh_institutions import (
    NEHR_API_URL,
    NEHR_DATASET_ID,
    NEHR_DATASET_URL,
    fetch_nehr_records,
    normalize_panel_name,
    parse_institution_records,
    record_to_row,
)
from src.scrapers.brochure_facts import parse_brochure_text

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / "tests/fixtures/moh_nehr_records.json").read_text())
RECORDS = parse_institution_records(FIXTURE["result"]["records"])


class FakeResponse:
    def __init__(self, status_code=200):
        self.status_code = status_code
        self.headers = {"retry-after": "0"} if status_code == 429 else {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")
        return None

    def json(self):
        return FIXTURE


class FakeSession:
    def __init__(self):
        self.urls = []

    def get(self, url, timeout, headers):
        self.urls.append(url)
        self.timeout = timeout
        self.headers = headers
        return FakeResponse()


class RateLimitedSession(FakeSession):
    def get(self, url, timeout, headers):
        self.urls.append(url)
        self.timeout = timeout
        self.headers = headers
        return FakeResponse(status_code=429 if len(self.urls) == 1 else 200)


class MOHInstitutionTests(unittest.TestCase):
    def test_fetch_nehr_records_uses_data_gov_dataset_api(self):
        session = FakeSession()
        rows = fetch_nehr_records(session=session, limit=4)

        self.assertEqual(len(rows), 4)
        self.assertTrue(session.urls[0].startswith(NEHR_API_URL))
        self.assertIn(f"resource_id={NEHR_DATASET_ID}", session.urls[0])
        self.assertEqual(session.timeout, 30)
        self.assertIn("be-sure-ance-bot", session.headers["User-Agent"])

    def test_fetch_nehr_records_retries_rate_limits(self):
        session = RateLimitedSession()
        rows = fetch_nehr_records(session=session, limit=4)

        self.assertEqual(len(rows), 4)
        self.assertEqual(len(session.urls), 2)

    def test_nehr_records_expand_parenthetical_institutions(self):
        names = {record.canonical_name for record in RECORDS}

        self.assertIn("Singapore General Hospital", names)
        self.assertIn("Tan Tock Seng Hospital", names)
        self.assertIn("National University Hospital", names)
        self.assertIn("Ang Mo Kio - Thye Kwan Hospital Ltd.", names)

    def test_rows_keep_source_ids_and_aliases(self):
        record = next(
            item for item in RECORDS if item.canonical_name == "Singapore General Hospital"
        )
        row = record_to_row(record, scraped_at="2026-07-02T00:00:00Z")

        self.assertEqual(row["canonical_id"], "nehr-4-singapore-general-hospital")
        self.assertEqual(row["source_dataset_id"], NEHR_DATASET_ID)
        self.assertEqual(row["source_url"], NEHR_DATASET_URL)
        self.assertIn("Singapore General Hospital", row["aliases"])

    def test_known_hospital_variation_normalizes_with_confidence(self):
        match = normalize_panel_name("Singapore Gen Hospital", RECORDS)

        self.assertEqual(match["normalized_name"], "Singapore General Hospital")
        self.assertEqual(match["match_status"], "matched")
        self.assertGreaterEqual(match["match_confidence"], 88)
        self.assertFalse(match["review_required"])

    def test_uncertain_matches_are_reviewable(self):
        match = normalize_panel_name("Example Medical Centre", RECORDS)

        self.assertEqual(match["normalized_name"], "Example Medical Centre")
        self.assertEqual(match["match_status"], "needs_review")
        self.assertTrue(match["review_required"])
        self.assertIsNone(match["canonical_id"])
        self.assertEqual(match["suggested_normalized_name"], "Admiralty Medical Centre")

    def test_unmatched_names_are_reviewable(self):
        match = normalize_panel_name("ZZZ Unknown Facility", RECORDS)

        self.assertEqual(match["normalized_name"], "ZZZ Unknown Facility")
        self.assertEqual(match["match_status"], "unmatched")
        self.assertTrue(match["review_required"])
        self.assertIsNone(match["canonical_id"])

    def test_brochure_panel_hospitals_use_moh_normalization(self):
        parsed = parse_brochure_text(
            "Panel Hospitals: Singapore Gen Hospital; Tan Tock Seng Hosp; Example Medical Centre.",
            institution_records=RECORDS,
        )
        items = parsed["panel_hospitals"]["items"]

        self.assertEqual(items[0]["normalized_name"], "Singapore General Hospital")
        self.assertEqual(items[0]["match_status"], "matched")
        self.assertEqual(items[1]["normalized_name"], "Tan Tock Seng Hospital")
        self.assertIn(items[1]["match_status"], {"matched", "needs_review"})
        self.assertEqual(items[2]["match_status"], "needs_review")
        self.assertEqual(items[2]["normalized_name"], "Example Medical Centre")
        self.assertTrue(parsed["panel_hospitals"]["review_required"])


if __name__ == "__main__":
    unittest.main()
