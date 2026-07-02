import json
import re
import tempfile
import unittest
from pathlib import Path

from scripts.supabase_logical_dump import create_demo_dump

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github/workflows/nightly-supabase-backup.yml").read_text()
BACKUP_DOC = (ROOT / "docs/BACKUP_RETENTION.md").read_text()
TAKEDOWN_DOC = (ROOT / "docs/TAKEDOWN_RUNBOOK.md").read_text()
COMPLIANCE = (ROOT / "docs/COMPLIANCE.md").read_text()
SUCCESSION = (ROOT / "docs/SUCCESSION.md").read_text()
README = (ROOT / "README.md").read_text()
ENV_EXAMPLE = (ROOT / ".env.example").read_text()


class BackupAndEthicsTests(unittest.TestCase):
    def test_demo_backup_artifact_can_be_produced_without_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            dump_path, manifest_path = create_demo_dump(Path(tmp), stamp="2026-07-02T00-00-00Z")
            manifest = json.loads(manifest_path.read_text())
            dump_text = dump_path.read_text()

        self.assertTrue(dump_path.name.endswith(".dump"))
        self.assertIn("backup_smoke_test", dump_text)
        self.assertEqual(manifest["retention_days"], 30)
        self.assertFalse(manifest["contains_secrets"])

    def test_nightly_workflow_uploads_30_day_artifact_and_optional_r2_copy(self):
        for required in (
            "nightly-supabase-backup",
            'cron: "0 17 * * *"',
            "SUPABASE_DB_URL",
            "python scripts/supabase_logical_dump.py --output-dir .backup-output",
            "actions/upload-artifact@v4",
            "retention-days: 30",
            "R2_BACKUP_BUCKET",
            "aws s3 cp .backup-output/",
        ):
            with self.subTest(required=required):
                self.assertIn(required, WORKFLOW)

    def test_backup_docs_explain_restore_and_retention(self):
        for required in (
            "30-day retention",
            "pg_dump --format=custom --no-owner --no-privileges",
            "pg_restore --clean --if-exists --no-owner --no-privileges",
            "R2 backup copies: configure lifecycle expiry to 30 days",
            "Local Smoke Test",
        ):
            with self.subTest(required=required):
                self.assertIn(required, BACKUP_DOC)

    def test_ethics_and_takedown_policy_are_visible(self):
        combined = TAKEDOWN_DOC + COMPLIANCE + README
        for required in (
            "be-sure-ance-bot/1.0 (mailto:gabrielzmong@gmail.com)",
            "Respect robots.txt",
            "Acknowledge credible requests within 2 business days",
            "7 calendar days",
            "[Takedown runbook](./docs/TAKEDOWN_RUNBOOK.md)",
        ):
            with self.subTest(required=required):
                self.assertIn(required, combined)

    def test_succession_and_env_docs_list_secret_locations_not_values(self):
        combined = SUCCESSION + README + ENV_EXAMPLE
        for required in (
            "SUPABASE_DB_URL",
            "R2_SECRET_ACCESS_KEY",
            "Nightly logical dumps require `SUPABASE_DB_URL`",
            "Use [Backup and retention](./BACKUP_RETENTION.md)",
        ):
            with self.subTest(required=required):
                self.assertIn(required, combined)

        forbidden_patterns = (
            r"sb_secret_[A-Za-z0-9_-]+",
            r"SUPABASE_DB_URL=postgresql://[^\\s<]+:[^\\s<]+@",
            r"R2_SECRET_ACCESS_KEY=\\S+",
        )
        for pattern in forbidden_patterns:
            with self.subTest(pattern=pattern):
                self.assertIsNone(
                    re.search(pattern, SUCCESSION + BACKUP_DOC + TAKEDOWN_DOC + README)
                )


if __name__ == "__main__":
    unittest.main()
