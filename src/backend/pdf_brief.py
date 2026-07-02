from __future__ import annotations

import io
from datetime import datetime, timezone
from html import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

MAX_PLANS_PER_BRIEF = 3
QUALITATIVE_FIELDS = (
    ("coverage_tags", "Coverage"),
    ("panel_hospitals", "Panel hospitals"),
    ("waiting_periods", "Waiting periods"),
    ("claim_deadlines", "Claim deadlines"),
    ("claim_sla", "Claim SLA"),
    ("exclusions", "Exclusions"),
    ("source_notes", "Source notes"),
)
NO_ADVICE_DISCLAIMER = (
    "This brief is for pre-meeting research only. It is not financial advice, insurance advice, "
    "legal advice, a recommendation, a ranking, a quote, or a policy transaction. Verify every "
    "fact against the carrier source, compareFIRST where applicable, and the adviser's licensed "
    "compliance workflow."
)


def generated_timestamp(value: datetime | None = None) -> str:
    generated_at = value or datetime.now(timezone.utc)
    return generated_at.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def validate_plan_selection(plans: list[dict]) -> None:
    if not plans:
        raise ValueError("At least one plan is required.")
    if len(plans) > MAX_PLANS_PER_BRIEF:
        raise ValueError(f"PDF briefs support up to {MAX_PLANS_PER_BRIEF} plans.")


def build_pdf_brief(plans: list[dict], generated_at: datetime | None = None) -> bytes:
    return build_pdf_brief_with_branding(plans, branding=None, generated_at=generated_at)


def build_pdf_brief_with_branding(
    plans: list[dict],
    branding: dict | None = None,
    generated_at: datetime | None = None,
) -> bytes:
    validate_plan_selection(plans)
    timestamp = generated_timestamp(generated_at)
    footer_text = branding_footer_text(branding)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="Be-sure-ance Client Brief",
    )
    styles = brief_styles()
    story = [
        Paragraph("Be-sure-ance Client Brief", styles["Title"]),
        Paragraph(f"Generated at {timestamp}", styles["Meta"]),
        Spacer(1, 6 * mm),
        Paragraph(NO_ADVICE_DISCLAIMER, styles["Disclaimer"]),
        Spacer(1, 6 * mm),
        comparison_table(plans, styles),
        Spacer(1, 6 * mm),
        Paragraph("Sources", styles["Heading2"]),
        source_table(plans, styles),
    ]
    doc.build(
        story,
        onFirstPage=lambda canvas, document: draw_footer(canvas, document, footer_text),
        onLaterPages=lambda canvas, document: draw_footer(canvas, document, footer_text),
    )
    return buffer.getvalue()


def brief_styles() -> dict[str, ParagraphStyle]:
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="Meta",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#567086"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="Disclaimer",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            borderColor=colors.HexColor("#cbd5e1"),
            borderWidth=0.6,
            borderPadding=6,
            backColor=colors.HexColor("#f8fafc"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="Cell",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
        )
    )
    return styles


def comparison_table(plans: list[dict], styles: dict[str, ParagraphStyle]) -> Table:
    header = [Paragraph("Field", styles["Cell"])]
    header.extend(Paragraph(plan_heading(plan), styles["Cell"]) for plan in plans)
    rows = [header]
    for field_name, label in QUALITATIVE_FIELDS:
        row = [Paragraph(label, styles["Cell"])]
        row.extend(Paragraph(field_text(plan, field_name), styles["Cell"]) for plan in plans)
        rows.append(row)

    col_widths = [32 * mm]
    col_widths.extend([(178 * mm - col_widths[0]) / len(plans)] * len(plans))
    table = Table(rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(base_table_style())
    return table


def source_table(plans: list[dict], styles: dict[str, ParagraphStyle]) -> Table:
    rows = [[Paragraph("Plan", styles["Cell"]), Paragraph("Fact sources", styles["Cell"])]]
    for plan in plans:
        sources = []
        for field_name, label in QUALITATIVE_FIELDS:
            fact = (plan.get("facts") or {}).get(field_name) or {}
            source_url = fact.get("source_url")
            if not source_url:
                continue
            source_type = fact.get("source_type") or "source"
            verified_at = fact.get("last_verified_at") or "verification missing"
            sources.append(f"{label}: {source_type}; verified {verified_at}; {source_url}")
        rows.append(
            [
                Paragraph(plan_heading(plan), styles["Cell"]),
                Paragraph(
                    "<br/>".join(escape(item) for item in sources) or "No sources", styles["Cell"]
                ),
            ]
        )
    table = Table(rows, colWidths=[42 * mm, 136 * mm], repeatRows=1)
    table.setStyle(base_table_style())
    return table


def base_table_style() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#102747")),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
    )


def plan_heading(plan: dict) -> str:
    provider = safe_text(plan.get("providerName") or plan.get("insurer"))
    plan_name = safe_text(plan.get("plan_name"))
    return escape(f"{provider}: {plan_name}" if provider else plan_name)


def field_text(plan: dict, field_name: str) -> str:
    field_value = ((plan.get("facts") or {}).get(field_name) or {}).get("field_value") or {}
    if field_value.get("status") and field_value.get("status") != "known":
        return escape(field_value.get("status"))

    if field_name == "claim_sla":
        value = field_value.get("value") or {}
        if value.get("duration_days"):
            basis = f" ({safe_text(value.get('basis'))})" if value.get("basis") else ""
            return escape(f"{value['duration_days']} days{basis}")

    items = field_value.get("items") or []
    labels = [item_text(item, field_name) for item in items]
    return escape("; ".join(label for label in labels if label) or "Unknown")


def item_text(item, field_name: str) -> str:
    if isinstance(item, str):
        return safe_text(item)
    if not isinstance(item, dict):
        return ""
    if field_name == "waiting_periods" and item.get("duration_days") is not None:
        return f"{safe_text(item.get('condition'))}: {item['duration_days']} days"
    if field_name == "claim_deadlines" and item.get("deadline_days") is not None:
        return f"{safe_text(item.get('event'))}: {item['deadline_days']} days"
    return safe_text(
        item.get("normalized_name")
        or item.get("name")
        or item.get("label")
        or item.get("condition")
        or item.get("event")
        or item.get("details")
        or item.get("raw_text")
    )


def safe_text(value) -> str:
    return " ".join(str(value or "").split())


def branding_footer_text(branding: dict | None = None) -> str:
    branding = branding or {}
    agent_name = safe_text(branding.get("agent_name") or branding.get("agentName"))
    mas_rep_number = safe_text(branding.get("mas_rep_number") or branding.get("masRepNumber"))
    if agent_name and mas_rep_number:
        return f"Prepared by {agent_name} | MAS rep no. {mas_rep_number}"
    if agent_name:
        return f"Prepared by {agent_name} | MAS rep no. not provided"
    if mas_rep_number:
        return f"Prepared by unbranded adviser | MAS rep no. {mas_rep_number}"
    return "Prepared by unbranded adviser | MAS rep no. not provided"


def draw_footer(canvas, document, footer_text: str) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#567086"))
    canvas.drawString(document.leftMargin, 9 * mm, footer_text)
    canvas.drawRightString(
        A4[0] - document.rightMargin,
        9 * mm,
        f"Page {document.page}",
    )
    canvas.restoreState()
