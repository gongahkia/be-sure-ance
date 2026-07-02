import csv
import json
import tempfile
import unittest
from pathlib import Path

from src.backend.demo_data import demo_tables
from src.lib.open_dataset import SNAPSHOT_FIELDS, build_snapshot_rows, export_open_dataset


class OpenDatasetTests(unittest.TestCase):
    def test_snapshot_rows_include_plan_facts_sources_and_dates(self):
        rows = build_snapshot_rows(demo_tables(), "2026-07-02")

        self.assertGreater(len(rows), 0)
        first = rows[0]
        for field in SNAPSHOT_FIELDS:
            with self.subTest(field=field):
                self.assertIn(field, first)
        self.assertTrue(any(row["source_url"] for row in rows))
        self.assertTrue(any(row["last_verified_at"] for row in rows))
        self.assertTrue(any(row["canonical_carrier_name"] for row in rows))

    def test_snapshot_excludes_share_and_secret_like_fields(self):
        rows = build_snapshot_rows(demo_tables(), "2026-07-02")
        payload = json.dumps(rows)

        for forbidden in (
            "TELEGRAM_BOT_TOKEN",
            "SUPABASE_SECRET_KEY",
            "comparison_shares",
            "view_count",
            "agent_name",
            "mas_rep_number",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, payload)

    def test_export_open_dataset_writes_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "be-sure-ance-snapshot-2026-07-02.csv"
            row_count = export_open_dataset(output_path, "2026-07-02", demo_tables())

            self.assertGreater(row_count, 0)
            with output_path.open() as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(list(rows[0].keys()), list(SNAPSHOT_FIELDS))
            self.assertEqual(rows[0]["snapshot_date"], "2026-07-02")


if __name__ == "__main__":
    unittest.main()
