# Post-Launch Operations Cadence

Current state: cadence is ready, but public launch is still blocked until deployment, pre-flight, indexing, and compliance sign-off complete.

Owner: Gabriel Ong Zhe Mian.

Primary contact: `gabrielzmong@gmail.com`.

First scheduled review: [#99 Weekly scraper health review - 2026-07-14](https://github.com/gongahkia/be-sure-ance/issues/99).

## Weekly Scraper Health Review

Open a `Weekly scraper health review` issue from the GitHub issue form.

Evidence to inspect:

- `/status` public scraper health dashboard
- latest `refresh-static-data` GitHub Actions run and Netlify deploy log
- latest `validate-scraper-snapshots` artifact
- latest `publish-open-dataset` artifact
- Sentry frontend and scraper projects if DSNs are configured

Checklist:

1. Confirm every scheduled carrier is `supported` or intentionally `unsupported`.
2. Confirm `last_success_at`, `last_failure_at`, `row_count`, and `validation_status` are current on `/status`.
3. Open validation artifacts for failed, error, or no-baseline carriers.
4. Confirm public `/status` hides raw exceptions and secret-like values.
5. Confirm the open dataset artifact exists and does not include client, agent, share-link, or secret-like fields.
6. File follow-up issues for stale, failing, unsupported, or validation-failed carriers.

First health review can be performed from existing dashboards/artifacts after launch because `/status`, refresh workflow logs, validation artifacts, open dataset artifacts, and optional Sentry hooks are already defined.

## Monthly Brochure Alert And Dataset Review

Open a `Monthly brochure and dataset review` issue from the GitHub issue form.

Checklist:

1. Review `brochure_change_alerts` rows with `pending`, `sent`, or `suppressed` status.
2. Suppress alerts that are duplicate, source-owner disputed, unsupported, or not source-material changes.
3. Confirm no subscriber, client, agent, account, payment, or health-profile PII exists in brochure alert rows.
4. Review the latest open dataset CSV summary: row count, carriers represented, fields present, source URL coverage, and verification-date coverage.
5. Compare dataset caveats with README and `docs/COMPLIANCE.md`.
6. Record a short monthly summary in the issue.

Do not dispatch public brochure alerts until recipients, consent, unsubscribe, and privacy handling are separately reviewed.

## Quarterly Licensed-Advisor Review

Open a `Quarterly licensed-advisor review` issue from the GitHub issue form.

Reviewer requirement:

- A Singapore-licensed financial adviser or compliance-qualified reviewer must review a representative sample of qualitative entries before the project treats those entries as launch-quality.

Minimum sample:

- at least 3 scheduled carriers
- at least 2 plans per sampled carrier where data exists
- panel hospital facts
- exclusions and waiting-period facts
- claim-process facts
- brochure metadata and source links
- any MAS/LIA regulatory or canonicalization context shown for sampled carriers

Review questions:

1. Does any copy read like advice, ranking, suitability, quote, or inducement?
2. Are unknown, unsupported, stale, and source-missing facts clear enough?
3. Are source URLs and verification dates sufficient for manual review?
4. Should any qualitative field be hidden until manually verified?
5. Are PDF brief and share-link disclaimers clear enough?

Record only status, date, reviewer role, and non-private action items in GitHub. Keep private legal, compliance, or adviser notes outside the repository.

## Takedown And Stale-Data Response

Owner: Gabriel Ong Zhe Mian.

Contact: `gabrielzmong@gmail.com`.

SLA:

- Acknowledge credible carrier, source-owner, rights-holder, regulator, or stale-data requests within 2 business days.
- Suppress disputed source rows, plan facts, brochure objects, dataset rows, or alerts while reviewing if the request is credible.
- Resolve or provide written status within 7 calendar days.

Procedure: use `docs/TAKEDOWN_RUNBOOK.md`.

## Incident Triggers

Open an incident issue or private incident record if any of these occur:

- frontend exposes a server-side secret or service-role credential
- `/status` or artifacts expose raw exception payloads, request headers, tokens, or PII
- a scraper bypasses access controls, paywalls, CAPTCHA, robots.txt, or source-owner restrictions
- a source owner disputes stored brochure or plan facts
- a user reports advice-like, ranking-like, quote-like, or misleading copy
- backup, dataset, or validation artifacts fail for two consecutive scheduled runs

## Reminder Templates

GitHub issue forms exist for:

- weekly scraper health review
- monthly brochure and dataset review
- quarterly licensed-advisor review

Use issue forms instead of ad hoc notes so every review records the same evidence.
