import unittest
from pathlib import Path

from src.lib.lia_claim_turnaround import (
    LIA_2025_RESULTS_URL,
    LIA_MAKING_CLAIM_URL,
    NO_CARRIER_RANKING_LIMITATION,
    normalize_carrier_name,
    parse_annual_claim_payouts,
    parse_claim_handling_standards,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_TEXT = (ROOT / "tests/fixtures/lia_claims_report.txt").read_text()


class LiaClaimTurnaroundTests(unittest.TestCase):
    def test_claim_handling_standards_parse_public_lia_timelines(self):
        rows = parse_claim_handling_standards(
            FIXTURE_TEXT,
            source_url=LIA_MAKING_CLAIM_URL,
            source_year=2026,
            scraped_at="2026-07-02T00:00:00+00:00",
        )

        values = {row.metric_key: row.metric_value["value"] for row in rows}
        self.assertEqual(values["notice_deadline"]["days"], 30)
        self.assertEqual(values["acknowledge_notice"]["days"], 7)
        self.assertEqual(values["request_information"]["days"], 14)
        self.assertEqual(values["claim_decision"]["days"], 21)
        self.assertEqual(values["straightforward_payment"]["days"], 14)
        self.assertEqual(values["death_claim_interest"]["months"], 2)

    def test_annual_claim_payouts_parse_lia_full_year_report(self):
        rows = parse_annual_claim_payouts(
            FIXTURE_TEXT,
            source_url=LIA_2025_RESULTS_URL,
            source_year=2025,
            scraped_at="2026-07-02T00:00:00+00:00",
        )

        values = {row.metric_key: row.metric_value["value"] for row in rows}
        self.assertEqual(values["industry_claims_maturity_payouts"]["amount_sgd_billion"], 14.23)
        self.assertEqual(values["industry_death_tpd_ci_claims"]["amount_sgd_billion"], 2.05)
        self.assertEqual(values["industry_maturity_payouts"]["amount_sgd_billion"], 12.17)

    def test_rows_are_unranked_when_lia_source_is_industry_aggregate(self):
        row = parse_annual_claim_payouts(
            FIXTURE_TEXT,
            source_url=LIA_2025_RESULTS_URL,
            source_year=2025,
            scraped_at="2026-07-02T00:00:00+00:00",
        )[0].as_row()

        self.assertIsNone(row["rank"])
        self.assertEqual(row["carrier_key"], "industry")
        self.assertEqual(row["source_year"], 2025)
        self.assertEqual(row["source_url"], LIA_2025_RESULTS_URL)
        self.assertIn(NO_CARRIER_RANKING_LIMITATION, row["limitations"])

    def test_carrier_name_normalization_has_future_carrier_hooks(self):
        self.assertEqual(
            normalize_carrier_name("The Great Eastern Life Assurance Company Limited"),
            ("great_eastern", "Great Eastern Singapore"),
        )
        self.assertEqual(
            normalize_carrier_name("AIA Singapore Private Limited"),
            ("aia", "AIA Singapore"),
        )


if __name__ == "__main__":
    unittest.main()
