# ADR 0007: Defer OGP Tooling Integrations

## Status

Accepted - defer implementation.

## Context

Issue #64 asks whether to integrate OGP/GovTech tools for three workflows:

- Postman.gov.sg for brochure-change email alerts.
- FormSG for stale-data reports.
- Go.gov.sg for shared comparison links.

Current official references checked on 2026-07-02:

- Postman v1 Email API overview: https://postman-v1.guides.gov.sg/email-api-guide/overview
- Postman v1 Programmatic Email API: https://postman-v1.guides.gov.sg/email-api-guide/programmatic-email-api
- Postman v1 Programmatic Email API FAQ: https://postman-v1.guides.gov.sg/email-api-guide/frequently-asked-questions
- FormSG guide: https://guide.form.gov.sg/
- FormSG access FAQ: https://guide.form.gov.sg/faq/faq/access
- FormSG webhooks: https://guide.form.gov.sg/user-guides/advanced-guide/webhooks
- GoGovSG guide: https://guide.go.gov.sg/
- GoGovSG API docs: https://guide.go.gov.sg/developer-guide/api-documentation
- GoGovSG terms: https://guide.go.gov.sg/legal/termsofuse

## Tool Decisions

| Candidate | Decision | Access / blocker | Build condition |
| :-- | :-- | :-- | :-- |
| Postman.gov.sg brochure-change email alerts | Defer | Postman says it is not onboarding new programmatic email API users. Email sending is government-agency oriented and existing API use requires an API key. | Restart only with agency sponsorship or confirmed Postman onboarding access for this project. |
| FormSG stale-data reports | Defer | FormSG says only government agencies and approved organisations by Ministries can create forms. Webhooks require Storage Mode, an internet HTTPS endpoint, SDK-based verification/decryption, and duplicate-safe retry handling. | Restart only when a sponsoring agency or approved organisation owns the form and confirms webhook use. |
| Go.gov.sg shared-comparison short links | Defer | Go.gov.sg is intended for Singapore public sector agency use; public officers with government email can create links. API use requires a bearer token and HTTPS requests. | Restart only when an authorised public-sector owner provides a token and governance for link ownership. |

## Decision

Defer all three integrations. No code, configuration, production copy, or README badge should imply that Be-sure-ance currently sends Postman alerts, receives FormSG stale-data reports, or creates Go.gov.sg short links.

Rationale:

- The current project is not owned by a Singapore public sector agency.
- Access is not confirmed for any candidate.
- Adding fake connectors or optional environment variables would make the README look more mature than the deployed capability.
- Each integration would add governance, credential, audit, and incident-response obligations beyond the Phase 4 portfolio baseline.

## Follow-up Issues

No implementation issues are created while access is unconfirmed.

Create follow-up issues only after the matching build condition is satisfied:

- Postman: implement brochure-change alert dispatcher with opt-in recipients, delivery-status logging, unsubscribe/consent handling, and no-PII defaults.
- FormSG: implement stale-data intake webhook with SDK verification/decryption, duplicate-safe storage, triage status, and takedown/escalation workflow.
- Go.gov.sg: implement optional server-side short-link creation for `/share?plans=<refs>` URLs with token rotation, rate limiting, idempotency, and fallback to canonical URLs.

## Consequences

- Phase 4 can truthfully show that OGP tooling was evaluated.
- README stays conservative and does not promise unconfirmed integrations.
- Future sponsored work has clear restart conditions instead of speculative scaffolding.
