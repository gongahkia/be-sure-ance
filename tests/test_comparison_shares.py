import unittest

from fastapi import HTTPException

import src.backend.helper as helper
from src.backend.comparison_shares import (
    build_share_record,
    canonical_share_id,
    normalize_share_plans,
    share_path,
    share_public_payload,
)
from src.backend.pdf_brief import NO_ADVICE_DISCLAIMER
from src.backend.pdf_brief_api import (
    ShareRequest,
    create_comparison_share,
    register_comparison_share_view,
)


class FakeShareQuery:
    def __init__(self, parent, table_name):
        self.parent = parent
        self.table_name = table_name
        self.filters = []
        self.insert_payload = None
        self.update_payload = None
        self.limit_count = None

    def insert(self, rows):
        self.insert_payload = rows
        self.parent.inserts[self.table_name].append(rows)
        return self

    def select(self, columns):
        self.parent.calls[self.table_name].append(("select", columns))
        return self

    def eq(self, column, value):
        self.filters.append((column, value))
        self.parent.calls[self.table_name].append(("eq", column, value))
        return self

    def limit(self, count):
        self.limit_count = count
        self.parent.calls[self.table_name].append(("limit", count))
        return self

    def update(self, payload):
        self.update_payload = payload
        self.parent.updates[self.table_name].append((payload, self.filters))
        return self

    def execute(self):
        if self.insert_payload is not None:
            return type("Response", (), {"data": self.insert_payload})()
        rows = list(self.parent.rows.get(self.table_name, []))
        for column, value in self.filters:
            rows = [row for row in rows if row.get(column) == value]
        if self.limit_count is not None:
            rows = rows[: self.limit_count]
        if self.update_payload is not None:
            rows = [{**row, **self.update_payload} for row in rows]
            return type("Response", (), {"data": rows})()
        return type("Response", (), {"data": rows})()


class FakeShareClient:
    def __init__(self):
        self.tables = []
        self.inserts = {"comparison_shares": []}
        self.updates = {"comparison_shares": []}
        self.calls = {"comparison_shares": []}
        self.rows = {"comparison_shares": []}

    def table(self, table_name):
        self.tables.append(table_name)
        return FakeShareQuery(self, table_name)


class ComparisonShareTests(unittest.TestCase):
    def setUp(self):
        self.previous_supabase = helper.supabase
        self.previous_key = helper._supabase_key
        helper.supabase = FakeShareClient()
        helper._supabase_key = "sb_secret_test"

    def tearDown(self):
        helper.supabase = self.previous_supabase
        helper._supabase_key = self.previous_key

    def test_normalize_share_plans_stores_refs_only(self):
        plans = normalize_share_plans(
            [
                {
                    "insurer": "AIA",
                    "plan_slug": "sample-plan",
                    "plan_name": "Sample Plan",
                    "facts": {"coverage_tags": {}},
                }
            ]
        )

        self.assertEqual(plans, [{"insurer": "aia", "plan_slug": "sample-plan"}])
        self.assertNotIn("plan_name", plans[0])
        self.assertNotIn("facts", plans[0])

    def test_share_record_uses_uuid_and_no_pii_payload(self):
        share_id = "11111111-2222-4333-8444-555555555555"
        row = build_share_record(
            [{"insurer": "aia", "plan_slug": "sample-plan"}],
            share_id=share_id,
            created_at="2026-07-02T00:00:00+00:00",
        )

        self.assertEqual(row["id"], share_id)
        self.assertEqual(row["selected_plans"], [{"insurer": "aia", "plan_slug": "sample-plan"}])
        self.assertEqual(row["view_count"], 0)
        self.assertEqual(share_path(share_id), f"/share/{share_id}")
        self.assertEqual(canonical_share_id(share_id.upper()), share_id)

    def test_share_public_payload_stamps_no_advice_disclaimer(self):
        payload = share_public_payload(
            {
                "id": "11111111-2222-4333-8444-555555555555",
                "selected_plans": [{"insurer": "aia", "plan_slug": "sample-plan"}],
                "created_at": "2026-07-02T00:00:00+00:00",
                "view_count": 2,
                "last_viewed_at": None,
            }
        )

        self.assertEqual(payload["view_count"], 2)
        self.assertIn(NO_ADVICE_DISCLAIMER[:40], payload["disclaimer"])

    def test_create_share_endpoint_inserts_selected_plan_refs_only(self):
        response = create_comparison_share(
            ShareRequest(
                plans=[
                    {
                        "insurer": "aia",
                        "plan_slug": "sample-plan",
                        "plan_name": "Sample Plan",
                    }
                ]
            )
        )

        inserted = helper.supabase.inserts["comparison_shares"][0][0]
        self.assertEqual(
            inserted["selected_plans"], [{"insurer": "aia", "plan_slug": "sample-plan"}]
        )
        self.assertEqual(response["path"], f"/share/{response['id']}")
        self.assertIn("disclaimer", response)

    def test_view_endpoint_increments_non_identifying_counter(self):
        share_id = "11111111-2222-4333-8444-555555555555"
        helper.supabase.rows["comparison_shares"] = [
            {
                "id": share_id,
                "selected_plans": [{"insurer": "aia", "plan_slug": "sample-plan"}],
                "view_count": 3,
                "created_at": "2026-07-02T00:00:00+00:00",
            }
        ]

        response = register_comparison_share_view(share_id)

        self.assertEqual(response["view_count"], 4)
        self.assertEqual(
            helper.supabase.updates["comparison_shares"][0][0]["view_count"],
            4,
        )
        self.assertIn("last_viewed_at", helper.supabase.updates["comparison_shares"][0][0])

    def test_view_endpoint_rejects_invalid_uuid(self):
        with self.assertRaises(HTTPException):
            register_comparison_share_view("not-a-uuid")


if __name__ == "__main__":
    unittest.main()
