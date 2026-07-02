from __future__ import annotations

import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree

USER_AGENT = "be-sure-ance-indexing-preflight/1.0"
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
FORBIDDEN_JSON_LD_KEYS = {
    "annualPercentageRate",
    "feesAndCommissionsSpecification",
    "interestRate",
    "offers",
    "premium",
    "deductible",
    "coinsurance",
}


class HeadMetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.canonical = ""
        self.description = ""
        self._in_json_ld = False
        self.json_ld_chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key.lower(): value or "" for key, value in attrs}
        if tag == "link" and attr_map.get("rel") == "canonical":
            self.canonical = attr_map.get("href", "")
        if tag == "meta" and attr_map.get("name") == "description":
            self.description = attr_map.get("content", "")
        if tag == "script" and attr_map.get("type") == "application/ld+json":
            self._in_json_ld = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self._in_json_ld = False

    def handle_data(self, data: str) -> None:
        if self._in_json_ld:
            self.json_ld_chunks.append(data)


def fetch_text(url: str, timeout: float = 15.0) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        if response.status >= 400:
            raise RuntimeError(f"{url} returned HTTP {response.status}")
        return response.read().decode("utf-8", errors="replace")


def read_text_from_dist(dist_dir: Path, route: str) -> str:
    route = route.strip("/") or "index"
    if route == "sitemap.xml":
        return (dist_dir / "sitemap.xml").read_text()
    if route == "robots.txt":
        return (dist_dir / "robots.txt").read_text()
    index_path = dist_dir / route / "index.html"
    if route == "index":
        index_path = dist_dir / "index.html"
    return index_path.read_text()


def load_route(origin: str, dist_dir: Path | None, route: str) -> str:
    if dist_dir:
        return read_text_from_dist(dist_dir, route)
    return fetch_text(f"{origin.rstrip('/')}/{route.lstrip('/')}")


def validate_sitemap(sitemap_xml: str, origin: str) -> dict:
    root = ElementTree.fromstring(sitemap_xml)
    locs = [element.text or "" for element in root.findall(".//sm:loc", SITEMAP_NS)]
    if not locs:
        locs = [element.text or "" for element in root.findall(".//loc")]
    invalid = [loc for loc in locs if not loc.startswith(origin.rstrip("/") + "/")]
    duplicates = sorted({loc for loc in locs if locs.count(loc) > 1})
    return {
        "status": "passed" if locs and not invalid and not duplicates else "failed",
        "url_count": len(locs),
        "invalid_origin_urls": invalid,
        "duplicate_urls": duplicates,
        "plan_urls": [loc for loc in locs if "/plan/" in loc],
    }


def validate_robots(robots_txt: str, origin: str) -> dict:
    expected = f"Sitemap: {origin.rstrip('/')}/sitemap.xml"
    return {
        "status": "passed" if expected in robots_txt else "failed",
        "expected_sitemap_directive": expected,
    }


def contains_forbidden_key(value) -> bool:
    if isinstance(value, dict):
        return any(
            key in FORBIDDEN_JSON_LD_KEYS or contains_forbidden_key(entry)
            for key, entry in value.items()
        )
    if isinstance(value, list):
        return any(contains_forbidden_key(entry) for entry in value)
    return False


def validate_plan_page(html: str, expected_canonical: str) -> dict:
    parser = HeadMetadataParser()
    parser.feed(html)
    json_ld = json.loads("".join(parser.json_ld_chunks) or "{}")
    checks = {
        "canonical_matches": parser.canonical == expected_canonical,
        "description_present": bool(parser.description),
        "json_ld_type": json_ld.get("@type") == "FinancialProduct",
        "json_ld_url_matches": json_ld.get("url") == expected_canonical,
        "json_ld_has_subjects": bool(json_ld.get("subjectOf")),
        "json_ld_avoids_quantitative_offer_fields": not contains_forbidden_key(json_ld),
    }
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "canonical": parser.canonical,
        "checks": checks,
    }


def route_from_url(origin: str, url: str) -> str:
    return "/" + url.removeprefix(origin.rstrip("/") + "/").lstrip("/")


def run_preflight(origin: str, dist_dir: Path | None = None, representative_limit: int = 3) -> dict:
    origin = origin.rstrip("/")
    sitemap_xml = load_route(origin, dist_dir, "/sitemap.xml")
    robots_txt = load_route(origin, dist_dir, "/robots.txt")
    sitemap = validate_sitemap(sitemap_xml, origin)
    robots = validate_robots(robots_txt, origin)
    plan_results = []
    for plan_url in sitemap["plan_urls"][:representative_limit]:
        route = route_from_url(origin, plan_url)
        plan_results.append(validate_plan_page(load_route(origin, dist_dir, route), plan_url))

    statuses = [sitemap["status"], robots["status"], *(result["status"] for result in plan_results)]
    return {
        "origin": origin,
        "mode": "dist" if dist_dir else "origin",
        "overall_status": (
            "passed" if statuses and all(status == "passed" for status in statuses) else "failed"
        ),
        "sitemap": sitemap,
        "robots": robots,
        "representative_plan_pages": plan_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--origin", required=True)
    parser.add_argument("--dist-dir", type=Path)
    parser.add_argument(
        "--output", type=Path, default=Path("output/search-indexing/preflight.json")
    )
    parser.add_argument("--representative-limit", type=int, default=3)
    args = parser.parse_args()

    parsed = urlparse(args.origin)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("--origin must be an absolute http(s) origin")

    try:
        report = run_preflight(
            args.origin, dist_dir=args.dist_dir, representative_limit=args.representative_limit
        )
    except Exception as exc:
        report = {
            "origin": args.origin.rstrip("/"),
            "mode": "dist" if args.dist_dir else "origin",
            "overall_status": "failed",
            "error": str(exc),
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"search_indexing_report={args.output}")
    print(f"overall_status={report['overall_status']}")
    return 0 if report["overall_status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
