# BUILD — Korteste vej til første betalende kunde

**Dato:** 2026-08-25
**Status:** Pro monitoring bygget og live. Mangler Gumroad.

---

## Status: Koden er klar. Mangler ÉN ting: en konto der kan tage imod penge.

**Pro daily monitoring:** ✅ Bygget, deployet, verifikationstestet
- `eucomply-watch` Worker med cron 06:00 UTC
- 30-day score history i KV
- Public status endpoint: `GET /status?url=`
- Email alerts (kode klar, kræver Resend key)

**/pro/ sales page:** ✅ Live med demo-integration
- Live monitoring preview trækker fra watch Worker
- FAQPage structured data
- Gumroad integration kode klar (mangler produkt-URL)

---

## Mads' eneste handling: Opret Gumroad (2 min)

| Trin | Handling | Tid | Hvem |
|------|----------|-----|------|
| 1 | https://gumroad.com → "Start selling" | 30s | Mads |
| 2 | Email + password | 30s | Mads |
| 3 | Opret "EUComply Pro" $79/yr | 30s | Mads |
| 4 | Send mig produkt-linket | 10s | Mads |
| 5 | Jeg sætter linket ind, test køb | 10 min | Mig |
| **6** | **FØRSTE SALG muligt** | — | Begge |

**Pengene akkumuleres i Gumroad.** Payout-info kan tilføjes senere.

---

## Når Mads har oprettet Gumroad

1. Jeg sætter `GUMROAD_PRODUCT_URL` i site/pro/index.html
2. Fjerner "⏳ Join the waitlist" — Buy knappen sender til checkout
3. Tilføjer Gumroad Overlay JS (inline checkout)
4. Egen testkøb for 79¢ (Gumroad tillatter test-transaktioner)
5. Klar til rigtige kunder

---

## Bygget indtil videre

| Funktion | Bygget | Deployet | Live | Klar til kunder |
|----------|--------|----------|------|----------------|
| Universal scan engine | ✅ | ✅ | ✅ | ✅ |
| Daily monitoring (cron) | ✅ | ✅ | ✅ | ❌ (mangler checkout) |
| Pro sales page | ✅ | ✅ | ✅ | ❌ (mangler checkout) |
| Compliance scanner | ✅ | ✅ | ✅ | ✅ |
| Docs generator | ✅ | ✅ | ✅ | ✅ |
| Compliance badge | ✅ | ✅ | ✅ | ✅ |
| CLI tool | ✅ | ❌ | ❌ | ❌ (mangler npm) |
| Chrome extension | ✅ | ❌ | ❌ | ❌ (mangler CWS) |