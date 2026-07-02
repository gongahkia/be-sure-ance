# Open Dataset Snapshots

Weekly open dataset snapshots are published as GitHub Actions artifacts named `open-dataset-snapshot`.

The export command writes:

```text
data/be-sure-ance-snapshot-YYYY-MM-DD.csv
```

## Contents

Each row is one source-traceable plan fact joined to the public plan catalog and carrier canonicalization table.

Columns:

- `snapshot_date`
- `insurer`
- `plan_slug`
- `plan_name`
- `canonical_carrier_name`
- `carrier_mismatch_flags`
- `field_name`
- `field_status`
- `field_value_json`
- `source_url`
- `source_type`
- `scraped_at`
- `last_verified_at`
- `limitations`

The dataset intentionally excludes comparison share IDs, view counts, Telegram data, agent branding, client details, build hooks, bot tokens, and raw brochure PDF bytes.

## Provenance

Rows inherit source URLs and timestamps from public read-only tables:

- `plans`
- `plan_facts`
- `carrier_canonical_names`

Carrier canonicalization uses MAS Financial Institutions Directory Insurance-sector pages and the LIA Singapore member-companies directory. Panel-hospital normalization uses the MOH NEHR participating-institutions dataset on data.gov.sg. Claim and regulatory evidence remains in app tables but is not included in the v1 CSV unless represented as plan facts.

## License

Snapshots are released under [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/).

Suggested citation:

```text
Be-sure-ance contributors, "Be-sure-ance open dataset snapshot", YYYY-MM-DD,
GitHub Actions artifact open-dataset-snapshot, CC-BY-4.0.
```

## Limitations

This is a qualitative research dataset only. It is not financial advice, insurance advice, a quote, a ranking, a recommendation, or a policy transaction.

Verify every row against `source_url`, `source_type`, `scraped_at`, and `last_verified_at` before reuse. Missing or stale facts must remain marked unavailable rather than filled by inference.

## Refresh Cadence

`.github/workflows/publish-open-dataset.yml` runs weekly after the scrape window and can also be run manually. The workflow uploads an artifact; it does not deploy the app and does not write production secrets into the dataset.
