# STATUS — Iteration 399 — 28. august 2026

## Universalitetsvurdering — OPFYLT (bekræftet)

Kernen (shared/scan-engine.js + scan-worker) tager en vilkårlig URL og virker uanset CMS.
WordPress er kun én indgang blandt flere. Alle værktøjer (scanner, generatorer, fine
calculator) er platformneutrale, client-side eller Worker-baseret. **Ingen udtrækning nødvendig.**

## Udført denne iteration

1. Cross-linking af gratis-værktøjerne: /gdpr-fine-calculator/ linkede ikke til /tools/
   dokument-generatorerne, og /tools/ nævnte ikke calculator. Tilføjet links begge veje
   (tools intro + footer; calculator further-reading). Deployet og verificeret live.
2. Formålet: interne links er den billigste trafik- og konverteringskanal mens betaling
   venter — hver gratis-bruger ledes videre mod scanneren → Pro.

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
2. eucomplypro.com CNAME — token mangler DNS-edit
3. KDP upload — manuskript færdigt, venter på Mads

## Næste skridt

- Fortsat: flere gratis-værktøjsindgange + cross-linking indtil betaling er aktiv
