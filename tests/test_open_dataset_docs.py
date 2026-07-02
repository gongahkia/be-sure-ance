import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_README = (ROOT / "data/README.md").read_text()
WORKFLOW = (ROOT / ".github/workflows/publish-open-dataset.yml").read_text()
README = (ROOT / "README.md").read_text()


class OpenDatasetDocsTests(unittest.TestCase):
    def test_data_readme_documents_contents_license_and_limits(self):
        for required in (
            "CC-BY-4.0",
            "source_url",
            "last_verified_at",
            "comparison share IDs",
            "not financial advice",
            "Suggested citation",
        ):
            with self.subTest(required=required):
                self.assertIn(required, DATA_README)

    def test_weekly_workflow_exports_and_uploads_artifact(self):
        for required in (
            "name: publish-open-dataset",
            'cron: "0 20 * * 0"',
            "python3 -m src.lib.open_dataset",
            "data/be-sure-ance-snapshot-${snapshot_date}.csv",
            "actions/upload-artifact@v4",
            "open-dataset-snapshot",
        ):
            with self.subTest(required=required):
                self.assertIn(required, WORKFLOW)

    def test_readme_links_open_dataset_status(self):
        self.assertIn("Open dataset snapshots", README)
        self.assertIn("CC-BY-4.0 CSV artifacts", README)


if __name__ == "__main__":
    unittest.main()
