import base64
import json
import os
import sys
import unittest
from unittest.mock import patch

import src.backend.helper as helper
from src.backend.helper import (
    dry_run_enabled,
    flatten_rows,
    format_plan_rows,
    key_has_write_access,
    overwrite_plans_for_insurer,
)


def jwt_for_role(role):
    header = {"alg": "none", "typ": "JWT"}
    payload = {"role": role}
    parts = []
    for item in (header, payload):
        encoded = base64.urlsafe_b64encode(json.dumps(item).encode()).decode()
        parts.append(encoded.rstrip("="))
    return f"{parts[0]}.{parts[1]}."


class BackendHelperTests(unittest.TestCase):
    def tearDown(self):
        helper._supabase_key = None
        helper.supabase = None

    def test_key_has_write_access_rejects_anon_key(self):
        self.assertFalse(key_has_write_access(jwt_for_role("anon")))

    def test_key_has_write_access_accepts_legacy_service_role_key(self):
        self.assertTrue(key_has_write_access(jwt_for_role("service_role")))

    def test_key_has_write_access_accepts_secret_key(self):
        self.assertTrue(key_has_write_access("sb_secret_example"))

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

    def test_initialize_supabase_skips_client_setup_in_dry_run(self):
        with (
            patch.object(sys, "argv", ["scraper.py", "--dry-run"]),
            patch.dict(os.environ, {}, clear=True),
            patch("src.backend.helper.create_client") as create_client,
        ):
            helper.initialize_supabase()
        create_client.assert_not_called()

    def test_write_helpers_reject_anon_key(self):
        helper._supabase_key = jwt_for_role("anon")
        for write_call in (
            lambda: helper.clear_table_data("aia"),
            lambda: helper.clear_plans_for_insurer("aia"),
            lambda: helper.overwrite_plans_for_insurer("aia", [{"plan_name": "x"}]),
            lambda: helper.insert_generic_data("plan_comparison_facts", []),
        ):
            with self.subTest(write_call=write_call):
                with self.assertRaises(PermissionError):
                    write_call()

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

    def test_service_role_overwrite_plans_uses_insurer_scoped_table_api(self):
        class FakeQuery:
            def __init__(self):
                self.calls = []
                self.data = None

            def delete(self):
                self.calls.append(("delete",))
                return self

            def neq(self, column, value):
                self.calls.append(("neq", column, value))
                return self

            def eq(self, column, value):
                self.calls.append(("eq", column, value))
                return self

            def upsert(self, data, **kwargs):
                self.calls.append(("upsert", data, kwargs))
                return self

            def execute(self):
                self.calls.append(("execute",))
                return type("Response", (), {"data": [{"ok": True}]})()

        class FakeClient:
            def __init__(self):
                self.query = FakeQuery()
                self.tables = []

            def table(self, table_name):
                self.tables.append(table_name)
                return self.query

        fake_client = FakeClient()
        helper._supabase_key = jwt_for_role("service_role")
        helper.supabase = fake_client

        helper.overwrite_plans_for_insurer(
            "aia", [{"plan_name": "x", "plan_benefits": "benefit"}]
        )

        self.assertEqual(fake_client.tables, ["plans", "plans"])
        self.assertIn(("delete",), fake_client.query.calls)
        self.assertIn(("eq", "insurer", "aia"), fake_client.query.calls)
        upsert_calls = [
            call for call in fake_client.query.calls if call[0] == "upsert"
        ]
        self.assertEqual(upsert_calls[0][2], {"on_conflict": "insurer,plan_slug"})
        self.assertEqual(upsert_calls[0][1][0]["insurer"], "aia")
        self.assertEqual(upsert_calls[0][1][0]["plan_slug"], "x")
        self.assertEqual(upsert_calls[0][1][0]["plan_benefits"], ["benefit"])


if __name__ == "__main__":
    unittest.main()
