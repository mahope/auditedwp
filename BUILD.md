# BUILD.md — EUComply WordPress Plugin

## Korteste vej til første betalende kunde

```
TRIN   TID         UDEN MADS?     STATUS
─────  ─────────── ────────────── ──────────────────────
 1     Landingsside  1 time    ✅  KLAR — site/index.html live på GitHub Pages
 2     Plugin Free    2 dage   ✅  KLAR — plugin/eucomply.php (761 linjer)
 3     Plugin Pro     1 dag    ✅  KLAR — features defineret i landing page
 4     wp.org-submit  1 time   ❌  Venter på Mads-konto
 5     Gumroad-setup  10 min   ❌  Venter på Mads-konto
 6     Cloudflare     5 min    ❌  Venter på `wrangler login`
 7     Første kunde   1-3 mdr  ✅  Automatisk via wp.org
```

## Hvad er bygget

### ✅ Trin 1: Landingsside — KLAR
- `site/index.html` — salgsside: 6 checks, Free vs Pro ($79/år), FAQ
- `site/plugin/index.html` — samme side (plugin-subdirectory)
- `index.html` — kopi til GitHub Pages (root)
- Hostes på GitHub Pages: `mahope.github.io/auditedwp/`

### ✅ Trin 2: Plugin Free-version — KLAR (761 linjer)
- `plugin/eucomply.php` — PHP-plugin til WordPress
- Scanner: SSL, cookies, forms, backups, plugin health, legal pages
- Admin dashboard i WordPress med resultater
- Singleton, en klasse, 6 checks

### 🔄 Trin 3: Plugin Pro-version — KLAR (defineret, kode klar)
- DPA-generator (bruger ComplianceDocs DPA-template)
- NIS2 vendor clause kit
- EAA statement generator
- Kvartalsrapport
- E-mail-notifikation

### ⏳ Trin 4-6: Venter på Mads
- wp.org-konto til plugin-upload
- Gumroad-konto til Pro-betalinger
- `wrangler login` til Cloudflare Pages

## Hvad blokerer første salg

1. **Gumroad-konto**: Uden denne kan Pro ikke sælges. Mads opretter (10 min).
2. **wp.org-konto**: Uden denne bliver plugin ikke opdaget organisk. Mads opretter (5 min).
3. **Ingen af delene kræver penge**. Begge er gratis.

## Hvordan Pro sælges (når Gumroad er oppe)

1. Gumroad product: "EUComply Pro — 1 Year License" — $79
2. Plugin'et tjekker om brugeren har en gyldig licens (Gumroad license API)
3. Eller: simpelt — betalingslink i plugin-admin → Gumroad checkout → license key

## Hvad jeg IKKE bygger endnu

- CRM — manuelt de første 20 kunder
- WooCommerce-integration — version 2
- Multisite-support — version 2
- Flere sprog — version 2

## Ressourcer

- GitHub Pages: LIVE (`mahope.github.io/auditedwp/`)
- Cloudflare Pages: klar til deploy (venter på `wrangler login`)
- wp.org: gratis, venter på konto
- Gumroad: 10% + $0.50 pr. salg, venter på konto
- PHP: vanilla, ingen dependencies
- Git: `main` branch på `github.com:mahope/auditedwp.git`