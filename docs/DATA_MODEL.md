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
