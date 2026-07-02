# Why We Ripped Out Regex-Derived Premiums

Status: draft, unpublished.

## Summary

Be-sure-ance started as a Singapore insurance comparison scraper. The early version tried to infer premiums, deductibles, coinsurance, and scenario costs from carrier page text.

That was the wrong product.

Insurance cost figures are regulated, contextual, and easy to misread. A regex can recognize something that looks like `S$500` or `10%`, but it cannot reliably know whether that number is a premium, deductible, sub-limit, promotional claim, footnote, example, age-band value, or stale brochure fragment. Showing derived numbers next to plan names made the UI look more authoritative than the source extraction deserved.

The pivot was to remove the misleading quant layer and keep the part that can be made honest: source-traceable qualitative metadata for IFA pre-meeting research.

## What Broke

The old approach had three failure modes:

- Context loss: page text mixed premiums, claim examples, benefit limits, and unrelated marketing numbers.
- False precision: dollar and percent values looked exact even when they were inferred from narrative text.
- Compliance risk: a projected cost table can be read as advice, ranking, or suitability support.

The result was a liability surface, not a useful civic tool.

## What Changed

The project removed regex-derived premium and cost-sharing logic and deleted the scenario calculator UI.

The data model moved toward:

- `plans`: the plan catalog.
- `plan_facts`: source-linked qualitative facts with `source_url`, `source_type`, `scraped_at`, and `last_verified_at`.
- `brochure_version_history`: hash history for source brochures.
- `brochure_change_alerts`: reviewable change events.
- `scraper_health`: freshness, failure, and validation status.

The frontend now frames comparisons around coverage signals, panel/network facts, exclusions, process fields, brochure provenance, claims evidence, and regulatory context.

## Why compareFIRST Still Matters

compareFIRST remains the reference point for regulated quantitative life-insurance comparison in Singapore. Be-sure-ance should not duplicate or blur that role.

The useful gap is narrower:

- Which source was checked?
- When was it checked?
- Which brochure changed?
- Which panel/network text exists?
- Which entries are stale, incomplete, or unsupported?

That is pre-meeting research support. It is not a recommendation engine.

## Engineering Lessons

1. Do not extract numbers just because they are easy to match.
2. A scraper field should carry provenance or stay out of the UI.
3. The UI must expose uncertainty instead of hiding it.
4. Public-good positioning is weaker when the implementation overclaims.
5. Deleting a feature can be the most important product decision.

## Current Limits

The pivot does not make the project production-ready by itself.

Known limits:

- Some scrapers remain experimental and opt-in only.
- Automated accessibility and validation checks do not replace manual review.
- Brochure parsing can miss or misclassify facts.
- MAS/LIA/civic-source matching can need human review.
- No public relaunch should happen before Phase 5 and compliance review.

## Closing

The better portfolio story is not "we scraped insurance prices."

It is: "we found a place where automated extraction could mislead people, removed that surface, and rebuilt around source traceability, limitation disclosure, and maintenance evidence."

That is less flashy. It is also more defensible.
