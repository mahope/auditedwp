# STATUS — Iteration 402 — 28. august 2026

## Universalitetsvurdering — OPFYLT (punkt 1)

DeskUptime-kernen (src/engine.js + checkers/) tager en vilkårlig URL og virker uanset
CMS/stack. Re-verificeret denne iteration med live CLI-kørsel: example.com → 200 OK,
81ms, SSL 63 dage, content-hash. CLI, watch mode og den fremtidige Tauri-app er alle
indpakninger omkring samme kerne. Intet WordPress-afhængigt i produktet.

## Ærlig datarensning (vigtig)

Kontrollerede venteliste-KV'en direkte mod Cloudflare: de 2 "tilmeldinger" var begge mine
egne smoke-tests (`probe@mahope.dk` iter.364, `smoke@test.invalid`). **Begge er nu slettet.
Det rigtige tal er 0 tilmeldinger på tværs af alle produkter.** /stats-scans var allerede
renset for testdomæner. Siden viser nu kun sociale beviser når tallet er >0.

## Udført denne iteration

| # | Task | Status |
|---|------|--------|
| 1 | Universalitetsvurdering skrevet — DeskUptime opfylder punkt 1 (live-test som bevis) | ✅ |
| 2 | KV-databasen renset for egne smoke-tests — ventelistetæller = 0 (ægte tal) | ✅ |
| 3 | /deskuptime/ Pro-boks koblet på ægte waitlist-worker (POST + live count). Placeholder-Mailchimp-formular med `u=PLACEHOLDER&id=PLACEHOLDER` fjernet — den gav en død formular | ✅ |
| 4 | Samme boks tjekker worker `/config` hvert load: sættes `CHECKOUT_URLS=deskuptime:<url>` på scan-workeren, erstattes formularen automatisk af et rigtigt Buy-knappen | ✅ |
| 5 | Navlink "Monitor" tilføjet på /scan/, /pro/ og /book/ (kun forsiden havde det før) | ✅ |
| 6 | Deployet til auditedwp.pages.dev; alle 5 testsider 200, nyt indhold verificeret i live HTML; commitet + pushet | ✅ |

## Produktstatus

| Produkt | Status | Salg | Tilmeldinger (ægte) | Blokeret på |
|---------|--------|------|---------------------|-------------|
| DeskUptime Pro ($19) | Engine + CLI + watch færdig. Checkout auto-on når key kommer | **0** | 0 | LS API key |
| EUComply Pro ($79/yr) | Live, aflivet som fokus | 0 | 0 | — |
| KDP ebook ($9.99) | Manuskript færdigt | 0 | — | Mads uploader manuelt |

Trafik: 0 målte rigtige besøgende.

## Blokeringer (én linje hver)

1. LS API key i Bitwarden — stadig ikke modtaget (alt betaling er bygget klar rundt om den)

## Næste skridt

1. GitHub release workflow: build + upload CLI-binaries til mahope/deskuptime releases
2. SEO-indholdsside til lancering ("free uptime monitoring tool" vinkel)
3. Tauri desktop app når release-flowet står
4. Når LS key kommer: opret DeskUptime-produkt i LS → sæt `CHECKOUT_URLS=deskuptime:<url>` via wrangler → betaling live uden ny deploy
