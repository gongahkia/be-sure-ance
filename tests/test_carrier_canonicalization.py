import unittest

from src.lib.carrier_canonicalization import (
    LIA_MEMBER_COMPANIES_URL,
    MAS_FID_INSURANCE_URL,
    MATCHED_STATUS,
    NEEDS_REVIEW_STATUS,
    UNMATCHED_STATUS,
    build_canonical_records,
    parse_lia_member_records,
    parse_mas_fid_records,
)

MAS_HTML = """
<div class="result-list resize">
  <div class="inner">
    <a href="/fid/institution/detail/2452-AIA-SINGAPORE-PRIVATE-LIMITED">
      <h3 class="header-inner-2">AIA SINGAPORE PRIVATE LIMITED</h3>
    </a>
    <div class="category">
      <span>Direct Insurer (Composite)</span>
      <span>Exempt Financial Adviser</span>
    </div>
  </div>
  <div class="inner">
    <a href="/fid/institution/detail/999-AIA-FINANCIAL-ADVISERS-PRIVATE-LIMITED">
      <h3 class="header-inner-2">AIA FINANCIAL ADVISERS PRIVATE LIMITED</h3>
    </a>
    <div class="category"><span>Licensed Financial Adviser</span></div>
  </div>
</div>
"""

LIA_HTML = """
<h3>Ordinary Members</h3>
<p><a href="https://www.aia.com.sg">AIA Singapore Private Limited</a></p>
<p><a href="https://singlife.com/">Singapore Life Ltd.</a></p>
<h3>Associate Members</h3>
<p><a href="https://example.com/reinsurer">Example Reinsurer</a></p>
"""


class CarrierCanonicalizationTests(unittest.TestCase):
    def test_parse_mas_fid_result_cards(self):
        records = parse_mas_fid_records(MAS_HTML, MAS_FID_INSURANCE_URL)

        self.assertEqual(records[0].name, "AIA SINGAPORE PRIVATE LIMITED")
        self.assertIn("Direct Insurer (Composite)", records[0].licence_types)
        self.assertTrue(records[0].detail_url.endswith("2452-AIA-SINGAPORE-PRIVATE-LIMITED"))

    def test_parse_lia_ordinary_members_only(self):
        records = parse_lia_member_records(LIA_HTML, LIA_MEMBER_COMPANIES_URL)
        names = [record.name for record in records]

        self.assertIn("AIA Singapore Private Limited", names)
        self.assertIn("Singapore Life Ltd.", names)
        self.assertNotIn("Example Reinsurer", names)
        self.assertEqual(records[0].member_category, "Ordinary Members")

    def test_build_canonical_records_prefers_matched_mas_name_and_flags_lia_gap(self):
        mas_records = parse_mas_fid_records(MAS_HTML, MAS_FID_INSURANCE_URL)
        lia_records = parse_lia_member_records(LIA_HTML, LIA_MEMBER_COMPANIES_URL)
        records = build_canonical_records(
            mas_records,
            lia_records,
            scraped_at="2026-07-02T00:00:00+00:00",
        )
        by_key = {record.carrier_key: record for record in records}

        self.assertEqual(by_key["aia"].canonical_name, "AIA SINGAPORE PRIVATE LIMITED")
        self.assertEqual(by_key["aia"].mas_match_status, MATCHED_STATUS)
        self.assertEqual(by_key["aia"].lia_match_status, MATCHED_STATUS)
        self.assertEqual(by_key["singlife"].mas_match_status, UNMATCHED_STATUS)
        self.assertEqual(by_key["singlife"].lia_match_status, MATCHED_STATUS)
        self.assertIn("mas_unmatched", by_key["singlife"].mismatch_flags)

    def test_low_confidence_mas_name_is_needs_review(self):
        mas_records = parse_mas_fid_records(
            """
            <div class="inner">
              <a href="/fid/institution/detail/1-CHUBB-LIFE-SCIENCE-BROKER">
                <h3>CHUBB LIFE SCIENCE BROKER</h3>
              </a>
              <div class="category">Registered Insurance Broker</div>
            </div>
            """,
            MAS_FID_INSURANCE_URL,
        )
        records = build_canonical_records(mas_records, [], scraped_at="2026-07-02T00:00:00+00:00")
        chubb = {record.carrier_key: record for record in records}["chubb"]

        self.assertEqual(chubb.mas_match_status, NEEDS_REVIEW_STATUS)
        self.assertIn("mas_needs_review", chubb.mismatch_flags)

    def test_rows_include_source_urls_and_aliases(self):
        row = build_canonical_records(
            parse_mas_fid_records(MAS_HTML, MAS_FID_INSURANCE_URL),
            parse_lia_member_records(LIA_HTML, LIA_MEMBER_COMPANIES_URL),
            scraped_at="2026-07-02T00:00:00+00:00",
        )[0].as_row()

        self.assertIn(MAS_FID_INSURANCE_URL, row["source_urls"])
        self.assertIn(LIA_MEMBER_COMPANIES_URL, row["source_urls"])
        self.assertIn("AIA Singapore", row["aliases"])
        self.assertEqual(row["last_verified_at"], "2026-07-02T00:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
