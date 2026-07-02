from __future__ import annotations

from copy import deepcopy

DEMO_TIMESTAMP = "2026-07-02T00:00:00+00:00"
DEMO_SOURCE = "https://example.com/demo-source"


def fact(insurer, plan_slug, field_name, field_value, source_type="manual_entry"):
    return {
        "insurer": insurer,
        "plan_slug": plan_slug,
        "field_name": field_name,
        "field_value": field_value,
        "source_url": DEMO_SOURCE,
        "source_type": source_type,
        "scraped_at": DEMO_TIMESTAMP,
        "last_verified_at": DEMO_TIMESTAMP,
    }


DEMO_TABLES = {
    "plans": [
        {
            "id": 1,
            "insurer": "aia",
            "plan_name": "HealthShield Gold Max Demo",
            "plan_slug": "healthshield-gold-max-demo",
            "plan_benefits": ["Hospital coverage signals", "Panel lookup demo"],
            "plan_description": "Demo plan row for local qualitative workflow testing.",
            "plan_overview": "Uses seeded facts only; verify real facts against carrier sources.",
            "plan_url": "https://example.com/aia/demo-plan",
            "product_brochure_url": "https://example.com/aia/demo-brochure.pdf",
            "scraped_at": DEMO_TIMESTAMP,
        },
        {
            "id": 2,
            "insurer": "great_eastern",
            "plan_name": "SupremeHealth Demo",
            "plan_slug": "supremehealth-demo",
            "plan_benefits": ["Hospital coverage signals", "Waiting period demo"],
            "plan_description": "Second demo row for panel matrix comparison.",
            "plan_overview": "Seeded for the local Docker demo; not production data.",
            "plan_url": "https://example.com/great-eastern/demo-plan",
            "product_brochure_url": "https://example.com/great-eastern/demo-brochure.pdf",
            "scraped_at": DEMO_TIMESTAMP,
        },
    ],
    "plan_comparison_facts": [
        {
            "id": 1,
            "insurer": "aia",
            "plan_name": "HealthShield Gold Max Demo",
            "plan_slug": "healthshield-gold-max-demo",
            "panel_network_size": 2,
            "claim_sla_days": 14,
            "exclusions": ["Demo exclusion"],
            "waiting_period_days": 365,
            "coverage_tags": ["hospitalization", "brochure_available"],
            "brochure_hash": "demo-aia-brochure-hash",
            "brochure_last_changed_at": DEMO_TIMESTAMP,
            "comparison_notes": "Demo qualitative comparison notes with no premium estimate.",
            "source_url": DEMO_SOURCE,
        },
        {
            "id": 2,
            "insurer": "great_eastern",
            "plan_name": "SupremeHealth Demo",
            "plan_slug": "supremehealth-demo",
            "panel_network_size": 1,
            "claim_sla_days": None,
            "exclusions": ["Demo exclusion"],
            "waiting_period_days": 180,
            "coverage_tags": ["hospitalization", "brochure_available"],
            "brochure_hash": "demo-ge-brochure-hash",
            "brochure_last_changed_at": DEMO_TIMESTAMP,
            "comparison_notes": "Demo qualitative comparison notes for local review.",
            "source_url": DEMO_SOURCE,
        },
    ],
    "plan_facts": [
        fact(
            "aia",
            "healthshield-gold-max-demo",
            "coverage_tags",
            {"status": "known", "items": ["hospitalization", "brochure_available"]},
        ),
        fact(
            "aia",
            "healthshield-gold-max-demo",
            "panel_hospitals",
            {
                "status": "known",
                "items": [
                    {
                        "name": "Mount Elizabeth Novena Hospital",
                        "normalized_name": "Mount Elizabeth Novena Hospital",
                        "canonical_id": "demo-mount-elizabeth-novena",
                        "match_status": "matched",
                        "review_required": False,
                    },
                    {
                        "name": "Singapore General Hospital",
                        "normalized_name": "Singapore General Hospital",
                        "canonical_id": "demo-singapore-general-hospital",
                        "match_status": "matched",
                        "review_required": False,
                    },
                ],
            },
        ),
        fact(
            "aia",
            "healthshield-gold-max-demo",
            "waiting_periods",
            {
                "status": "known",
                "items": [
                    {
                        "condition": "Pre-existing condition demo",
                        "duration_days": 365,
                        "tags": ["pre_existing_condition"],
                    }
                ],
            },
        ),
        fact(
            "aia",
            "healthshield-gold-max-demo",
            "claim_deadlines",
            {
                "status": "known",
                "items": [{"event": "Submit demo claim documents", "deadline_days": 90}],
            },
        ),
        fact(
            "aia",
            "healthshield-gold-max-demo",
            "claim_sla",
            {"status": "known", "value": {"duration_days": 14, "basis": "demo source text"}},
        ),
        fact(
            "aia",
            "healthshield-gold-max-demo",
            "exclusions",
            {
                "status": "known",
                "items": [
                    {
                        "details": "Demo exclusion; verify against real brochure.",
                        "tags": ["needs_review"],
                    }
                ],
            },
        ),
        fact(
            "aia",
            "healthshield-gold-max-demo",
            "brochure_metadata",
            {
                "status": "known",
                "value": {
                    "url": "https://example.com/aia/demo-brochure.pdf",
                    "sha256": "demo-aia-brochure-hash",
                    "storage_bucket": "local-demo-no-bucket",
                    "storage_key": "brochures/aia/demo.pdf",
                    "fetched_at": DEMO_TIMESTAMP,
                },
            },
            source_type="brochure_pdf",
        ),
        fact(
            "great_eastern",
            "supremehealth-demo",
            "coverage_tags",
            {"status": "known", "items": ["hospitalization", "brochure_available"]},
        ),
        fact(
            "great_eastern",
            "supremehealth-demo",
            "panel_hospitals",
            {
                "status": "known",
                "items": [
                    {
                        "name": "Singapore General Hospital",
                        "normalized_name": "Singapore General Hospital",
                        "canonical_id": "demo-singapore-general-hospital",
                        "match_status": "matched",
                        "review_required": False,
                    }
                ],
            },
        ),
        fact(
            "great_eastern",
            "supremehealth-demo",
            "waiting_periods",
            {
                "status": "known",
                "items": [
                    {
                        "condition": "Specified treatment demo",
                        "duration_days": 180,
                        "tags": ["specified_treatment"],
                    }
                ],
            },
        ),
        fact(
            "great_eastern",
            "supremehealth-demo",
            "claim_deadlines",
            {"status": "unknown"},
        ),
        fact(
            "great_eastern",
            "supremehealth-demo",
            "claim_sla",
            {"status": "unknown"},
        ),
        fact(
            "great_eastern",
            "supremehealth-demo",
            "exclusions",
            {
                "status": "known",
                "items": [{"details": "Demo exclusion for local comparison.", "tags": []}],
            },
        ),
        fact(
            "great_eastern",
            "supremehealth-demo",
            "brochure_metadata",
            {
                "status": "known",
                "value": {
                    "url": "https://example.com/great-eastern/demo-brochure.pdf",
                    "sha256": "demo-ge-brochure-hash",
                    "storage_bucket": "local-demo-no-bucket",
                    "storage_key": "brochures/great_eastern/demo.pdf",
                    "fetched_at": DEMO_TIMESTAMP,
                },
            },
            source_type="brochure_pdf",
        ),
    ],
    "specialist_resources": [
        {
            "id": 1,
            "insurer": "aia",
            "plan_name": "HealthShield Gold Max Demo",
            "resource_type": "panel_directory",
            "resource_title": "Demo panel directory",
            "resource_description": "Local demo link; not production source data.",
            "resource_url": "https://example.com/aia/panel",
            "source_url": DEMO_SOURCE,
        }
    ],
    "claim_turnaround_metrics": [
        {
            "id": 1,
            "carrier_key": "industry",
            "carrier_name": "Industry demo",
            "metric_key": "claim_turnaround_demo",
            "metric_label": "Demo claim turnaround",
            "metric_value": {"status": "known", "value": {"days": 14}},
            "rank": None,
            "source_year": 2026,
            "source_url": "https://example.com/lia/demo-report.pdf",
            "limitations": ["Demo row only; LIA source rows are not suitability rankings."],
        }
    ],
    "mas_regulatory_events": [
        {
            "id": 1,
            "carrier_key": "aia",
            "carrier_name": "AIA Singapore",
            "matched_alias": "AIA",
            "match_status": "needs_review",
            "event_title": "Demo MAS source review item",
            "summary": "Demo regulatory-context row; verify against MAS source.",
            "event_date": "2026-07-02",
            "source_url": "https://example.com/mas/demo-event",
        }
    ],
    "brochure_change_alerts": [
        {
            "id": 1,
            "insurer": "aia",
            "plan_slug": "healthshield-gold-max-demo",
            "source_url": "https://example.com/aia/demo-brochure.pdf",
            "previous_sha256": "old-demo-hash",
            "current_sha256": "demo-aia-brochure-hash",
            "previous_captured_at": "2026-06-25T00:00:00+00:00",
            "current_captured_at": DEMO_TIMESTAMP,
            "change_detected_at": DEMO_TIMESTAMP,
            "alert_status": "pending",
            "summary": "Demo brochure hash changed; review source document.",
        }
    ],
    "comparison_shares": [
        {
            "id": "11111111-2222-4333-8444-555555555555",
            "selected_plans": [{"insurer": "aia", "plan_slug": "healthshield-gold-max-demo"}],
            "view_count": 0,
            "created_at": DEMO_TIMESTAMP,
            "last_viewed_at": None,
        }
    ],
    "carrier_canonical_names": [
        {
            "id": 1,
            "carrier_key": "aia",
            "display_name": "AIA Singapore",
            "canonical_name": "AIA SINGAPORE PRIVATE LIMITED",
            "aliases": ["AIA Singapore", "AIA Singapore Private Limited", "AIA"],
            "mas_entity_name": "AIA SINGAPORE PRIVATE LIMITED",
            "mas_detail_url": "https://eservices.mas.gov.sg/fid/institution/detail/2452-AIA-SINGAPORE-PRIVATE-LIMITED",
            "mas_licence_types": ["Direct Insurer (Composite)", "Exempt Financial Adviser"],
            "mas_match_status": "matched",
            "lia_member_name": "AIA Singapore Private Limited",
            "lia_member_url": "https://www.aia.com.sg",
            "lia_member_category": "Ordinary Members",
            "lia_match_status": "matched",
            "source_urls": [
                "https://eservices.mas.gov.sg/fid/institution?sector=Insurance",
                "https://www.lia.org.sg/about-us/member-companies/",
            ],
            "mismatch_flags": [],
            "scraped_at": DEMO_TIMESTAMP,
            "last_verified_at": DEMO_TIMESTAMP,
        },
        {
            "id": 2,
            "carrier_key": "great_eastern",
            "display_name": "Great Eastern Singapore",
            "canonical_name": "THE GREAT EASTERN LIFE ASSURANCE COMPANY LIMITED",
            "aliases": [
                "Great Eastern Singapore",
                "The Great Eastern Life Assurance Company Limited",
            ],
            "mas_entity_name": "THE GREAT EASTERN LIFE ASSURANCE COMPANY LIMITED",
            "mas_detail_url": "https://eservices.mas.gov.sg/fid/institution/detail/103-THE-GREAT-EASTERN-LIFE-ASSURANCE-COMPANY-LIMITED",
            "mas_licence_types": ["Direct Insurer (Life)", "Exempt Financial Adviser"],
            "mas_match_status": "matched",
            "lia_member_name": "The Great Eastern Life Assurance Company Limited",
            "lia_member_url": "https://www.greateasternlife.com",
            "lia_member_category": "Ordinary Members",
            "lia_match_status": "matched",
            "source_urls": [
                "https://eservices.mas.gov.sg/fid/institution?sector=Insurance",
                "https://www.lia.org.sg/about-us/member-companies/",
            ],
            "mismatch_flags": [],
            "scraped_at": DEMO_TIMESTAMP,
            "last_verified_at": DEMO_TIMESTAMP,
        },
    ],
}


def demo_tables():
    return deepcopy(DEMO_TABLES)
