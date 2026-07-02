import unittest

import src.backend.helper as helper
from src.scrapers import comparison_facts, panel_resources


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def select(self, columns):
        self.calls.append(("select", columns))
        return self

    def eq(self, column, value):
        self.calls.append(("eq", column, value))
        return self

    def execute(self):
        self.calls.append(("execute",))
        return type("Response", (), {"data": self.rows})()


class FakeSupabase:
    def __init__(self, rows):
        self.rows = rows
        self.tables = []
        self.query = FakeQuery(rows)

    def table(self, table_name):
        self.tables.append(table_name)
        return self.query


class PlansSourceTests(unittest.TestCase):
    def tearDown(self):
        helper.supabase = None

    def test_comparison_facts_fetches_from_plans_by_insurer(self):
        fake = FakeSupabase([{"plan_name": "x"}])
        comparison_facts.helper.supabase = fake

        self.assertEqual(comparison_facts.fetch_rows("aia"), [{"plan_name": "x"}])
        self.assertEqual(fake.tables, ["plans"])
        self.assertIn(("eq", "insurer", "aia"), fake.query.calls)

    def test_panel_resources_fetches_from_plans_by_insurer(self):
        fake = FakeSupabase([{"plan_name": "x"}])
        panel_resources.helper.supabase = fake

        self.assertEqual(panel_resources.fetch_plans("aia"), [{"plan_name": "x"}])
        self.assertEqual(fake.tables, ["plans"])
        self.assertIn(("eq", "insurer", "aia"), fake.query.calls)


if __name__ == "__main__":
    unittest.main()
