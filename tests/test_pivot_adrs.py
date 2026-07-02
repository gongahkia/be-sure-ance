import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADR_DIR = ROOT / "docs" / "adr"


class PivotAdrTests(unittest.TestCase):
    def test_expected_pivot_adrs_exist(self):
        expected = (
            "0001-remove-regex-derived-premiums.md",
            "0002-single-plans-table.md",
            "0003-qualitative-positioning-vs-comparefirst.md",
            "0004-vue-cli-to-vite.md",
            "0005-plan-facts-provenance.md",
            "0006-defer-chrome-extension-sidebar.md",
        )

        for filename in expected:
            with self.subTest(filename=filename):
                self.assertTrue((ADR_DIR / filename).exists())

    def test_pivot_adrs_have_required_sections(self):
        for path in sorted(ADR_DIR.glob("000[1-5]-*.md")):
            text = path.read_text()
            for required in (
                "## Context",
                "## Decision",
                "## Rejected Approaches",
                "## Consequences",
            ):
                with self.subTest(path=path.name, required=required):
                    self.assertIn(required, text)

    def test_pivot_adrs_capture_required_decisions(self):
        required_by_file = {
            "0001-remove-regex-derived-premiums.md": (
                "Remove runtime premium, deductible, coinsurance, and cost-projection features",
                "No active UI should render premium estimates",
            ),
            "0002-single-plans-table.md": (
                "Use `public.plans` as the canonical plan catalog.",
                "Public clients receive read-only access through RLS",
            ),
            "0003-qualitative-positioning-vs-comparefirst.md": (
                "complements compareFIRST",
                "does not replace compareFIRST",
            ),
            "0004-vue-cli-to-vite.md": (
                "Use Vite as the frontend build tool.",
                "only public `VITE_*` values",
            ),
            "0005-plan-facts-provenance.md": (
                "Use `plan_facts` as the canonical fact table",
                "`source_url`, `source_type`, `scraped_at`, and `last_verified_at`",
            ),
        }

        for filename, required_items in required_by_file.items():
            text = (ADR_DIR / filename).read_text()
            for required in required_items:
                with self.subTest(filename=filename, required=required):
                    self.assertIn(required, text)

    def test_readme_links_adr_folder(self):
        readme = (ROOT / "README.md").read_text()

        self.assertIn("[docs/adr](./docs/adr/)", readme)


if __name__ == "__main__":
    unittest.main()
