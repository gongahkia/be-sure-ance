# Launch Outreach Drafts

Status: drafts ready. Do not post yet: wait until production URL, staging pre-flight, search-indexing pre-flight, and compliance sign-off are complete.

Live URL placeholder: `<LIVE_URL>`.

Feedback channels to monitor after any post:

- GitHub Issues for bug reports and stale-source reports.
- Takedown contact: `gabrielzmong@gmail.com`.
- Source-owner or carrier requests under `docs/TAKEDOWN_RUNBOOK.md`.
- Platform comments or replies for each outreach post for at least 7 calendar days.
- Owner until delegated: Gabriel Ong.

## Guardrails

- Do not claim financial advice, insurance advice, quotes, recommendations, rankings, premium estimates, or cost projections.
- Do not claim all Singapore carriers are supported. Current scheduled support is 19 carriers; other scrapers remain experimental opt-in.
- Do not claim production analytics, alert dispatch, Google/Bing indexing, OGP integration, Postman, FormSG, or Go.gov.sg integration unless those statuses are separately verified.
- Do not post to communities that disallow self-promotion or require moderator approval.
- Prefer feedback requests over launch announcements.

Sources checked on 2026-07-07:

- Seedly guidelines apply to user-generated discussions, comments, replies, reviews, and opinions: https://seedlysg.zendesk.com/hc/en-gb/articles/38628154878105-Seedly-Guidelines-Overview
- Reddit's legacy self-promotion page says it is no longer updated and points to Reddit Help, so subreddit rules and moderator approval must be checked immediately before posting: https://www.reddit.com/r/reddit.com/wiki/selfpromotion/ and https://support.reddithelp.com/hc/en-us
- Show HN is for something people can try and discuss: https://news.ycombinator.com/showhn.html

## Readiness Matrix

| Channel | Draft status | Publish gate | Monitoring gate |
| :-- | :-- | :-- | :-- |
| Seedly | Ready, unposted | Recheck Seedly rules, production URL, search-indexing pre-flight, compliance sign-off | Watch replies and GitHub Issues for 7 calendar days |
| SG IFA Telegram/WhatsApp | Ready, unposted | Ask group admins, production URL, compliance sign-off, no client data | Watch group replies for 7 calendar days |
| Reddit | Ready, unposted | Recheck target subreddit sidebar/wiki, message mods if unclear, production URL, no vote requests | Watch thread replies and domain mentions for 7 calendar days |
| Show HN | Ready, unposted | Live app must be usable without a signup wall; do not ask for votes | Watch HN thread replies for 7 calendar days |
| MAS/OGP/GovTech | Ready, unsent | Production URL, compliance sign-off, search indexing, public docs | Track email replies and follow-up action items |

## Seedly Draft

Channel: Seedly community discussion.

Precondition: production URL works, compliance sign-off is recorded, and the post complies with current Seedly rules.

Draft:

```text
I built a small public-good insurance research tool for pre-meeting fact checks: <LIVE_URL>

The most useful view is the panel-hospital matrix. It tries to make source-linked qualitative facts easier to check before an adviser or consumer goes back to the carrier brochure, compareFIRST, or a licensed advisory workflow.

What it does:
- shows plan-level qualitative metadata such as panel/network clues, exclusions, waiting-period text, claim-process text, regulatory-event context, and brochure provenance
- links facts back to public carrier, MOH, LIA, or MAS sources where available
- marks missing or unsupported facts instead of guessing

Limitations:
- not financial advice, insurance advice, a quote, a recommendation, a ranking, or a purchase path
- no premium estimates or cost projections
- 19 scheduled carriers only; other scrapers are experimental and not part of the public scheduled set
- source data can be stale or incomplete, so every fact still needs verification against carrier documents and compareFIRST where applicable

I’m mainly looking for feedback on whether the panel-hospital workflow is useful and where the source/limitation wording is unclear.
```

## SG IFA Telegram/WhatsApp Draft

Channel: private IFA Telegram or WhatsApp group.

Precondition: ask group admins before posting.

Draft:

```text
Hi all, I’m looking for low-key feedback on a pre-meeting research tool: <LIVE_URL>

The PDF brief feature lets you select up to 3 plans and export a short qualitative brief with source-linked facts and no client data persisted. It is meant for internal fact checking before using carrier docs, compareFIRST, and your licensed advisory process.

Current scope:
- qualitative facts only: panel clues, exclusions, waiting periods, claim process text, brochure provenance, and related source links
- no advice, recommendation, suitability ranking, premium estimate, quote, or purchase flow
- no client names, NRICs, contact details, health profile, or policyholder data
- 19 scheduled carriers; unsupported or uncertain fields are shown as incomplete instead of inferred

Feedback I’m looking for:
- is the PDF brief format useful before a client meeting?
- which limitation/source labels are confusing?
- which facts should be suppressed unless verified manually?

Please treat it as a research prototype, not a production advisory system.
```

## Reddit Open Dataset Draft

Candidate communities: only subreddits where self-promotion and civic/open-data posts are allowed. Check rules and message mods first when unclear.

Draft:

```text
Title: I made an open CSV snapshot of source-linked qualitative Singapore insurance plan metadata

I built Be-sure-ance as a public-good research project after removing regex-derived premiums/cost projections that made the old version look more certain than the sources were.

The open dataset snapshot exports qualitative plan facts, source URLs, and verification dates: <LIVE_URL>

What is included:
- plan-level qualitative metadata where source-linked facts exist
- carrier/source URLs and verification dates
- fields for unknown, not found, unsupported, or stale facts

What is not included:
- no financial advice or insurance advice
- no quotes, recommendations, suitability rankings, premium estimates, deductibles, coinsurance, or projected-cost fields
- no client, policyholder, account, payment, or health-profile data
- no claim that all Singapore carriers are supported

The intended use is civic-tech/data-quality feedback: are the source links and limitation states clear enough to audit?
```

## Show HN Draft

Precondition: the live app must be usable because Show HN is for something people can try.

Draft:

```text
Title: Show HN: Be-sure-ance - source-linked qualitative metadata for SG insurance plan research

I built this after ripping out regex-derived premiums and cost projections from an older insurance scraper. The current version deliberately avoids advice, quotes, rankings, and price-like comparisons.

What you can try:
- browse source-linked qualitative plan facts
- compare panel-hospital clues
- open the public scraper health page
- inspect generated static plan pages and sitemap
- export a no-client-data qualitative PDF brief

What it is not:
- not financial advice or insurance advice
- not a quote or recommendation engine
- not a complete carrier database
- not a substitute for compareFIRST, carrier brochures, or licensed advisory workflows

I’m interested in feedback on the architecture and whether the provenance/unknown-state model makes the data safer to inspect.
```

## MAS/OGP/GovTech Note Draft

Precondition: production URL, compliance sign-off, search indexing, and public docs are complete.

Draft:

```text
Subject: Low-key feedback request: source-linked qualitative insurance plan metadata prototype

Hi,

I’m sharing a small public-good prototype for feedback: <LIVE_URL>

Be-sure-ance is an open-source pre-meeting research tool for source-linked qualitative metadata on Singapore insurance plans. It is intentionally not an advice, recommendation, quote, ranking, or purchase tool. It complements regulated references such as compareFIRST by making plan-level source provenance, missing facts, scraper health, and stale-source states more visible.

Relevant docs:
- Compliance posture: <LIVE_URL_OR_REPO_DOC>
- Open dataset snapshot: <LIVE_URL_OR_REPO_DOC>
- Takedown/source-removal contact: gabrielzmong@gmail.com

I’m not asking for endorsement. I’m looking for feedback on whether the data-source boundaries, no-advice framing, takedown path, and public-good positioning are clear enough.

Regards,
Gabriel Ong
```

## Do Not Post Yet

Current blockers:

- `https://be-sure-ance.netlify.app` returns HTTP 404.
- Google/Bing sitemap submission is not done.
- Compliance sign-off is not obtained.
- Search-indexing and staging pre-flight evidence has not passed against a live production URL.
