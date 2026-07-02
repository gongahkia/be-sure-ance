import hashlib
import unittest
from collections import defaultdict
from unittest.mock import patch

import src.backend.helper as helper


class FakeDownloadResponse:
    def __init__(self, content, headers=None, fail=False):
        self.content = content
        self.headers = headers or {"content-type": "application/pdf"}
        self.fail = fail

    def raise_for_status(self):
        if self.fail:
            raise RuntimeError("download failed")


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, url, timeout, headers):
        self.calls.append((url, timeout, headers))
        return self.response


class FakeStorageBucket:
    def __init__(self):
        self.uploads = []

    def upload(self, path, file, file_options):
        self.uploads.append((path, file, file_options))
        return type("UploadResponse", (), {"path": path})()


class FakeStorage:
    def __init__(self, bucket):
        self.bucket = bucket
        self.bucket_names = []

    def from_(self, bucket_name):
        self.bucket_names.append(bucket_name)
        return self.bucket


class FakeQuery:
    def __init__(self, parent, table_name):
        self.parent = parent
        self.table_name = table_name
        self.filters = []
        self.limit_count = None
        self.update_payload = None
        self.upsert_payload = None

    def upsert(self, rows, on_conflict):
        self.upsert_payload = (rows, on_conflict)
        self.parent.upserts[self.table_name].append((rows, on_conflict))
        return self

    def select(self, columns):
        self.parent.calls[self.table_name].append(("select", columns))
        return self

    def eq(self, column, value):
        self.filters.append((column, value))
        self.parent.calls[self.table_name].append(("eq", column, value))
        return self

    def order(self, column, desc=False):
        self.parent.calls[self.table_name].append(("order", column, desc))
        return self

    def limit(self, count):
        self.limit_count = count
        self.parent.calls[self.table_name].append(("limit", count))
        return self

    def update(self, payload):
        self.update_payload = payload
        self.parent.calls[self.table_name].append(("update", payload))
        return self

    def execute(self):
        if self.update_payload is not None:
            self.parent.updates[self.table_name].append((self.update_payload, self.filters))
            return type("Response", (), {"data": [{"ok": True}]})()
        if self.upsert_payload is not None:
            return type("Response", (), {"data": self.upsert_payload[0]})()
        rows = list(self.parent.select_rows[self.table_name])
        for column, value in self.filters:
            rows = [row for row in rows if row.get(column) == value]
        if self.limit_count is not None:
            rows = rows[: self.limit_count]
        return type("Response", (), {"data": rows})()


class FakeLocalClient:
    def __init__(self):
        self.bucket = FakeStorageBucket()
        self.storage = FakeStorage(self.bucket)
        self.tables = []
        self.upserts = defaultdict(list)
        self.updates = defaultdict(list)
        self.calls = defaultdict(list)
        self.select_rows = defaultdict(list)

    def table(self, table_name):
        self.tables.append(table_name)
        return FakeQuery(self, table_name)


class BrochureCaptureTests(unittest.TestCase):
    def setUp(self):
        self.previous_client = helper.injected_client
        self.previous_key = helper._write_key
        self.previous_bucket = helper.os.environ.get("BROCHURE_STORAGE_BUCKET")
        helper.injected_client = FakeLocalClient()
        helper._write_key = "local-test-key"
        helper.os.environ["BROCHURE_STORAGE_BUCKET"] = "plan-brochures-test"

    def tearDown(self):
        helper.injected_client = self.previous_client
        helper._write_key = self.previous_key
        if self.previous_bucket is None:
            helper.os.environ.pop("BROCHURE_STORAGE_BUCKET", None)
        else:
            helper.os.environ["BROCHURE_STORAGE_BUCKET"] = self.previous_bucket

    def test_download_brochure_requires_http_pdf(self):
        with self.assertRaises(ValueError):
            helper.download_brochure("javascript:alert(1)")

        with self.assertRaises(ValueError):
            helper.download_brochure(
                "https://example.com/page",
                session=FakeSession(
                    FakeDownloadResponse(b"<html></html>", {"content-type": "text/html"})
                ),
            )

    def test_capture_brochure_uploads_stable_hash_and_upserts_metadata(self):
        content = b"%PDF-1.4 sample"
        content_hash = hashlib.sha256(content).hexdigest()
        plan = {
            "plan_slug": "sample-plan",
            "product_brochure_url": "https://example.com/sample.pdf",
        }
        session = FakeSession(
            FakeDownloadResponse(
                content,
                {
                    "content-type": "application/pdf",
                    "last-modified": "Wed, 01 Jul 2026 00:00:00 GMT",
                },
            )
        )

        with patch("src.backend.helper.extract_brochure_text", return_value="Sample text"):
            fact = helper.capture_brochure_for_plan(
                "aia",
                plan,
                session=session,
                captured_at="2026-07-02T00:00:00Z",
            )

        expected_key = f"brochures/aia/sample-plan/{content_hash}.pdf"
        self.assertEqual(fact["field_name"], "brochure_metadata")
        self.assertEqual(fact["source_type"], "brochure_pdf")
        self.assertEqual(fact["field_value"]["value"]["sha256"], content_hash)
        self.assertEqual(fact["field_value"]["value"]["storage_key"], expected_key)
        self.assertEqual(fact["field_value"]["value"]["size_bytes"], len(content))
        self.assertEqual(helper.injected_client.storage.bucket_names, ["plan-brochures-test"])
        self.assertEqual(helper.injected_client.bucket.uploads[0][0], expected_key)
        self.assertEqual(helper.injected_client.bucket.uploads[0][1], content)
        self.assertEqual(helper.injected_client.bucket.uploads[0][2]["upsert"], "true")
        self.assertEqual(
            helper.injected_client.tables,
            ["plan_facts", "brochure_version_history", "brochure_version_history"],
        )
        self.assertEqual(
            helper.injected_client.upserts["plan_facts"][0][1],
            "insurer,plan_slug,field_name",
        )
        version_row = helper.injected_client.upserts["brochure_version_history"][0][0][0]
        self.assertEqual(version_row["sha256"], content_hash)
        self.assertEqual(version_row["source_url"], "https://example.com/sample.pdf")
        self.assertEqual(helper.injected_client.upserts["brochure_change_alerts"], [])

    def test_failed_brochure_capture_returns_none_without_upsert(self):
        result = helper.capture_brochure_for_plan(
            "aia",
            {
                "plan_slug": "sample-plan",
                "product_brochure_url": "https://example.com/sample.pdf",
            },
            session=FakeSession(FakeDownloadResponse(b"", fail=True)),
            captured_at="2026-07-02T00:00:00Z",
        )

        self.assertIsNone(result)
        self.assertEqual(helper.injected_client.bucket.uploads, [])
        self.assertEqual(dict(helper.injected_client.upserts), {})

    def test_record_brochure_version_updates_seen_for_unchanged_hash(self):
        content = b"current"
        content_hash = hashlib.sha256(content).hexdigest()
        captured_at = "2026-07-02T00:00:00Z"
        plan = {
            "plan_name": "Sample Plan",
            "plan_slug": "sample-plan",
            "product_brochure_url": "https://example.com/sample.pdf",
        }
        fact_row = helper.build_brochure_metadata_fact(
            "aia",
            plan,
            {"content": content, "content_type": "application/pdf", "last_modified_at": None},
            captured_at,
        )
        helper.injected_client.select_rows["brochure_version_history"] = [
            {
                "id": 7,
                "insurer": "aia",
                "plan_slug": "sample-plan",
                "source_url": "https://example.com/sample.pdf",
                "sha256": content_hash,
                "captured_at": "2026-07-01T00:00:00Z",
            }
        ]

        with patch("src.backend.helper.extract_brochure_text", return_value="Current"):
            result = helper.record_brochure_version("aia", plan, fact_row, content, captured_at)

        self.assertEqual(result["status"], "unchanged")
        self.assertEqual(
            helper.injected_client.updates["brochure_version_history"],
            [({"last_seen_at": captured_at}, [("id", 7)])],
        )
        self.assertEqual(helper.injected_client.upserts["brochure_change_alerts"], [])

    def test_record_brochure_version_creates_alert_for_changed_hash(self):
        content = b"current"
        content_hash = hashlib.sha256(content).hexdigest()
        captured_at = "2026-07-02T00:00:00Z"
        plan = {
            "plan_name": "Sample Plan",
            "plan_slug": "sample-plan",
            "product_brochure_url": "https://example.com/sample.pdf",
        }
        fact_row = helper.build_brochure_metadata_fact(
            "aia",
            plan,
            {"content": content, "content_type": "application/pdf", "last_modified_at": None},
            captured_at,
        )
        helper.injected_client.select_rows["brochure_version_history"] = [
            {
                "id": 7,
                "insurer": "aia",
                "plan_slug": "sample-plan",
                "plan_name": "Sample Plan",
                "source_url": "https://example.com/sample.pdf",
                "sha256": "previous-hash",
                "captured_at": "2026-07-01T00:00:00Z",
                "size_bytes": 10,
                "extracted_text": "old limit",
            }
        ]

        with patch("src.backend.helper.extract_brochure_text", return_value="new limit"):
            result = helper.record_brochure_version("aia", plan, fact_row, content, captured_at)

        self.assertEqual(result["status"], "changed")
        self.assertEqual(
            helper.injected_client.upserts["brochure_version_history"][0][1],
            "insurer,plan_slug,source_url,sha256",
        )
        alert = helper.injected_client.upserts["brochure_change_alerts"][0][0][0]
        self.assertEqual(alert["previous_sha256"], "previous-hash")
        self.assertEqual(alert["current_sha256"], content_hash)
        self.assertEqual(alert["source_url"], "https://example.com/sample.pdf")
        self.assertEqual(alert["change_detected_at"], captured_at)
        self.assertEqual(alert["alert_status"], "pending")
        self.assertIn("-old limit", alert["text_diff"])
        self.assertIn("+new limit", alert["text_diff"])


if __name__ == "__main__":
    unittest.main()
