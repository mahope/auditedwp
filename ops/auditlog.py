#!/usr/bin/env python3
"""
AuditedWP — audit trail pipeline (delivery layer).

Records maintenance operations against WordPress sites and produces a
revision-ready change log per site (JSONL source of truth + HTML report).

Design goals (per DECISION.md):
- Every entry: timestamped, attributable, before/after versions.
- Exportable as HTML (PDF-ready print stylesheet) per site per period.
- Zero external dependencies beyond Python stdlib. Runs on the operator's
  machine or a cron box; data stays in EU-controlled storage.

Usage:
  auditlog.py init SITE_ID
  auditlog.py record SITE_ID --op update --target akismet --from 5.3.2 --to 5.3.3 --operator agent-01 [--notes "..."]
  auditlog.py record SITE_ID --op backup --target full --to s3://eu-bucket/site-x/2026-08-24.sql.gz --operator agent-01 --verified
  auditlog.py record SITE_ID --op restore --target db --from backup-2026-08-20 --operator mads --notes "post-update failure rollback"
  auditlog.py list SITE_ID
  auditlog.py report SITE_ID [--month YYYY-MM] [--out FILE.html]

Ops vocabulary (fixed, so reports stay comparable):
  update | patch | backup | restore | scan | config | onboard
"""

import argparse
import datetime as dt
import html
import json
import os
import sys

DATA_DIR = os.environ.get("AUDITEDWP_DATA", os.path.join(os.path.dirname(__file__), "data"))

OPS = {"update", "patch", "backup", "restore", "scan", "config", "onboard"}


def site_path(site_id):
    return os.path.join(DATA_DIR, f"{site_id}.jsonl")


def now_iso():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def cmd_init(args):
    p = site_path(args.site)
    if os.path.exists(p):
        sys.exit(f"error: site '{args.site}' already exists ({p})")
    os.makedirs(DATA_DIR, exist_ok=True)
    genesis = {
        "ts": now_iso(),
        "site": args.site,
        "op": "onboard",
        "target": "baseline",
        "from": None,
        "to": None,
        "operator": args.operator,
        "verified": True,
        "notes": "Audit trail opened; baseline recorded.",
    }
    with open(p, "w") as f:
        f.write(json.dumps(genesis) + "\n")
    print(f"initialized {p}")


def cmd_record(args):
    if args.op not in OPS:
        sys.exit(f"error: op must be one of {sorted(OPS)}")
    entry = {
        "ts": now_iso(),
        "site": args.site,
        "op": args.op,
        "target": args.target,
        "from": args.frm,
        "to": args.to,
        "operator": args.operator,
        "verified": args.verified,
        "notes": args.notes or "",
    }
    p = site_path(args.site)
    if not os.path.exists(p):
        sys.exit(f"error: unknown site '{args.site}' — run 'init {args.site}' first")
    with open(p, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"recorded: {entry['ts']} [{args.op}] {args.target} "
          f"{args.frm or '-'} -> {args.to or '-'} by {args.operator}")


def load_entries(site_id):
    p = site_path(site_id)
    if not os.path.exists(p):
        sys.exit(f"error: unknown site '{site_id}'")
    entries = []
    with open(p) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def cmd_list(args):
    entries = load_entries(args.site)
    for e in entries[-int(args.limit):]:
        v = "OK " if e.get("verified") else "--"
        print(f"{e['ts']} [{e['op']:8}] {v} {e['target']:24} "
              f"{str(e['from'] or '-'):>12} -> {str(e['to'] or '-'):<16} by {e['operator']}")
    print(f"\n{len(entries)} total entries for {args.site}")


REPORT_TMPL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Change log — {site} — {period}</title>
<style>
  body{{font-family:-apple-system,"Segoe UI",Roboto,sans-serif;color:#101828;margin:40px auto;max-width:900px;padding:0 24px}}
  h1{{font-size:26px;letter-spacing:-.02em}} .meta{{color:#475467;font-size:14px;margin-bottom:28px}}
  table{{width:100%;border-collapse:collapse;font-size:13.5px}}
  th,td{{text-align:left;padding:9px 10px;border-bottom:1px solid #e4e7ec;vertical-align:top}}
  th{{background:#f9fafb;font-size:11.5px;text-transform:uppercase;letter-spacing:.05em;color:#475467}}
  .ok{{color:#067647;font-weight:700}} .no{{color:#b54708}}
  .sum{{background:#f9fafb;border:1px solid #e4e7ec;border-radius:8px;padding:14px 18px;margin-bottom:24px;font-size:14px}}
  @media print{{body{{margin:10mm}} a{{text-decoration:none;color:inherit}}}}
</style>
</head>
<body>
<h1>Maintenance change log</h1>
<p class="meta">Site: <strong>{site}</strong> &nbsp;·&nbsp; Period: <strong>{period}</strong> &nbsp;·&nbsp;
Generated: {generated} UTC &nbsp;·&nbsp; Operator of record: AuditedWP (white-label)</p>
<div class="sum">{summary}</div>
<table>
<tr><th>Timestamp (UTC)</th><th>Operation</th><th>Target</th><th>From</th><th>To</th><th>Verified</th><th>Operator</th><th>Notes</th></tr>
{rows}
</table>
<p style="margin-top:28px;font-size:12.5px;color:#475467">This document is an immutable export of the operational change log.
Each row is timestamped and attributable. Suitable as evidence for DORA Art. 28 vendor reviews,
NIS2 supply-chain documentation and insurer questionnaires.</p>
</body></html>"""


def cmd_report(args):
    entries = load_entries(args.site)
    period = args.month or dt.date.today().strftime("%Y-%m")
    sel = [e for e in entries if e["ts"].startswith(period)]
    if not sel:
        sys.exit(f"error: no entries in {period} for {args.site}")

    counts = {}
    for e in sel:
        counts[e["op"]] = counts.get(e["op"], 0) + 1
    verified_n = sum(1 for e in sel if e.get("verified"))
    summary = (f"<strong>{len(sel)} operations</strong> this period: "
               + ", ".join(f"{v}× {k}" for k, v in sorted(counts.items()))
               + f". Verified: <span class='ok'>{verified_n}/{len(sel)}</span>.")

    rows = []
    for e in sel:
        v = "<span class='ok'>✔ yes</span>" if e.get("verified") else "<span class='no'>— no</span>"
        rows.append(
            "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td><b>{}</b></td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                html.escape(e["ts"]), html.escape(e["op"]), html.escape(str(e["target"])),
                html.escape(str(e["from"] or "—")), html.escape(str(e["to"] or "—")),
                v, html.escape(e["operator"]), html.escape(e.get("notes", ""))))
    out = args.out or os.path.join(os.path.dirname(__file__), "reports",
                                   f"{args.site}-{period}.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        f.write(REPORT_TMPL.format(site=html.escape(args.site), period=period,
                                   generated=now_iso(), summary=summary,
                                   rows="\n".join(rows)))
    print(f"report written: {out}")


def main():
    ap = argparse.ArgumentParser(description="AuditedWP audit trail pipeline")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init"); s.add_argument("site"); s.add_argument("--operator", default="agent-01")
    s.set_defaults(fn=cmd_init)

    r = sub.add_parser("record"); r.add_argument("site"); r.add_argument("--op", required=True)
    r.add_argument("--target", required=True); r.add_argument("--from", dest="frm")
    r.add_argument("--to"); r.add_argument("--operator", required=True)
    r.add_argument("--notes"); r.add_argument("--verified", action="store_true")
    r.set_defaults(fn=cmd_record)

    l = sub.add_parser("list"); l.add_argument("site"); l.add_argument("--limit", default="50")
    l.set_defaults(fn=cmd_list)

    p = sub.add_parser("report"); p.add_argument("site"); p.add_argument("--month"); p.add_argument("--out")
    p.set_defaults(fn=cmd_report)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
