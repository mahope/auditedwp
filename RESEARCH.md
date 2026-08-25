# RESEARCH — 25. august 2026, divergens med pengelinsen

## Ærlig vurdering: min nuværende beslutning holder IKKE

**Fakta:** 5 produkter er live, 0 kan tage imod penge. Alt er blokeret på LS API key
i Bitwarden (endnu ikke ankommet, 1+ døgn forsinket) + Leanpub-konto (Mads skal
oprette). Selvom idéerne er gode, er ALLE afhængige af Mads' manuelle handling.

Under Mads' regel ("blokeret = start noget nyt") må jeg acceptere:
- Spor A (LS opsætning) — afventer Mads. Én linje i STATUS.md.
- Spor B (Leanpub ebook) — afventer Mads. Én linje i STATUS.md.
- Jeg gentager IKKE blokeringen iteration efter iteration.

**Hvad kan jeg gøre NU uden at vente på nogen?**
- Bygge distribution (npm, web, content) der skaber brugere NU
- Bygge noget der tjener penge VIA en markedsplads jeg selv kan oprette mig på
- Alternativt: forberede produkter så de KAN tjene penge sekundet LS ankommer

---

## Divergens: 30+ idéer vurderet på 5 kriterier

| # | Idé | Kategori | Første betaling | Beløb | Marked | Gentagelse | Leveringsomk. | Dom |
|---|-----|----------|-----------------|-------|--------|-----------|--------------|-----|
| 1 | **npm publish quick-format CLI** | Devtools | ⏳ venter LS | $9 engang | Stort (alle udviklere) | Nej | 0 kr | ✅ NEMT |
| 2 | **VS Code extension (format converter)** | Devtools | ⏳ venter LS/marked | $5-$9 | Meget stort | Nej | 0 kr | ✅ |
| 3 | **ESLint plugin til compliance-regler** | Devtools | ⏳ venter LS | $19/yr | Lille-niche | Ja | 0 kr | ❌ Smalt |
| 4 | **Homebrew tap til quick-format** | Devtools | ⏳ venter LS | $9 | macOS-udviklere | Nej | 0 kr | ✅ |
| 5 | **CLI token/linter (bygget på QF-engine)** | Devtools | ⏳ venter LS | $9-$29 | Mellem | Nej | 0 kr | ⚠️ |
| 6 | **Prettier plugin (JSON/YAML formatter)** | Devtools | ⏳ venter LS | $0/free | Mellem | Nej | 0 kr | ❌ For gratis |
| 7 | **curl-klon med JSON-respons formattering** | Devtools | ⏳ venter LS | $9 | Lille | Nej | 0 kr | ❌ For niche |
| 8 | **Git pre-commit hook (format + lint)** | Devtools | ⏳ venter LS | $5 | Mellem | Nej | 0 kr | ❌ For småt |
| 9 | **Obisidian plugin (format converter)** | Obsidian | ⏳ venter marketplace | $0/free+tip | 100K brugere | Nej | 0 kr | ❌ Gratis |
| 10 | **Raycast extension (quick-format)** | Raycast | ⏳ venter store | $0/free | 50K brugere | Nej | 0 kr | ⚠️ |
| 11 | **Alfred workflow (format converter)** | Alfred | ⏳ venter | $0/free | 30K brugere | Nej | 0 kr | ❌ For småt |
| 12 | **Webflow plugin (compliance checker)** | Webflow | ⏳ venter LS | $29/md | Mellem | Ja | 0 kr | ⚠️ |
| 13 | **Shopify app (compliance scan)** | Shopify | ⏳ venter godkendelse | $19/md | Stort | Ja | 0 kr | ⚠️ Kræver partner |
| 14 | **Wix app (compliance)** | Wix | ⏳ venter | $19/md | Mellem | Ja | 0 kr | ⚠️ |
| 15 | **Chrome extension (DevNotify)** | Browser | ⏳ CWS OAuth | $19/yr | Stort | Ja | 0 kr | ❌ BLOKERET |
| 16 | **Firefox addon (DevNotify)** | Browser | ⏳ venter godkendelse | $19/yr | Mellem | Ja | 0 kr | ⚠️ |
| 17 | **API-tjeneste: format conversion API** | API | ⏳ venter LS | $5/md | Småt | Ja | 0 kr | ⚠️ |
| 18 | **API-tjeneste: compliance check API** | API | ⏳ venter LS | $79/yr | Mellem | Ja | 0 kr | ✅ EKSISTERER |
| 19 | **API-pakke: EUComply scanner som npm modul** | API | ⏳ venter LS | $29/yr | Lille | Ja | 0 kr | ✅ |
| 20 | **Payhip: sælg templates/PDFs** | Marketplace | ❌ kræver bankkonto | $10-$150 | Stort | Nej | 5% fee | ❌ KYC-bloaker |
| 21 | **Etsy: sælg compliance-templates** | Marketplace | ❌ kræver bankkonto | $10-$50 | Stort | Nej | 6.5% fee | ❌ KYC-bloaker |
| 22 | **Sellfy: sælg PDF-guides** | Marketplace | ❌ kræver bankkonto | $10 | Mellem | Nej | 0 kr | ❌ KYC-bloaker |
| 23 | **Ebook på Amazon KDP** | Publishing | ❌ Mads uploader | $4.99-$9.99 | Meget stort | Nej | 0 kr | ❌ Mads-handling |
| 24 | **Ebook på Leanpub** | Publishing | ❌ Mads opretter konto | $14.99 | Mellem | Nej | 0 kr | ❌ Mads-handling |
| 25 | **Ebook på Apple Books** | Publishing | ❌ Mads uploader | $4.99 | Stort | Nej | 0 kr | ❌ Mads-handling |
| 26 | **Freemium web tools → SEO traffic** | Content | ⏳ venter LS (ads/upgrade) | 0 kr nu | Stort | Ja (via LS) | 0 kr | ✅ KAN NU |
| 27 | **YouTube/screencast: dev tutorials** | Content | ❌ kræver Mads-konto | 0- variable | Stort | Ja (annoncer) | 0 kr | ❌ Mads-handling |
| 28 | **Blog + affiliate links** | Content | ❌ kræver payout-konto | 0- variable | Stort | Ja | 0 kr | ❌ KYC-bloaker |
| 29 | **Tauri desktop app (QuickFormat) $9** | Desktop | ⏳ venter LS | $9 | Mellem | Nej | 0 kr | ✅ EKSISTERER |
| 30 | **Electron app (Compliance monitor)** | Desktop | ⏳ venter LS | $49/yr | Lille | Ja | 0 kr | ❌ For småt |
| 31 | **Lemon Squeezy-ready produkter** | **ALLE** | ⏳ venter LS key | $9-$149 | — | Ja/Nej | 0 kr | ✅ KLAR |
| 32 | **GitHub Actions marketplace: format-action** | Actions | ⏳ venter LS | $0/free | Mellem | Nej | 0 kr | ⚠️ |

---

## Kategorisering efter hvad jeg KAN gøre NU (uden Mads)

### Spor 1: Distribution der bygger brugerbase NU (0 kr, 0 Mads-afhængighed)

| # | Handling | Effekt |
|---|----------|--------|
| ✅ | npm publish `quick-format` CLI | Installerbare downloads → brand awareness |
| ✅ | npm publish `eucomply-scanner` CLI | Devs kan køre compliance-scan fra terminal |
| ✅ | Homebrew tap | Mac-brugere: `brew install quick-format` |
| ✅ | Byg flere gratis web tools | SEO traffic, viser produktværdi |
| ✅ | GitHub repository med README + demo | Open source synlighed |

### Spor 2: Produkter der kan tjene penge NÅR LS ankommer (forberedt)

| # | Produkt | Status |
|---|---------|--------|
| ✅ | EUComply Free + Pro ($79/yr) | Live, universel, klar |
| ✅ | QuickFormat ($9 desktop) | Live, Tauri-app bygget, klar |
| ✅ | DevNotify ($19/yr) | Live, Chrome-extension klar |
| ✅ | ComplianceDocs ($29-$149) | Live, klar |
| ✅ | Ebook ($14.99 PDF) | Skrevet, knap klar |
| ✅ | ls-setup-all.sh script | Ét klik → alle 5 produkter kan tage penge |

### Spor 3: Helt nye idéer der kræver 0 Mads (payment via egen markedsplads)

**REALITETSTJEK:** Alle platforme med betalingsformidling kræver KYC (bankkonto,
skatte-ID). Da jeg ikke må oprette konti i Mads' navn, og payout går til hans
bank, kræver ALLE betalingsformidlere hans involvering.

Den eneste undtagelse: **platforme der betaler ud til PayPal-konto** — hvis
Mads har en PayPal-konto, kan payout gå dertil uden at jeg opretter noget i
hans navn. Men jeg skal stadig spørge.

---

## KONKLUSION: Min beslutning holder ikke under pengekriteriet

**Den hårde sandhed:** Jeg kan ikke tjene én krone uden at Mads handler. Alle
6 produkter (5 LS + ebook) er klar til at tage penge, men alle er blokeret på
Mads' konti/nøgler.

**Hvad jeg gør i stedet (ventetid = arbejdstid):**
1. **npm publish** QuickFormat CLI og EUComply scanner CLI — bygger distribution
2. **Homebrew tap** — mac-brugere kan installere med én kommando
3. **Forbedr web tools** — mere SEO-trafik, flere leads
4. **Forbered alt** så det KAN tjene penge sekundet LS ankommer

**Når LS ankommer:** kør ls-setup-all.sh → 5 produkter live → første salg
samme dag.