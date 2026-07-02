# Data Model

## Tables

`plans` is the plan catalog. It stores one row per insurer plan with stable `insurer` and `plan_slug` identifiers plus display fields from scraper output.

`plan_comparison_facts` is an interim UI summary table. It keeps the current qualitative comparison fields used by the frontend while Phase 2 migrates facts into the source-traceable model.

`plan_facts` is the canonical source-traceable fact table. It stores one fact per `(insurer, plan_slug, field_name)` with a JSON value, source URL, source type, scrape timestamp, and verification timestamp.

## `plan_facts`

Required columns:

- `insurer`
- `plan_slug`
- `field_name`
- `field_value`
- `source_url`
- `source_type`
- `scraped_at`
- `last_verified_at`

Supported `source_type` values:

- `brochure_pdf`
- `product_page`
- `manual_entry`

Writers must use deterministic upserts on `(insurer, plan_slug, field_name)`:

```sql
ON CONFLICT (insurer, plan_slug, field_name) DO UPDATE SET
    field_value = EXCLUDED.field_value,
    source_url = EXCLUDED.source_url,
    source_type = EXCLUDED.source_type,
    scraped_at = EXCLUDED.scraped_at,
    last_verified_at = EXCLUDED.last_verified_at
```

Public clients can read `plan_facts`. Only `service_role` can write.

## Fact Taxonomy V1

The shared contract lives in `src/lib/plan_facts_contract.json`. Scrapers and frontend code must use those `field_name` values and JSON envelopes.

Status values:

- `known`: source supports the fact.
- `unknown`: source exists, but the fact has not been checked yet.
- `not_found`: source was checked and the fact was not found.
- `not_applicable`: fact does not apply to this plan type.

V1 fields:

| Field | Shape | Example `field_value` |
| :--- | :--- | :--- |
| `coverage_tags` | list | `{"status":"known","items":["accident","emergency"],"raw_text":"Personal accident and emergency support","notes":[]}` |
| `panel_hospitals` | list | `{"status":"known","items":[{"name":"Sample Hospital","normalized_name":"Sample Hospital","source_label":"Panel hospital"}],"raw_text":"Sample Hospital - Panel hospital","notes":[]}` |
| `exclusions` | list | `{"status":"known","items":[{"label":"Pre-existing conditions","details":"See policy wording for full clause."}],"raw_text":"Pre-existing conditions are excluded...","notes":[]}` |
| `waiting_periods` | list | `{"status":"known","items":[{"condition":"Specified condition","duration_days":90,"raw_text":"90 days waiting period"}],"raw_text":"90 days waiting period","notes":[]}` |
| `claim_deadlines` | list | `{"status":"known","items":[{"event":"Hospitalisation claim","deadline_days":30,"raw_text":"Submit within 30 days"}],"raw_text":"Submit within 30 days","notes":[]}` |
| `claim_sla` | structured | `{"status":"known","value":{"duration_days":10,"basis":"published target"},"raw_text":"Claims are processed within 10 working days","notes":[]}` |
| `brochure_metadata` | structured | `{"status":"known","value":{"url":"https://example.com/brochure.pdf","sha256":"example-sha256","content_type":"application/pdf","fetched_at":"2026-07-02T00:00:00Z","last_modified_at":null},"raw_text":"brochure.pdf","notes":[]}` |
| `source_notes` | list | `{"status":"known","items":["Brochure section heading found, but table layout needs manual review."],"raw_text":"Manual review note","notes":[]}` |

The app must never infer premium amounts, deductibles, coinsurance, cash value projections, claim approval likelihood, medical advice, financial advice, plan recommendations, or panel membership without a source.
