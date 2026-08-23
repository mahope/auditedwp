# DATA PROCESSING AGREEMENT (DPA)
## AuditedWP — White-label WordPress Maintenance Operations

Template v1.0 — 2026-08-23. To be reviewed by counsel before first signature.
Structure follows EU GDPR Art. 28 requirements. Placeholders in [BRACKETS].

## Parties

- **Controller:** [AGENCY LEGAL NAME], [address], [CVR/registration no.] ("Agency")
- **Processor:** AuditedWP / [OPERATOR LEGAL ENTITY], Denmark ("Processor")

## 1. Subject matter

Processor provides WordPress maintenance operations (updates, backups, security
patching, monitoring, recovery) on websites designated by Agency, including
storage of operational data and backups within the European Union, per the
Onboarding Manual referenced as Annex A.

## 2. Categories of data subjects and data

- Data subjects: visitors of Agency's client websites (only incidentally,
  e.g. in backups/content), and admin users of those sites.
- Data categories: website content contained in backups (files + database),
  admin credentials (held via secret manager, rotated), technical logs,
  change-log metadata (timestamps, versions, operator identity).

## 3. Processor obligations

3.1 Processing only on documented instruction from Agency (this Agreement +
    Onboarding Manual), unless required by EU/member-state law.
3.2 All persons authorized to process are bound by confidentiality.
3.3 Security measures: encryption in transit (TLS) and at rest for backups;
    access limited to named operators; credential rotation after onboarding;
    weekly malware scans; quarterly restore tests. Evidence retained in the
    audit log for 12 months.
3.4 Sub-processors: hosting provider [EU PROVIDER NAME] and secret-manager
    provider [PROVIDER]. Current list at signing; Agency notified ≥30 days
    before any addition, may object on reasonable grounds.
3.5 Assistance with data-subject requests and DPIAs within 5 business days.
3.6 Deletion or return of all personal data within 30 days of termination;
    confirmation in writing (per Onboarding Manual §6).
3.7 Audit support: Agency may inspect audit-log exports and evidence annually
    and upon material incident.
3.8 Notification of personal-data breach to Agency without undue delay and
    no later than 48 hours after awareness.

## 4. Transfers

All processing and storage takes place within the EU/EEA. No transfers to
third countries. Backups replicated only within EU regions.

## 5. Liability and term

Liability as agreed in the Master Services Terms. Term follows the service
subscription; survives until deletion confirmed under clause 3.6.

## Annex A — Onboarding Manual (current version)
## Annex B — Sub-processor list (at signature)
