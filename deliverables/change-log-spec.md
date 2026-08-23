# AUDIT CHANGE LOG — FORMAT SPECIFICATION

**ComplianceDocs** · v1.0, August 2026.

One row per operational action, per site. Exported monthly per agency as CSV.

## CSV schema

```
entry_id,date_utc,site,action,object,before,after,operator,source,result,notes
```

| Field | Meaning |
|---|---|
| entry_id | Monotonic ID, e.g. `CL-2026-000123` |
| date_utc | ISO-8601 timestamp of action completion |
| site | Site identifier agreed at onboarding |
| action | `update`\|`patch`\|`backup`\|`restore-test`\|`restore`\|`scan`\|`baseline-audit`\|`access-change` |
| object | What was touched: `core`, `plugin/akismet`, `php`, `full-backup` … |
| before / after | Versions or state (`7.2 → 8.1`, `n/a`) |
| operator | Named account performing the action (never personal accounts) |
| source | `manual` \| `mainwp` \| `scheduled` |
| result | `success` \| `failed-rolled-back` \| `warning` |
| notes | Free text; mandatory for failures and restores |

## Rules

1. Append-only. No edits or deletions; corrections are new rows referencing
   the entry_id.
2. Every restore and every failure MUST have a note explaining cause and
   verification step.
3. Retention: 12 months online, then archived export retained for contract
   term + 12 months.

## Example rows

```
CL-2026-000101,2026-08-04T02:14:52Z,client-a-main,update,plugin/gravityforms,4.4.1,4.5.2,auditedwp-ops,scheduled,success,"post-update form smoke test passed"
CL-2026-000102,2026-08-05T03:00:11Z,client-a-main,backup,full-backup,n/a,n/a,auditedwp-ops,scheduled,success,"files 412MB + db 88MB, sha256 recorded"
CL-2026-000103,2026-08-06T09:41:07Z,client-b-shop,patch,plugin/woocommerce,8.9.0,9.0.1,auditedwp-ops,manual,success,"security release, deployed day 1"
CL-2026-000104,2026-08-12T22:03:44Z,client-a-main,update,plugin/seo-framework,5.0.3,5.1.0,auditedwp-ops,scheduled,failed-rolled-back,"conflict with custom snippet; rolled back, issue filed to agency"
CL-2026-000105,2026-08-15T01:20:33Z,client-a-main,restore-test,full-backup,n/a,verified,auditedwp-ops,manual,success,"staged restore verified against checklist"
```
