import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import src.backend.helper as helper
from src.backend.helper import (
    dry_run_enabled,
    flatten_rows,
    format_plan_rows,
    key_has_write_access,
    overwrite_plans_for_insurer,
)
from src.lib.local_data_store import LocalDataClient


class BackendHelperTests(unittest.TestCase):
    def tearDown(self):
        helper.data_store = None
        helper.injected_client = None
        helper._write_key = "local-data-store"

    def test_key_has_write_access_rejects_empty_key(self):
        self.assertFalse(key_has_write_access(""))

    def test_key_has_write_access_accepts_local_key(self):
        self.assertTrue(key_has_write_access("local-data-store"))

    def test_flatten_rows_flattens_one_level(self):
        self.assertEqual(flatten_rows([[{"a": 1}], {"b": 2}]), [{"a": 1}, {"b": 2}])

    def test_dry_run_enabled_detects_flag(self):
        self.assertTrue(dry_run_enabled(["--dry-run"]))
        self.assertFalse(dry_run_enabled([]))

    def test_overwrite_plans_for_insurer_skips_writes_in_dry_run(self):
        with (
            patch.object(sys, "argv", ["scraper.py", "--dry-run"]),
            patch("src.backend.helper.clear_plans_for_insurer") as clear_plans,
        ):
            overwrite_plans_for_insurer("aia", [{"plan_name": "x"}])
        clear_plans.assert_not_called()

    def test_initialize_data_store_skips_client_setup_in_dry_run(self):
        with patch.object(sys, "argv", ["scraper.py", "--dry-run"]):
            helper.initialize_data_store()
        self.assertIsNone(helper.data_store)

    def test_format_plan_rows_adds_insurer_slug_and_scraped_at(self):
        rows = format_plan_rows(
            "aia",
            [
                [
                    {
                        "plan_name": "Sample Plan",
                        "plan_benefits": [["Benefit A"], "Benefit B"],
                    }
                ],
                {"plan_name": "Sample Plan", "plan_benefits": "Benefit C"},
            ],
            scraped_at="2026-07-02T00:00:00+00:00",
        )

        self.assertEqual(rows[0]["insurer"], "aia")
        self.assertEqual(rows[0]["plan_slug"], "sample-plan")
        self.assertEqual(rows[1]["plan_slug"], "sample-plan-2")
        self.assertEqual(rows[0]["plan_benefits"], ["Benefit A", "Benefit B"])
        self.assertEqual(rows[1]["plan_benefits"], ["Benefit C"])
        self.assertEqual(rows[0]["scraped_at"], "2026-07-02T00:00:00+00:00")

    def test_overwrite_plans_uses_local_table_store(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            helper.data_store = LocalDataClient(Path(tmpdir))
            helper.overwrite_plans_for_insurer(
                "aia", [{"plan_name": "x", "plan_benefits": "benefit"}]
            )

            rows = helper.data_store.read_table("plans")

        self.assertEqual(rows[0]["insurer"], "aia")
        self.assertEqual(rows[0]["plan_slug"], "x")
        self.assertEqual(rows[0]["plan_benefits"], ["benefit"])


if __name__ == "__main__":
    unittest.main()
