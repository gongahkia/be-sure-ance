from __future__ import annotations

import difflib
import hashlib
import io
from datetime import datetime, timezone

from pypdf import PdfReader


def extract_brochure_text(content: bytes, max_pages: int = 20) -> str:
    try:
        reader = PdfReader(io.BytesIO(content))
    except Exception:
        return ""
    pages = [page.extract_text() or "" for page in reader.pages[:max_pages]]
    return normalize_text("\n".join(pages))


def build_version_row(
    insurer: str,
    plan: dict,
    metadata: dict,
    captured_at: str,
    extracted_text: str,
) -> dict:
    return {
        "insurer": insurer,
        "plan_slug": plan["plan_slug"],
        "plan_name": plan.get("plan_name") or plan["plan_slug"],
        "source_url": metadata["url"],
        "sha256": metadata["sha256"],
        "storage_bucket": metadata["storage_bucket"],
        "storage_key": metadata["storage_key"],
        "size_bytes": metadata["size_bytes"],
        "content_type": metadata["content_type"],
        "source_last_modified_at": metadata.get("last_modified_at"),
        "first_seen_at": captured_at,
        "last_seen_at": captured_at,
        "captured_at": captured_at,
        "extracted_text": extracted_text,
        "text_sha256": sha256_text(extracted_text) if extracted_text else None,
    }


def version_change_status(previous_version: dict | None, current_sha256: str) -> str:
    if not previous_version:
        return "new"
    if previous_version.get("sha256") == current_sha256:
        return "unchanged"
    return "changed"


def build_change_alert(
    previous_version: dict,
    current_version: dict,
    detected_at: str | None = None,
) -> dict:
    detected_at = detected_at or datetime.now(timezone.utc).isoformat()
    previous_text = previous_version.get("extracted_text") or ""
    current_text = current_version.get("extracted_text") or ""
    text_diff = unified_text_diff(previous_text, current_text)
    html_diff = html_text_diff(previous_text, current_text)
    return {
        "insurer": current_version["insurer"],
        "plan_slug": current_version["plan_slug"],
        "plan_name": current_version["plan_name"],
        "source_url": current_version["source_url"],
        "previous_sha256": previous_version["sha256"],
        "current_sha256": current_version["sha256"],
        "previous_captured_at": previous_version.get("captured_at")
        or previous_version.get("first_seen_at"),
        "current_captured_at": current_version["captured_at"],
        "change_detected_at": detected_at,
        "alert_status": "pending",
        "text_diff": text_diff,
        "html_diff": html_diff,
        "summary": change_summary(previous_version, current_version, text_diff),
    }


def unified_text_diff(previous_text: str, current_text: str) -> str:
    if not previous_text or not current_text:
        return ""
    return "\n".join(
        difflib.unified_diff(
            previous_text.splitlines(),
            current_text.splitlines(),
            fromfile="previous",
            tofile="current",
            lineterm="",
        )
    )


def html_text_diff(previous_text: str, current_text: str) -> str:
    if not previous_text or not current_text:
        return ""
    return difflib.HtmlDiff().make_table(
        previous_text.splitlines(),
        current_text.splitlines(),
        fromdesc="previous",
        todesc="current",
        context=True,
        numlines=2,
    )


def change_summary(previous_version: dict, current_version: dict, text_diff: str) -> str:
    if text_diff:
        changed_lines = sum(
            1
            for line in text_diff.splitlines()
            if line[:1] in {"+", "-"} and not line.startswith(("+++", "---"))
        )
        return f"Brochure hash changed; {changed_lines} diff lines generated."
    previous_size = previous_version.get("size_bytes")
    current_size = current_version.get("size_bytes")
    if previous_size != current_size:
        return f"Brochure hash changed; size changed from {previous_size} to {current_size} bytes."
    return "Brochure hash changed; text diff unavailable."


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_text(value: str) -> str:
    return "\n".join(line.strip() for line in str(value or "").splitlines() if line.strip())
