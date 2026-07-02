# ADR 0005: Use `plan_facts` As Source-Traceable Fact Model

## Status

Accepted.

## Context

Plan cards need more than a flat plan catalog. Qualitative claims must show where they came from, when they were scraped, and when they were last verified. Without this, stale brochure text and parser mistakes look authoritative.

Phase 2 introduced `plan_facts` with one fact per `(insurer, plan_slug, field_name)`, a JSON value envelope, source metadata, and read-only public access.

## Decision

Use `plan_facts` as the canonical fact table for qualitative user-facing metadata. Every displayed fact should preserve `source_url`, `source_type`, `scraped_at`, and `last_verified_at`.

Scrapers and frontend code should use the shared contract in `src/lib/plan_facts_contract.json` for field names, value shapes, and unsupported states.

## Rejected Approaches

- Store all extracted facts as unstructured text blobs. Rejected because UI grouping, provenance display, and test assertions become weak.
- Add many nullable columns to `plans`. Rejected because fact types evolve faster than core plan identity.
- Display inferred facts without a source URL. Rejected because it undermines the source-traceable promise.

## Consequences

- Parsers must emit structured fact envelopes rather than ad hoc strings.
- UI code can render provenance and stale/incomplete states per fact.
- Schema and contract changes need tests because downstream surfaces depend on stable field names.
