# Talks

## Draft Proposal

Title: Scraping 28 SG insurer sites without lying to anyone

Format: 15-minute talk.

Audience: civic-tech, public-good engineering, and insurance/fintech builders.

Abstract:

Be-sure-ance began as a scraper-backed Singapore insurance comparison project. The uncomfortable finding was that extracting dollar values from insurer prose with regex made the UI look more certain than the source data was. This talk walks through the decision to remove regex-derived premiums, pivot to qualitative source-traceable metadata, and build maintenance evidence around provenance, validation drift, public health status, and compliance boundaries.

Outline:

1. Original architecture and why it was risky.
2. What regex-derived premiums got wrong.
3. How compareFIRST shaped the product boundary.
4. The source-traceable `plan_facts` model.
5. Scraper drift, validation artifacts, and `/status`.
6. What "public good" means when the honest answer is "unknown".

Demo assets to prepare:

- Panel hospital matrix.
- Plan card with provenance footer.
- Shared comparison with no-advice disclaimer.
- Scraper health dashboard.
- Brochure-version change row.

Status:

- Proposal drafted.
- Slides not created yet.
- No conference submitted yet.
