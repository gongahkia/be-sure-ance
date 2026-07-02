# Takedown And Source Removal Runbook

Contact: `gabrielzmong@gmail.com`.

## Intake

Accept requests from:

- carrier representatives
- rights holders
- regulators
- source-site owners
- affected users reporting stale or unsafe public data

Record privately outside the repository:

- requestor name and organisation
- contact channel
- date received
- source URL or plan identifier
- requested action
- evidence supplied
- action taken

Do not commit requestor PII or private correspondence.

## SLA

- Acknowledge credible requests within 2 business days.
- Disable disputed source rows, plan facts, brochure objects, or alerts while reviewing if the request is credible.
- Resolve or provide written status within 7 calendar days.

## Removal Procedure

1. Identify affected rows in `plans`, `plan_facts`, `plan_comparison_facts`, `brochure_version_history`, `brochure_change_alerts`, `specialist_resources`, and derived open dataset artifacts.
2. Prefer suppression or correction over hard deletion when auditability matters.
3. If deleting, use service-role credentials only from a private local shell or approved GitHub Actions workflow.
4. Remove affected brochure objects from private storage when rights or source-owner concerns require it.
5. Rebuild dependent summaries such as comparison facts, open dataset snapshots, and status notes.
6. Add a private incident note with date, source URL, action, and reviewer.

## Scraping Ethics Checklist

- Use `be-sure-ance-bot/1.0 (mailto:gabrielzmong@gmail.com)` as the User-Agent.
- Respect robots.txt and carrier takedown requests.
- Keep scheduled scraping weekly unless a source owner approves more frequent checks.
- Do not bypass authentication, paywalls, CAPTCHAs, rate limits, or access controls.
- Do not scrape client, policyholder, payment, account, or health-profile data.
- Mark unsupported carriers as unsupported instead of forcing extraction from unstable or restricted pages.

## Public Communication

If a public correction is needed:

- State what source or field changed.
- Avoid naming private requestors unless they gave explicit consent.
- Do not disclose secrets, database URLs, private storage keys, or personal data.
- Keep no-advice language intact.
