# AuditedWP — Agency Onboarding Manual

Internal + agency-facing runbook for delivering white-label WordPress maintenance
with a compliance-grade audit trail. Concierge-MVP version: everything below is
executed manually with existing tooling until scale forces software.

## 0. What the agency bought

- Wholesale WordPress maintenance: €29/site/month (1–25 sites) or €19/site/month
  (26+ sites, 12-month term).
- One-time setup €290: onboarding, DPA/NDA signing, white-label report templates.
- Deliverables they resell: updates, backups, security patches, monitoring,
  next-business-day recovery — plus the **audit log** and optional **quarterly
  compliance narrative** (€99/qtr add-on).

## 1. Onboarding flow (per agency)

Day 0:
1. Kickoff call (30 min): confirm site list, update policy, maintenance windows,
   communication rules (we never contact their clients).
2. Send DPA + NDA for signature (standard templates, e-signature).
3. Grant access: agency creates a dedicated admin user per site
   (`auditedwp-ops`) — never reuse personal accounts. Credentials via shared
   secret manager link, rotated after onboarding.

Days 1–3 (per batch of sites):
4. Baseline audit per site: WP/core/plugin/theme versions, PHP version,
   active plugins list, known vulnerabilities → recorded as row 1 of the
   site's change log.
5. Full backup snapshot (files + DB), restore-tested once, record test result.
6. Agree patch policy: security releases deployed ≤7 days; feature updates in
   monthly windows unless agency opts into immediate.

## 2. Ongoing operations (per site, monthly cycle)

| Task | Cadence | Evidence produced |
|---|---|---|
| Core/plugin/theme updates | Monthly window | Change-log entry: item, old→new version, date, operator |
| Security patches | ≤7 days from release | Same |
| Backups | Weekly (min.) | Backup record incl. size + checksum |
| Restore test | Quarterly | Restore-test record |
| Uptime + integrity monitoring | Continuous | Alert history retained 12 months |
| Malware scan | Weekly | Scan report |

## 3. The audit log (the product's core)

Format per entry (CSV/PDF exportable):
`date | site | action | object | before→after | operator | notes`

Tooling (MVP): MainWP self-hosted on EU VPS generates most entries automatically;
operator appends manual notes. Export monthly per agency, PDF + CSV.

## 4. White-label reporting

Monthly: one email from agency's own address is THEIR job — we supply the raw
report content (branded template provided). Quarterly narrative (if purchased):
plain-language summary — changes made, risks closed, upcoming work — written to be
forwarded verbatim to their client.

## 5. Boundaries (say no early)

- No 24/7 incident response — next-business-day only.
- No content edits, design work, or development — maintenance operations only.
- Non-WP CMS only by explicit engagement.

## 6. Exit (per contract)

Full handover package: latest backups, complete change-history export,
credentials removed, confirmation of deletion within 30 days.
