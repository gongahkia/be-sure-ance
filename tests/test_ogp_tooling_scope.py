import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADR = (ROOT / "docs/adr/0007-defer-ogp-tooling-integrations.md").read_text()
ADR_INDEX = (ROOT / "docs/adr/README.md").read_text()
README = (ROOT / "README.md").read_text()


class OgpToolingScopeTests(unittest.TestCase):
    def test_adr_records_defer_decision_for_each_candidate(self):
        for required in (
            "Accepted - defer implementation.",
            "Postman.gov.sg brochure-change email alerts | Defer",
            "FormSG stale-data reports | Defer",
            "Go.gov.sg shared-comparison short links | Defer",
            "No implementation issues are created while access is unconfirmed.",
        ):
            with self.subTest(required=required):
                self.assertIn(required, ADR)

    def test_adr_records_access_blockers(self):
        for required in (
            "not onboarding new programmatic email API users",
            "only government agencies and approved organisations by Ministries can create forms",
            "intended for Singapore public sector agency use",
            "API use requires a bearer token",
        ):
            with self.subTest(required=required):
                self.assertIn(required, ADR)

    def test_adr_lists_restart_conditions_and_future_issue_scope(self):
        for required in (
            "agency sponsorship or confirmed Postman onboarding access",
            "sponsoring agency or approved organisation owns the form",
            "authorised public-sector owner provides a token",
            "implement brochure-change alert dispatcher",
            "implement stale-data intake webhook",
            "implement optional server-side short-link creation",
        ):
            with self.subTest(required=required):
                self.assertIn(required, ADR)

    def test_readme_does_not_claim_unconfirmed_integrations(self):
        for required in (
            "OGP/GovTech tooling scope",
            "No integration is currently claimed",
            "deferred until public-sector ownership, access, and governance are confirmed",
        ):
            with self.subTest(required=required):
                self.assertIn(required, README)

    def test_adr_index_links_scope_record(self):
        self.assertIn("0007-defer-ogp-tooling-integrations.md", ADR_INDEX)


if __name__ == "__main__":
    unittest.main()
