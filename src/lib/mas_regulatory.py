from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import urljoin

from bs4 import BeautifulSoup

MAS_BASE_URL = "https://www.mas.gov.sg"
MAS_NEWS_URL = (
    "https://www.mas.gov.sg/news?"
    "content_type=Enforcement+Actions+Media+Releases&content_type=Media+Releases&page=1"
)
MAS_ENFORCEMENT_URL = "https://www.mas.gov.sg/regulation/enforcement/enforcement-actions"
MAS_DIRECT_NEWS_ITEMS = (
    (
        "Key Enforcement Actions Taken by MAS in Q2 2026",
        "https://www.mas.gov.sg/news/media-releases/2026/key-enforcement-actions-taken-by-mas-in-q2-2026",
    ),
    (
        "Key Enforcement Actions Taken by MAS in Q1 2026",
        "https://www.mas.gov.sg/news/media-releases/2026/key-enforcement-actions-taken-by-mas-in-q1-2026",
    ),
    (
        "Key Enforcement Actions Taken by MAS in Q4 2025",
        "https://www.mas.gov.sg/news/media-releases/2026/key-enforcement-actions-taken-by-mas-in-q4-2025",
    ),
    (
        "Key Regulatory and Enforcement Actions Taken by MAS in Q3 2025",
        "https://www.mas.gov.sg/news/media-releases/2025/key-regulatory-and-enforcement-actions-taken-by-mas-in-q3-2025",
    ),
    (
        "Key Regulatory and Enforcement Actions Taken by MAS in Q2 2025",
        "https://www.mas.gov.sg/news/media-releases/2025/key-regulatory-and-enforcement-actions-taken-by-mas-in-q2-2025",
    ),
    (
        "Key Regulatory and Enforcement Actions Taken by MAS in Q1 2025",
        "https://www.mas.gov.sg/news/media-releases/2025/key-regulatory-and-enforcement-actions-taken-by-mas-in-q1-2025",
    ),
)
MATCHED_STATUS = "matched"
NEEDS_REVIEW_STATUS = "needs_review"

CARRIER_ALIASES = {
    "aia": {
        "name": "AIA Singapore",
        "aliases": ("aia singapore private limited", "aia singapore", "aia"),
    },
    "great_eastern": {
        "name": "Great Eastern Singapore",
        "aliases": (
            "great eastern life assurance",
            "great eastern life",
            "great eastern",
        ),
    },
    "hsbc": {
        "name": "HSBC Life Singapore",
        "aliases": ("hsbc insurance singapore", "hsbc life singapore", "hsbc"),
    },
    "income": {
        "name": "Income Insurance",
        "aliases": ("income insurance", "ntuc income", "income"),
    },
    "manulife": {
        "name": "Manulife Singapore",
        "aliases": ("manulife singapore", "manulife"),
    },
    "prudential": {
        "name": "Prudential Singapore",
        "aliases": ("prudential assurance", "prudential singapore", "prudential"),
    },
    "singlife": {
        "name": "Singlife",
        "aliases": ("singlife", "singapore life", "aviva"),
    },
    "tokio_marine": {
        "name": "Tokio Marine Life Singapore",
        "aliases": ("tokio marine life", "tokio marine"),
    },
    "etiqa": {"name": "Etiqa Singapore", "aliases": ("etiqa insurance", "etiqa")},
    "fwd": {"name": "FWD Singapore", "aliases": ("fwd singapore", "fwd")},
    "raffles_health": {
        "name": "Raffles Health Insurance",
        "aliases": ("raffles health insurance", "raffles health"),
    },
    "chubb": {"name": "Chubb Singapore", "aliases": ("chubb insurance singapore", "chubb")},
    "china_life": {
        "name": "China Life Singapore",
        "aliases": ("china life insurance singapore", "china life singapore", "china life"),
    },
    "iii": {
        "name": "India International Insurance Singapore",
        "aliases": ("india international insurance", "iii"),
    },
    "sunlife": {
        "name": "Sun Life Singapore",
        "aliases": ("sun life assurance company of canada", "sun life singapore", "sun life"),
    },
    "uoi": {
        "name": "United Overseas Insurance",
        "aliases": ("united overseas insurance", "uoi"),
    },
}

EVENT_TYPES = {
    "composition_penalty": ("composition penalty", "composition fine"),
    "reprimand": ("reprimand", "reprimanded"),
    "prohibition_order": ("prohibition order", " po "),
    "revocation": ("revoked", "revocation", "cancelled"),
    "civil_penalty": ("civil penalty",),
    "warning": ("warning",),
}


@dataclass(frozen=True)
class MasNewsItem:
    title: str
    source_url: str
    published_at: str
    summary: str = ""


@dataclass(frozen=True)
class MasRegulatoryEvent:
    carrier_key: str
    carrier_name: str
    event_title: str
    event_type: str
    event_date: str
    source_url: str
    source_type: str
    summary: str
    matched_alias: str
    match_confidence: float
    match_status: str
    source_published_at: str
    limitations: list[str] = field(default_factory=list)
    scraped_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def as_row(self) -> dict:
        return {
            "carrier_key": self.carrier_key,
            "carrier_name": self.carrier_name,
            "event_title": self.event_title,
            "event_type": self.event_type,
            "event_date": self.event_date,
            "source_url": self.source_url,
            "source_type": self.source_type,
            "summary": self.summary,
            "matched_alias": self.matched_alias,
            "match_confidence": self.match_confidence,
            "match_status": self.match_status,
            "source_published_at": self.source_published_at,
            "limitations": self.limitations,
            "scraped_at": self.scraped_at,
            "last_verified_at": self.scraped_at,
        }


def parse_mas_news_listing(html: str, base_url: str = MAS_BASE_URL) -> list[MasNewsItem]:
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for link in soup.find_all("a", href=True):
        title = normalize_whitespace(link.get_text(" ", strip=True))
        href = link.get("href")
        if not title or not href:
            continue
        if "enforcement" not in title.lower() and "enforcement" not in href.lower():
            continue
        container = nearest_container(link)
        container_text = normalize_whitespace(container.get_text(" ", strip=True))
        published_at = extract_date(container_text) or extract_date(title)
        if not published_at:
            continue
        items.append(
            MasNewsItem(
                title=title,
                source_url=urljoin(base_url, href),
                published_at=published_at,
                summary=container_text,
            )
        )
    return dedupe_news_items(items)


def direct_mas_news_items() -> list[MasNewsItem]:
    return [
        MasNewsItem(title=title, source_url=url, published_at="")
        for title, url in MAS_DIRECT_NEWS_ITEMS
    ]


def is_mas_unavailable(html: str) -> bool:
    lowered = normalize_whitespace(html).lower()
    return any(
        marker in lowered
        for marker in (
            "<title>maintenance</title>",
            "this service is currently unavailable",
            "undergoing scheduled maintenance",
            "maintenance.mas.gov.sg",
            "work in progress",
        )
    )


def extract_events_from_text(
    title: str,
    text: str,
    source_url: str,
    published_at: str,
    scraped_at: str | None = None,
) -> list[MasRegulatoryEvent]:
    body = normalize_whitespace(f"{title}. {text}")
    events = []
    for carrier_key, carrier_name, alias, confidence in match_carriers(body):
        status = MATCHED_STATUS if confidence >= 0.85 else NEEDS_REVIEW_STATUS
        context = context_near_match(body, alias)
        event_type = classify_event_type(context or body)
        summary = (context or body)[:480]
        event_date = extract_nearest_date(body, alias) or published_at
        events.append(
            MasRegulatoryEvent(
                carrier_key=carrier_key,
                carrier_name=carrier_name,
                event_title=title,
                event_type=event_type,
                event_date=event_date,
                source_url=source_url,
                source_type="mas_news",
                summary=summary,
                matched_alias=alias,
                match_confidence=confidence,
                match_status=status,
                source_published_at=published_at,
                limitations=[
                    "MAS item is source-linked regulatory context, not advice or a carrier suitability signal.",
                    "Needs-review matches must be verified against the MAS source before use.",
                ],
                scraped_at=scraped_at or datetime.now(timezone.utc).isoformat(),
            )
        )
    return events


def match_carriers(text: str) -> list[tuple[str, str, str, float]]:
    normalized = f" {normalize_whitespace(text).lower()} "
    matches = []
    for carrier_key, carrier in CARRIER_ALIASES.items():
        best_match = None
        for alias in carrier["aliases"]:
            if re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", normalized):
                confidence = 0.7 if len(alias) <= 6 else 0.95
                if best_match is None or confidence > best_match[1]:
                    best_match = (alias, confidence)
        if best_match:
            matches.append((carrier_key, carrier["name"], best_match[0], best_match[1]))
    return matches


def classify_event_type(text: str) -> str:
    normalized = f" {normalize_whitespace(text).lower()} "
    for event_type, needles in EVENT_TYPES.items():
        if any(needle in normalized for needle in needles):
            return event_type
    return "regulatory_item"


def nearest_container(link):
    for parent in link.parents:
        if parent.name in {"article", "li", "tr", "div"}:
            return parent
    return link


def dedupe_news_items(items: list[MasNewsItem]) -> list[MasNewsItem]:
    seen = set()
    deduped = []
    for item in items:
        key = (item.title, item.source_url)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def extract_date(value: str) -> str:
    match = re.search(date_pattern(), value)
    if not match:
        return ""
    return format_date_match(match)


def extract_nearest_date(text: str, needle: str) -> str:
    normalized = normalize_whitespace(text)
    match = re.search(re.escape(needle), normalized, flags=re.IGNORECASE)
    if not match:
        return extract_date(normalized)
    before = normalized[max(0, match.start() - 180) : match.start()]
    before_dates = list(re.finditer(date_pattern(), before))
    if before_dates:
        return format_date_match(before_dates[-1])
    after = normalized[match.end() : match.end() + 180]
    after_dates = list(re.finditer(date_pattern(), after))
    return format_date_match(after_dates[0]) if after_dates else ""


def context_near_match(text: str, needle: str) -> str:
    normalized = normalize_whitespace(text)
    match = re.search(re.escape(needle), normalized, flags=re.IGNORECASE)
    if not match:
        return normalized
    date_matches = list(re.finditer(date_pattern(), normalized))
    prior_dates = [date_match for date_match in date_matches if date_match.start() <= match.start()]
    later_dates = [date_match for date_match in date_matches if date_match.start() > match.start()]
    start = prior_dates[-1].start() if prior_dates else max(0, match.start() - 180)
    end = later_dates[0].start() if later_dates else min(len(normalized), match.end() + 180)
    return normalize_whitespace(normalized[start:end])


def format_date_match(match: re.Match) -> str:
    day, month_name, year = match.groups()
    month = month_number(month_name)
    if not month:
        return ""
    return f"{year}-{month:02d}-{int(day):02d}"


def date_pattern() -> str:
    return r"\b(\d{1,2})\s+([A-Za-z]+)\s+(20\d{2})\b"


def month_number(value: str) -> int:
    months = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }
    return months.get(value.lower(), 0)


def normalize_whitespace(value: str | None) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()
