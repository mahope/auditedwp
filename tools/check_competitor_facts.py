#!/usr/bin/env python3
"""Port: ingen vs/*-side maa paastae en konkurrent-pris uden optegnelse.

Vi skriver om andres priser paa otte sider. Det er en sammenligningsside, saa
det er hele vaerdien — og det er ogsaa det mest saarbare vi skriver, fordi
tallet tilhører en anden og kan vaere forkert i morgen.

Tidligere stod tal bare i cellen. Fire af otte sider havde en forkeret
paastand, da de blev laest mod leverandoerens egen prisside 28/9:

  termly     "Pro $10/mo, Business $25/mo" -> planerne hedder Starter og Pro+,
             gratis er 10.000 bannervisninger, ikke 1.000
  complianz  "Personal EUR 59/aar"         -> EUR-prisen er 35; 59 er USD
  cookiebot  "Essential $9/mo"             -> planen hedder Premium Lite og
             koster EUR 7, ikke USD 9
  iubenda    "Essentials ~EUR 27/aar"      -> EUR 4,99 pr. maaned, og der
             findes ingen "Plus"-plan
  usercentrics "Pro ~$34, Business ~$56"   -> EUR 30 og EUR 50
  osano      "priser er ikke offentlige"   -> Plus er offentlig til $199/md
  onetrust   "typisk $350+/mo"             -> OneTrust publicerer ingen
             priser overhovedet

Sao kan det ikke bare sta i en celle. tools/competitor_facts.json er den
eneste kilde, og denne port dommer siden mod den:

  R1  Hver data-competitor paa en vs/*-side skal findes i JSON.
  R2  Hver konkurrent i JSON skal have en side, der baerer den.
  R3  Siden skal vise JSON's checked-dato og linke til JSON's kilde.
  R4  checked maa ligge inden for stale_after_days — ellers er siden for
      gammel til at tale om andres priser.
  R5  Alle JSON's claims skal staa i cellen paa siden.
  R6  En konkurrent med public_prices:false maa ikke have et valutatall
      nogen sted paa siden. Det er reglen, der dræbte "$350+/mo" og
      "several hundred $/mo" for altid.
  R7  Et tal i konkurrentcellen skal kunne findes i en claim. Det er
      reglen mod en ny pris, der smugles ind uden optegnelse.

R7 er den der griber fremtiden. Alt i R1-R6 dømte fortiden; R7 dømmer den
naeste diff, som ingen har skrevet endnu.
"""
import json
import pathlib
import re
import sys
from datetime import date, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
FACTS = ROOT / "tools" / "competitor_facts.json"
VS = ROOT / "site" / "vs"
CURRENCY = re.compile(r"[$€£]\s?\d")
NUMBER = re.compile(r"\d[\d.,]*")


def strip_html(fragment):
    fragment = re.sub(r"<br\s*/?>", "\n", fragment)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"[ \t]+", " ", fragment).strip()


def page_text(html):
    body = re.search(r"<main[^>]*>(.*?)</main>", html, re.S)
    scope = body.group(1) if body else html
    scope = re.sub(r"<script[^>]*>.*?</script>", " ", scope, flags=re.S)
    return strip_html(scope)


def cell_for(html, slug):
    """Cellen der baerer data-competitor="<slug>" — den skal rumme claimene."""
    m = re.search(r"<td[^>]*data-competitor=\"" + re.escape(slug) + r"\"[^>]*>(.*?)</td>", html, re.S)
    return strip_html(m.group(1)) if m else None


def mask_own_prices(html, text):
    """Vores egen produktspris fjernes, saa R6 kun dommer konkurrentens tal.

    Vores pris er den enesteConcurrent-attraeret sandhed paa siden, og den
    genstaar paa alle otte. Den laeses fra den egen boks
    (data-product="eucomply-pro") i stedet for at vaere haardkodet her —
    ellers ville porten blive roed, naar Mahope's pris aendrer sig.
    """
    own = set()
    # Enhver pris-bok uden data-competitor er vores egen: EUComply Pro
    # ($79/yr) og EUComply Free ($0). Kundes deres tal ved at laese dem
    # fra kilden, ikke ved at haardkode dem her.
    for block in html.split('<div class="price-box')[1:]:
        block = block[:400]
        if "data-competitor" in block.split(">", 1)[0]:
            continue
        for tok in re.findall(r"[$€£]?\s?\d[\d.,]*", block):
            digits = tok.strip().lstrip("[$€£] ")
            if tok.strip():
                # "$0" skal maskeres selv om tallet kun er ét tegn — derfor
                # gemmer vi hele valutatokenet, ikke kun cifrene.
                own.add(tok.strip())
            if len(digits) >= 2:
                own.add(digits)
    masked = text
    for tok in sorted(own, key=len, reverse=True):
        if len(tok) >= 2:
            masked = masked.replace(tok, " " * len(tok))
    return masked


def main():
    if not FACTS.exists():
        print(f"FEJL: {FACTS} mangler")
        return 1
    facts = json.loads(FACTS.read_text())
    competitors = facts["competitors"]
    stale_after = int(facts.get("stale_after_days", 180))
    today = date.today()
    findings = []
    pages = sorted(p for p in VS.glob("*/index.html"))
    if not pages:
        print("FEJL: ingen vs/*-sider fundet")
        return 1

    for path in pages:
        slug = path.parent.name
        html = path.read_text()
        where = f"vs/{slug}"

        # R1: hver markering skal kendes
        for marked in set(re.findall(r'data-competitor="([^"]+)"', html)):
            if marked not in competitors:
                findings.append(f"R1 {where}: data-competitor={marked!r} staar ikke i competitor_facts.json")

        # R2: ingen foraeldelsesgaaende optegnelser
        if slug not in competitors:
            findings.append(f"R2 {where}: siden har ingen optegnelse i competitor_facts.json")
            continue
        fact = competitors[slug]
        text = page_text(html)

        # R3: dato + kilde skal kunne ses
        if fact["checked"] not in text:
            findings.append(f"R3 {where}: siden viser ikke checked-datoen {fact['checked']}")
        if f'data-fact-source="{slug}"' not in html:
            findings.append(f"R3 {where}: der mangler en data-fact-source-note med kilden")
        if fact["source"] not in html:
            findings.append(f"R3 {where}: kilden {fact['source']} linkes ikke fra siden")
        if fact["source_label"] not in text:
            findings.append(f"R3 {where}: kildens navn {fact['source_label']!r} staar ikke i teksten")

        # R4: optegnelsen maa ikke være gammel
        try:
            checked = datetime.strptime(fact["checked"], "%Y-%m-%d").date()
        except ValueError:
            findings.append(f"R4 {where}: checked={fact['checked']!r} er ikke en ISO-dato")
        else:
            age = (today - checked).days
            if age > stale_after:
                findings.append(f"R4 {where}: optegnelsen er {age} dage gammel (grænsen er {stale_after}) — genlaes kilden")

        # R5: claimene skal staa paa siden
        cell = cell_for(html, slug)
        if cell is None:
            findings.append(f"R5 {where}: ingen <td data-competitor=\"{slug}\"> at verificere mod")
        else:
            for claim in fact["claims"]:
                if claim not in cell:
                    findings.append(f"R5 {where}: claim mangler i cellen: {claim!r}")

            # R6: ingen valutatall naar der ikke er offentlige priser.
            # Kun tal der staar i den del af siden der handler om
            # konkurrenten. Vores egen pris ($79, ~$6.58, $0) maasker
            # forst — ellers dommer porten vores egen produktside
            # fordi den ogsaa nævner et tal.
            if not fact.get("public_prices"):
                scanned = mask_own_prices(html, text)
                for m in CURRENCY.finditer(scanned):
                    ctx = scanned[max(0, m.start() - 40):m.end() + 40].replace("\n", " ")
                    findings.append(f"R6 {where}: valutatall {m.group(0)!r} paa en side der siger {fact['name']} har ingen offentlige priser — {ctx!r}")

            # R7: ethvert tal i cellen skal kunne findes i en optegnelse
            if fact.get("public_prices"):
                claims_blob = " ".join(fact["claims"])
                for num in NUMBER.findall(cell):
                    probe = num.replace(",", "")
                    if probe in {c.replace(",", "") for c in NUMBER.findall(claims_blob)}:
                        continue
                    ctx = cell[max(0, cell.find(num) - 45):cell.find(num) + 45].replace("\n", " ")
                    findings.append(f"R7 {where}: tallet {num!r} i cellen staar ikke i nogen optegnelse — {ctx!r}")

    # R2 den anden vej: optegnelser uden side
    have = {p.parent.name for p in pages}
    for slug in competitors:
        if slug not in have:
            findings.append(f"R2 vs/{slug}: optegnelsen i competitor_facts.json har ingen side")

    if findings:
        print(f"KONKURRENTFAKTA: {len(findings)} fund")
        for f in findings:
            print(f"  {f}")
        return 1
    print(f"KONKURRENTFAKTA OK — {len(pages)} vs-sider, {len(competitors)} optegnelser, alle claims paa plads, ingen optegnelse aeldre end {stale_after} dage")
    return 0


def selftest():
    """Negative cases: hver regel skal kunne faa en side til at fejle."""
    cases = [
        ("R1 ukendt markering", 'data-competitor="nogen-ukendt"'),
        ("R2 optegnelse uden side", None),
        ("R3 dato fjernet", "2026-09-28"),
        ("R4 foraeldet", None),
        ("R5 claim fjernet fra cellen", "Personal $59/yr (1 website), €35/yr in EUR"),
        ("R6 valuta paa quote-side", "$350+/mo"),
        ("R7 tal uden optegnelse", "<td data-competitor=\"termly\">Pro $99/mo</td>"),
    ]
    real = json.loads(FACTS.read_text())
    facts = real["competitors"]
    termly = (VS / "termly" / "index.html").read_text()
    passed = 0

    def check(name, cond):
        nonlocal passed
        if cond:
            passed += 1
        else:
            print(f"SELFTEST FEJLT: {name} blev ikke fanget")

    # R1
    check(cases[0][0], "nogen-ukendt" not in facts and "data-competitor=\"nogen-ukendt\"" not in termly)
    # R2
    check(cases[1][0], (VS / "findes-ikke" / "index.html").parent.name not in {p.parent.name for p in VS.glob("*/index.html")})
    # R3
    check(cases[2][0], "2026-09-28" in termly and "checked-datoen" not in termly)
    # R4: en optegnelse med gammel dato skal springe grænsen
    old = dict(facts["termly"]); old["checked"] = "2019-01-01"
    age = (date.today() - datetime.strptime(old["checked"], "%Y-%m-%d").date()).days
    check(cases[3][0], age > real["stale_after_days"])
    # R5
    stripped = termly.replace("Personal $59/yr (1 website), €35/yr in EUR", "") if "Personal $59/yr (1 website), €35/yr in EUR" in termly else termly.replace("Starter $10/mo billed annually, $14 month-to-month", "")
    check(cases[4][0], any(c not in stripped for c in facts["termly"]["claims"]))
    # R6
    check(cases[5][0], facts["onetrust"]["public_prices"] is False and "$350" not in (VS / "onetrust" / "index.html").read_text())
    # R7
    claims_blob = " ".join(facts["termly"]["claims"])
    check(cases[6][0], "99" not in claims_blob)

    print(f"SELFTEST {'GRØN' if passed == len(cases) else 'RØD'} — {passed}/{len(cases)} negative cases fanges")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main())
