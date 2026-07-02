from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from src.backend.pdf_brief import MAX_PLANS_PER_BRIEF, NO_ADVICE_DISCLAIMER

SAFE_REF_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,119}$")


def generated_timestamp(value: datetime | None = None) -> str:
    generated_at = value or datetime.now(timezone.utc)
    return generated_at.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def normalize_share_plans(plans: list[dict]) -> list[dict]:
    if not plans:
        raise ValueError("At least one plan is required.")
    if len(plans) > MAX_PLANS_PER_BRIEF:
        raise ValueError(f"Share links support up to {MAX_PLANS_PER_BRIEF} plans.")

    normalized = []
    seen = set()
    for plan in plans:
        if not isinstance(plan, dict):
            raise ValueError("Shared plan references must be objects.")
        insurer = normalize_ref(plan.get("insurer") or plan.get("providerKey"))
        plan_slug = normalize_ref(plan.get("plan_slug") or plan.get("planSlug"))
        key = (insurer, plan_slug)
        if key in seen:
            continue
        seen.add(key)
        normalized.append({"insurer": insurer, "plan_slug": plan_slug})

    if not normalized:
        raise ValueError("At least one valid plan reference is required.")
    return normalized


def normalize_ref(value) -> str:
    text = str(value or "").strip().lower()
    if not SAFE_REF_PATTERN.fullmatch(text):
        raise ValueError("Shared plan references must use stable insurer keys and plan slugs.")
    return text


def build_share_record(
    plans: list[dict],
    share_id: str | None = None,
    created_at: str | None = None,
) -> dict:
    share_uuid = canonical_share_id(share_id or str(uuid.uuid4()))
    return {
        "id": share_uuid,
        "selected_plans": normalize_share_plans(plans),
        "view_count": 0,
        "created_at": created_at or generated_timestamp(),
    }


def canonical_share_id(value: str) -> str:
    return str(uuid.UUID(str(value)))


def share_path(share_id: str) -> str:
    return f"/share/{canonical_share_id(share_id)}"


def share_public_payload(row: dict) -> dict:
    return {
        "id": canonical_share_id(row["id"]),
        "selected_plans": normalize_share_plans(row.get("selected_plans") or []),
        "created_at": row.get("created_at") or "",
        "view_count": int(row.get("view_count") or 0),
        "last_viewed_at": row.get("last_viewed_at"),
        "disclaimer": NO_ADVICE_DISCLAIMER,
    }
