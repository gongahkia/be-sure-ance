# Compliance Posture

This is an engineering posture document, not legal advice. Before any public relaunch, get a Singapore fintech/compliance lawyer to review the live product, scraper behavior, database policies, hosting logs, and user-facing copy.

## Scope

`Be-sure-ance` is an IFA pre-meeting research tool for qualitative insurance-plan metadata. It is intended to complement, not replace, regulated quantitative comparison sources such as [compareFIRST](https://www.comparefirst.sg/wap/homeEvent.action), [MoneySense insurance guidance](https://www.moneysense.gov.sg/insurance-basics/), carrier sites, and licensed advisory workflows.

The app must not provide:

- financial advice, insurance advice, legal advice, or medical advice
- quotes, premium estimates, cost projections, or affordability calculations
- suitability rankings, plan recommendations, or claim approval likelihood
- policy purchase, application, payment, or transaction flows
- client data capture, CRM notes, or generated advice records

## PDPA Stance

V1 collects no PII in the application data model.

Current behavior:

- No user accounts or authentication.
- No client data capture, CRM notes, or generated advice records.
- No client names, NRIC/FIN, contact details, health information, financial profile, or meeting notes are stored.
- PDF brief generation accepts up to three selected plan payloads plus optional session-only agent name and MAS representative number, returns a PDF response, and does not persist client or agent details.
- Frontend reads public `plans`, `plan_facts`, and provider-resource data with the Supabase anon key.
- Scrapers write only plan/source metadata with server-side Supabase credentials.
- MAS regulatory-event rows are source-linked and dated; low-confidence carrier matches must be shown as review-needed context, not definitive carrier findings.
- Brochure change-alert rows store source URLs, hashes, timestamps, generated diffs, and alert status only; no subscriber, client, or agent PII is stored.
- Saved comparison links store only selected `insurer` and `plan_slug` references plus aggregate view counts; no client, agent, visitor, account, cookie, IP address, or user-agent data is stored in `comparison_shares`.
- Telegram bot beta responses are read-only plan lookups with no-advice wording. The repository does not persist Telegram chat IDs, usernames, phone numbers, or message text; in-memory rate limiting is the only bot-side abuse control.

Before relaunch:

- Review hosting, analytics, CDN, error-reporting, and server logs for incidental personal data such as IP addresses or user-agent strings.
- Add a privacy notice before adding analytics, saved comparisons, PDF exports with agent/client details, or any form submission.
- Keep any future client-brief export no-PII by default unless a separate PDPA review is completed.
- Document Telegram platform metadata handling before any public bot launch.

Reference: Singapore PDPC describes the PDPA as governing collection, use, and disclosure of personal data while balancing legitimate organisational use and individual protection.

## Error Observability

Sentry is the selected Phase 4 error monitor. It stays disabled unless DSN environment variables are set.

Current behavior:

- Frontend reporting uses `VITE_SENTRY_DSN`, `VITE_SENTRY_ENVIRONMENT`, `VITE_SENTRY_RELEASE`, and `VITE_SENTRY_TRACES_SAMPLE_RATE`.
- Scraper/backend reporting uses `SENTRY_DSN`, `SENTRY_ENVIRONMENT`, `SENTRY_RELEASE`, and `SENTRY_TRACES_SAMPLE_RATE`.
- SDKs are initialized with default PII disabled.
- Event scrubbers redact authorization headers, cookies, Supabase keys, Telegram bot tokens, Sentry DSNs, bearer tokens, service-role JWT-like values, and `sb_secret_*` values before sending.
- Scraper exception context is limited to carrier key, source URL, command context, and sanitized exception metadata.
- `/status` shows aggregate failing-rate and validation state, not raw exception messages.

Before relaunch:

- Confirm Sentry project data residency, retention, team access, and alert recipients.
- Keep DSNs and auth tokens out of committed files and frontend code except the public frontend DSN.
- Review a test event payload before enabling alerts for production traffic.

## MAS FAA Stance

[Inference] Based on current product behavior, the project is intended to stay outside financial-advisory and transaction flows by presenting source-linked qualitative facts only. This is not a legal conclusion.

Current behavior:

- No advice, recommendation, suitability, or ranking engine.
- No quote, premium, deductible, coinsurance, or projected-cost UI.
- PDF briefs contain qualitative facts, provenance, generated timestamps, and a no-advice/no-transaction disclaimer.
- No purchase, lead-generation, application, payment, or referral flow.
- External links point users to compareFIRST and carrier sites for regulated quantitative comparison, official product documents, quotes, or transactions.

Before relaunch:

- Have counsel review whether any UI text, sorting, filtering, PDF export, saved comparison, or future assistant feature could be treated as advice, arranging, recommendation, or inducement.
- Keep the README, app copy, and legal disclaimer aligned with this no-advice stance.
- Do not add affiliate links or carrier-paid placement without a fresh compliance review.

References: the Financial Advisers Act regulates financial advisers and related representatives; MAS states that a company conducting financial advisory services such as advising on or arranging life policies generally requires a financial adviser licence unless exempted.

## Source Traceability

Every user-facing qualitative fact should be traceable to:

- `source_url`
- `source_type`
- `scraped_at`
- `last_verified_at`
- a structured `field_value` status: `known`, `unknown`, `not_found`, or `not_applicable`

Frontend behavior:

- Known facts show provenance metadata.
- Missing or unsourced facts are marked incomplete.
- Stale verification states are shown by the provenance UI.
- External provenance links use safe URL parsing plus `target="_blank"`, `rel="noopener noreferrer"`, and `referrerpolicy="no-referrer"`.

Post-launch qualitative entries require quarterly licensed-advisor or compliance-qualified review as documented in [Post-launch operations cadence](./OPERATIONS.md).

## Scraping Ethics

Operating policy:

- Respect robots.txt and carrier takedown requests.
- Identify automated requests with a project User-Agent and contact email.
- Keep scrape frequency low; scheduled runs are weekly.
- Fetch only public carrier/product resources needed for plan facts and provenance.
- Do not bypass authentication, paywalls, rate limits, CAPTCHAs, or access controls.
- Do not scrape or store client/policyholder personal data.

Current implementation status:

- Weekly GitHub Actions scrape is scheduled for Monday 00:00 SGT.
- Playwright and HTTP scraper paths use `be-sure-ance-bot/1.0 (mailto:gabrielzmong@gmail.com)`.
- Repo-wide robots.txt enforcement is not complete yet. Phase 5/compliance sign-off must verify robots.txt handling consistently before public relaunch.

Reference: RFC 9309 defines the Robots Exclusion Protocol as the mechanism for service owners to control how crawlers access content.

## Takedown Handling

Contact: [gabrielzmong@gmail.com](mailto:gabrielzmong@gmail.com)

Takedown SLA:

- Acknowledge carrier or rights-holder takedown requests within 2 business days.
- Disable the disputed source, plan fact, or brochure object while reviewing if the request is credible.
- Resolve or provide a written status update within 7 calendar days.
- Keep a private audit note of the request, source URL, action taken, and date.

Manual removal procedure: [Takedown and source removal runbook](./TAKEDOWN_RUNBOOK.md).

## Launch Gate

Do not publicly relaunch until:

- `docs/COMPLIANCE.md`, README, and in-app disclaimers are consistent.
- Source provenance is visible for user-facing facts.
- Robots.txt handling and User-Agent behavior are verified.
- No PII collection is introduced without a PDPA review.
- A Singapore fintech/compliance lawyer has reviewed the live behavior.
- The [launch pre-flight runbook](./LAUNCH_PREFLIGHT.md) passes against staging and records compliance sign-off status.
