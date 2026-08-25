# DECISION — 25. august 2026 (Iteration 331)

## Status: Spor B — distribution — er nu bygget færdig. Stadig blokeret på LS.

### Hvad der blev bygget

DECISION's næste step (it. 327) var:
1. Twitter/LinkedIn share-knapper med score ✅ (eksisterede allerede ved it. 330)
2. Social-card / badge-mekanik ✅ (ny i it. 331):
   - OG-image (1200×630): `/images/eucomply-og.png` — mørkt tema med EUComply
     branding, domænefelt, score-chip, compliance-kategorier
   - `og:image` + `twitter:image` på forsiden og /scan/ — delte links viser nu
     et rigt kort i X, LinkedIn, Slack, Messenger, iMessage
   - "Download score card"-knap i scan-resultater: canvas-genereret PNG med
     domæne, ring-score, passed/total — downloades som `{domain}-eucomply-score.png`

### Hvorfor stadig ikke et nyt produkt

Alle 5 produkter (EUComply Free/Pro, QuickFormat, DevNotify, ComplianceDocs,
Chrome Extension) er bygget og klar til betaling. Intet kan tage imod penge før
LS API-nøglen ligger i Bitwarden.

At starte et nyt produkt nu ville bygge oven på den samme blokering — bare en
ny landing page der heller ikke kan sælge noget. Samtidig siger Mads' instruks:
"Gør ét færdigt (virker, udgivet, kan tage imod penge) før du starter det næste."
Indtil LS key kommer, kan intet produkt opfylde "kan tage imod penge".

Derfor: maksimér distributionsværdien af det der allerede er bygget.

### Næste (når LS key ligger i Bitwarden)

1. Opret Produkt (EUComply Pro, $79/yr) på Lemon Squeezy via API
2. Sæt LS checkout URL som Pages secret på /config endpoint
3. Test et køb end-to-end
4. Sæt DevNotify ($19/yr) og QuickFormat ($9) op bag efter
5. Aktivér social distribution (delt scorekort → lead → Pro-konvertering)