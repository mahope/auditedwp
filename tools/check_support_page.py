#!/usr/bin/env python3
"""Porten skal finde de sider, hele sitet lover, og ikke kun dem der er til.

Projektfasen (24/9) siger det to steder, at hvert site skal have en
`/support`-side med donationslinket, og `.github/FUNDING.yml` skal pege på
samme adresse. Links er dog nemme at love og nemme at glemme: da målingen
blev kørt 29/9 svarede `https://eucomplypro.com/support/` **404**, fordi
siden aldrig var lavet — og ingen side linkede til den, så hverken
link-tjekket eller søgeindekset havde grund til at mærke det.

Denne port er derfor ikke et link-tjek. Den dømmer den modsatte retning:
**en side, hele produktet lover, skal findes** — også når intet i træet
peger på den. Det er den fejl, et link-tjek aldrig kan finde, fordi den
forudsætter en reference der ikke findes.

Krav: Python 3.10+. Se `tools/pyreq.py`.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pyreq

pyreq.require(__file__)

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

DONATION = "https://donate.stripe.com/7sYeVcbn50wieFM8gDbMQ0c"

# Sider hele produktet lover, med den tekst de skal kunne findes på. Hver
# post er (sti, krav), fordi en tom side er heller ikke en side: titel,
# en h1, donationen hvor der loves en, og en inbound reference.
KRAV: list[tuple[str, tuple[str, ...]]] = [
    ("support/", ("<h1", "donate.stripe.com/7sYeVcbn50wieFM8gDbMQ0c",
                  "eucomply-scanner/issues")),
    ("privacy/", ("<h1",)),
    ("terms/", ("<h1",)),
    ("pro/thank-you/", ("<h1",)),
    ("pro/sample-report/", ("<h1",)),
]


def side(rel: str) -> pathlib.Path:
    return SITE / rel.strip("/") / "index.html"


def find(kaver: list[tuple[str, tuple[str, ...]]] = KRAV) -> list[str]:
    """Fundene er pr. krav, ikke pr. fil, så en side der halter, tælles rigtigt."""
    fund: list[str] = []
    for rel, krav in kaver:
        p = side(rel)
        if not p.exists():
            fund.append(f"{rel} findes ikke (lovet side, 404)")
            continue
        html = p.read_text(encoding="utf-8", errors="replace")
        for k in krav:
            if k not in html:
                fund.append(f"{rel} mangler {k!r}")
    # Donationen skal også ligge i footeren, som er den ene sted alle 231
    # sider har. Uden denne tjek kan en skalkørsel slette den globale linje
    # og alle 20 sider der linker direkte, stadig være grønne.
    footer = (SITE / "_partials" / "footer.html")
    if not footer.exists() or DONATION not in footer.read_text(encoding="utf-8"):
        fund.append(f"_partials/footer.html mangler donationslinket {DONATION}")
    # FUNDING.yml er den anden halvdel af samme løfte (fra FUNDING.yml-perspektivet).
    funding = ROOT / ".github" / "FUNDING.yml"
    if not funding.exists() or DONATION not in funding.read_text(encoding="utf-8"):
        fund.append(f".github/FUNDING.yml mangler donationslinket {DONATION}")
    return fund


def _selftest() -> int:
    """Selvporten skal kunne dømme et fejltræ. Uden dette er fundene i
    `find()` lige så stærke som et gæt."""
    fejl = 0
    # 1. En side der mangler helt skal fundes — det er den rigtige fejl, og
    #    den kræver ingen monkeypatch, fordi stien simpelthen ikke findes.
    if not find([("support-kan-ikke-finde/", ("<h1",))]):
        print("SELFTEST RØD — en side der mangler, blev ikke fundet")
        fejl += 1
    # 2. En side der findes, men mangler sit krav, skal også findes. Derfor
    #    peges `side()` midlertidigt på en side med tomt indhold.
    class Tom:
        def exists(self) -> bool:
            return True

        def read_text(self, **_k) -> str:
            return "<html><body>ingenting</body></html>"

    rigtig_side = globals()["side"]
    globals()["side"] = lambda _rel: Tom()
    try:
        if not find([("support/", ("<h1",))]):
            print("SELFTEST RØD — en side uden h1 blev ikke fundet")
            fejl += 1
    finally:
        globals()["side"] = rigtig_side
    # 3. Det virkelige træ skal være grønt.
    rigtige = find()
    if rigtige:
        print("SELFTEST RØD — det virkelige træ har fund:", *rigtige, sep="\n  ")
        fejl += 1
    if fejl:
        return 1
    print("SELFTEST OK — porten finder både en manglende side og en side "
          "uden sit krav, og det virkelige træ er grønt.")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return _selftest()
    fund = find()
    if fund:
        print(f"FUND — {len(fund)} brud på sider, hele produktet lover:")
        for f in fund:
            print(f"  {f}")
        return 1
    print(f"SUPPORT-PORT GRØN — {len(KRAV)} lovede sider findes med deres krav, "
          "og donationen ligger i footeren og i FUNDING.yml.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
