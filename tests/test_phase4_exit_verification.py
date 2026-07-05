import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHASE4 = (ROOT / "docs/PHASE4_EXIT_VERIFICATION.md").read_text()
README = (ROOT / "README.md").read_text()
COMPLIANCE = (ROOT / "docs/COMPLIANCE.md").read_text()


class Phase4ExitVerificationTests(unittest.TestCase):
    def test_readme_links_phase4_exit_record(self):
        self.assertIn("[Phase 4 exit verification](./docs/PHASE4_EXIT_VERIFICATION.md)", README)

    def test_reviewer_orientation_is_recorded(self):
        for required in (
            "public-good IFA pre-meeting research tool",
            "compareFIRST",
            "no advice, quotes, recommendations",
            "16 supported scheduled carriers",
            "5,305 MOH institutions",
            "12 LIA claim metrics",
            "$0/mo",
            "ADR 0007",
            "LICENSE",
            "CONTRIBUTING.md",
            "CODE_OF_CONDUCT.md",
        ):
            with self.subTest(required=required):
                self.assertIn(required, PHASE4)

    def test_operational_docs_status_and_observability_are_recorded(self):
        for required in (
            "docs/COMPLIANCE.md",
            "docs/DATA_MODEL.md",
            "docs/SUCCESSION.md",
            "docs/BACKUP_RETENTION.md",
            "docs/TAKEDOWN_RUNBOOK.md",
            "/status",
            "scraper_health",
            "Sentry",
            "refresh workflow logs",
        ):
            with self.subTest(required=required):
                self.assertIn(required, PHASE4)

    def test_portfolio_evidence_is_recorded(self):
        for required in (
            "0 Axe violations / Lighthouse 100",
            "docs/ACCESSIBILITY.md",
            "Manual screen-reader testing remains a Phase 5 prelaunch requirement",
            ".github/workflows/publish-open-dataset.yml",
            "CC-BY-4.0 CSV artifacts",
            "docs/case-studies/README.md",
            "not to invent testimonials",
            "docs/blog/why-we-ripped-out-regex-derived-premiums.md",
            "docs/talks/README.md",
        ):
            with self.subTest(required=required):
                self.assertIn(required, PHASE4)

    def test_only_phase5_and_compliance_launch_gates_remain(self):
        for required in (
            "The only remaining public-launch blockers recorded here are Phase 5 deployment",
            "remote CI/indexing/operations verification",
            "Singapore fintech/compliance lawyer sign-off",
            "live scraper robots.txt handling",
        ):
            with self.subTest(required=required):
                self.assertIn(required, PHASE4)

        self.assertIn("Phase 5/compliance sign-off must verify robots.txt handling", COMPLIANCE)


if __name__ == "__main__":
    unittest.main()
