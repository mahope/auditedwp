# STATUS — Iteration 98 (24. august 2026): Universalitet, email-capture, SEO-sammenligninger, deploy

---

## Punkt 1-vurdering (universalitet) — BESTÅET ✅

Kernen (`shared/scan-engine.js`) tager en vilkårlig URL uden CMS-forudsætninger.
Fire indpakninger: web, API/Worker, CLI, WordPress-plugin. Chrome extension
bygget. Ingen platform-binding. Kodegennemgang bekræftet.

---

## Beslutning revurderet under pengekriteriet — HOLDER ✅

EUComply scorer 5/5 på fire faktorer. LS-nøgle forventes i dag. Beslutningen
holder. I stedet for at vente på LS-nøglen er denne iteration brugt på
distribution: email-capture + SEO-sammenligningssider + blogindlæg.

---

## Gjort denne iteration

| Opgave | Status | Detaljer |
|--------|--------|----------|
| 1. Punkt 1 universalitet — kodegennemgang | ✅ | Ingen CMS-binding i kernen. 4 indpakninger. |
| 2. Email-capture på scanner | ✅ | POST /subscribe endpoint i worker-scan. KV namespace oprettet. Formular i scan-resultater. |
| 3. Sammenligningsside: vs Cookiebot | ✅ | /vs/cookiebot/ — målretter "Cookiebot alternative" (massiv søgetrafik pga. prisstigning) |
| 4. Sammenligningsside: vs Termly | ✅ | /vs/termly/ — compliance scanner vs policy generator |
| 5. Sammenligningsside: vs iubenda | ✅ | /vs/iubenda/ — scanner vs legal document hub |
| 6. Blogindlæg: Cookiebot Alternative 2026 | ✅ | /blog/cookiebot-alternative-2026/ — SEO-indhold |
| 7. Sitemap opdateret | ✅ | + Cookiebot blog, +3 vs-sider. Gamle /pro/vs-* URL'er fjernet |
| 8. Blog index opdateret | ✅ | Cookiebot Alternative post øverst |
| 9. Worker deploy | ✅ | eucomply-scan med SUBSCRIBERS KV |
| 10. Site deploy | ✅ | 6 nye filer, alt verificeret |

---

## Traction (rigtige tal, ikke egne tests)

Rigtige tilmeldinger: **0** · Rigtige scanninger (andre end os): **0** ·
Omsætning: **$0** · Email subscribers: **0** (lige bygget)

---

## Budget

| Post | Status | Beløb |
|------|--------|-------|
| **Brugt** | | **0 kr** |
| Domæne: eucomply.dev | Forhåndsgodkendt, ~$12 | ~90 DKK |
| **Tilbage** | | **~910 kr af 1.000 kr** |

---

## Venter på Mads

| Hvad | Hvorfor | Noter |
|------|---------|-------|
| **Lemon Squeezy API-nøgle** | Opret produkt, CHECKOUT_URL, første betaling | Forventes i Bitwarden 24/8 |
| **Domænekøb: eucomply.dev** | Forhåndsgodkendt, Cloudflare Registrar | ~$12, sættes foran pages.dev |
| **KDP-upload af bogen** | Manuel, ~10 min | /book/ klar |

---

## Næste iteration

1. **LS-nøgle i Bitwarden → produktskabelse via API → CHECKOUT_URL → deploy → test-køb → første betaling**
2. **Domæne: eucomply.dev købes → sættes foran pages.dev → canonical URLs opdateres**
3. **Email capture: hvis vi har subscribers, send en launch notice**
4. **Chrome extension udgiv via Web Store API (når credentials ligger i Bitwarden)**
5. **Blog: fortsæt 1/uge — næste: "NIS2 Compliance Checklist for SaaS"**

---

## Blokeringer

LS-nøglen er den eneste blokering for revenue. Den er noteret i tabellen
ovenfor og gentages ikke herfra.