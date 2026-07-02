# ADR 0001: Remove Regex-Derived Premiums And Cost Projections

## Status

Accepted.

## Context

The original comparison flow attempted to derive premiums, deductibles, coinsurance, and scenario assumptions from insurer narrative text. That created a misleading quantitative surface: source brochures often describe benefits, exclusions, or examples without publishing enough structured premium data to support projections.

The pivot target is IFA pre-meeting research. In that workflow, qualitative source evidence is useful; invented or weakly inferred dollar figures are not. compareFIRST, carrier documents, and licensed advisory workflows remain the proper places for regulated quantitative comparison and advice.

## Decision

Remove runtime premium, deductible, coinsurance, and cost-projection features from scraper and frontend behavior. Keep `plan_comparison_facts` qualitative, with nullable fields for panel size, claim SLA, exclusions, waiting periods, coverage tags, brochure hash, and comparison notes.

No active UI should render premium estimates, suitability rankings, recommendations, or scenario cost projections.

## Rejected Approaches

- Keep the calculator with stronger disclaimers. Rejected because the numbers would still appear precise.
- Scrape premiums opportunistically from mixed carrier pages. Rejected because coverage age, sum assured, underwriting, rider, and campaign context are not consistently represented.
- Hide projections behind an "advanced" toggle. Rejected because it would keep the liability surface alive.

## Consequences

- The product is less attractive as a consumer quote tool.
- The app becomes easier to explain as a qualitative research layer that complements compareFIRST.
- Future quantitative work needs explicit licensed/compliance review, structured source data, and separate approval.
