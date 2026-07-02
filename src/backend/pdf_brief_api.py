from __future__ import annotations

from fastapi import FastAPI, Response
from pydantic import BaseModel, Field

from src.backend.pdf_brief import build_pdf_brief

app = FastAPI(title="Be-sure-ance PDF brief backend")


class BriefRequest(BaseModel):
    plans: list[dict] = Field(..., min_length=1, max_length=3)


@app.post("/briefs/client.pdf")
def create_client_brief(request: BriefRequest):
    pdf_bytes = build_pdf_brief(request.plans)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="be-sure-ance-client-brief.pdf"',
            "Cache-Control": "no-store",
        },
    )
