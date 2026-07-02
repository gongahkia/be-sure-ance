from __future__ import annotations

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

from src.backend import helper
from src.backend.comparison_shares import (
    build_share_record,
    canonical_share_id,
    generated_timestamp,
    share_path,
    share_public_payload,
)
from src.backend.pdf_brief import build_pdf_brief_with_branding

app = FastAPI(title="Be-sure-ance backend")


class BriefRequest(BaseModel):
    plans: list[dict] = Field(..., min_length=1, max_length=3)
    branding: dict | None = None


class ShareRequest(BaseModel):
    plans: list[dict] = Field(..., min_length=1, max_length=3)


@app.post("/briefs/client.pdf")
def create_client_brief(request: BriefRequest):
    pdf_bytes = build_pdf_brief_with_branding(request.plans, branding=request.branding)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="be-sure-ance-client-brief.pdf"',
            "Cache-Control": "no-store",
        },
    )


@app.post("/shares")
def create_comparison_share(request: ShareRequest):
    try:
        row = build_share_record(request.plans)
        response = writable_client().table("comparison_shares").insert([row]).execute()
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=503, detail="Share storage unavailable.") from error

    stored_row = (response.data or [row])[0]
    payload = share_public_payload(stored_row)
    return {**payload, "path": share_path(payload["id"])}


@app.post("/shares/{share_id}/view")
def register_comparison_share_view(share_id: str):
    try:
        normalized_id = canonical_share_id(share_id)
        client = writable_client()
        response = (
            client.table("comparison_shares").select("*").eq("id", normalized_id).limit(1).execute()
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail="Invalid share id.") from error
    except Exception as error:
        raise HTTPException(status_code=503, detail="Share storage unavailable.") from error

    rows = response.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="Shared comparison not found.")

    current_row = rows[0]
    view_count = int(current_row.get("view_count") or 0) + 1
    update_payload = {
        "view_count": view_count,
        "last_viewed_at": generated_timestamp(),
    }
    update_response = (
        client.table("comparison_shares").update(update_payload).eq("id", normalized_id).execute()
    )
    updated_row = (update_response.data or [{**current_row, **update_payload}])[0]
    return {
        "id": canonical_share_id(updated_row["id"]),
        "view_count": int(updated_row.get("view_count") or view_count),
    }


def writable_client():
    if helper.supabase is None:
        helper.initialize_supabase()
    helper.require_write_key()
    return helper.require_client()
