import hashlib
import unittest

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
    def __init__(self):
        self.upserts = []

    def upsert(self, rows, on_conflict):
        self.upserts.append((rows, on_conflict))
        return self

    def execute(self):
        return type("Response", (), {"data": [{"ok": True}]})()


class FakeSupabase:
    def __init__(self):
        self.bucket = FakeStorageBucket()
        self.storage = FakeStorage(self.bucket)
        self.query = FakeQuery()
        self.tables = []

    def table(self, table_name):
        self.tables.append(table_name)
        return self.query


class BrochureCaptureTests(unittest.TestCase):
    def setUp(self):
        self.previous_supabase = helper.supabase
        self.previous_key = helper._supabase_key
        self.previous_bucket = helper.os.environ.get("BROCHURE_STORAGE_BUCKET")
        helper.supabase = FakeSupabase()
        helper._supabase_key = "sb_secret_test"
        helper.os.environ["BROCHURE_STORAGE_BUCKET"] = "plan-brochures-test"

    def tearDown(self):
        helper.supabase = self.previous_supabase
        helper._supabase_key = self.previous_key
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
        self.assertEqual(helper.supabase.storage.bucket_names, ["plan-brochures-test"])
        self.assertEqual(helper.supabase.bucket.uploads[0][0], expected_key)
        self.assertEqual(helper.supabase.bucket.uploads[0][1], content)
        self.assertEqual(helper.supabase.bucket.uploads[0][2]["upsert"], "true")
        self.assertEqual(helper.supabase.tables, ["plan_facts"])
        self.assertEqual(helper.supabase.query.upserts[0][1], "insurer,plan_slug,field_name")

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
        self.assertEqual(helper.supabase.bucket.uploads, [])
        self.assertEqual(helper.supabase.query.upserts, [])


if __name__ == "__main__":
    unittest.main()
