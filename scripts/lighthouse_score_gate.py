from __future__ import annotations

import argparse
import json
from pathlib import Path

DEFAULT_CATEGORIES = ("performance", "accessibility", "best-practices", "seo")


def load_scores(path: Path, categories: tuple[str, ...] = DEFAULT_CATEGORIES) -> dict[str, float]:
    payload = json.loads(path.read_text())
    lighthouse_categories = payload.get("categories", {})
    return {
        category: float(lighthouse_categories.get(category, {}).get("score", 0))
        for category in categories
    }


def check_lighthouse_files(
    paths: tuple[Path, ...],
    minimum: float = 0.9,
    categories: tuple[str, ...] = DEFAULT_CATEGORIES,
) -> dict:
    results = []
    for path in paths:
        scores = load_scores(path, categories)
        failures = [
            {"category": category, "score": score}
            for category, score in scores.items()
            if score < minimum
        ]
        results.append(
            {
                "path": str(path),
                "scores": scores,
                "status": "passed" if not failures else "failed",
                "failures": failures,
            }
        )
    return {
        "minimum": minimum,
        "categories": list(categories),
        "status": "passed" if all(result["status"] == "passed" for result in results) else "failed",
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--minimum", type=float, default=0.9)
    args = parser.parse_args()

    report = check_lighthouse_files(tuple(args.files), minimum=args.minimum)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
