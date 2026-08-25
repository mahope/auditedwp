# DECISION — 25. august 2026 (Iteration 318, nyt mandat)

## Forældet: GAMMEL DECISION (iter. 297)
"Stop building. Focus on removing blocks."

Det var skrevet under "nytænkning"-mandatet. Mads har siden lempet kravet:
- **Penge er det eneste kriterium.** Kedelig er fint.
- **Når blokeret: start noget nyt.**
- **Ventetid er arbejdstid.**

At vente passivt på konti er ikke længere den rigtige strategi.

## Ny DECISION — 25. august 2026

**To spor, parallelt:**

### Spor A: Fjern blokeringer (samme som før)
Fasteste vej til $1 er stadig Mads' 20 min i LS dashboard. Jeg holder
LS-MANUAL.md klar, bygger ikke mere der kræver betalingskonto. Dette spor
handler om at gøre det SÅ let for Mads at sige ja, at der ikke er nogen
grund til at vente.

Blokeringer (EN linje):
- CNAME @/www -> auditedwp.pages.dev (2 domæner)
- 20 min LS manuel setup ELLER LS API key fra Bitwarden
- CWS OAuth credentials (Chrome extension publishing)
- Affiliate signups (Cookiebot/Complianz/iubenda)

### Spor B: Byg distribution på MINE flader (igen i gang)
Mads' mandat: "Marketing og drift er dit ansvar. Alt hvad der foregår på
dine EGNE flader, styrer du selv."

Jeg har ~50 HTML-sider, 31 blog guides, 3 produktlinjer, 139 sitemap-URL'er —
men INGEN samlet trafik-optimeret struktur. Google skal kunne crawle alt,
forstå hvad siden handler om, og sende besøgende til de rigtige sider.

**Jeg bygger:**
1. **/guides/** — en SEO-hub der samler alle guider på tværs af produkter
   (compliance + DevNotify + QuickFormat) i én vertikal. Giver Google én
   stærk side at ranke, i stedet for 50 spredte.
2. **Sitemap-opdatering** — mangler /guides/, /cmp-comparison/, /blog/ hver
   enkelt guide, og nye QuickFormat-sider.
3. **Interne links** mellem produkter — scanner → guides → store → comparison,
   så PageRank flyder og besøgende bliver på sitet.

## Hvorfor det her er rigtigt under pengekriteriet

| Faktor | Vurdering |
|--------|-----------|
| Tid til 1. kunde | Stadig timer efter Mads' LS-opsætning |
| Hvad jeg gør imens | Bygger trafik så der ER besøgende NÅR LS går live |
| Omkostning | 0 kr — alt er statisk HTML på Cloudflare gratis |
| Mål | $0 → $1 hurtigst muligt, derefter $100/md → $1000/md |

## Hvad jeg IKKE gør
- Bygger nye produkter der kræver betalingskonto (spild — rammer samme mur)
- Research-runder uden pengeperspektiv
- Ventetid (Mads sagde: ventetid er arbejdstid)

## Næste step
Byg /guides/ hub. Opdater sitemap. Deploy. Mål: at sitet kan crawles og
indekseres optimalt, så der er et publikum når betaling går live.