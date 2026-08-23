# BUILD — DevNotify: korteste vej til første betalende kunde

Opdateret 26. august 2026.

## Produktet
macOS menu bar app (Tauri v2), bygget og kompileret: `devnotify/src-tauri/target/release/bundle/macos/DevNotify.app` + DMG.
$19 lifetime license via Lemon Squeezy (MoR — håndterer moms). Brugeren giver sin egen GitHub PAT; app'en er 100% lokal.

## Universel kerne
Kernen er en **notifications-klient**: GitHub REST API → normaliseret notifikationsliste → UI + polling. GitHub-integrationen er én adapter. Senere indpakninger: GitLab, Linear, Jira adapters mod samme UI/kerne.

## Vejen til første betaling (rækkefølge)

| # | Skridt | Status | Blokering |
|---|--------|--------|-----------|
| 1 | Landingsside der sælger (hvad/hvem/pris/køb) | ✅ Bygget denne iteration | — |
| 2 | DMG uploades som release-asset på GitHub (offentligt repo i mit eget navn er ikke muligt — se blokering) | ⏳ | Venter: repo skal oprettes i Mads' GitHub eller direkte download fra sitet |
| 3 | Lemon Squeezy: opret produkt $19 + license key via API | ⏳ | LS API-nøgle i Bitwarden (app kører, låst) |
| 4 | App'en validerer license key mod LS API (gratis trial 7 dage uden key) | ✅ Trial implementeret i binær (iter. 114); remote LS-validering venter nøgle | — |
| 5 | Checkout-knap på landingsside → LS checkout URL | 🔶 Midlertidigt: buy-knap åbner notify-me-formular (iter. 118) — e-mails samles op i Worker-KV, sendes ved launch | Samme nøgle |
| 6 | Notify-me-liste live (worker `/subscribe`, test-adresse-afvisning, privacy.html opdateret) | ✅ Iteration 118 | — |

## Priser
- $19 lifetime, én licens pr. bruger.
- Gratis: 7 dages trial fuld funktionalitet.
- Ingen abonnement før der er betalende kunder.

## Distribution (uden app store)
Direkte download af DMG fra landingssiden. Ikke-notarized DMG kræver højreklik → Open første gang; det står i FAQ. Notarization ($99/år Apple Developer) er en fremtidig udgift — beder IKKE om den nu; først når der er revenue.

## Marketing (mine egne flader, ingen henvendelser)
- SEO-tekst på landingssiden ("github notifications mac menubar")
- Sitemap + robots.txt
- Product Hunt / Reddit-posts skrevet FÆRDIGE og lagt i POSTS/, venter på Mads' ja

## Definition of "færdigt nok til at tjene penge"
Landingsside live + DMG downloadbar + LS-checkout aktiv = kan tage imod penge.
