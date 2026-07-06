import asyncio
import unittest
from pathlib import Path

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from src.lib.http_identity import BOT_USER_AGENT
from src.scrapers import navigation
from src.scrapers.registry import SUPPORTED_SCRAPERS

ROOT = Path(__file__).resolve().parents[1]
SCRAPER_DIR = ROOT / "src/scrapers"


class FakePage:
    def __init__(self, failures=None):
        self.failures = list(failures or [])
        self.goto_calls = []
        self.load_state_calls = []

    async def goto(self, url, wait_until, timeout):
        self.goto_calls.append((url, wait_until, timeout))
        if self.failures:
            raise self.failures.pop(0)
        return {"url": url, "wait_until": wait_until}

    async def wait_for_load_state(self, state, timeout):
        self.load_state_calls.append((state, timeout))


class ScraperNavigationTests(unittest.TestCase):
    def test_bot_user_agent_is_contactable(self):
        self.assertEqual(
            BOT_USER_AGENT,
            "be-sure-ance-bot/1.0 (mailto:gabrielzmong@gmail.com)",
        )

    def test_new_bot_context_sets_user_agent(self):
        class FakeBrowser:
            async def new_context(self, **kwargs):
                return kwargs

        context_kwargs = asyncio.run(navigation.new_bot_context(FakeBrowser()))
        self.assertEqual(context_kwargs["user_agent"], BOT_USER_AGENT)

    def test_goto_with_retry_retries_transient_playwright_errors(self):
        page = FakePage(failures=[PlaywrightError("temporary")])

        response = asyncio.run(
            navigation.goto_with_retry(page, "https://example.com", backoff_seconds=0)
        )

        self.assertEqual(response["url"], "https://example.com")
        self.assertEqual(len(page.goto_calls), 2)
        self.assertEqual(page.goto_calls[0][1], "networkidle")

    def test_goto_with_retry_falls_back_after_networkidle_timeout(self):
        page = FakePage(failures=[PlaywrightTimeoutError("networkidle timeout")])

        response = asyncio.run(
            navigation.goto_with_retry(page, "https://example.com", backoff_seconds=0)
        )

        self.assertEqual(response["wait_until"], "domcontentloaded")
        self.assertEqual(page.load_state_calls, [("networkidle", 5000)])

    def test_gather_scrape_results_logs_and_skips_failed_urls(self):
        async def scrape(url):
            if url.endswith("/bad"):
                raise RuntimeError("boom")
            if url.endswith("/single"):
                return {"url": url}
            return [{"url": url}]

        rows = asyncio.run(
            navigation.gather_scrape_results(
                "test",
                [
                    "https://example.com/list",
                    "https://example.com/bad",
                    "https://example.com/single",
                ],
                scrape,
            )
        )

        self.assertEqual(
            rows,
            [{"url": "https://example.com/list"}, {"url": "https://example.com/single"}],
        )

    def test_supported_scrapers_use_shared_result_gatherer(self):
        for scraper_name in SUPPORTED_SCRAPERS:
            source = (SCRAPER_DIR / f"{scraper_name}.py").read_text()
            with self.subTest(scraper=scraper_name):
                self.assertTrue(
                    "gather_scrape_results" in source
                    or "run_static_product_scraper" in source
                    or "run_cli_scraper" in source
                )

    def test_no_direct_page_goto_outside_navigation_helper(self):
        for path in SCRAPER_DIR.glob("*.py"):
            if path.name in {"navigation.py"}:
                continue
            with self.subTest(path=path.name):
                self.assertNotIn("page.goto", path.read_text())


if __name__ == "__main__":
    unittest.main()
