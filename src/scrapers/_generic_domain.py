from __future__ import annotations

import argparse
import asyncio
import re
from dataclasses import dataclass, field, replace
from typing import Iterable
from urllib.parse import urldefrag, urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from src.backend.helper import initialize_data_store, overwrite_plans_for_insurer
from src.lib.search import search_wrapper
from src.scrapers.navigation import goto_with_retry, new_bot_context

DEFAULT_SEARCH_QUERY = (
    "insurance protection plan policy health life medical hospital accident "
    "travel motor home benefits brochure coverage claim support"
)
DEFAULT_EXCLUDED_KEYWORDS = (
    "claim",
    "claims",
    "career",
    "careers",
    "press",
    "newsroom",
    "privacy",
    "terms",
    "sitemap",
    "contact-us",
)


@dataclass
class GenericScraperConfig:
    table_name: str
    search_query: str = DEFAULT_SEARCH_QUERY
    excluded_keywords: tuple[str, ...] = DEFAULT_EXCLUDED_KEYWORDS
    max_seed_pages: int = 24
    max_follow_links: int = 6
    max_bullet_points: int = 6
    timeout_ms: int = 45000
    explicit_skip_contains: tuple[str, ...] = field(default_factory=tuple)


def extract_urls(module_doc: str | None) -> list[str]:
    if not module_doc:
        return []
    return [match.rstrip(".,") for match in re.findall(r"https?://[^\s\"']+", module_doc)]


def normalize_whitespace(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def normalize_text_block(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\n{2,}", "\n\n", re.sub(r"[ \t]+", " ", value)).strip()


def should_skip_url(url: str, excluded_keywords: Iterable[str]) -> bool:
    lowered = url.lower()
    return any(keyword in lowered for keyword in excluded_keywords)


def compact_text(value: str, limit: int = 1200) -> str:
    value = normalize_text_block(value)
    if len(value) <= limit:
        return value
    return f"{value[: limit - 1].rstrip()}…"


def dedupe_preserve_order(values: Iterable[str]) -> list[str]:
    seen = set()
    output = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            output.append(value)
    return output


async def read_page(page, url: str, config: GenericScraperConfig):
    await goto_with_retry(page, url, timeout_ms=config.timeout_ms)
    html = await page.content()
    soup = BeautifulSoup(html, "html.parser")

    for element in soup(["script", "style", "noscript"]):
        element.decompose()

    title = normalize_whitespace(soup.title.get_text(" ", strip=True) if soup.title else "")
    h1 = normalize_whitespace(soup.find("h1").get_text(" ", strip=True) if soup.find("h1") else "")

    paragraphs = [
        normalize_whitespace(paragraph.get_text(" ", strip=True))
        for paragraph in soup.find_all(["p", "article", "section"], limit=12)
    ]
    paragraphs = [paragraph for paragraph in paragraphs if paragraph]

    bullets = [
        normalize_whitespace(item.get_text(" ", strip=True))
        for item in soup.find_all(["li"], limit=24)
    ]
    bullets = [bullet for bullet in bullets if bullet]

    pdf_links = []
    internal_links = []
    base_host = urlparse(url).netloc
    for anchor in soup.find_all("a", href=True):
        href = urljoin(url, anchor["href"])
        href = urldefrag(href).url
        anchor_text = normalize_whitespace(anchor.get_text(" ", strip=True))
        parsed_href = urlparse(href)
        if parsed_href.scheme not in {"http", "https"}:
            continue
        if href.lower().endswith(".pdf"):
            pdf_links.append(href)
        if parsed_href.netloc == base_host:
            internal_links.append({"url": href, "text": anchor_text})

    body_text = normalize_text_block(
        "\n\n".join(filter(None, [h1, title, *paragraphs[:8], *bullets[:8]]))
    )
    searchable_text = " ".join(filter(None, [title, h1, body_text, " ".join(bullets[:10])]))

    return {
        "url": url,
        "title": title,
        "h1": h1,
        "paragraphs": paragraphs,
        "bullets": bullets,
        "pdf_links": dedupe_preserve_order(pdf_links),
        "internal_links": internal_links,
        "searchable_text": searchable_text,
    }


def score_candidates(
    search_query: str, links: list[dict], excluded_keywords: Iterable[str], limit: int
):
    filtered_links = [
        link
        for link in links
        if link["url"] and not should_skip_url(link["url"], excluded_keywords)
    ]
    corpus = [normalize_whitespace(f'{link["text"]} {link["url"]}') for link in filtered_links]
    ranked = search_wrapper(search_query, corpus, method="hybrid", threshold=0.12, limit=limit)

    ranked_urls = []
    for match in ranked:
        index = corpus.index(match["text"])
        ranked_urls.append(filtered_links[index]["url"])
    return dedupe_preserve_order(ranked_urls)[:limit]


def should_include_page(page_data: dict, config: GenericScraperConfig):
    haystack = f'{page_data["url"]} {page_data["title"]} {page_data["h1"]} {page_data["searchable_text"]}'.lower()
    if any(keyword in haystack for keyword in config.explicit_skip_contains):
        return False
    if should_skip_url(page_data["url"], config.excluded_keywords):
        return False
    if len(page_data["searchable_text"]) < 120:
        return False
    return bool(
        search_wrapper(
            config.search_query, [page_data["searchable_text"]], method="hybrid", threshold=0.12
        )
    )


def build_plan_record(page_data: dict, config: GenericScraperConfig):
    plan_name = normalize_whitespace(page_data["h1"] or page_data["title"])
    if not plan_name:
        return None

    description = normalize_whitespace(
        page_data["paragraphs"][0] if page_data["paragraphs"] else ""
    )
    overview_source = (
        page_data["paragraphs"][1:4]
        if len(page_data["paragraphs"]) > 1
        else page_data["paragraphs"][:2]
    )
    overview = compact_text("\n\n".join(overview_source))
    if not overview:
        overview = compact_text(page_data["searchable_text"])

    benefits = dedupe_preserve_order(page_data["bullets"][: config.max_bullet_points])

    return {
        "plan_name": plan_name,
        "plan_benefits": benefits,
        "plan_description": description,
        "plan_overview": overview,
        "plan_url": page_data["url"],
        "product_brochure_url": page_data["pdf_links"][0] if page_data["pdf_links"] else "",
    }


async def scrape_generic_insurer(config: GenericScraperConfig, module_doc: str | None):
    seed_urls = extract_urls(module_doc)[: config.max_seed_pages]
    if not seed_urls:
        raise ValueError(f"No seed URLs found for {config.table_name}")

    visited = set()
    queued = dedupe_preserve_order(seed_urls)
    plans = []
    emitted_keys = set()

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await new_bot_context(browser)
        page = await context.new_page()

        while queued and len(visited) < config.max_seed_pages:
            url = queued.pop(0)
            if url in visited:
                continue

            visited.add(url)
            try:
                page_data = await read_page(page, url, config)
            except Exception as exc:
                print(f"[{config.table_name}] skipping {url}: {exc}")
                continue

            if should_include_page(page_data, config):
                plan = build_plan_record(page_data, config)
                if plan:
                    plan_key = f'{plan["plan_name"]}|{plan["plan_url"]}'
                    if plan_key not in emitted_keys:
                        emitted_keys.add(plan_key)
                        plans.append(plan)

            candidate_urls = score_candidates(
                config.search_query,
                page_data["internal_links"],
                config.excluded_keywords,
                limit=config.max_follow_links,
            )
            for candidate_url in candidate_urls:
                if candidate_url not in visited and candidate_url not in queued:
                    queued.append(candidate_url)

        await browser.close()

    return plans


def run_cli_scraper(config: GenericScraperConfig, module_doc: str | None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-seed-pages", type=int)
    parser.add_argument("--max-follow-links", type=int)
    parser.add_argument("--timeout-ms", type=int)
    args = parser.parse_args()

    runtime_config = replace(
        config,
        max_seed_pages=args.max_seed_pages or config.max_seed_pages,
        max_follow_links=args.max_follow_links or config.max_follow_links,
        timeout_ms=args.timeout_ms or config.timeout_ms,
    )
    rows = asyncio.run(scrape_generic_insurer(runtime_config, module_doc))
    print(f"[{config.table_name}] produced {len(rows)} plan rows")

    if args.dry_run or not rows:
        return

    initialize_data_store()
    overwrite_plans_for_insurer(config.table_name, rows)
