# Data Model

## Tables

`plans` is the plan catalog. It stores one row per insurer plan with stable `insurer` and `plan_slug` identifiers plus display fields from scraper output.

`plan_comparison_facts` is an interim UI summary table. It keeps the current qualitative comparison fields used by the frontend while Phase 2 migrates facts into the source-traceable model.

`comparison_shares` stores UUID-addressed saved comparison sets with selected plan references only.

`plan_facts` is the canonical source-traceable fact table. It stores one fact per `(insurer, plan_slug, field_name)` with a JSON value, source URL, source type, scrape timestamp, and verification timestamp.

`moh_institutions` is the canonical MOH institution lookup table for panel-hospital normalization. It is populated from the data.gov.sg MOH NEHR participating-institutions dataset (`d_2864c425e22ddb89969585820629adf8`) and stores source-backed names, aliases, source record IDs, and scrape timestamps.

`carrier_canonical_names` stores MAS FID and LIA member-directory cross-checks for tracked carrier keys. It is refreshed by the weekly scraper workflow and is used to expose source-backed canonical carrier names and review flags in UI/export surfaces.

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

## `claim_turnaround_metrics`

`claim_turnaround_metrics` stores LIA-sourced claims evidence for the frontend claim board.

- `carrier_key`
- `carrier_name`
- `metric_key`
- `metric_label`
- `metric_value`
- `metric_unit`
- `rank`
- `source_year`
- `source_url`
- `source_type`
- `limitations`
- `scraped_at`
- `last_verified_at`

`rank` is nullable. Current LIA sources provide industry-level handling timelines and annual claims/maturity payout totals; LIA does not publish carrier-level turnaround rankings in these sources. UI rows must show source year and limitations, and must not present aggregate LIA metrics as carrier suitability evidence.

## `mas_regulatory_events`

`mas_regulatory_events` stores source-linked MAS news/enforcement items that mention tracked carriers.

- `carrier_key`
- `carrier_name`
- `event_title`
- `event_type`
- `event_date`
- `source_url`
- `source_type`
- `summary`
- `matched_alias`
- `match_confidence`
- `match_status`
- `source_published_at`
- `limitations`
- `scraped_at`
- `last_verified_at`

`match_status = "needs_review"` must be shown as a possible carrier match, not a definitive finding. Rows are regulatory context only and are not advice, ratings, suitability rankings, or carrier recommendations.

## `carrier_canonical_names`

`carrier_canonical_names` stores source-backed canonical carrier names and aliases for tracked carrier keys.

- `carrier_key`
- `display_name`
- `canonical_name`
- `aliases`
- `mas_entity_name`
- `mas_detail_url`
- `mas_licence_types`
- `mas_match_status`
- `lia_member_name`
- `lia_member_url`
- `lia_member_category`
- `lia_match_status`
- `source_urls`
- `mismatch_flags`
- `scraped_at`
- `last_verified_at`

Sources:

- MAS Financial Institutions Directory, Insurance sector: `https://eservices.mas.gov.sg/fid/institution?sector=Insurance`
- LIA Singapore member companies: `https://www.lia.org.sg/about-us/member-companies/`

Rows are upserted by `carrier_key`. The weekly scraper queries MAS FID with tracked carrier aliases and parses LIA ordinary-member links. `canonical_name` prefers a matched MAS FID entity, then a matched LIA member name, then the configured display name.

`mas_match_status` and `lia_match_status` use `matched`, `needs_review`, or `unmatched`. `mismatch_flags` is non-empty when a source is missing, low-confidence, or when MAS and LIA source names diverge materially. UI and exports may display canonical names, but source flags must remain available so unresolved mismatches are not hidden.

## `comparison_shares`

`comparison_shares` stores saved comparison links without client, agent, or visitor identity fields.

- `id`
- `selected_plans`
- `view_count`
- `created_at`
- `last_viewed_at`

`selected_plans` is a JSON array of up to three objects containing only `insurer` and `plan_slug`. The frontend reconstructs plan names, facts, provenance, and no-advice copy from current public read-only tables at `/share/<uuid>`.

`view_count` is a non-identifying aggregate counter. It must not be joined to IP addresses, user agents, cookies, accounts, or contact details.

## `brochure_version_history`

`brochure_version_history` stores source brochure hash history by insurer, plan, URL, and capture timestamp.

- `insurer`
- `plan_slug`
- `plan_name`
- `source_url`
- `sha256`
- `storage_bucket`
- `storage_key`
- `size_bytes`
- `content_type`
- `source_last_modified_at`
- `first_seen_at`
- `last_seen_at`
- `captured_at`
- `extracted_text`
- `text_sha256`

Rows are deduped on `(insurer, plan_slug, source_url, sha256)`. Unchanged captures update `last_seen_at`; changed hashes create a new version row.

## `brochure_change_alerts`

`brochure_change_alerts` stores deduped change alerts generated from adjacent brochure versions.

- `insurer`
- `plan_slug`
- `plan_name`
- `source_url`
- `previous_sha256`
- `current_sha256`
- `previous_captured_at`
- `current_captured_at`
- `change_detected_at`
- `alert_status`
- `summary`
- `text_diff`
- `html_diff`
- `created_at`

`alert_status` is prepared for email or Telegram dispatch hooks with `pending`, `sent`, and `suppressed` states. No subscriber, client, or agent PII is stored in these rows.

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

The same capture writes `brochure_version_history` and, when the latest stored hash differs, creates one `brochure_change_alerts` row with source URL, previous/current hashes, timestamps, and text/HTML redline output where PDF text extraction succeeds.

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
| `exclusions` | list | `{"status":"known","items":[{"label":"Pre-existing conditions","details":"See policy wording for full clause.","tags":["pre_existing_condition"],"taxonomy_status":"tagged","review_required":false,"review_reason":""}],"raw_text":"Pre-existing conditions are excluded...","notes":[],"taxonomy_version":1,"review_required":false}` |
| `waiting_periods` | list | `{"status":"known","items":[{"condition":"Specified condition","duration_days":90,"raw_text":"90 days waiting period","tags":["specified_condition"],"taxonomy_status":"tagged","review_required":false,"review_reason":""}],"raw_text":"90 days waiting period","notes":[],"taxonomy_version":1,"review_required":false}` |
| `claim_deadlines` | list | `{"status":"known","items":[{"event":"Hospitalisation claim","deadline_days":30,"raw_text":"Submit within 30 days"}],"raw_text":"Submit within 30 days","notes":[]}` |
| `claim_sla` | structured | `{"status":"known","value":{"duration_days":10,"basis":"published target"},"raw_text":"Claims are processed within 10 working days","notes":[]}` |
| `brochure_metadata` | structured | `{"status":"known","value":{"url":"https://example.com/brochure.pdf","sha256":"example-sha256","storage_bucket":"plan-brochures","storage_key":"brochures/aia/sample-plan/example-sha256.pdf","size_bytes":12345,"content_type":"application/pdf","fetched_at":"2026-07-02T00:00:00Z","last_modified_at":null},"raw_text":"brochure.pdf","notes":[]}` |
| `source_notes` | list | `{"status":"known","items":["Brochure section heading found, but table layout needs manual review."],"raw_text":"Manual review note","notes":[]}` |

The app must never infer premium amounts, deductibles, coinsurance, cash value projections, claim approval likelihood, medical advice, financial advice, plan recommendations, or panel membership without a source.

Exclusion and waiting-period items carry controlled `tags`, `taxonomy_status`, and `review_required` fields. Empty tag matches must be represented as `taxonomy_status = "needs_review"` with the raw source item retained.
