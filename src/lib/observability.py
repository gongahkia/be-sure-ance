from __future__ import annotations

import os
import re
from copy import deepcopy
from typing import Any

import sentry_sdk
from dotenv import load_dotenv

SECRET_PATTERNS = (
    re.compile(r"Bearer\s+[A-Za-z0-9._-]+", re.IGNORECASE),
    re.compile(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"),
)
SENSITIVE_KEYS = {
    "authorization",
    "apikey",
    "cookie",
    "set-cookie",
    "telegram_bot_token",
    "sentry_dsn",
}
_initialized = False


def initialize_observability(surface: str = "scraper") -> bool:
    global _initialized
    if _initialized:
        return True

    load_dotenv()
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return False

    sentry_sdk.init(
        dsn=dsn,
        environment=os.getenv("SENTRY_ENVIRONMENT") or os.getenv("ENVIRONMENT") or "local",
        release=os.getenv("SENTRY_RELEASE"),
        traces_sample_rate=parse_sample_rate(os.getenv("SENTRY_TRACES_SAMPLE_RATE")),
        send_default_pii=False,
        before_send=sanitize_event,
    )
    sentry_sdk.set_tag("surface", surface)
    _initialized = True
    return True


def capture_scraper_exception(
    carrier_key: str,
    error: BaseException,
    *,
    source_url: str | None = None,
    context: dict[str, Any] | None = None,
) -> str | None:
    initialize_observability("scraper")
    with sentry_sdk.new_scope() as scope:
        scope.set_tag("surface", "scraper")
        scope.set_tag("carrier", carrier_key)
        scope.set_context(
            "scraper",
            scrub(
                {
                    "carrier_key": carrier_key,
                    "source_url": source_url,
                    **(context or {}),
                }
            ),
        )
        return sentry_sdk.capture_exception(error)


def sanitize_event(event, hint):
    return scrub(deepcopy(event))


def scrub(value):
    if isinstance(value, dict):
        scrubbed = {}
        for key, child in value.items():
            if str(key).lower() in SENSITIVE_KEYS:
                scrubbed[key] = "[redacted]"
            else:
                scrubbed[key] = scrub(child)
        return scrubbed
    if isinstance(value, list):
        return [scrub(item) for item in value]
    if isinstance(value, tuple):
        return tuple(scrub(item) for item in value)
    if isinstance(value, str):
        return scrub_text(value)
    return value


def scrub_text(value: str) -> str:
    text = value
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("[redacted]", text)
    return text


def parse_sample_rate(value: str | None) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0
