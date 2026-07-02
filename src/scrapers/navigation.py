from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Iterable

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from src.lib.http_identity import BOT_USER_AGENT

DEFAULT_NAVIGATION_TIMEOUT_MS = 60000
DEFAULT_NETWORKIDLE_TIMEOUT_MS = 5000
DEFAULT_NAVIGATION_RETRIES = 3
DEFAULT_BACKOFF_SECONDS = 1.0


async def new_bot_context(browser, **kwargs):
    return await browser.new_context(user_agent=BOT_USER_AGENT, **kwargs)


async def goto_with_retry(
    page,
    url: str,
    *,
    timeout_ms: int = DEFAULT_NAVIGATION_TIMEOUT_MS,
    wait_until: str = "networkidle",
    fallback_wait_until: str = "domcontentloaded",
    retries: int = DEFAULT_NAVIGATION_RETRIES,
    backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
    networkidle_timeout_ms: int = DEFAULT_NETWORKIDLE_TIMEOUT_MS,
):
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            return await page.goto(url, wait_until=wait_until, timeout=timeout_ms)
        except PlaywrightTimeoutError as error:
            last_error = error
            if wait_until == "networkidle" and fallback_wait_until:
                try:
                    response = await page.goto(
                        url,
                        wait_until=fallback_wait_until,
                        timeout=timeout_ms,
                    )
                    try:
                        await page.wait_for_load_state(
                            "networkidle",
                            timeout=min(timeout_ms, networkidle_timeout_ms),
                        )
                    except PlaywrightTimeoutError as idle_error:
                        print(f"[navigation] networkidle fallback timeout for {url}: {idle_error}")
                    return response
                except PlaywrightError as fallback_error:
                    last_error = fallback_error
        except PlaywrightError as error:
            last_error = error

        print(f"[navigation] attempt {attempt}/{retries} failed for {url}: {last_error}")
        if attempt < retries:
            await asyncio.sleep(backoff_seconds * (2 ** (attempt - 1)))

    raise last_error or RuntimeError(f"Navigation failed for {url}")


def log_url_failure(scraper_name: str, url: str, error: Exception):
    print(f"[{scraper_name}] skipping {url}: {type(error).__name__}: {error}")


async def gather_scrape_results(
    scraper_name: str,
    scrape_list: Iterable[str],
    scrape_func: Callable[[str], Awaitable[list[dict] | dict | None]],
) -> list[dict]:
    urls = list(scrape_list)
    results = await asyncio.gather(
        *(scrape_func(url) for url in urls),
        return_exceptions=True,
    )

    rows = []
    for url, result in zip(urls, results):
        if isinstance(result, Exception):
            log_url_failure(scraper_name, url, result)
            continue
        if isinstance(result, list):
            rows.extend(result)
        elif result:
            rows.append(result)
    return rows
