from __future__ import annotations

import argparse
import ast
import io
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

import src.backend.helper as helper
from src.backend.helper import initialize_supabase, overwrite_generic_table_data
from src.lib.http_identity import BOT_USER_AGENT

SCRAPER_DIR = Path(__file__).resolve().parent
SUPPORTED_INSURERS = (
    "aia",
    "uoi",
    "china_life",
    "chubb",
    "tokio_marine",
    "sunlife",
    "singlife",
    "great_eastern",
    "hsbc",
    "iii",
)
PLAN_KEYWORDS = (
    "accident",
    "medical",
    "health",
    "hospital",
    "critical illness",
    "life",
    "shield",
    "care",
)
RESOURCE_KEYWORDS = (
    "specialist",
    "panel",
    "hospital list",
    "hospital",
    "medical provider",
    "provider",
    "medical network",
    "network",
    "directory",
)
USER_AGENT = BOT_USER_AGENT


def normalize_whitespace(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "resource"


def extract_urls(module_doc: str | None) -> list[str]:
    if not module_doc:
        return []

    urls = []
    seen = set()
    for match in re.findall(r"https?://[^\s\"']+", module_doc):
        candidate = match.rstrip(".,")
        if candidate in seen:
            continue
        seen.add(candidate)
        urls.append(candidate)
    return urls


def read_scraper_docstring(insurer: str) -> str | None:
    scraper_path = SCRAPER_DIR / f"{insurer}.py"
    if not scraper_path.exists():
        return None
    tree = ast.parse(scraper_path.read_text(), filename=str(scraper_path))
    return ast.get_docstring(tree)


def insurer_seed_urls(insurer: str) -> list[str]:
    docstring = read_scraper_docstring(insurer)
    return extract_urls(docstring)[:3]


def is_supported_plan(plan: dict) -> bool:
    haystack = normalize_whitespace(
        " ".join(
            [
                plan.get("plan_name", ""),
                plan.get("plan_description", ""),
                plan.get("plan_overview", ""),
                " ".join(plan.get("plan_benefits") or []),
            ]
        )
    ).lower()
    return any(keyword in haystack for keyword in PLAN_KEYWORDS)


def dedupe_by_url(candidates: list[dict]) -> list[dict]:
    seen = set()
    deduped = []
    for candidate in candidates:
        url = candidate["url"]
        if not url or url in seen:
            continue
        seen.add(url)
        deduped.append(candidate)
    return deduped


def discover_pdf_candidates(
    seed_url: str,
    request_timeout: int,
    session: requests.Session,
    html_cache: dict[str, list[dict]],
) -> list[dict]:
    if not seed_url:
        return []
    if seed_url in html_cache:
        return html_cache[seed_url]

    candidates = []
    try:
        response = session.get(seed_url, timeout=request_timeout)
        response.raise_for_status()
    except Exception:
        html_cache[seed_url] = []
        return []

    content_type = response.headers.get("content-type", "").lower()
    if "pdf" in content_type or seed_url.lower().endswith(".pdf"):
        filename = Path(urlparse(seed_url).path).name or "provider-resource.pdf"
        candidates = [
            {
                "url": seed_url,
                "title": filename,
                "context": "",
                "source_url": seed_url,
            }
        ]
        html_cache[seed_url] = candidates
        return candidates

    soup = BeautifulSoup(response.text, "html.parser")
    for anchor in soup.find_all("a", href=True):
        href = urljoin(seed_url, anchor["href"])
        parsed = urlparse(href)
        if parsed.scheme not in {"http", "https"}:
            continue
        if not href.lower().endswith(".pdf"):
            continue

        context = normalize_whitespace(anchor.parent.get_text(" ", strip=True))
        candidates.append(
            {
                "url": href,
                "title": normalize_whitespace(anchor.get_text(" ", strip=True)),
                "context": context[:400],
                "source_url": seed_url,
            }
        )

    html_cache[seed_url] = dedupe_by_url(candidates)
    return html_cache[seed_url]


def extract_pdf_text(
    url: str,
    request_timeout: int,
    session: requests.Session,
    pdf_cache: dict[str, str],
    max_pages: int = 5,
) -> str:
    if url in pdf_cache:
        return pdf_cache[url]

    try:
        response = session.get(url, timeout=request_timeout)
        response.raise_for_status()
        reader = PdfReader(io.BytesIO(response.content))
        pages = []
        for page in reader.pages[:max_pages]:
            try:
                pages.append(page.extract_text() or "")
            except Exception:
                continue
        pdf_cache[url] = normalize_whitespace("\n".join(pages))
    except Exception:
        pdf_cache[url] = ""

    return pdf_cache[url]


def matched_resource_keywords(text: str) -> list[str]:
    lowered = text.lower()
    return sorted({keyword for keyword in RESOURCE_KEYWORDS if keyword in lowered})


def infer_resource_type(keywords: list[str]) -> str:
    if any("specialist" in keyword for keyword in keywords):
        return "specialist_list"
    if any(keyword in {"panel", "hospital list", "medical provider"} for keyword in keywords):
        return "panel_list"
    return "provider_directory"


def description_snippet(pdf_text: str) -> str:
    if not pdf_text:
        return ""
    snippet = pdf_text[:280].strip()
    return f"{snippet}..." if len(pdf_text) > 280 else snippet


def fetch_plans(insurer: str) -> list[dict]:
    response = helper.supabase.table("plans").select("*").eq("insurer", insurer).execute()
    return response.data or []


def gather_candidates_for_insurer(
    insurer: str,
    plans: list[dict],
    request_timeout: int,
    session: requests.Session,
    html_cache: dict[str, list[dict]],
) -> list[dict]:
    seed_urls = insurer_seed_urls(insurer)
    for plan in plans:
        if plan.get("plan_url"):
            seed_urls.append(plan["plan_url"])
        if plan.get("product_brochure_url"):
            seed_urls.append(plan["product_brochure_url"])

    candidates = []
    for seed_url in seed_urls:
        candidates.extend(
            discover_pdf_candidates(
                seed_url=seed_url,
                request_timeout=request_timeout,
                session=session,
                html_cache=html_cache,
            )
        )
    return dedupe_by_url(candidates)


def build_resource_row(
    insurer: str, plan: dict, candidate: dict, keywords: list[str], pdf_text: str
) -> dict:
    title = candidate["title"] or Path(urlparse(candidate["url"]).path).name or "Provider resource"
    return {
        "insurer": insurer,
        "plan_name": plan["plan_name"],
        "resource_type": infer_resource_type(keywords),
        "resource_title": normalize_whitespace(title),
        "resource_url": candidate["url"],
        "resource_description": description_snippet(pdf_text) or candidate["context"],
        "resource_keywords": keywords,
        "source_url": candidate["source_url"],
    }


def run_panel_resource_scrape(
    insurers: list[str], request_timeout: int, max_plans: int | None
) -> list[dict]:
    html_cache: dict[str, list[dict]] = {}
    pdf_cache: dict[str, str] = {}
    rows = []
    emitted = set()

    with requests.Session() as session:
        session.headers.update({"User-Agent": USER_AGENT})

        for insurer in insurers:
            all_plans = fetch_plans(insurer)
            supported_plans = [plan for plan in all_plans if is_supported_plan(plan)]
            if max_plans is not None:
                supported_plans = supported_plans[:max_plans]

            candidates = gather_candidates_for_insurer(
                insurer=insurer,
                plans=supported_plans,
                request_timeout=request_timeout,
                session=session,
                html_cache=html_cache,
            )

            relevant_resources = []
            for candidate in candidates:
                pdf_text = extract_pdf_text(
                    url=candidate["url"],
                    request_timeout=request_timeout,
                    session=session,
                    pdf_cache=pdf_cache,
                )
                combined_text = normalize_whitespace(
                    " ".join([candidate["url"], candidate["title"], candidate["context"], pdf_text])
                )
                keywords = matched_resource_keywords(combined_text)
                if len(keywords) < 2:
                    continue

                relevant_resources.append(
                    {
                        "candidate": candidate,
                        "keywords": keywords,
                        "pdf_text": pdf_text,
                    }
                )

            for plan in supported_plans:
                for resource in relevant_resources:
                    key = (insurer, plan["plan_name"], resource["candidate"]["url"])
                    if key in emitted:
                        continue
                    emitted.add(key)
                    rows.append(
                        build_resource_row(
                            insurer=insurer,
                            plan=plan,
                            candidate=resource["candidate"],
                            keywords=resource["keywords"],
                            pdf_text=resource["pdf_text"],
                        )
                    )

    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--insurers", help="Comma-separated supported insurer table names.")
    parser.add_argument("--request-timeout", type=int, default=20)
    parser.add_argument("--max-plans", type=int)
    args = parser.parse_args()

    insurers = (
        [item.strip() for item in args.insurers.split(",") if item.strip()]
        if args.insurers
        else list(SUPPORTED_INSURERS)
    )

    initialize_supabase()
    rows = run_panel_resource_scrape(
        insurers=insurers,
        request_timeout=args.request_timeout,
        max_plans=args.max_plans,
    )

    summary = {
        "insurers": insurers,
        "resource_count": len(rows),
        "resources_by_insurer": {
            insurer: sum(1 for row in rows if row["insurer"] == insurer) for insurer in insurers
        },
    }
    print(json.dumps(summary, indent=2, sort_keys=True))

    if args.dry_run:
        return

    overwrite_generic_table_data("specialist_resources", rows)


if __name__ == "__main__":
    main()
