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

Before relaunch:

- Review hosting, analytics, CDN, error-reporting, and server logs for incidental personal data such as IP addresses or user-agent strings.
- Add a privacy notice before adding analytics, saved comparisons, PDF exports with agent/client details, or any form submission.
- Keep any future client-brief export no-PII by default unless a separate PDPA review is completed.

Reference: Singapore PDPC describes the PDPA as governing collection, use, and disclosure of personal data while balancing legitimate organisational use and individual protection.

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
- Repo-wide robots.txt enforcement is not complete yet. Public relaunch is blocked until scraper hardening verifies robots handling consistently.

Reference: RFC 9309 defines the Robots Exclusion Protocol as the mechanism for service owners to control how crawlers access content.

## Takedown Handling

Contact: [gabrielzmong@gmail.com](mailto:gabrielzmong@gmail.com)

Takedown SLA:

- Acknowledge carrier or rights-holder takedown requests within 2 business days.
- Disable the disputed source, plan fact, or brochure object while reviewing if the request is credible.
- Resolve or provide a written status update within 7 calendar days.
- Keep a private audit note of the request, source URL, action taken, and date.

## Launch Gate

Do not publicly relaunch until:

- `docs/COMPLIANCE.md`, README, and in-app disclaimers are consistent.
- Source provenance is visible for user-facing facts.
- Robots.txt handling and User-Agent behavior are verified.
- No PII collection is introduced without a PDPA review.
- A Singapore fintech/compliance lawyer has reviewed the live behavior.
