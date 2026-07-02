from __future__ import annotations

import argparse
import ast
import difflib
import hashlib
import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, Tag

from src.lib.http_identity import BOT_USER_AGENT
from src.scrapers.registry import SUPPORTED_SCRAPERS

SCRAPER_DIR = Path(__file__).resolve().parents[1] / "scrapers"
DEFAULT_OUTPUT_DIR = Path(".validation-output")
EXCLUDED_SCRAPER_FILES = {"__init__.py", "_generic_domain.py", "run_all.py"}
USER_AGENT = BOT_USER_AGENT


@dataclass(frozen=True)
class ValidationTarget:
    insurer: str
    url: str
    domain: str
    source_file: str


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "root"


def extract_urls(module_doc: str | None) -> list[str]:
    if not module_doc:
        return []

    unique_urls = []
    seen = set()
    for match in re.findall(r"https?://[^\s\"']+", module_doc):
        candidate = match.rstrip(".,")
        parsed = urlparse(candidate)
        if parsed.scheme not in {"http", "https"}:
            continue
        if candidate.lower().endswith(".pdf"):
            continue
        if candidate in seen:
            continue
        seen.add(candidate)
        unique_urls.append(candidate)
    return unique_urls


def discover_targets(
    scraper_dir: Path = SCRAPER_DIR,
    max_urls_per_insurer: int = 2,
) -> list[ValidationTarget]:
    targets: list[ValidationTarget] = []
    for path in sorted(scraper_dir.glob("*.py")):
        if path.name in EXCLUDED_SCRAPER_FILES:
            continue
        if path.stem not in SUPPORTED_SCRAPERS:
            continue

        tree = ast.parse(path.read_text(), filename=str(path))
        urls = extract_urls(ast.get_docstring(tree))
        for url in urls[:max_urls_per_insurer]:
            domain = urlparse(url).netloc.lower().removeprefix("www.")
            targets.append(
                ValidationTarget(
                    insurer=path.stem,
                    url=url,
                    domain=domain,
                    source_file=path.name,
                )
            )
    return targets


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def fetch_html(url: str, request_timeout: int) -> str:
    response = requests.get(
        url,
        timeout=request_timeout,
        headers={"User-Agent": USER_AGENT},
    )
    response.raise_for_status()
    return response.text


def sanitize_html(html: str) -> BeautifulSoup:
    soup = BeautifulSoup(html, "html.parser")
    root = soup.body or soup
    for element in root(["script", "style", "noscript", "svg"]):
        element.decompose()
    for element in root.find_all(attrs=True):
        for attribute in list(element.attrs):
            if attribute in {"style", "class", "id", "data-testid"} or attribute.startswith(
                "data-"
            ):
                del element.attrs[attribute]
    return soup


def iter_child_tags(node: Tag) -> Iterable[Tag]:
    for child in node.children:
        if isinstance(child, Tag):
            yield child


def collect_tag_sequence(node: Tag) -> list[str]:
    sequence = [node.name]
    for child in iter_child_tags(node):
        sequence.extend(collect_tag_sequence(child))
    return sequence


def collect_paths(node: Tag, parent_path: str = "") -> list[str]:
    current_path = f"{parent_path}/{node.name}"
    paths = [current_path]
    for child in iter_child_tags(node):
        paths.extend(collect_paths(child, current_path))
    return paths


def snapshot_from_html(target: ValidationTarget, html: str) -> dict:
    soup = sanitize_html(html)
    root = soup.body or soup

    tag_sequence = collect_tag_sequence(root)
    unique_paths = sorted(set(collect_paths(root)))
    normalized_text = normalize_text(" ".join(root.stripped_strings))
    normalized_html = normalize_text(str(root))
    parsed_url = urlparse(target.url)
    path_identifier = parsed_url.path or "root"
    if parsed_url.query:
        path_identifier = f"{path_identifier}?{parsed_url.query}"
    path_slug = slugify(path_identifier)

    return {
        "insurer": target.insurer,
        "url": target.url,
        "domain": target.domain,
        "source_file": target.source_file,
        "path_slug": path_slug,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "root_tag": root.name,
        "tag_sequence": tag_sequence,
        "tag_count": len(tag_sequence),
        "unique_paths": unique_paths,
        "unique_path_count": len(unique_paths),
        "structure_hash": sha256_text("\n".join(unique_paths)),
        "text_hash": sha256_text(normalized_text),
        "normalized_html": normalized_html,
    }


def load_snapshot(snapshot_path: Path) -> dict | None:
    if not snapshot_path.exists():
        return None
    return json.loads(snapshot_path.read_text())


def compare_snapshot_pair(
    baseline_snapshot: dict,
    current_snapshot: dict,
    max_path_drift: float,
    max_tag_drift: float,
) -> dict:
    baseline_paths = set(baseline_snapshot["unique_paths"])
    current_paths = set(current_snapshot["unique_paths"])
    union = baseline_paths | current_paths
    symmetric_difference = baseline_paths ^ current_paths

    path_drift = (len(symmetric_difference) / len(union)) if union else 0.0
    tag_similarity = difflib.SequenceMatcher(
        None,
        baseline_snapshot["tag_sequence"],
        current_snapshot["tag_sequence"],
    ).ratio()
    tag_drift = 1 - tag_similarity

    added_paths = sorted(current_paths - baseline_paths)[:20]
    removed_paths = sorted(baseline_paths - current_paths)[:20]
    failures = []

    if baseline_snapshot["root_tag"] != current_snapshot["root_tag"]:
        failures.append(
            f'Root tag changed from "{baseline_snapshot["root_tag"]}" '
            f'to "{current_snapshot["root_tag"]}"'
        )
    if path_drift > max_path_drift:
        failures.append(f"Path drift {path_drift:.3f} exceeded threshold {max_path_drift:.3f}")
    if tag_drift > max_tag_drift:
        failures.append(f"Tag drift {tag_drift:.3f} exceeded threshold {max_tag_drift:.3f}")

    return {
        "status": "failed" if failures else "passed",
        "path_drift": round(path_drift, 6),
        "tag_drift": round(tag_drift, 6),
        "tag_similarity": round(tag_similarity, 6),
        "structure_hash_changed": baseline_snapshot["structure_hash"]
        != current_snapshot["structure_hash"],
        "text_hash_changed": baseline_snapshot["text_hash"] != current_snapshot["text_hash"],
        "added_paths": added_paths,
        "removed_paths": removed_paths,
        "failures": failures,
    }


def snapshot_output_path(output_dir: Path, snapshot: dict) -> Path:
    domain_slug = slugify(snapshot["domain"])
    return (
        output_dir
        / "snapshots"
        / snapshot["insurer"]
        / f"{domain_slug}__{snapshot['path_slug']}.json"
    )


def snapshot_html_path(output_dir: Path, snapshot: dict) -> Path:
    domain_slug = slugify(snapshot["domain"])
    return (
        output_dir
        / "snapshots"
        / snapshot["insurer"]
        / f"{domain_slug}__{snapshot['path_slug']}.html"
    )


def baseline_snapshot_path(baseline_dir: Path, snapshot: dict) -> Path:
    return snapshot_output_path(baseline_dir, snapshot)


def write_snapshot_artifacts(output_dir: Path, snapshot: dict) -> tuple[Path, Path]:
    json_path = snapshot_output_path(output_dir, snapshot)
    html_path = snapshot_html_path(output_dir, snapshot)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(snapshot, indent=2, sort_keys=True))
    html_path.write_text(snapshot["normalized_html"])
    return json_path, html_path


def build_summary_markdown(report: dict) -> str:
    lines = [
        "# Validation Summary",
        "",
        f'- Targets checked: {report["summary"]["total_targets"]}',
        f'- Passed: {report["summary"]["passed"]}',
        f'- Failed: {report["summary"]["failed"]}',
        f'- Errors: {report["summary"]["errors"]}',
        f'- No baseline: {report["summary"]["no_baseline"]}',
        "",
        "| Target | Status | Path Drift | Tag Drift | Notes |",
        "| --- | --- | --- | --- | --- |",
    ]

    for result in report["results"]:
        target_name = f'{result["insurer"]}::{result["domain"]}'
        notes = "; ".join(result.get("failures", []) or result.get("errors", []) or ["-"])
        lines.append(
            f"| {target_name} | {result['status']} | "
            f"{result.get('path_drift', '-')} | {result.get('tag_drift', '-')} | {notes} |"
        )
    lines.append("")
    return "\n".join(lines)


def run_validation(
    output_dir: Path,
    baseline_dir: Path | None,
    max_urls_per_insurer: int,
    request_timeout: int,
    max_path_drift: float,
    max_tag_drift: float,
) -> int:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    has_failures = False

    for target in discover_targets(max_urls_per_insurer=max_urls_per_insurer):
        result = {
            "insurer": target.insurer,
            "url": target.url,
            "domain": target.domain,
            "source_file": target.source_file,
        }

        try:
            html = fetch_html(target.url, request_timeout=request_timeout)
            current_snapshot = snapshot_from_html(target, html)
            current_json_path, current_html_path = write_snapshot_artifacts(
                output_dir, current_snapshot
            )
            result["snapshot_json"] = str(current_json_path)
            result["snapshot_html"] = str(current_html_path)
        except Exception as exc:
            result["status"] = "error"
            result["errors"] = [str(exc)]
            results.append(result)
            has_failures = True
            continue

        if baseline_dir is None:
            result["status"] = "no_baseline"
            results.append(result)
            continue

        baseline_path = baseline_snapshot_path(baseline_dir, current_snapshot)
        baseline_snapshot = load_snapshot(baseline_path)
        if baseline_snapshot is None:
            result["status"] = "no_baseline"
            results.append(result)
            continue

        comparison = compare_snapshot_pair(
            baseline_snapshot=baseline_snapshot,
            current_snapshot=current_snapshot,
            max_path_drift=max_path_drift,
            max_tag_drift=max_tag_drift,
        )
        result.update(comparison)
        results.append(result)
        if comparison["status"] == "failed":
            has_failures = True

    summary = {
        "total_targets": len(results),
        "passed": sum(1 for result in results if result["status"] == "passed"),
        "failed": sum(1 for result in results if result["status"] == "failed"),
        "errors": sum(1 for result in results if result["status"] == "error"),
        "no_baseline": sum(1 for result in results if result["status"] == "no_baseline"),
    }
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "settings": {
            "max_urls_per_insurer": max_urls_per_insurer,
            "request_timeout": request_timeout,
            "max_path_drift": max_path_drift,
            "max_tag_drift": max_tag_drift,
        },
        "summary": summary,
        "results": results,
    }

    report_path = output_dir / "report.json"
    summary_path = output_dir / "summary.md"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True))
    summary_path.write_text(build_summary_markdown(report))

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 1 if has_failures else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--baseline-dir", type=Path)
    parser.add_argument("--max-urls-per-insurer", type=int, default=2)
    parser.add_argument("--request-timeout", type=int, default=30)
    parser.add_argument("--max-path-drift", type=float, default=0.35)
    parser.add_argument("--max-tag-drift", type=float, default=0.30)
    args = parser.parse_args()

    baseline_dir = args.baseline_dir
    if baseline_dir is not None and not baseline_dir.exists():
        baseline_dir = None

    return run_validation(
        output_dir=args.output_dir,
        baseline_dir=baseline_dir,
        max_urls_per_insurer=args.max_urls_per_insurer,
        request_timeout=args.request_timeout,
        max_path_drift=args.max_path_drift,
        max_tag_drift=args.max_tag_drift,
    )


if __name__ == "__main__":
    raise SystemExit(main())
