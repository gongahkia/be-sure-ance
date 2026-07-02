import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_SQL = (ROOT / "src/lib/create.sql").read_text()
MIGRATION_SQL = (
    ROOT / "src/lib/migrations/0000_enforce_readonly_rls.sql"
).read_text()


def squash(sql):
    return re.sub(r"\s+", " ", sql.upper())


class SupabaseSchemaSecurityTests(unittest.TestCase):
    def test_schema_does_not_grant_public_writes(self):
        combined = squash(f"{SCHEMA_SQL}\n{MIGRATION_SQL}")

        for statement in combined.split(";"):
            if not statement.strip().startswith("GRANT"):
                continue
            if not re.search(r"\bTO\b.*\b(?:ANON|AUTHENTICATED)\b", statement):
                continue
            with self.subTest(statement=statement.strip()):
                self.assertIsNone(
                    re.search(r"\b(?:ALL|INSERT|UPDATE|DELETE)\b", statement)
                )

    def test_schema_enables_read_only_rls_for_public_tables(self):
        combined = squash(f"{SCHEMA_SQL}\n{MIGRATION_SQL}")

        required_snippets = [
            "ENABLE ROW LEVEL SECURITY",
            'CREATE POLICY "PUBLIC READ ACCESS"',
            "FOR SELECT TO ANON, AUTHENTICATED USING (TRUE)",
            "REVOKE ALL ON TABLE",
            "FROM ANON, AUTHENTICATED",
            "GRANT SELECT ON TABLE",
            "TO ANON, AUTHENTICATED",
            "GRANT ALL ON TABLE",
            "TO SERVICE_ROLE",
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, combined)

    def test_no_public_write_policies_exist(self):
        combined = squash(f"{SCHEMA_SQL}\n{MIGRATION_SQL}")

        for operation in ("INSERT", "UPDATE", "DELETE", "ALL"):
            for role in ("ANON", "AUTHENTICATED"):
                with self.subTest(operation=operation, role=role):
                    self.assertNotIn(f"FOR {operation} TO {role}", combined)


if __name__ == "__main__":
    unittest.main()
