import unittest

from src.bot.lookup import (
    NO_ADVICE_LINE,
    RATE_LIMIT_MESSAGE,
    SAFE_FAILURE_MESSAGE,
    PlanFactIndex,
    RateLimiter,
    answer_fact_query,
    answer_panel_query,
    help_text,
    safe_answer,
)


def sample_index():
    plans = [
        {
            "insurer": "aia",
            "plan_slug": "health-shield",
            "plan_name": "AIA Health Shield",
        }
    ]
    facts = [
        {
            "insurer": "aia",
            "plan_slug": "health-shield",
            "field_name": "panel_hospitals",
            "field_value": {
                "status": "known",
                "items": [
                    {
                        "normalized_name": "Singapore General Hospital",
                        "source_label": "Panel hospital",
                    }
                ],
            },
            "source_url": "https://example.com/brochure.pdf",
            "last_verified_at": "2026-07-02T00:00:00Z",
        },
        {
            "insurer": "aia",
            "plan_slug": "health-shield",
            "field_name": "claim_sla",
            "field_value": {
                "status": "known",
                "value": {"duration_days": 10, "basis": "published target"},
            },
            "source_url": "https://example.com/claims",
            "last_verified_at": "2026-07-02T00:00:00Z",
        },
        {
            "insurer": "aia",
            "plan_slug": "health-shield",
            "field_name": "exclusions",
            "field_value": {
                "status": "known",
                "items": [{"label": "Pre-existing conditions"}],
            },
            "source_url": "https://example.com/exclusions",
            "last_verified_at": "2026-07-02T00:00:00Z",
        },
    ]
    return PlanFactIndex(plans=plans, facts=facts)


class TelegramBotLookupTests(unittest.TestCase):
    def test_panel_lookup_includes_plan_source_verified_date_and_no_advice(self):
        answer = answer_panel_query(sample_index(), "Singapore General")

        self.assertIn("AIA Health Shield", answer)
        self.assertIn("Singapore General Hospital", answer)
        self.assertIn("https://example.com/brochure.pdf", answer)
        self.assertIn("2026-07-02T00:00:00Z", answer)
        self.assertIn(NO_ADVICE_LINE, answer)

    def test_fact_lookup_filters_by_field_alias(self):
        answer = answer_fact_query(sample_index(), "health-shield claim")

        self.assertIn("Claim SLA: 10 days (published target)", answer)
        self.assertIn("https://example.com/claims", answer)
        self.assertIn(NO_ADVICE_LINE, answer)

    def test_missing_lookup_uses_safe_no_match_message(self):
        answer = answer_panel_query(sample_index(), "Unknown Hospital")

        self.assertIn("No panel-hospital match found.", answer)
        self.assertIn(NO_ADVICE_LINE, answer)

    def test_rate_limiter_blocks_after_window_quota(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        self.assertTrue(limiter.allow("chat-1", now=1))
        self.assertTrue(limiter.allow("chat-1", now=2))
        self.assertFalse(limiter.allow("chat-1", now=3))
        self.assertTrue(limiter.allow("chat-1", now=70))

    def test_safe_answer_returns_rate_limit_and_generic_failure(self):
        limiter = RateLimiter(max_requests=0, window_seconds=60)
        self.assertEqual(
            safe_answer("panel", "Singapore", sample_index(), "chat-1", limiter),
            RATE_LIMIT_MESSAGE,
        )

        class BrokenIndex:
            def lookup_panel_hospital(self, query):
                raise RuntimeError("boom")

        self.assertEqual(
            safe_answer("panel", "Singapore", BrokenIndex(), "chat-2", RateLimiter()),
            SAFE_FAILURE_MESSAGE,
        )

    def test_help_text_documents_commands_and_no_advice(self):
        text = help_text()

        self.assertIn("/panel <hospital name>", text)
        self.assertIn("/fact <plan name or slug>", text)
        self.assertIn(NO_ADVICE_LINE, text)


if __name__ == "__main__":
    unittest.main()
