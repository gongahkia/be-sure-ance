from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.validation.differ import (
    ValidationTarget,
    compare_snapshot_pair,
    run_validation,
    snapshot_from_html,
    write_snapshot_artifacts,
)

ROOT = Path(__file__).resolve().parents[1]


class ValidationDifferTests(unittest.TestCase):
    def setUp(self):
        self.target = ValidationTarget(
            insurer="demo",
            url="https://example.com/products",
            domain="example.com",
            source_file="demo.py",
        )
        self.baseline_html = """
        <html>
          <body>
            <main>
              <section>
                <h1>Plan A</h1>
                <p>Core summary</p>
              </section>
            </main>
          </body>
        </html>
        """
        self.changed_html = """
        <html>
          <body>
            <main>
              <article>
                <header><h1>Plan A</h1></header>
                <section><p>Core summary</p><ul><li>Benefit</li></ul></section>
              </article>
            </main>
          </body>
        </html>
        """

    def test_compare_snapshot_pair_passes_for_identical_structure(self):
        baseline = snapshot_from_html(self.target, self.baseline_html)
        current = snapshot_from_html(self.target, self.baseline_html)

        comparison = compare_snapshot_pair(
            baseline_snapshot=baseline,
            current_snapshot=current,
            max_path_drift=0.2,
            max_tag_drift=0.2,
        )

        self.assertEqual(comparison["status"], "passed")
        self.assertEqual(comparison["path_drift"], 0.0)
        self.assertEqual(comparison["tag_drift"], 0.0)

    def test_compare_snapshot_pair_fails_for_different_structure(self):
        baseline = snapshot_from_html(self.target, self.baseline_html)
        current = snapshot_from_html(self.target, self.changed_html)

        comparison = compare_snapshot_pair(
            baseline_snapshot=baseline,
            current_snapshot=current,
            max_path_drift=0.1,
            max_tag_drift=0.1,
        )

        self.assertEqual(comparison["status"], "failed")
        self.assertTrue(comparison["failures"])

    def test_canonicalization_ignores_volatile_attributes_and_text_for_status(self):
        target = ValidationTarget(
            insurer="demo",
            url="https://example.com/products/plan",
            domain="example.com",
            source_file="demo.py",
            page_role="product_detail",
            expected_selectors=("main h1",),
        )
        baseline = snapshot_from_html(
            target,
            """
            <html><body><main id="old" data-build="1">
              <h1 class="hero">Plan A</h1><p>Price 2025</p>
            </main></body></html>
            """,
        )
        current = snapshot_from_html(
            target,
            """
            <html><body><main id="new" data-build="2">
              <h1 class="hero-new">Plan A</h1><p>Price 2026</p>
            </main></body></html>
            """,
        )

        comparison = compare_snapshot_pair(
            baseline_snapshot=baseline,
            current_snapshot=current,
            max_path_drift=0.0,
            max_tag_drift=0.0,
        )

        self.assertEqual(comparison["status"], "passed")
        self.assertTrue(comparison["text_hash_changed"])

    def test_selector_missing_fails_validation(self):
        target = ValidationTarget(
            insurer="demo",
            url="https://example.com/products/plan",
            domain="example.com",
            source_file="demo.py",
            page_role="product_detail",
            expected_selectors=("main h1",),
        )
        baseline = snapshot_from_html(
            target, "<html><body><main><h1>Plan</h1></main></body></html>"
        )
        current = snapshot_from_html(target, "<html><body><main><p>Plan</p></main></body></html>")

        comparison = compare_snapshot_pair(
            baseline_snapshot=baseline,
            current_snapshot=current,
            max_path_drift=1,
            max_tag_drift=1,
        )

        self.assertEqual(comparison["status"], "failed")
        self.assertTrue(any("Expected selector missing" in item for item in comparison["failures"]))

    def test_plan_count_swing_fails_validation(self):
        target = ValidationTarget(
            insurer="demo",
            url="https://example.com/products",
            domain="example.com",
            source_file="demo.py",
            page_role="listing",
            expected_selectors=("main",),
            max_plan_count_delta=1,
        )
        baseline = snapshot_from_html(
            target,
            """
            <html><body><main>
              <a href="/a">Plan A Insurance</a>
              <a href="/b">Plan B Insurance</a>
              <a href="/c">Plan C Insurance</a>
            </main></body></html>
            """,
        )
        current = snapshot_from_html(target, "<html><body><main></main></body></html>")

        comparison = compare_snapshot_pair(
            baseline_snapshot=baseline,
            current_snapshot=current,
            max_path_drift=1,
            max_tag_drift=1,
        )

        self.assertEqual(comparison["status"], "failed")
        self.assertTrue(
            any(
                "Accepted plan count changed from 3 to 0" in item for item in comparison["failures"]
            )
        )

    def test_run_validation_writes_machine_readable_report_and_fails_on_drift(self):
        with (
            tempfile.TemporaryDirectory() as baseline_tmp,
            tempfile.TemporaryDirectory() as output_tmp,
        ):
            baseline_dir = Path(baseline_tmp)
            output_dir = Path(output_tmp)

            baseline_snapshot = snapshot_from_html(self.target, self.baseline_html)
            write_snapshot_artifacts(baseline_dir, baseline_snapshot)

            with (
                patch(
                    "src.validation.differ.discover_targets",
                    return_value=[self.target],
                ),
                patch(
                    "src.validation.differ.fetch_html",
                    return_value=self.changed_html,
                ),
            ):
                exit_code = run_validation(
                    output_dir=output_dir,
                    baseline_dir=baseline_dir,
                    max_urls_per_insurer=1,
                    request_timeout=5,
                    max_path_drift=0.1,
                    max_tag_drift=0.1,
                )

            report = json.loads((output_dir / "report.json").read_text())
            self.assertEqual(exit_code, 1)
            self.assertEqual(report["summary"]["failed"], 1)
            self.assertEqual(report["results"][0]["status"], "failed")
            self.assertIn("structure_hash", report["results"][0])
            self.assertIn("selector_presence", report["results"][0])
            self.assertIn("accepted_plan_count", report["results"][0])
            self.assertIn(
                "| Target | Role | Status | Plans | Selectors |",
                (output_dir / "summary.md").read_text(),
            )

    def test_workflow_verifies_json_report_and_human_summary_artifacts(self):
        workflow = (ROOT / ".github/workflows/validate-scraper-snapshots.yml").read_text()

        self.assertIn("test -s .validation-output/report.json", workflow)
        self.assertIn("test -s .validation-output/summary.md", workflow)


if __name__ == "__main__":
    unittest.main()
