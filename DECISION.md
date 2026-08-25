# DECISION — 25. august 2026 (Iteration 297, strategisk skift)

## Realiteten

Alle produkter er bygget, testet, udgivet. **Revenue: $0.** Blokeringen er IKKE
kode — det er konti og opsætning der kræver Mads. Jeg har bygget i 27 dage på
noget der ikke kan tage imod penge.

## Nyt strategisk fokus: Distribution over produkt, betaling over kode

**Jeg bygger INTET nyt indtil første betaling.** Fra nu af handler hver iteration
om at fjerne blokeringer og sætte distributionskanaler op — ikke om at skrive mere kode.

### To parallelle veje (begge kræver Mads' tid)

**Vej A — LS manuel fallback (anbefalet, kortest til $1)**
- Mads har allerede LS-konto (`mads@mahope.dk`)
- 20 min i dashboard → 6 produkter oprettet → checkout-URL'er
- Jeg sætter dem ind på site, deployer, sandbox-tester
- Første betaling: **samme time**
- Dokumentation: `LS-MANUAL.md` (klar)

**Vej B — Affiliate-links på scanner (kører i parallel)**
- Cookiebot (30% recurring, 12 mdr), Complianz (30%), iubenda (40%)
- Mads: 15 min signup hos 3 programmer → PayPal til udbetaling
- Jeg: sætter links ind på scanner-resultater + CMP comparison page
- Første kommission: indenfor dage efter signup

### Hvorfor ikke bygge noget nyt

| Forsøgt | Resultat |
|---------|---------|
| 5 produkter bygget | $0 — alle kræver betalingsopsætning |
| 50+ sider compliance-indhold | 0 organisk trafik |
| GitHub open source | 3 stargazers, 0 konverteringer |
| WordPress-plugin | $0 |
| Chrome-extension | Bygget, pakket, kan ikke udgives (CWS OAuth i Bitwarden) |
| Tauri desktop app | Bygget, klar, venter på LS key |

**Enhver ny idé rammer samme mur:** betaling kræver en konto hos en payment
provider, og den konto ejer Mads.

## De 5 pengefaktorer (revurderet for nuværende position)

| Faktor | Vurdering |
|--------|-----------|
| Tid til 1. kunde | **Timer** efter Mads' 20 min i LS dashboard |
| Beløb pr. kunde | $29-$149 (templates) / $79/år (Pro) |
| Markedsstørrelse | 5M+ EU-virksomheder |
| Betalingsvilje | HØJ — lovkrav |
| Driftsomkostning | 0 kr/md |

## Hvad der skal til (til Mads)

**Vælg én af disse og sig til:**
1. "Jeg logger ind på LS og laver produkterne" — 20 min, så er vi i gang
2. "Jeg tilmelder mig Cookiebot/Complianz/iubenda affiliate" — 15 min
3. "Jeg unlocker Bitwarden så du kan bruge LS API'en" — 5 min

Indtil da: $0.