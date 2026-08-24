# BUILD — Korteste vej til første betalende kunde

Opdateret: 24. august 2026 (Iteration 267 — strategisk skift til distribution)

## Blokering

**Bitwarden er låst (unauthenticated).** Indeholder LS API key — uden den kan intet produkt tage imod betaling.

## Nuværende fokus: Byg distribution (kan gøres UDEN LS key)

### 1. Open source GitHub repo ✅ (NY — denne iteration)
- `github.com/mahope/eucomply-scanner`
- Standalone Node.js engine + CLI + API docs
- MIT licens — udviklere kan finde, bruge og dele det
- Kanal: GitHub discovery (stjerner, forks, organisk)

### 2. Domæne: eucomplypro.com (foreslået, venter på køb)
- ~$12/år via Cloudflare Registrar
- Sættes foran auditedwp.pages.dev
- Uden et .com-domæne har intet produkt troværdighed

## Når LS key kommer — tidslinje (minutter)

```
Minute 0:  bw unlock → LS API key → curl LS API create product + checkout
Minute 5:  ./scripts/eucomply-flip.sh <checkout-url>
Minute 10: npm publish eucomply-scanner (nu med "Pro" tier)
Minute 15: Test checkout → første kunde
```

## Prissætning (klar, venter på key)

| Produkt | Pris | Model |
|---------|------|-------|
| EUComply Pro | $79/år | Recurring |
| QuickFormat | $9 once | One-time |

## Hvad er bygget og klar

| Komponent | Status |
|-----------|--------|
| Scanner engine (universel, platform-uafhængig) | ✅ Testet, live på Worker |
| Gratis scanning API (REST, CORS-enabled) | ✅ Live |
| Open source GitHub repo | ✅ NY — live |
| CLI (npx eucomply-scanner) | ✅ NY — via GitHub |
| 30+ platform guides (SEO-indhold) | ✅ STOPPET — 0 trafik |
| QuickFormat CLI + web tool | ✅ Bygget, venter |
| Produktside EUComply Pro | ✅ Live |
| Flip-scripts (klar til checkout) | ✅ Klar |

## Distribution der mangler trafik

| Kanal | Status | Næste |
|-------|--------|-------|
| GitHub organisk | 🆕 Lige startet | Tilføj README badges, eksempler |
| npm (når key kommer) | ⏳ Venter | npm publish |
| Domæne (eucomplypro.com) | ⏳ Foreslået | Køb → redirect → SEO |