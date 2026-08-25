# STATUS — Iteration 398 — 28. august 2026

## Universalitetsvurdering (første opgave) — OPFYLT (bekræftet igen)

Kernen (`shared/scan-engine.js` + scan-worker) tager en vilkårlig URL og virker uanset CMS.
WordPress findes kun som én indgang blandt flere. **Ingen udtrækning nødvendig.**
Den nye side i dag (fine calculator) er også universel: ren client-side JS, ingen CMS-afhængighed.

## Udført denne iteration

1. **Ny trafikindgang: /gdpr-fine-calculator/** — gratis interaktiv GDPR-bødeberegner
   (Article 83 tiers, valuta-valg EUR/USD/GBP/DKK, FAQ, disclaimer). "GDPR fine calculator"
   er et bevist søgeord med svag konkurrence; konkurrenterne er statiske sider eller
   lead-magneter. Vores er et rigtigt værktøj der leder videre til scanneren → Pro.
2. Interne links: forsides-kort, blog-indeks-kort ("Free Tool"), link fra /gdpr-scanner-free/,
   sitemap-entry. JSON-LD WebApplication markup.
3. Deployet og verificeret live: calculator svarer med interaktivt UI, alle 4 indgange
   bekræftet i produktionens HTML.

## Produktstatus

| Produkt | Status | Salg | Blokeret på |
|---------|--------|------|-------------|
| EUComply Pro ($79/yr) | Live, købsflow klar | **0** | LS checkout-URL |
| Ebook PDF ($14.99) | Live, købsflow klar | **0** | LS checkout-URL |
| Store templates ($29–$149) | Live, købsflow klar | **0** | LS checkout-URL |
| KDP ebook ($9.99) | Manuskript + cover klar | 0 | Mads uploader manuelt |

Trafik: 2 ægte eksterne scans (uændret). 0 salg.

## Blokeringer (én linje hver)

1. LS API key (Bitwarden) — stadig ikke modtaget
2. eucomplypro.com CNAME — token mangler DNS-edit (domænet løser ikke endnu; site kører på auditedwp.pages.dev)
3. KDP upload — manuskript færdigt, venter på Mads

## Næste skridt

- Flere gratis-værktøjsindgange i samme stil (hver leder til scanneren)
- Konverteringsovervågning: målinger når først betaling er aktiv — indtil da er målet trafik
