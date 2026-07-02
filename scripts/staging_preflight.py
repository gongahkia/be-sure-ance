from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

DEFAULT_ROUTES = (
    "/",
    "/matrix/panel-hospitals",
    "/status",
    "/share/11111111-2222-4333-8444-555555555555",
    "/sitemap.xml",
    "/robots.txt",
)
REQUIRED_SECURITY_HEADERS = (
    "content-security-policy",
    "x-content-type-options",
    "referrer-policy",
    "permissions-policy",
)
USER_AGENT = "be-sure-ance-preflight/1.0"


def normalize_origin(origin: str) -> str:
    parsed = urlparse(origin)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("origin must be an absolute http(s) URL")
    return origin.rstrip("/")


def route_url(origin: str, route: str) -> str:
    return urljoin(f"{normalize_origin(origin)}/", route.lstrip("/"))


def fetch_url(url: str, timeout: float = 10.0) -> dict:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    started = time.perf_counter()
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read(4096)
            status = response.status
            headers = dict(response.headers.items())
            error = ""
    except HTTPError as exc:
        body = exc.read(4096)
        status = exc.code
        headers = dict(exc.headers.items())
        error = str(exc)
    except URLError as exc:
        body = b""
        status = 0
        headers = {}
        error = str(exc.reason)

    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    return {
        "url": url,
        "status_code": status,
        "elapsed_ms": elapsed_ms,
        "ok": 200 <= status < 400 and bool(body),
        "bytes_sampled": len(body),
        "headers": headers,
        "error": error,
    }


def smoke_check(origin: str, routes: tuple[str, ...], timeout: float) -> dict:
    route_results = [fetch_url(route_url(origin, route), timeout=timeout) for route in routes]
    return {
        "status": "passed" if all(result["ok"] for result in route_results) else "failed",
        "routes": route_results,
    }


def lowercase_headers(headers: dict) -> dict:
    return {key.lower(): value for key, value in headers.items()}


def security_header_check(home_result: dict, require_hsts: bool) -> dict:
    headers = lowercase_headers(home_result["headers"])
    missing = [header for header in REQUIRED_SECURITY_HEADERS if header not in headers]
    if require_hsts and "strict-transport-security" not in headers:
        missing.append("strict-transport-security")
    invalid = []
    if headers.get("x-content-type-options", "").lower() != "nosniff":
        invalid.append("x-content-type-options")
    return {
        "status": "passed" if not missing and not invalid else "failed",
        "missing_headers": missing,
        "invalid_headers": invalid,
        "observed_headers": {
            header: headers.get(header, "") for header in REQUIRED_SECURITY_HEADERS
        },
    }


def p95_ms(elapsed_values: list[float]) -> float:
    if not elapsed_values:
        return 0.0
    sorted_values = sorted(elapsed_values)
    index = min(len(sorted_values) - 1, int(round((len(sorted_values) - 1) * 0.95)))
    return round(sorted_values[index], 2)


def load_check(
    origin: str,
    path: str,
    request_count: int,
    concurrency: int,
    timeout: float,
    max_p95_ms: float,
) -> dict:
    url = route_url(origin, path)
    results = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(fetch_url, url, timeout) for _ in range(request_count)]
        for future in as_completed(futures):
            results.append(future.result())

    failures = [result for result in results if not result["ok"]]
    p95 = p95_ms([result["elapsed_ms"] for result in results])
    return {
        "status": "passed" if not failures and p95 <= max_p95_ms else "failed",
        "url": url,
        "request_count": request_count,
        "concurrency": concurrency,
        "failure_count": len(failures),
        "p95_ms": p95,
        "max_p95_ms": max_p95_ms,
    }


def run_preflight(
    origin: str,
    routes: tuple[str, ...] = DEFAULT_ROUTES,
    load_path: str = "/status",
    load_requests: int = 24,
    load_concurrency: int = 3,
    timeout: float = 10.0,
    max_p95_ms: float = 1500.0,
) -> dict:
    origin = normalize_origin(origin)
    smoke = smoke_check(origin, routes, timeout)
    home = next(result for result in smoke["routes"] if result["url"] == route_url(origin, "/"))
    security = security_header_check(home, require_hsts=urlparse(origin).scheme == "https")
    load = load_check(origin, load_path, load_requests, load_concurrency, timeout, max_p95_ms)
    checks = (smoke["status"], security["status"], load["status"])
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "origin": origin,
        "overall_status": "passed" if all(status == "passed" for status in checks) else "failed",
        "smoke": smoke,
        "security": security,
        "load": load,
        "compliance_signoff_status": "documented-separately",
    }


def write_report(report: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--origin", required=True)
    parser.add_argument(
        "--output", type=Path, default=Path("output/staging-preflight/preflight.json")
    )
    parser.add_argument("--route", action="append", dest="routes")
    parser.add_argument("--load-path", default="/status")
    parser.add_argument("--load-requests", type=int, default=24)
    parser.add_argument("--load-concurrency", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--max-p95-ms", type=float, default=1500.0)
    args = parser.parse_args()

    routes = tuple(args.routes) if args.routes else DEFAULT_ROUTES
    report = run_preflight(
        args.origin,
        routes=routes,
        load_path=args.load_path,
        load_requests=args.load_requests,
        load_concurrency=args.load_concurrency,
        timeout=args.timeout,
        max_p95_ms=args.max_p95_ms,
    )
    write_report(report, args.output)
    print(f"preflight_report={args.output}")
    print(f"overall_status={report['overall_status']}")
    return 0 if report["overall_status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
