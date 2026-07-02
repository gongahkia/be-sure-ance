# Data Model

## Tables

`plans` is the plan catalog. It stores one row per insurer plan with stable `insurer` and `plan_slug` identifiers plus display fields from scraper output.

`plan_comparison_facts` is an interim UI summary table. It keeps the current qualitative comparison fields used by the frontend while Phase 2 migrates facts into the source-traceable model.

`plan_facts` is the canonical source-traceable fact table. It stores one fact per `(insurer, plan_slug, field_name)` with a JSON value, source URL, source type, scrape timestamp, and verification timestamp.

`moh_institutions` is the canonical MOH institution lookup table for panel-hospital normalization. It is populated from the data.gov.sg MOH NEHR participating-institutions dataset (`d_2864c425e22ddb89969585820629adf8`) and stores source-backed names, aliases, source record IDs, and scrape timestamps.

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

## `moh_institutions`

Required columns:

- `canonical_id`
- `canonical_name`
- `aliases`
- `organization_name`
- `effective_date`
- `source_dataset_id`
- `source_record_id`
- `source_url`
- `scraped_at`

The scraper expands parenthetical NEHR entries into individual institution records. For example, a source row for a healthcare group can produce child records for each named hospital or centre inside the parentheses. Public clients can read the normalized lookup table. Only `service_role` can write.

## Brochure Storage

Raw brochure PDFs are stored in Supabase Storage. The default bucket is `plan-brochures`; override it with `BROCHURE_STORAGE_BUCKET`.

Bucket setup:

- Create a private Supabase Storage bucket named `plan-brochures`.
- Grant scraper writes through the existing server-side `SUPABASE_SECRET_KEY` or `SUPABASE_SERVICE_ROLE_KEY`.
- Do not expose the bucket as a frontend public upload surface.

Stored object keys are deterministic:

```text
brochures/{insurer}/{plan_slug}/{sha256}.pdf
```

Each successful capture writes a `plan_facts` row with `field_name = "brochure_metadata"` and `source_type = "brochure_pdf"`. `field_value.value` stores `url`, `sha256`, `storage_bucket`, `storage_key`, `size_bytes`, `content_type`, `fetched_at`, and `last_modified_at`.

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
| `panel_hospitals` | list | `{"status":"known","items":[{"name":"Sample Hospital","normalized_name":"Sample Hospital","source_label":"Panel hospital","match_status":"matched","match_confidence":100,"matched_alias":"Sample Hospital","canonical_id":"nehr-1-sample-hospital","review_required":false}],"raw_text":"Sample Hospital - Panel hospital","notes":[],"review_required":false}` |
| `exclusions` | list | `{"status":"known","items":[{"label":"Pre-existing conditions","details":"See policy wording for full clause."}],"raw_text":"Pre-existing conditions are excluded...","notes":[]}` |
| `waiting_periods` | list | `{"status":"known","items":[{"condition":"Specified condition","duration_days":90,"raw_text":"90 days waiting period"}],"raw_text":"90 days waiting period","notes":[]}` |
| `claim_deadlines` | list | `{"status":"known","items":[{"event":"Hospitalisation claim","deadline_days":30,"raw_text":"Submit within 30 days"}],"raw_text":"Submit within 30 days","notes":[]}` |
| `claim_sla` | structured | `{"status":"known","value":{"duration_days":10,"basis":"published target"},"raw_text":"Claims are processed within 10 working days","notes":[]}` |
| `brochure_metadata` | structured | `{"status":"known","value":{"url":"https://example.com/brochure.pdf","sha256":"example-sha256","storage_bucket":"plan-brochures","storage_key":"brochures/aia/sample-plan/example-sha256.pdf","size_bytes":12345,"content_type":"application/pdf","fetched_at":"2026-07-02T00:00:00Z","last_modified_at":null},"raw_text":"brochure.pdf","notes":[]}` |
| `source_notes` | list | `{"status":"known","items":["Brochure section heading found, but table layout needs manual review."],"raw_text":"Manual review note","notes":[]}` |

The app must never infer premium amounts, deductibles, coinsurance, cash value projections, claim approval likelihood, medical advice, financial advice, plan recommendations, or panel membership without a source.
