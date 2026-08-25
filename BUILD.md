# BUILD — Korteste vej til første betalende kunde (25. august 2026)

## Realiteten

5 produkter bygget, testet, live. 0 betalende kunder. Blokeringen er IKKE kode —
det er konti og opsætning der sidder hos Mads.

**Tre parallelle veje, alle kræver lidt af Mads:**

| Vej | Mads' tid | Indtjening | Status |
|-----|-----------|------------|--------|
| A: LS manuel fallback | ~20 min i LS dashboard | $29-$149/tx | ⏳ Klar — venter på Mads |
| B: Affiliate links | ~15 min signup (3 programmer) | 30% recurring på CMP-salg | 🏗️ Side bygget, links mangler IDs |
| C: Polar.sh ny konto | ~10 min signup | $29-$149/tx (4% fee) | 🆕 Alternativ hvis LS ikke virker |

## Vej A: LS manuel fallback (anbefalet — hurtigst)

Mads har ALLEREDE en Lemon Squeezy-konto (`mads@mahope.dk`). Bitwarden blokeringen
stopper kun den automatiserede API-script. Plan B: log ind manuelt i dashboardet.

**Mads skal gøre (20 min):**
1. Gå til https://app.lemonsqueezy.com — log ind
2. Products → New product (6 gange, se LS-MANUAL.md for exact indstillinger)
3. Upload PDF fra `gumroad/products/`, indsæt titel/beskrivelse/pris
4. Publicér → kopier checkout-URL → send til agenten

**Agenten gør:**
- Sætter checkout-URL'er ind i site/store/index.html
- Fjerner waitlist-bannere
- Deployer
- Kører sandbox-testkøb (kort 4242 4242 4242 4242)

**First $1:** Samme time som Mads sender URLs.

## Vej B: Affiliate-links (kører i parallel)

Cookiebot: 30% recurring commission i 12 måneder. Complianz: 30% one-time.
iubenda: op til 40%. Ingen Bitwarden, ingen LS key. Kun Mads' signup.

**Mads skal gøre (15 min):**
1. Tilmeld Cookiebot affiliate: cookiebot.com/us/affiliates/ (PayPal til udbetaling)
2. Tilmeld Complianz affiliate: complianz.io/affiliates/
3. Tilmeld iubenda affiliate: iubenda.com/partners/affiliates

**Agenten gør (allerede klar):**
- CMP comparison page (/cmp-comparison/) — bygget, deployes når IDs er klar
- Affiliate-disclosure på privacy policy — klar til deploy
- Scanner-resultater anbefaler specifik CMP via affiliate-link — backend klar

**First $1:** Indenfor dage efter Mads' signup (første gang nogen scanner, klikker, og køber en CMP).

## Det jeg IKKE gør mere

- Nye produkter indtil vej A eller B har givet revenue
- Flere universality-audits (produkterne er allerede universelle)
- Flere guides, blog posts, eller indhold der kræver trafik
- Nogen som helst kodeændring der ikke handler om at få penge ind

## Måling

- Betalinger: LS dashboard (Vej A) — tjek dagligt
- Affiliate-kommissioner: Cookiebot/Complianz/iubenda dashboards (Vej B)
- Status: $0 indtil en af vejene aktiveres