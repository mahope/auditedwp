# DECISION — Iteration 98 (24. august 2026)

**Status:** HOLDER under pengekriteriet. Email-capture bygget + SEO-sammenligningssider
+ Cookiebot-alternative blogindlæg. LS-nøgle er stadig eneste blokering for revenue.

---

## Primært produkt: EUComply — Universal Website Compliance Platform

### Pengekriterie-vurdering (24. august, revideret)

| Faktor | EUComply | Score |
|--------|----------|-------|
| Tid til 1. kunde | Timer efter LS-nøgle i Bitwarden | ⭐⭐⭐⭐⭐ |
| Beløb pr. kunde | $79/år (B2B, impulse-buy niveau) | ⭐⭐⭐⭐ |
| Markedsstørrelse | 25M+ websites, universel kerne | ⭐⭐⭐⭐⭐ |
| Tilbagevendende | Årligt abonnement | ⭐⭐⭐⭐⭐ |
| Omkostning | 0 kr/md — Cloudflare gratis-tier | ⭐⭐⭐⭐⭐ |
| Traction | 0 reelle tilmeldinger, 0 scanninger, $0 | ⭐ |

**Konklusion:** Beslutningen holder. Fem af seks kategorier er top-score.
Traction (0) er et distributionsproblem — denne iteration har adresseret det
med email-capture + SEO-sammenligningssider + Cookiebot-indhold.

### Nye aktiver denne iteration
- ✅ Email-capture: POST /subscribe worker + KV namespace + formular på scan-siden
- ✅ Sammenligningsside: /vs/cookiebot/ — målretter "Cookiebot alternative" (massiv søgetrafik)
- ✅ Sammenligningsside: /vs/termly/ — compliance scanner vs policy generator
- ✅ Sammenligningsside: /vs/iubenda/ — scanner vs legal document hub
- ✅ Blogindlæg: /blog/cookiebot-alternative-2026/ — SEO-indhold
- ✅ Sitemap + blog index opdateret
- ✅ Worker deployet med SUBSCRIBERS KV

### Venter på
- **Lemon Squeezy API-nøgle** i Bitwarden (forventet 24/8)
- **Domæne: eucomply.dev** køb (forhåndsgodkendt, ~$12)

---

## Parallelt spor: Amazon KDP ebook (ikke blokeret på LS)

**Status:** Skrevet, klar til upload. Kræver Mads uploader manuelt på KDP.

---

## Domæne: eucomply.dev

Valgt, ledig, forhåndsgodkendt til køb via Cloudflare Registrar. Koster ~$12/år.
**Sig til:** når Mads godkender, købes domænet og sættes foran pages.dev.

---

## Næste iteration

1. **LS-nøgle:** Samme dag den ligger i Bitwarden — opret produkt via API, deploy CHECKOUT_URL, første betaling
2. **Domæne:** eucomply.dev købes, sættes foran pages.dev
3. **Email capture:** Hvis subscribers findes, send launch notice
4. **Chrome extension:** Udgiv via Web Store API (når credentials ligger i Bitwarden)
5. **Blog:** Fortsæt 1/uge — næste: "NIS2 Compliance Checklist for SaaS"