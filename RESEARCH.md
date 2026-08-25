# RESEARCH — 26. august 2026 — Pivot

## Status: Pivot gennemført

**Konklusion:** EUComply scanner er blokeret på LS key (Bitwarden). Siden iteration ~372 (5+ iterationer) har jeg rapporteret den samme blokering. Mads siger: "Er du blokeret, start noget NYT." Og: "Gentag aldrig den samme blokering."

Jeg har valgt at starte et **helt nyt produkt** i et andet territorium: developer tools.

## Hvorfor Regex Tester

| Kriterie | Vurdering |
|----------|-----------|
| Hvor hurtigt første kunde betaler? | ⏳ Gratis nu. Pro ($2/mo) når LS key kommer. Dag 1 når LS åbner |
| Hvor stort beløb? | $2/mo eller $19/år — modest, men høj volume (udviklere) |
| Hvor mange kunder realistisk? | SEO-drevet. "regex tester" har høj søgevolume. 1000 brugere/måned → 1% konvertering = 10 Pro × $19 = $190/år |
| Tilbagevendende indtægt? | Ja — Pro abonnement. Men lavt beløb pr. kunde |
| Hvad koster det at levere? | $0 — 100% client-side, ingen server |

**Styrken:** Ingen afhængigheder overhovedet. 0 kr at drive. Ingen konti, ingen keys, ingen permissions. Bare en HTML-fil på Cloudflare Pages.

**Svage punkt:** Lavt beløb pr. kunde. Skal have VOLUME for at tjene noget. Men det er OK — produktet koster 0 at drive, så selv $5/måned i samlet indtægt er profit.

## Hvad jeg droppede og hvorfor

| Idé | Grund til drop |
|-----|----------------|
| Fortsat SEO-content til EUComply | Blokeret på betaling. Flere scanninger = 0 kr. |
| Chrome extension | Blokeret på CWS credentials (Bitwarden) |
| Desktop app (Tauri) | Kræver betaling for at sælge. Blokeret på LS key |
| QuickFormat lancering | Blokeret på LS key |
| Nyt SaaS-produkt | Alle kræver payment processor = blokeret på LS key |
| Betalt annonce | Budgetudgift, kræver Mads' godkendelse + betaling |

## Markedsanalyse (hurtig)

Regex101.com: ~5M visits/month, ~14 år gammel. Dominant. Men: reklamer, tracking, ingen betalte features.

Regexr.com: ~500K visits/month. Free, donation-drevet. 

Plads til en **ren, lynhurtig, privat** alternativ — især blandt udviklere der værdsætter privacy og performance. Pro-lock-in: gemte mønstre + deling + API (når LS kommer).

## Strategi

1. Byg regex tester (✅ denne iteration)
2. SEO-indhold: "How to write better regex" / "Regex cheat sheet" blog posts
3. Submit sitemap til Google/Search Console når Mads åbner
4. Når LS key kommer: aktiver Pro tier ($2/mo / $19/yr)
5. Byg linkbuilding: open source alternativ til regex101