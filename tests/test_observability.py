import unittest
from pathlib import Path
from unittest.mock import patch

from src.lib import observability

ROOT = Path(__file__).resolve().parents[1]
MAIN_JS = (ROOT / "src/be-sure-ance-app/src/main.js").read_text()
FRONTEND_OBSERVABILITY = (ROOT / "src/be-sure-ance-app/src/observability.js").read_text()
PY_OBSERVABILITY = (ROOT / "src/lib/observability.py").read_text()
PACKAGE_JSON = (ROOT / "src/be-sure-ance-app/package.json").read_text()
REQUIREMENTS = (ROOT / "requirements.txt").read_text()
NAVIGATION = (ROOT / "src/scrapers/navigation.py").read_text()
RUN_ALL = (ROOT / "src/scrapers/run_all.py").read_text()
HELPER = (ROOT / "src/backend/helper.py").read_text()
ENV_EXAMPLE = (ROOT / ".env.example").read_text()
README = (ROOT / "README.md").read_text()
COMPLIANCE = (ROOT / "docs/COMPLIANCE.md").read_text()
REFRESH_WORKFLOW = (ROOT / ".github/workflows/refresh-static-data.yml").read_text()
VALIDATE_WORKFLOW = (ROOT / ".github/workflows/validate-scraper-snapshots.yml").read_text()


class ObservabilityTests(unittest.TestCase):
    def tearDown(self):
        observability._initialized = False

    def test_frontend_uses_sentry_before_mount_with_release_environment_and_scrubber(self):
        for required in (
            '"@sentry/vue"',
            "initializeObservability(app)",
            "app.mount('#app')",
            "VITE_SENTRY_DSN",
            "VITE_SENTRY_ENVIRONMENT",
            "VITE_SENTRY_RELEASE",
            "beforeSend: sanitizeEvent",
            "sendDefaultPii: false",
            "captureFrontendError",
            "Sentry.captureException(error)",
        ):
            with self.subTest(required=required):
                self.assertIn(required, PACKAGE_JSON + MAIN_JS + FRONTEND_OBSERVABILITY)

    def test_scraper_paths_capture_exceptions_with_context(self):
        for required in (
            "sentry-sdk==2.64.0",
            'initialize_observability("scraper")',
            "capture_scraper_exception(scraper_name, error, source_url=url)",
            "capture_scraper_exception(",
            "carrier_key",
            "source_url",
            "send_default_pii=False",
        ):
            with self.subTest(required=required):
                self.assertIn(
                    required, REQUIREMENTS + NAVIGATION + RUN_ALL + HELPER + PY_OBSERVABILITY
                )

    def test_python_scrubber_removes_keys_and_token_shapes(self):
        event = {
            "request": {
                "headers": {
                    "Authorization": "Bearer abc",
                    "apikey": "private-token",
                }
            },
            "extra": {"message": "token eyJaaa.bbb.ccc"},
        }

        scrubbed = observability.sanitize_event(event, hint={})

        self.assertEqual(scrubbed["request"]["headers"]["Authorization"], "[redacted]")
        self.assertEqual(scrubbed["request"]["headers"]["apikey"], "[redacted]")
        self.assertEqual(scrubbed["extra"]["message"], "token [redacted]")

    def test_python_capture_sets_scraper_context_without_requiring_dsn_in_tests(self):
        with (
            patch("src.lib.observability.initialize_observability", return_value=False),
            patch("src.lib.observability.sentry_sdk.new_scope") as new_scope,
            patch("src.lib.observability.sentry_sdk.capture_exception", return_value="event-id"),
        ):
            scope = new_scope.return_value.__enter__.return_value
            event_id = observability.capture_scraper_exception(
                "aia",
                RuntimeError("boom"),
                source_url="https://example.com/source",
                context={"Authorization": "Bearer abc"},
            )

        self.assertEqual(event_id, "event-id")
        scope.set_tag.assert_any_call("carrier", "aia")
        scope.set_context.assert_called_once()
        context_payload = scope.set_context.call_args.args[1]
        self.assertEqual(context_payload["carrier_key"], "aia")
        self.assertEqual(context_payload["Authorization"], "[redacted]")

    def test_docs_and_workflows_explain_operational_alerts_and_privacy(self):
        combined = ENV_EXAMPLE + README + COMPLIANCE + REFRESH_WORKFLOW + VALIDATE_WORKFLOW
        for required in (
            "VITE_SENTRY_DSN",
            "SENTRY_DSN",
            "SENTRY_ENVIRONMENT",
            "SENTRY_RELEASE",
            "SENTRY_TRACES_SAMPLE_RATE",
            "Sentry is the selected Phase 4 error monitor",
            "SDKs are initialized with default PII disabled",
            "Event scrubbers redact",
            "Review a test event payload before enabling alerts",
        ):
            with self.subTest(required=required):
                self.assertIn(required, combined)


if __name__ == "__main__":
    unittest.main()
