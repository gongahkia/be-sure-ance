# ADR 0002: Use A Single `plans` Table Over Per-Insurer Tables

## Status

Accepted.

## Context

The earlier schema used one table per insurer. That made reads fan out across many tables, made frontend loading harder to reason about, and pushed schema drift into every carrier integration.

The Phase 1 data model introduced `public.plans` with `(insurer, plan_slug)` as the stable lookup pair. Per-insurer tables are left only as legacy migration inputs for one migration window.

## Decision

Use `public.plans` as the canonical plan catalog. The generated static app data exports that shape into one public JSON path. Store carrier identity in the `insurer` column and keep `plan_slug` stable per carrier.

Writes remain service-role only. Public clients receive read-only access through RLS and explicit grants.

## Rejected Approaches

- Keep per-insurer tables and add frontend caching. Rejected because schema drift and multi-query loading remain.
- Add a view over per-insurer tables only. Rejected because it keeps the old write model and migration complexity.
- Move plan search to an external index before normalizing storage. Rejected because it adds infrastructure before the base model is coherent.

## Consequences

- Frontend code can load and group plans from one table.
- Scrapers need to write normalized rows with an explicit `insurer`.
- Legacy table cleanup still needs a later migration once no reader or rollback depends on them.
