# RESEARCH — iteration 53 (24. august 2026)

## Universel-vurdering (24. august, denne iterations hovedopgave)

**Spørgsmål:** Er det bygget bundet til én platform? Skal kernen trækkes ud?

**Metode:** Kildekodelæsning af `worker-scan/index.js` + grep efter platform-afhængigheder
(`wordpress`, `wp-`, `wp_`).

**Fund:**
- Kernen (269 linjer) tager en vilkårlig URL. Ingen CMS-forudsætninger.
- WordPress-nævnes kun i to detektions-signaturer (`wp-content|wp-json|generator`) og én
  consent-API-check — dvs. kernen *genkender* WordPress blandt andre platforme, den er ikke
  afhængig af det. Det er universel detektion, ikke platform-binding.
- Verificeret live tidligere på wordpress.org, wix.com, shopify.com.
- Fire indpakninger findes allerede om samme kerne: web (/scan/), CLI (cli/bin/),
  API (Worker), WP-plugin (plugin/eucomply.php). Pluginet er én indpakning — korrekt arkitektur.

**Konklusion:** Punkt 1 bestået. Intet at trække ud, intet at bygge om.

## Mandatændring 23. august — implementeret og vurderet

- **Nytænkning lempet:** Idéen behøver ikke være original. Kedelig er fint.
- **Eneste kriterium: Tjen penge.** Så mange som muligt, så hurtigt som muligt.
- **Universelt:** Allerede opfyldt — Worker tager enhver URL, verificeret live
- **Flere produkter:** Nu bygget: Product #1 (EUComply scanner) + Product #2 (Compliance Docs Generator)
- **Byg på pages.dev:** Allerede live

## Research: Hurtigste vej til $1 (24. august)

Nøgternt screen: kan jeg finde EN VEJ til indtjening der ikke kræver Mads' konti?

**Svar: Nej.** Alle betalingskanaler kræver en juridisk person (Mads) med payout-konto:
- Gumroad — gratis, 10% + $0,50 pr. salg. Kræver: Mads' email + payout-konto
- Stripe — 2,9% + $0,30 pr. transaktion. Kræver: Mads' personlige/juridiske oplysninger
- npm paid packages — kræver Stripe Connect (samme som Stripe)
- Chrome Web Store paid — kræver $5 + payout-profil
- LemonSqueezy — kræver Mads' oplysninger
- GitHub Sponsors — kræver Stripe Connect

**Konklusion: Ingen vej udenom. Men ét setup (Gumroad) åbner ALLE indtægtsstrømme.**

## Research: Micro SaaS benchmarks (frisk research 24. august)

Kilder: questera.ai, startuptideasdb.com, flowjam.com, indietools.market, dev.to CLI tool guide

### Hvad virker for solo-founders i 2026:
1. **CLI tools på npm** — Freemium. $50/dev/month. Real case: $10K MRR med PostgreSQL migration tool. Ingen UI. Distribution via GitHub + HN.
2. **Browser extensions** — Hurtigste at bygge. Chrome Web Store har 2B+ brugere. $5 engangs-gebyr.
3. **Boring vertical SaaS** — Niche-specifikke værktøjer for uglamourøse brancher. $79-299/md.
4. **Content/SEO** — Gratis trafik gennem guides, tutorials, værktøjer. Langsom opstart, ingen omkostning.

### Hvad virker IKKE:
- AI wrappers (intet moat, nemt at kopiere, ingen betalingsvilje)
- Generiske project managers (kan ikke out-feature Notion/Linear)
- Free-to-have (ingen reel smerte)

### Prisbenchmarks for micro SaaS:
- Median: ~$500/md
- Succesfulde: $5K-$30K/md
- 15% krydser $10K MRR
- $79-$149/md sweet spot for B2B solo

### Fordeling for CLI tools (kilde: dev.to CLI monetization guide):
- Måned 1 (launch): 5-15 salg, $75-300
- Måned 2-3 (organisk dryp): 3-8 salg/md, $45-200/md
- Måned 4-6 (compounding): 10-20 salg/md, $150-500/md
- Real case: $10K MRR på 8 måneder med 40 kunder (5 seats * $50/dev/month)

## Tidligere idéer — genbesøgt under pengekriteriet

| Idé | Vurdering | Dom |
|-----|-----------|:---:|
| EUComply (Product #1) | Bygget, live, universel. 0 kr/md. Eneste blokering: Mads' konti | ✅ Holder |
| ComplianceDocs Generator (Product #2) | Ny, bygget. SEO-trafik driver til betalte templates | ✅ Bygget |
| CLI tool (npm) | Kode klar. Publicering kræver Mads' npm-konto | ⏳ Venter på Mads |
| Chrome extension | Ikke bygget endnu. Kræver $5 + Mads' konto | ⏳ Venter på Mads |
| Alt andet | Kræver byggetid + Mads' konti = længere vej | ❌ Samme flaskehals |

## Noter til næste iteration

- Når Gumroad er oppe: Product #3 (Chrome extension — compliance score badge + link til Pro)
- SEO-strategi: målret "free privacy policy generator", "GDPR compliance scanner", "EAA accessibility statement"
- Marketing: skriv færdige udsendelser, læg klar til Mads